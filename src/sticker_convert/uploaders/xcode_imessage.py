#!/usr/bin/env python3
import copy
import json
import os
import plistlib
import shutil
import zipfile
from pathlib import Path
from queue import Queue
from typing import Union, Any, Optional

from sticker_convert.converter import StickerConvert
from sticker_convert.definitions import ROOT_DIR
from sticker_convert.job_option import CompOption, CredOption, OutputOption
from sticker_convert.uploaders.upload_base import UploadBase
from sticker_convert.utils.callback import Callback, CallbackReturn
from sticker_convert.utils.files.metadata_handler import MetadataHandler
from sticker_convert.utils.files.sanitize_filename import sanitize_filename
from sticker_convert.utils.media.codec_info import CodecInfo
from sticker_convert.utils.media.format_verify import FormatVerify


class XcodeImessageIconset:
    iconset: dict[str, tuple[int, int]] = {}

    def __init__(self):
        if self.iconset != {}:
            return

        if (ROOT_DIR / "ios-message-stickers-template").is_dir():
            with open(
                ROOT_DIR
                / "ios-message-stickers-template/stickers StickerPackExtension/Stickers.xcstickers/iMessage App Icon.stickersiconset/Contents.json"
            ) as f:
                dict = json.load(f)
        elif (ROOT_DIR / "ios-message-stickers-template.zip").is_file():
            with zipfile.ZipFile(
                (ROOT_DIR / "ios-message-stickers-template.zip"), "r"
            ) as f:
                dict = json.loads(
                    f.read(
                        "stickers StickerPackExtension/Stickers.xcstickers/iMessage App Icon.stickersiconset/Contents.json"
                    ).decode()
                )
        else:
            raise FileNotFoundError("ios-message-stickers-template not found")

        for i in dict["images"]:
            filename = i["filename"]
            size = i["size"]
            size_w = int(size.split("x")[0])
            size_h = int(size.split("x")[1])
            scale = int(i["scale"].replace("x", ""))
            size_w_scaled = size_w * scale
            size_h_scaled = size_h * scale

            self.iconset[filename] = (size_w_scaled, size_h_scaled)

        # self.iconset = {
        #     'App-Store-1024x1024pt.png': (1024, 1024),
        #     'iPad-Settings-29pt@2x.png': (58, 58),
        #     'iPhone-settings-29pt@2x.png': (58, 58),
        #     'iPhone-settings-29pt@3x.png': (87, 87),
        #     'Messages27x20pt@2x.png': (54, 40),
        #     'Messages27x20pt@3x.png': (81, 60),
        #     'Messages32x24pt@2x.png': (64, 48),
        #     'Messages32x24pt@3x.png': (96, 72),
        #     'Messages-App-Store-1024x768pt.png': (1024, 768),
        #     'Messages-iPad-67x50pt@2x.png': (134, 100),
        #     'Messages-iPad-Pro-74x55pt@2x.png': (148, 110),
        #     'Messages-iPhone-60x45pt@2x.png': (120, 90),
        #     'Messages-iPhone-60x45pt@3x.png': (180, 135)
        # }


class XcodeImessage(UploadBase):
    def __init__(self, *args: Any, **kwargs: Any):
        super(XcodeImessage, self).__init__(*args, **kwargs)
        self.iconset = XcodeImessageIconset().iconset

        base_spec = CompOption()
        base_spec.size_max = 500000
        base_spec.res = 300
        base_spec.format = ["png", ".apng", ".gif", ".jpeg", "jpg"]
        base_spec.square = True

        self.small_spec = copy.deepcopy(base_spec)

        self.medium_spec = copy.deepcopy(base_spec)
        self.medium_spec.res = 408

        self.large_spec = copy.deepcopy(base_spec)
        self.large_spec.res = 618

    def create_imessage_xcode(self) -> list[str]:
        urls: list[str] = []
        title, author, _ = MetadataHandler.get_metadata(
            self.opt_output.dir,
            title=self.opt_output.title,
            author=self.opt_output.author,
        )
        if not author:
            self.cb.put("author is required for creating Xcode iMessage sticker pack")
            return urls
        if not title:
            self.cb.put("title is required for creating Xcode iMessage sticker pack")
            return urls

        author = author.replace(" ", "_")
        title = title.replace(" ", "_")
        packs = MetadataHandler.split_sticker_packs(
            self.opt_output.dir,
            title=title,
            file_per_pack=100,
            separate_image_anim=False,
        )

        res_choice = None
        spec_choice = None
        opt_comp_merged = copy.deepcopy(self.opt_comp)

        for pack_title, stickers in packs.items():
            pack_title = sanitize_filename(pack_title)

            for src in stickers:
                self.cb.put(f"Verifying {src} for creating Xcode iMessage sticker pack")

                fpath = Path(self.opt_output.dir, src)

                if res_choice is None:
                    res_choice, _ = CodecInfo.get_file_res(fpath)

                    if res_choice == 618:
                        spec_choice = self.large_spec
                    elif res_choice == 408:
                        spec_choice = self.medium_spec
                    else:
                        # res_choice == 300
                        spec_choice = self.small_spec

                    opt_comp_merged.merge(spec_choice)

                assert spec_choice
                if not FormatVerify.check_file(src, spec=spec_choice):
                    StickerConvert.convert(
                        fpath, fpath, opt_comp_merged, self.cb, self.cb_return
                    )

            self.add_metadata(author, pack_title)
            self.create_xcode_proj(author, pack_title)

            result = Path(self.opt_output.dir / pack_title).as_posix()
            self.cb.put(result)
            urls.append(result)

        return urls

    def add_metadata(self, author: str, title: str):
        first_image_path = Path(
            self.opt_output.dir,
            [
                i
                for i in sorted(self.opt_output.dir.iterdir())
                if (self.opt_output.dir / i).is_file() and i.suffix == ".png"
            ][0],
        )
        cover_path = MetadataHandler.get_cover(self.opt_output.dir)
        if cover_path:
            icon_source = cover_path
        else:
            icon_source = first_image_path

        for icon, res in self.iconset.items():
            spec_cover = CompOption()
            spec_cover.res_w = res[0]
            spec_cover.res_h = res[1]
            spec_cover.fps = 0

            icon_path = self.opt_output.dir / icon
            if Path(icon) in [
                i for i in self.opt_output.dir.iterdir()
            ] and not FormatVerify.check_file(icon_path, spec=spec_cover):
                StickerConvert.convert(
                    icon_path, icon_path, spec_cover, self.cb, self.cb_return
                )
            else:
                StickerConvert.convert(
                    icon_source, icon_path, spec_cover, self.cb, self.cb_return
                )

        MetadataHandler.set_metadata(self.opt_output.dir, author=author, title=title)

    def create_xcode_proj(self, author: str, title: str):
        pack_path = self.opt_output.dir / title
        if (ROOT_DIR / "ios-message-stickers-template.zip").is_file():
            with zipfile.ZipFile(
                ROOT_DIR / "ios-message-stickers-template.zip", "r"
            ) as f:
                f.extractall(pack_path)
        elif (ROOT_DIR / "ios-message-stickers-template").is_dir():
            shutil.copytree(ROOT_DIR / "ios-message-stickers-template", pack_path)
        else:
            self.cb.put(
                "Failed to create Xcode project: ios-message-stickers-template not found"
            )

        os.remove(pack_path / "README.md")
        shutil.rmtree(
            pack_path / "stickers.xcodeproj/project.xcworkspace",
            ignore_errors=True,
        )
        shutil.rmtree(pack_path / "stickers.xcodeproj/xcuserdata", ignore_errors=True)

        with open(
            pack_path / "stickers.xcodeproj/project.pbxproj",
            encoding="utf-8",
        ) as f:
            pbxproj_data = f.read()

        pbxproj_data = pbxproj_data.replace(
            "stickers StickerPackExtension", f"{title} StickerPackExtension"
        )
        pbxproj_data = pbxproj_data.replace("stickers.app", f"{title}.app")
        pbxproj_data = pbxproj_data.replace("/* stickers */", f"/* {title} */")
        pbxproj_data = pbxproj_data.replace("name = stickers", f"name = {title}")
        pbxproj_data = pbxproj_data.replace(
            "productName = stickers", f"productName = {title}"
        )
        pbxproj_data = pbxproj_data.replace(
            '/* Build configuration list for PBXProject "stickers" */',
            f'/* Build configuration list for PBXProject "{title}" */',
        )
        pbxproj_data = pbxproj_data.replace(
            '/* Build configuration list for PBXNativeTarget "stickers StickerPackExtension" */',
            f'/* Build configuration list for PBXNativeTarget "{title} StickerPackExtension" */',
        )
        pbxproj_data = pbxproj_data.replace(
            '/* Build configuration list for PBXNativeTarget "stickers" */',
            f'/* Build configuration list for PBXNativeTarget "{title}" */',
        )
        pbxproj_data = pbxproj_data.replace("com.niklaspeterson", f"com.{author}")
        pbxproj_data = pbxproj_data.replace(
            "stickers/Info.plist", f"{title}/Info.plist"
        )

        with open(
            pack_path / "stickers.xcodeproj/project.pbxproj",
            "w+",
            encoding="utf-8",
        ) as f:
            f.write(pbxproj_data)

        # packname StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack
        stickers_path = (
            pack_path
            / "stickers StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack"
        )

        for i in stickers_path.iterdir():
            if i.suffix == ".sticker":
                shutil.rmtree(stickers_path / i)

        stickers_lst: list[str] = []
        for i in sorted(self.opt_output.dir.iterdir()):
            if (
                CodecInfo.get_file_ext(i) == ".png"
                and i.stem != "cover"
                and i.name not in self.iconset
            ):
                sticker_dir = f"{i.stem}.sticker"  # 0.sticker
                stickers_lst.append(sticker_dir)
                # packname StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack/0.sticker
                sticker_path = stickers_path / sticker_dir
                os.mkdir(sticker_path)
                # packname StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack/0.sticker/0.png
                shutil.copy(self.opt_output.dir / i.name, sticker_path / i.name)

                json_content = {
                    "info": {
                        "author": "xcode",
                        "version": 1,
                    },
                    "properties": {"filename": str(i)},
                }

                # packname StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack/0.sticker/Contents.json
                with open(sticker_path / "Contents.json", "w+") as f:
                    json.dump(json_content, f, indent=2)

        # packname StickerPackExtension/Stickers.xcstickers/Sticker Pack.stickerpack/Contents.json
        with open(stickers_path / "Contents.json") as f:
            json_content = json.load(f)

        json_content["stickers"] = []
        for i in stickers_lst:
            json_content["stickers"].append({"filename": i})

        with open(stickers_path / "Contents.json", "w+") as f:
            json.dump(json_content, f, indent=2)

        # packname StickerPackExtension/Stickers.xcstickers/iMessage App Icon.stickersiconset
        iconset_path = (
            pack_path
            / "stickers StickerPackExtension/Stickers.xcstickers/iMessage App Icon.stickersiconset"
        )

        for i in iconset_path.iterdir():
            if Path(i).suffix == ".png":
                os.remove(iconset_path / i)

        icons_lst: list[str] = []
        for i in self.iconset:
            shutil.copy(self.opt_output.dir / i, iconset_path / i)
            icons_lst.append(i)

        # packname/Info.plist
        plist_path = pack_path / "stickers/Info.plist"
        with open(plist_path, "rb") as f:
            plist_dict = plistlib.load(f)
        plist_dict["CFBundleDisplayName"] = title

        with open(plist_path, "wb+") as f:
            plistlib.dump(plist_dict, f)

        Path(pack_path, "stickers").rename(Path(pack_path, title))
        Path(pack_path, "stickers StickerPackExtension").rename(
            Path(pack_path, f"{title} StickerPackExtension")
        )
        Path(pack_path, "stickers.xcodeproj").rename(
            Path(pack_path, f"{title}.xcodeproj")
        )

    @staticmethod
    def start(
        opt_output: OutputOption,
        opt_comp: CompOption,
        opt_cred: CredOption,
        cb: Union[
            Queue[
                Union[
                    tuple[str, Optional[tuple[str]], Optional[dict[str, str]]],
                    str,
                    None,
                ]
            ],
            Callback,
        ],
        cb_return: CallbackReturn,
    ) -> list[str]:
        exporter = XcodeImessage(opt_output, opt_comp, opt_cred, cb, cb_return)
        return exporter.create_imessage_xcode()
