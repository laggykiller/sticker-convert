#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, cast
from urllib.parse import urlparse

import requests

from sticker_convert.downloaders.download_base import DownloadBase
from sticker_convert.job_option import CredOption, InputOption
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.emoji import extract_emojis
from sticker_convert.utils.files.metadata_handler import MetadataHandler

# References:
# https://github.com/ThaTiemsz/Discord-Emoji-Downloader/blob/master/assets/app.js
# https://github.com/zgibberish/discord-emoji-scraper/blob/main/emoji_scraper.py


class DownloadDiscord(DownloadBase):
    # def __init__(self, *args: Any, **kwargs: Any) -> None:
    #     super().__init__(*args, **kwargs)

    def download_stickers_discord(self) -> Tuple[int, int]:
        if self.opt_cred is None or self.opt_cred.discord_token == "":
            self.cb.put("Error: Downloading from Discord requires token")
            return 0, 0

        gid: Optional[str] = None
        if self.url.isnumeric():
            gid = self.url
        else:
            url_parsed = urlparse(self.url)
            if url_parsed.netloc == "discord.com":
                gid = url_parsed.path.split("/")[2]

        if gid is None or gid.isnumeric() is False:
            self.cb.put("Error: Invalid url")
            return 0, 0

        headers = {
            "Authorization": self.opt_cred.discord_token,
        }

        r = requests.get(f"https://discord.com/api/v10/guilds/{gid}", headers=headers)
        r_json = json.loads(r.text)

        if self.input_option == "discord_emoji":
            stickers = r_json["emojis"]
        else:
            stickers = r_json["stickers"]

        targets: List[Tuple[str, Path]] = []
        emoji_dict: Dict[str, str] = {}
        for i, sticker in enumerate(stickers):
            f_id = str(i).zfill(3)
            sticker_id = sticker["id"]
            if self.input_option == "discord_emoji":
                f_ext = ".gif" if sticker["animated"] else ".png"
                sticker_url = f"https://cdn.discordapp.com/emojis/{sticker_id}{f_ext}?size=4096&quality=lossless"
            else:
                # https://discord.com/developers/docs/resources/sticker#sticker-object-sticker-format-types
                format_type = cast(int, sticker["format_type"])
                f_ext = [".png", ".png", ".json", ".gif"][format_type - 1]
                sticker_url = f"https://cdn.discordapp.com/stickers/{sticker_id}{f_ext}?size=4096&quality=lossless"
                emoji_dict[f_id] = extract_emojis(sticker["tags"])
            f_name = f_id + f_ext
            f_path = Path(self.out_dir, f_name)
            targets.append((sticker_url, f_path))

        results = self.download_multiple_files(targets)

        server_name = r_json["name"]
        MetadataHandler.set_metadata(
            self.out_dir,
            title=server_name,
            author=server_name,
            emoji_dict=emoji_dict if self.input_option == "discord" else None,
        )

        return sum(results.values()), len(targets)

    @staticmethod
    def start(
        opt_input: InputOption,
        opt_cred: Optional[CredOption],
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int]:
        downloader = DownloadDiscord(opt_input, opt_cred, cb, cb_return)
        return downloader.download_stickers_discord()
