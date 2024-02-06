#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from multiprocessing.managers import BaseProxy

from typing import Optional, Union

import requests

from sticker_convert.job_option import CredOption  # type: ignore
from sticker_convert.utils.callback import Callback, CallbackReturn  # type: ignore

class DownloadBase:
    def __init__(
        self,
        url: str,
        out_dir: Path,
        opt_cred: Optional[CredOption] = None,
        cb: Union[BaseProxy, Callback, None] = None,
        cb_return: Optional[CallbackReturn] = None,
    ):
        
        if not cb:
            cb = Callback(silent=True)
            cb_return = CallbackReturn()

        self.url: str = url
        self.out_dir: Path = out_dir
        self.opt_cred: Optional[CredOption] = opt_cred
        self.cb: Union[BaseProxy, Callback, None] = cb
        self.cb_return: Optional[CallbackReturn] = cb_return

    def download_multiple_files(
        self, targets: list[tuple[str, str]], retries: int = 3, **kwargs
    ):
        # targets format: [(url1, dest2), (url2, dest2), ...]
        self.cb.put(("bar", None, {
            "set_progress_mode": "determinate",
            "steps": len(targets)
        }))

        for url, dest in targets:
            self.download_file(url, dest, retries, show_progress=False, **kwargs)

            self.cb.put("update_bar")

    def download_file(
        self,
        url: str,
        dest: Optional[str] = None,
        retries: int = 3,
        show_progress: bool = True,
        **kwargs,
    ) -> Union[bool, bytes]:
        result = b""
        chunk_size = 102400

        for retry in range(retries):
            try:
                response = requests.get(url, stream=True, **kwargs)
                total_length = int(response.headers.get("content-length"))  # type: ignore[arg-type]

                if response.status_code != 200:
                    return False
                else:
                    self.cb.put(f"Downloading {url}")

                if show_progress:
                    steps = (total_length / chunk_size) + 1
                    self.cb.put(("bar", None, {
                        "set_progress_mode": "determinate",
                        "steps": int(steps)
                    }))

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
            return False
        elif dest:
            with open(dest, "wb+") as f:
                f.write(result)
            msg = f"Downloaded {url}"
            self.cb.put(msg)
            return True
        else:
            return result
