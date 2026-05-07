#!/usr/bin/env python3
import tarfile
from pathlib import Path
from typing import Any, List, Tuple, cast
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import CallbackProtocol, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.translate import I


class UploadMastodon(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.MSG_NO_TOKEN = I(
            "Error: Cannot get authenticity_token, upload to Mastodon failed"
        )

    def upload_mastodon(self) -> Tuple[int, int, List[str]]:
        title, _, _ = MetadataHandler.get_metadata(
            self.opt_output.dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )
        title = title if title != "" else "result"
        emojis = MetadataHandler.get_stickers_present(self.opt_output.dir)

        tar_path = Path(self.opt_output.dir, f"{title}.tar.gz")
        with tarfile.open(tar_path, "w:gz") as tar:
            for emoji in emojis:
                if emoji.stem.count("-") == 1:
                    name = emoji.stem.split("-", 1)[-1] + "".join(emoji.suffixes)
                else:
                    name = emoji.name.replace("-", "_")
                tar.add(emoji, arcname=emoji.name)

        if self.opt_cred.mastodon_cookies == "":
            self.cb.put(I("Note: mastodon_cookies required for uploading to Mastodon"))
            return len(emojis), len(emojis), [str(tar_path)]
        if self.opt_cred.mastodon_url == "":
            self.cb.put(I("Note: mastodon_url required for uploading to Mastodon"))
            return len(emojis), len(emojis), [str(tar_path)]

        scheme = urlparse(self.opt_cred.mastodon_url).scheme
        scheme = scheme if scheme != "" else "https"
        netloc = urlparse(self.opt_cred.mastodon_url).netloc
        domain = f"{scheme}://{netloc}"

        response = requests.get(
            domain, cookies={"_session_id": self.opt_cred.mastodon_cookies}
        )
        mastodon_session = response.cookies.get_dict().get("_mastodon_session")
        if mastodon_session is None:
            self.cb.put(I("Note: Invalid mastodon_cookies, upload to Mastodon failed"))
            return True, len(emojis), [str(tar_path)]
        cookies = {
            "_session_id": self.opt_cred.mastodon_cookies,
            "_mastodon_session": mastodon_session,
        }

        response = requests.get(f"{domain}/admin/custom_emojis/new", cookies=cookies)
        soup = BeautifulSoup(response.text, "html.parser")
        authenticity_token_tag = soup.find("meta", {"name": "csrf-token"})
        if authenticity_token_tag is None:
            self.cb.put(self.MSG_NO_TOKEN)
            return 0, len(emojis), [str(tar_path)]

        authenticity_token = cast(Tag, authenticity_token_tag).get("content")
        if authenticity_token is None:
            self.cb.put(self.MSG_NO_TOKEN)
            return 0, len(emojis), [str(tar_path)]

        success = 0
        for emoji in emojis:
            self.cb.put("update_bar")
            if emoji.name.count("-") == 1:
                name = emoji.name.split("-", 1)[-1].split(".")[0]
                category = emoji.name.split("-", 1)[0]
            else:
                name = emoji.name.replace("-", "_").split(".")[0]
                category = None
            if emoji.suffix == ".gif":
                content_type = "image/gif"
            elif emoji.suffix == ".png":
                content_type = "image/png"
            else:
                self.cb.put(
                    I("Failed to upload {} to Mastodon as not png or gif").format(name)
                )
                continue
            response = requests.post(
                f"{domain}/admin/custom_emojis",
                headers={"Referer": f"{domain}/admin/custom_emojis/new"},
                cookies=cookies,
                data={
                    "authenticity_token": authenticity_token,
                    "custom_emoji[shortcode]": name,
                    "custom_emoji[category_name]": category,
                    "button": "",
                },
                files={
                    "custom_emoji[image]": (
                        emoji.name,
                        open(str(emoji), "rb"),
                        content_type,
                    )
                },
            )
            if "is invalid" in response.text:
                self.cb.put(I("{} name invalid").format(name))
                continue
            elif "has already been taken" in response.text:
                self.cb.put(I("{} already uploaded").format(name))
                continue
            elif response.status_code != 200:
                self.cb.put(
                    I("Failed to upload {} to Mastodon: {}").format(
                        name, response.status_code
                    )
                )
                continue

            self.cb.put(I(f"Uploaded {name}"))

            if category is None:
                success += 1
            else:
                response = requests.get(
                    f"{domain}/admin/custom_emojis",
                    cookies=cookies,
                    params={
                        "shortcode": name,
                        "local": "1",
                    },
                )
                soup = BeautifulSoup(response.text, "html.parser")
                samp_tag = soup.find("samp", string=f":{name}:")
                if samp_tag is None:
                    self.cb.put(
                        I(
                            "Failed to assign category {} to {}: Cannot search for emoji"
                        ).format(category, name)
                    )
                    continue
                samp_tag = cast(Tag, samp_tag)

                row_tag = samp_tag.find_parent("div", {"class": "batch-table__row"})
                if row_tag is None:
                    self.cb.put(
                        I("Failed to assign category {} to {}: Cannot find row").format(
                            category, name
                        )
                    )
                row_tag = cast(Tag, row_tag)

                input_tag = row_tag.find(
                    "input", {"name": "form_custom_emoji_batch[custom_emoji_ids][]"}
                )
                if input_tag is None:
                    self.cb.put(
                        I(
                            "Failed to assign category {} to {}: Cannot find input"
                        ).format(category, name)
                    )
                input_tag = cast(Tag, input_tag)

                custom_emoji_id = input_tag.get("value")
                if custom_emoji_id is None:
                    self.cb.put(
                        I(
                            "Failed to assign category {} to {}: Cannot find custom_emoji_id"
                        ).format(category, name)
                    )

                response = requests.post(
                    f"{domain}/admin/custom_emojis/batch",
                    cookies=cookies,
                    headers={
                        "Referer": f"{domain}/admin/custom_emojis?local=1&shortcode={name}"
                    },
                    data={
                        "authenticity_token": authenticity_token,
                        "page": "1",
                        "local": "1",
                        "shortcode": name,
                        "update": "",
                        "form_custom_emoji_batch[category_id]": "",
                        "form_custom_emoji_batch[category_name]": category,
                        "form_custom_emoji_batch[custom_emoji_ids][]": [
                            custom_emoji_id
                        ],
                    },
                )
                self.cb.put(I("Assigned category {} to {}").format(category, name))
                success += 1

        return success, len(emojis), [str(tar_path)]

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: CallbackProtocol,
        cb_return: CallbackReturn,
    ) -> Tuple[int, int, List[str]]:
        exporter = UploadMastodon(opt_output, opt_comp, opt_cred, cb, cb_return)
        return exporter.upload_mastodon()
