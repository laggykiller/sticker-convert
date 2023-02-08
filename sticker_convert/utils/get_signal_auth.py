import os
import shutil
import stat
import sys
import platform
import time
import zipfile
import string
import tempfile
import webbrowser

import requests
from selenium import webdriver
from selenium.common.exceptions import JavascriptException

from .run_bin import RunBin

# https://stackoverflow.com/a/17197027
def strings(filename, min=4):
    with open(filename, errors="ignore") as f:
        result = ""
        for c in f.read():
            if c in string.printable:
                result += c
                continue
            if len(result) >= min:
                yield result
            result = ""
        if len(result) >= min:  # catch result at EOF
            yield result

class SignalDesktopManager:
    def __init__(self, cb_msg=print, cb_input=input):
        self.cb_msg = cb_msg
        self.cb_input = cb_input

    def download_signal_desktop(self, download_url, signal_bin_path):
        webbrowser.open(download_url)

        if self.cb_input == input:
            prompt = 'Enter'
        else:
            prompt = 'OK'

        while not (os.path.isfile(signal_bin_path) or shutil.which(signal_bin_path)):
            self.cb_input(f'Signal Desktop not detected.\nDownload and install Signal Desktop from {download_url}\nAfter installation, quit Signal Desktop and press {prompt}')

    def get_signal_chromedriver_version(self, electron_bin_path):
        if RunBin.get_bin('strings'):
            output_str = RunBin.run_cmd(cmd_list=['strings', electron_bin_path], silence=True)
            ss = output_str.split('\n')
        else:
            ss = strings(electron_bin_path)

        for s in ss:
            if 'Chrome/' in s and ' Electron/' in s:
                major_version = s.replace('Chrome/', '').split('.', 1)[0]
                if major_version.isnumeric():
                    return major_version
    
    def get_local_chromedriver(self, chromedriver_download_dir):
        local_chromedriver_version = None
        if sys.platform == 'win32':
            chromedriver_name = 'chromedriver.exe'
        else:
            chromedriver_name = 'chromedriver'
        chromedriver_path = os.path.abspath(os.path.join(chromedriver_download_dir, chromedriver_name))
        if not os.path.isfile(chromedriver_path):
            chromedriver_path = shutil.which('chromedriver')

        if chromedriver_path:
            output_str = RunBin.run_cmd(cmd_list=[chromedriver_path, '-v'], silence=True)
            local_chromedriver_version = output_str.split(' ')[1].split('.', 1)[0]
        
        return chromedriver_path, local_chromedriver_version
    
    def download_chromedriver(self, major_version, chromedriver_download_dir=''):
        chromedriver_version_url = f'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}'
        chromedriver_version = requests.get(chromedriver_version_url).text

        if sys.platform == 'win32':
            chromedriver_platform = 'win32'
        elif sys.platform == 'darwin':
            if platform.processor().lower() == 'arm64':
                chromedriver_platform = 'mac_arm64'
            else:
                chromedriver_platform = 'mac64'
        else:
            chromedriver_platform = 'linux64'
        
        chromedriver_url = f'https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_{chromedriver_platform}.zip'

        with tempfile.TemporaryDirectory() as tmpdir:
            chromedriver_zip_path = os.path.join(tmpdir, 'chromedriver.zip')
            with open(chromedriver_zip_path, 'wb+') as f:
                f.write(requests.get(chromedriver_url).content)
            
            with zipfile.ZipFile(chromedriver_zip_path, 'r') as zip_ref:
                zip_ref.extractall(chromedriver_download_dir)
        
        if sys.platform == 'win32':
            chromedriver_name = 'chromedriver.exe'
        else:
            chromedriver_name = 'chromedriver'
        
        chromedriver_path = os.path.abspath(os.path.join(chromedriver_download_dir, chromedriver_name))
        if not sys.platform == 'win32':
            st = os.stat(chromedriver_path)
            os.chmod(chromedriver_path, st.st_mode | stat.S_IEXEC)
        
        return chromedriver_path
    
    def killall_signal(self):
        if sys.platform == 'win32':
            os.system('taskkill /F /im "Signal.exe"')
            os.system('taskkill /F /im "Signal Beta.exe"')
        else:
            RunBin.run_cmd(cmd_list=['killall', 'signal-desktop'], silence=True)
            RunBin.run_cmd(cmd_list=['killall', 'signal-desktop-beta'], silence=True)
    
    def launch_signal(self, signal_bin_path, signal_user_data_dir, chromedriver_path):
        options = webdriver.ChromeOptions()
        options.binary_location = signal_bin_path
        options.add_argument(f"user-data-dir={signal_user_data_dir}")
        options.add_argument('no-sandbox')

        self.driver = webdriver.Chrome(options=options, executable_path=chromedriver_path)

    def get_cred(self, signal_bin_version):
        while True:
            try:
                if signal_bin_version == 'prod':
                    uuid = self.driver.execute_script('return window.reduxStore.getState().items.uuid_id')
                    password = self.driver.execute_script('return window.reduxStore.getState().items.password')
                else:
                    uuid = self.driver.execute_script('return window.SignalDebug.getReduxState().items.uuid_id')
                    password = self.driver.execute_script('return window.SignalDebug.getReduxState().items.password')
            except JavascriptException:
                uuid, password = None, None

            if uuid and password:
                return uuid, password
            time.sleep(1)

    def close_driver(self):
        self.driver.quit()

    def get_uuid_password(self, signal_bin_version='beta', chromedriver_download_dir='./bin'):
        if sys.platform == 'win32':
            signal_bin_path_prod = os.path.expandvars("%localappdata%/Programs/signal-desktop/Signal.exe")
            signal_bin_path_beta = os.path.expandvars("%localappdata%/Programs/signal-desktop-beta/Signal Beta.exe")
            signal_user_data_dir_prod = os.path.abspath(os.path.expandvars('%appdata%/Signal'))
            signal_user_data_dir_beta = os.path.abspath(os.path.expandvars('%appdata%/Signal Beta'))
            electron_bin_path_prod = signal_bin_path_prod
            electron_bin_path_beta = signal_bin_path_beta
        elif sys.platform == 'darwin':
            signal_bin_path_prod = "/Applications/Signal.app/Contents/MacOS/Signal"
            signal_bin_path_beta = "/Applications/Signal Beta.app/Contents/MacOS/Signal Beta"
            signal_user_data_dir_prod = os.path.expanduser('~/Library/Application Support/Signal')
            signal_user_data_dir_beta = os.path.expanduser('~/Library/Application Support/Signal Beta')
            electron_bin_path_prod = '/Applications/Signal.app/Contents/Frameworks/Electron Framework.framework/Electron Framework'
            electron_bin_path_beta = '/Applications/Signal Beta.app/Contents/Frameworks/Electron Framework.framework/Electron Framework'
        else:
            signal_bin_path_prod = "signal-desktop"
            signal_bin_path_beta = "signal-desktop-beta"
            signal_user_data_dir_prod = os.path.expanduser('~/.config/Signal')
            signal_user_data_dir_beta = os.path.expanduser('~/.config/Signal Beta')
            electron_bin_path_prod = signal_bin_path_prod
            electron_bin_path_beta = signal_bin_path_beta

        if signal_bin_version == 'prod':
            signal_bin_path = signal_bin_path_prod
            signal_user_data_dir = signal_user_data_dir_prod
            electron_bin_path = electron_bin_path_prod
            signal_download_url = 'https://signal.org/en/download/'
        else:
            signal_bin_path = signal_bin_path_beta
            signal_user_data_dir = signal_user_data_dir_beta
            electron_bin_path = electron_bin_path_beta
            signal_download_url = 'https://support.signal.org/hc/en-us/articles/360007318471-Signal-Beta'

        if not (os.path.isfile(signal_bin_path) or shutil.which(signal_bin_path)):
            self.download_signal_desktop(signal_download_url, signal_bin_path)
        
        electron_bin_path = shutil.which(electron_bin_path) if not os.path.isfile(electron_bin_path) else electron_bin_path
        
        signal_bin_path = signal_bin_path if not shutil.which(signal_bin_path) else shutil.which(signal_bin_path)
        
        major_version = self.get_signal_chromedriver_version(electron_bin_path)
        
        chromedriver_path, local_chromedriver_version = self.get_local_chromedriver(chromedriver_download_dir=chromedriver_download_dir)
        if not (chromedriver_path and local_chromedriver_version == major_version):
            chromedriver_path = self.download_chromedriver(major_version, chromedriver_download_dir=chromedriver_download_dir)
        self.killall_signal()
        self.launch_signal(signal_bin_path, signal_user_data_dir, chromedriver_path)
        uuid, password = self.get_cred(signal_bin_version)
        self.close_driver()

        return uuid, password

class GetSignalAuth:
    @staticmethod
    def get_signal_auth(cb_msg=print, cb_input=input):
        m = SignalDesktopManager(cb_msg, cb_input)
        uuid, password = m.get_uuid_password()
        return uuid, password