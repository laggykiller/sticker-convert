#!/usr/bin/env python3
import os
import zipfile
from pathlib import Path
from typing import Any, Optional, Tuple

from sticker_convert.auth.auth_whatsapp import SWB
from sticker_convert.definitions import CONFIG_DIR
from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.translate import I


class DownloadWhatsapp(DownloadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def download_stickers_whatsapp(self) -> Tuple[int, int]:
        swb = SWB()
        if swb.success is False:
            self.cb.put(("msg_block", (swb.msg,), None))
            return 0, 0
        cmds = [
            "recv",
            "--json",
            "--no-write-meta",
            "--dest",
            str(self.out_dir),
            "--auth-info",
            str(CONFIG_DIR / "SWB/auth"),
        ]

        self.cb.put(("msg_dynamic", (I("Logging in WhatsApp, please wait..."),), None))
        prompt = I(
            "Please send stickers to WhatsApp group 'sticker-whatsapp-bridge'; When done, press OK"
        )

        logged_in = False
        prompt_showing = False
        count = 0
        for r in swb.run(cmds):
            if logged_in is True:
                if prompt_showing is False:
                    self.cb.put(("msg_block", (prompt,), None))
                    prompt_showing = True
                if self.cb_return.response_event.is_set():
                    break
            if r is None:
                continue
            if r["event"] == "recv":
                if r["type"] == "pack":
                    zip_path = self.out_dir / r["fname"]
                    with zipfile.ZipFile(zip_path, "r") as zip_f:
                        for i in zip_f.namelist():
                            if i[:2].isnumeric():
                                out_f_stem = str(count).zfill(3)
                                count += 1
                            else:
                                out_f_stem = "cover"
                            ext = Path(i).suffix
                            info = zip_f.getinfo(i)
                            info.filename = out_f_stem + ext
                            zip_f.extract(i, path=self.out_dir)
                            self.cb.put(
                                (
                                    "msg",
                                    (I("Downloaded {}").format(info.filename),),
                                    None,
                                )
                            )
                    os.remove(zip_path)

                    if (self.out_dir / "title.txt").exists():
                        self.cb.put("Warning: Overwriting title.txt")
                    with open(self.out_dir / "title.txt", "w+") as f:
                        f.write(r["name"])

                    if (self.out_dir / "author.txt").exists():
                        self.cb.put("Warning: Overwriting author.txt")
                    with open(self.out_dir / "author.txt", "w+") as f:
                        f.write(r["publisher"])

                elif r["type"] == "sticker":
                    out_f_path = (self.out_dir / str(count).zfill(3)).with_suffix(
                        r["ext"]
                    )
                    out_f_path_orig = self.out_dir / r["fname"]
                    os.rename(out_f_path_orig, out_f_path)
                    self.cb.put(("msg", (I("Downloaded {}").format(r["fname"]),), None))
                    count += 1
                else:
                    continue

            elif r["event"] == "login_success":
                logged_in = True
                self.cb.put(("msg_dynamic", (None,), None))
            elif r["event"] == "error":
                self.cb.put(I("Failed to download: {}").format(r["message"]))
        self.cb.put(("msg_dynamic", (None,), None))
        swb.kill()

        return count, count

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadWhatsapp(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_whatsapp()
