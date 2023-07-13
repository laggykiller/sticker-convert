#!/usr/bin/env python3
import subprocess
import os
import shutil
import sys
import tempfile

class RunBin:
    @staticmethod
    def get_bin(bin, silent=False, cb_msg=print):
        if os.path.isfile(bin):
            return bin

        if sys.platform == 'win32':
            bin = bin + '.exe'

        # Prioritize local binaries
        if os.path.isdir('./bin') and bin in os.listdir('./bin'):
            return os.path.abspath(f'./bin/{bin}')
        elif os.path.isdir('./ImageMagick') and bin in os.listdir('./ImageMagick'):
            return os.path.abspath(f'./ImageMagick/{bin}')
        elif os.path.isdir('./ImageMagick/bin') and bin in os.listdir('./ImageMagick/bin'):
            return os.path.abspath(f'./ImageMagick/bin/{bin}')

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

    @staticmethod
    def check_bin(bin, check_cmd=['-v'], cb_ask_bool=input, cb_msg=print):
        while True:
            msg = RunBin.check_bin_once(bin, check_cmd, cb_ask_bool, cb_msg)

            if msg:
                response = cb_ask_bool(msg)
                if response:
                    continue
                else:
                    return False
            
            return True

    @staticmethod
    def check_bin_once(bin, check_cmd=['-v'], cb_ask_bool=input, cb_msg=print):
        msg = None

        bin_path = RunBin.get_bin(bin)
        if not bin_path:
            msg = f'Failed to find binary {bin}.\nRead Documentations to check how to download it.\nCheck again?'
            return msg

        if sys.platform == 'darwin':
            RunBin.run_cmd(['xattr', '-d', 'com.apple.quarantine', bin_path], silence=True, cb_msg=cb_msg)

        with tempfile.TemporaryDirectory() as tempdir:
            if bin == 'apngasm' or bin == 'apngdis':
                shutil.copy('./resources/testing.png', os.path.join(tempdir, 'testing.png'))
                check_cmd_replaced = []
                for i in check_cmd:
                    if i.startswith('{tempdir}/'):
                        i = os.path.join(tempdir, i.replace('{tempdir}/', ''))
                    check_cmd_replaced.append(i)
            else:
                check_cmd_replaced = check_cmd

            returncode = subprocess.call([bin_path, *check_cmd_replaced], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if returncode != 0:
                advice = ''
                if sys.platform != 'win32':
                    advice += '\nIs the permission correct?'
                elif sys.platform == 'darwin':
                    advice += '\nDid MacOS blocked it because from identified developer?'
                    advice += '\nGo to System Preferences > Security & Privacy and click "Open Anyway"'
                msg = f'Error occured when executing binary {bin}.{advice}\nCheck again?'
                return msg

            try:
                if bin == 'apngasm':
                    os.remove(os.path.join(tempdir, 'testing_apngasm.png'))
                elif bin == 'apngdis':
                    os.remove(os.path.join(tempdir, 'testing_strip.png'))
            except OSError:
                msg = f'Executing binary {bin} gave unexpected result.\nCheck again?'
                return msg