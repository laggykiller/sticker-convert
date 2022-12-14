import subprocess
import os
import shutil
import sys

class RunBin:
    @staticmethod
    def get_bin(bin, silent=False):
        if sys.platform == 'win32':
            bin = bin + '.exe'
        which_result = shutil.which(bin)
        if which_result != None:
            return os.path.abspath(which_result)
        elif os.path.isdir('./bin') and bin in os.listdir('./bin'):
            return os.path.abspath(f'./bin/{bin}')
        elif os.path.isdir('./ImageMagick/bin') and bin in os.listdir('./ImageMagick/bin'):
            return os.path.abspath(f'./ImageMagick/bin/{bin}')
        else:
            if silent == False:
                print(f'Warning: Cannot find binary file {bin}')
    
    @staticmethod
    def run_cmd(cmd_list, silence=False):
        cmd_list[0] = RunBin.get_bin(cmd_list[0])

        # subprocess.call(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        sp = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        output, error = sp.communicate()

        output_str = output.decode()
        error_str = error.decode()

        if silence == False and error_str != '':
            print(error_str)

        return output_str