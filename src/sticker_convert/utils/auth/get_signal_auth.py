#!/usr/bin/env python3
import os
import json
import platform
import shutil
from sqlcipher3 import dbapi2 as sqlite3
from pathlib import Path
from typing import Optional


class GetSignalAuth:
    def get_signal_desktop(self) -> tuple[Optional[str], Optional[str]]:
        if platform.system() == "Windows":
            signal_bin_path_prod = os.path.expandvars(
                "%localappdata%/Programs/signal-desktop/Signal.exe"
            )
            signal_bin_path_beta = os.path.expandvars(
                "%localappdata%/Programs/signal-desktop-beta/Signal Beta.exe"
            )
            signal_user_data_dir_prod = os.path.abspath(
                os.path.expandvars("%appdata%/Signal")
            )
            signal_user_data_dir_beta = os.path.abspath(
                os.path.expandvars("%appdata%/Signal Beta")
            )
        elif platform.system() == "Darwin":
            signal_bin_path_prod = "/Applications/Signal.app/Contents/MacOS/Signal"
            signal_bin_path_beta = (
                "/Applications/Signal Beta.app/Contents/MacOS/Signal Beta"
            )
            signal_user_data_dir_prod = os.path.expanduser(
                "~/Library/Application Support/Signal"
            )
            signal_user_data_dir_beta = os.path.expanduser(
                "~/Library/Application Support/Signal Beta"
            )
        else:
            if not (signal_bin_path_prod := shutil.which("signal-desktop")):  # type: ignore
                signal_bin_path_prod = "signal-desktop"
            if not (signal_bin_path_beta := shutil.which("signal-desktop-beta")):  # type: ignore
                signal_bin_path_beta = "signal-desktop-beta"
            signal_user_data_dir_prod = os.path.expanduser("~/.config/Signal")
            signal_user_data_dir_beta = os.path.expanduser("~/.config/Signal Beta")

        if Path(signal_bin_path_prod).is_file():
            return signal_bin_path_prod, signal_user_data_dir_prod
        elif Path(signal_bin_path_beta).is_file():
            return signal_bin_path_beta, signal_user_data_dir_beta
        else:
            return None, None

    def get_cred(self) -> tuple[Optional[str], Optional[str], str]:
        signal_bin_path, signal_user_data_dir = self.get_signal_desktop()

        if not (signal_bin_path and signal_user_data_dir):
            msg = "Signal Desktop not detected.\n"
            msg += "Download and install Signal Desktop,\n"
            msg += "then login to Signal Desktop and try again."

            return None, None, msg

        signal_config = Path(signal_user_data_dir, "config.json")

        if not signal_config.is_file():
            msg = "Signal Desktop installed,\n"
            msg += "but it's config file not found.\n"
            msg += "Please login to Signal Desktop and try again.\n"
            msg += "\n"
            msg += f"{signal_bin_path=}\n"
            msg += f"{signal_user_data_dir=}\n"
            return None, None, msg

        with open(signal_config) as f:
            config = json.load(f)
        key = config.get("key")
        db_key = f"x'{key}'"

        signal_database = Path(signal_user_data_dir, "sql/db.sqlite")

        if not signal_database.is_file():
            msg = "Signal Desktop installed,\n"
            msg += "but database file not found.\n"
            msg += "Please login to Signal Desktop and try again.\n"
            msg += "\n"
            msg += f"{signal_bin_path=}\n"
            msg += f"{signal_user_data_dir=}\n"
            return None, None, msg

        db_conn = sqlite3.connect(signal_database.as_posix())  # type: ignore
        db_cursor = db_conn.cursor()
        db_cursor.execute(f'PRAGMA key="{db_key}"')
        db_cursor.execute("SELECT * FROM items")
        result = db_cursor.fetchall()
        db_conn.close()

        uuid_id = None
        password = None
        for r in result:
            if "uuid_id" in r:
                uuid_id = json.loads(r[1])["value"]
            if "password" in r:
                password = json.loads(r[1])["value"]
            if uuid_id and password:
                msg = "Got uuid and password successfully:\n"
                msg += f"{uuid_id=}\n"
                msg += f"{password=}"
                return uuid_id, password, msg

        msg = "Signal Desktop installed and Database found,\n"
        msg += "but uuid and password not found.\n"
        msg += "Please login to Signal Desktop and try again.\n"
        msg += "\n"
        msg += f"{signal_bin_path=}\n"
        msg += f"{signal_user_data_dir=}\n"
        return None, None, msg
