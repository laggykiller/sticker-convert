#!/usr/bin/env python3
from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any

import anyio
import httpx
import requests

from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.translate import I


class DownloadBase:
    def __init__(
        self,
        opt_input: InputOption,
        opt_cred: CredOption | None,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> None:
        self.url = opt_input.url
        self.out_dir = opt_input.dir
        self.input_option = opt_input.option
        self.opt_cred = opt_cred
        self.cb = cb
        self.cb_return = cb_return

    def download_multiple_files(
        self,
        targets: list[tuple[str, Path]],
        retries: int = 3,
        headers: dict[Any, Any] | None = None,
        semaphore_cnt: int = 4,
        **kwargs: Any,
    ) -> dict[str, bool]:
        results: dict[str, bool] = {}
        anyio.run(
            partial(
                self.download_multiple_files_async,
                targets,
                retries,
                headers,
                results,
                semaphore_cnt,
                **kwargs,
            )
        )
        return results

    async def download_multiple_files_async(
        self,
        targets: list[tuple[str, Path]],
        retries: int = 3,
        headers: dict[Any, Any] | None = None,
        results: dict[str, bool] | None = None,
        semaphore_cnt: int = 4,
        **kwargs: Any,
    ) -> None:
        # targets format: [(url1, dest2), (url2, dest2), ...]
        self.cb.put(
            ("bar", None, {"set_progress_mode": "determinate", "steps": len(targets)})
        )

        semaphore = anyio.Semaphore(semaphore_cnt)

        async with httpx.AsyncClient() as client, anyio.create_task_group() as tg:
            for url, dest in targets:
                tg.start_soon(
                    self.download_file_async,
                    semaphore,
                    client,
                    url,
                    dest,
                    retries,
                    headers,
                    results,
                    **kwargs,
                )

    async def download_file_async(
        self,
        semaphore: anyio.Semaphore,
        client: httpx.AsyncClient,
        url: str,
        dest: Path,
        retries: int = 3,
        headers: dict[Any, Any] | None = None,
        results: dict[str, bool] | None = None,
        **kwargs: Any,
    ) -> None:
        async with semaphore:
            self.cb.put(I("Downloading {}").format(url))
            success = False
            for retry in range(retries):
                response = await client.get(
                    url, follow_redirects=True, headers=headers, **kwargs
                )
                success = response.is_success

                if success:
                    async with await anyio.open_file(dest, "wb+") as f:
                        await f.write(response.content)
                    self.cb.put(I("Downloaded {}").format(url))
                else:
                    self.cb.put(
                        I("Error {}: {} (tried {}/{} times)").format(
                            response.status_code, url, retry + 1, retries
                        )
                    )

            if results is not None:
                results[url] = success

            self.cb.put("update_bar")

    def download_file(
        self,
        url: str,
        dest: Path | None = None,
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

                self.cb.put(I("Downloading {}").format(url))

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
                    I("Cannot download {} (tried {}/{} times): {}").format(
                        url, retry + 1, retries, e
                    )
                )

        if not result:
            return b""
        if dest:
            with open(dest, "wb+") as f:
                f.write(result)
            self.cb.put(I("Downloaded {}").format(url))
            return b""
        return result
