#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from queue import Queue
from typing import Optional, Union, Any

import requests

from sticker_convert.job_option import CredOption
from sticker_convert.utils.callback import Callback, CallbackReturn


class DownloadBase:
    def __init__(
        self,
        url: str,
        out_dir: Path,
        opt_cred: Optional[CredOption],
        cb: Union[
            Queue[
                Union[
                    tuple[str, Optional[tuple[str]], Optional[dict[str, Any]]],
                    str,
                    None,
                ]
            ],
            Callback,
        ],
        cb_return: CallbackReturn,
    ):
        self.url: str = url
        self.out_dir: Path = out_dir
        self.opt_cred: Optional[CredOption] = opt_cred
        self.cb: Union[
            Queue[
                Union[
                    tuple[str, Optional[tuple[str]], Optional[dict[str, Any]]],
                    str,
                    None,
                ]
            ],
            Callback,
        ] = cb
        self.cb_return: CallbackReturn = cb_return

    def download_multiple_files(
        self, targets: list[tuple[str, Path]], retries: int = 3, **kwargs: Any
    ):
        # targets format: [(url1, dest2), (url2, dest2), ...]
        self.cb.put(
            ("bar", None, {"set_progress_mode": "determinate", "steps": len(targets)})
        )

        for url, dest in targets:
            self.download_file(url, dest, retries, show_progress=False, **kwargs)

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
                response = requests.get(url, stream=True, **kwargs)
                total_length = int(response.headers.get("content-length"))  # type: ignore

                if response.status_code != 200:
                    return b""
                else:
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
            except requests.exceptions.RequestException:
                msg = f"Cannot download {url} (tried {retry+1}/{retries} times)"
                self.cb.put(msg)

        if not result:
            return b""
        elif dest:
            with open(dest, "wb+") as f:
                f.write(result)
            msg = f"Downloaded {url}"
            self.cb.put(msg)
            return b""
        else:
            return result
