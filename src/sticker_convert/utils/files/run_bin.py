#!/usr/bin/env python3
import subprocess
import os
import shutil
import platform
from typing import Union, AnyStr


class RunBin:
    @staticmethod
    def get_bin(
        bin: str, silent: bool = False, cb_msg=print
    ) -> Union[str, AnyStr, None]:
        if os.path.isfile(bin):
            return bin

        if platform.system() == "Windows":
            bin = bin + ".exe"

        which_result = shutil.which(bin)
        if which_result != None:
            return os.path.abspath(which_result)  # type: ignore[type-var]
        elif silent == False:
            cb_msg(f"Warning: Cannot find binary file {bin}")

        return None

    @staticmethod
    def run_cmd(
        cmd_list: list[str], silence: bool = False, cb_msg=print
    ) -> Union[bool, str]:
        bin_path = RunBin.get_bin(cmd_list[0])  # type: ignore[assignment]

        if bin_path:
            cmd_list[0] = bin_path
        else:
            if silence == False:
                cb_msg(
                    f"Error while executing {' '.join(cmd_list)} : Command not found"
                )
            return False

        # sp = subprocess.Popen(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        sp = subprocess.run(
            cmd_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        output_str = sp.stdout.decode()
        error_str = sp.stderr.decode()

        if silence == False and error_str != "":
            cb_msg(f"Error while executing {' '.join(cmd_list)} : {error_str}")
            return False

        return output_str
