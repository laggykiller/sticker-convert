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

        if silence:
            sp = subprocess.Popen(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        else:
            sp = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        output, error = sp.communicate()

        output_str = ''
        if output:
            output_str = output.decode()
        
        error_str = ''
        if error:
            error_str = error.decode()

        if silence == False and error_str != '':
            cb_msg(f"Error while executing {' '.join(cmd_list)} : {error_str}")
            return False

        return output_str, sp.returncode

    @staticmethod
    def check_bin(bin, check_cmd=['-v'], cb_ask_bool=input, cb_msg=print):
        while True:
            msg = ''
            advice = ''

            bin_path = RunBin.get_bin(bin)

            if not bin_path:
                msg = f'Failed to find binary {bin}.\nRead Documentations to check how to download it.\nCheck again?'
            else:
                if sys.platform == 'darwin':
                    RunBin.run_cmd(['xattr', '-d', 'com.apple.quarantine', bin_path], silence=True, cb_msg=cb_msg)
                output_str, returncode = RunBin.run_cmd([bin, *check_cmd], silence=True)
                if returncode != 0 and not (bin == 'apngasm' and returncode == 2) and not (bin == 'apngdis' and returncode == 1):
                    msg = f'Error occured when executing binary {bin}.{advice}\nCheck again?'
                    if sys.platform != 'win32':
                        advice += '\nIs the permission correct?'
                    if sys.platform == 'darwin':
                        advice += '\nDid MacOS blocked it because from identified developer?'
                        advice += '\nGo to System Preferences > Security & Privacy and click "Open Anyway"'
                
            if msg != '':
                response = cb_ask_bool(f'Error occured when executing binary {bin}.{advice}\nCheck again?')
                if response:
                    continue
                else:
                    return False
            
            return True