#!/usr/bin/env python3
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Union, Callable, Any


class RunBin:
    @staticmethod
    def get_bin(
        bin: str, silent: bool = False, cb_msg: Callable[..., Any] = print
    ) -> Union[str, None]:
        if Path(bin).is_file():
            return bin

        if platform.system() == "Windows":
            bin = bin + ".exe"

        which_result = shutil.which(bin)
        if which_result is not None:
            return str(Path(which_result).resolve())
        elif silent is False:
            cb_msg(f"Warning: Cannot find binary file {bin}")

        return None

    @staticmethod
    def run_cmd(
        cmd_list: list[str], silence: bool = False, cb_msg: Callable[..., Any] = print
    ) -> tuple[bool, str]:
        bin_path = RunBin.get_bin(cmd_list[0])

        if bin_path:
            cmd_list[0] = bin_path
        else:
            if silence is False:
                cb_msg(
                    f"Error while executing {' '.join(cmd_list)} : Command not found"
                )
            return False, ""

        # sp = subprocess.Popen(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        sp = subprocess.run(
            cmd_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        output_str = sp.stdout.decode()
        error_str = sp.stderr.decode()

        if silence is False and error_str != "":
            cb_msg(f"Error while executing {' '.join(cmd_list)} : {error_str}")
            return False, ""

        return True, output_str
