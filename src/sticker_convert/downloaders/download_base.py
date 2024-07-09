#!/usr/bin/env python3
from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, List, Optional, Tuple

import anyio
import requests

from sticker_convert.job_option import CredOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn


class DownloadBase:
    def __init__(
        self,
        url: str,
        out_dir: Path,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> None:
        self.url = url
        self.out_dir = out_dir
        self.opt_cred = opt_cred
        self.cb = cb
        self.cb_return = cb_return

    def download_multiple_files(
        self, targets: List[Tuple[str, Path]], retries: int = 3, **kwargs: Any
    ) -> None:
        anyio.run(
            partial(self.download_multiple_files_async, targets, retries, **kwargs)
        )

    async def download_multiple_files_async(
        self, targets: List[Tuple[str, Path]], retries: int = 3, **kwargs: Any
    ) -> None:
        # targets format: [(url1, dest2), (url2, dest2), ...]
        self.cb.put(
            ("bar", None, {"set_progress_mode": "determinate", "steps": len(targets)})
        )

        async with anyio.create_task_group() as tg:
            for url, dest in targets:
                tg.start_soon(self.download_file_async, url, dest, retries, **kwargs)

    async def download_file_async(
        self,
        url: str,
        dest: Path,
        retries: int = 3,
        **kwargs: Any,
    ) -> None:
        for retry in range(retries):
            try:
                response = requests.get(url, allow_redirects=True, **kwargs)

                if not response.ok:
                    self.cb.put("update_bar")
                    raise requests.exceptions.RequestException(
                        f"Error {response.status_code}"
                    )

                self.cb.put(f"Downloading {url}")
                with open(dest, "wb+") as f:
                    f.write(response.content)
                self.cb.put(f"Downloaded {url}")
                break

            except requests.exceptions.RequestException as e:
                self.cb.put(
                    f"Cannot download {url} (tried {retry+1}/{retries} times): {e}"
                )

        self.cb.put("update_bar")

    def download_file(
        self,
        url: str,
        dest: Optional[Path] = None,
        retries: int = 3,
        show_progress: bool = True,
        **kwargs: Any,
    ) -> bytes:
        result = b""
        chunk_size = 102400

        for retry in range(retries):
            try:
                response = requests.get(
                    url, stream=True, allow_redirects=True, **kwargs
                )
                if not response.ok:
                    return b""
                total_length = int(response.headers.get("content-length"))  # type: ignore

                self.cb.put(f"Downloading {url}")

                if show_progress:
                    steps = (total_length / chunk_size) + 1
                    self.cb.put(
                        (
                            "bar",
                            None,
                            {"set_progress_mode": "determinate", "steps": int(steps)},
                        )
                    )

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        result += chunk
                        if show_progress:
                            self.cb.put("update_bar")

                break
            except requests.exceptions.RequestException as e:
                self.cb.put(
                    f"Cannot download {url} (tried {retry+1}/{retries} times): {e}"
                )

        if not result:
            return b""
        if dest:
            with open(dest, "wb+") as f:
                f.write(result)
            self.cb.put(f"Downloaded {url}")
            return b""
        return result
