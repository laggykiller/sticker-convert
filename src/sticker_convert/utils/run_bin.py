#!/usr/bin/env python3
import subprocess
import os
import shutil
import sys

class RunBin:
    @staticmethod
    def get_bin(bin, silent=False, cb_msg=print):
        if os.path.isfile(bin):
            return bin

        if sys.platform == 'win32':
            bin = bin + '.exe'

        which_result = shutil.which(bin)
        if which_result != None:
            return os.path.abspath(which_result)
        elif silent == False:
            cb_msg(f'Warning: Cannot find binary file {bin}')
    
    @staticmethod
    def run_cmd(cmd_list, silence=False, cb_msg=print):
        cmd_list[0] = RunBin.get_bin(cmd_list[0])

        # sp = subprocess.Popen(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        sp = subprocess.run(cmd_list, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        output_str = sp.stdout.decode()
        error_str = sp.stderr.decode()

        if silence == False and error_str != '':
            cb_msg(f"Error while executing {' '.join(cmd_list)} : {error_str}")
            return False

        return output_str