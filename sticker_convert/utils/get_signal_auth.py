#!/usr/bin/env python3
import os
import shutil
import stat
import sys
import platform
import zipfile
import string
import webbrowser

import requests
from selenium import webdriver
from selenium.common.exceptions import JavascriptException

from .run_bin import RunBin
from .cache_store import CacheStore

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

class GetSignalAuth:
    def __init__(self, signal_bin_version='beta', chromedriver_download_dir='./bin', cb_msg=print, cb_ask_str=input):
        self.signal_bin_version = signal_bin_version
        self.chromedriver_download_dir = chromedriver_download_dir

        self.cb_ask_str = cb_ask_str
        self.cb_msg = cb_msg

        self.launch_signal_desktop()

    def download_signal_desktop(self, download_url, signal_bin_path):
        webbrowser.open(download_url)

        self.cb_msg(download_url)

        prompt = f'Signal Desktop not detected.\nDownload and install Signal Desktop BETA version\nAfter installation, quit Signal Desktop before continuing'
        while not (os.path.isfile(signal_bin_path) or shutil.which(signal_bin_path)):
            if self.cb_ask_str != input:
                self.cb_ask_str(prompt, initialvalue=download_url, cli_show_initialvalue=False)
            else:
                input(prompt)

    def get_signal_chromedriver_version(self, electron_bin_path):
        if RunBin.get_bin('strings', silent=True):
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
        self.cb_msg(f'Downloading chromedriver: {chromedriver_url}')

        with CacheStore.get_cache_store() as tempdir:
            chromedriver_zip_path = os.path.join(tempdir, 'chromedriver.zip')
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

    def get_cred(self):
        # https://stackoverflow.com/a/73456344
        uuid, password = None, None
        try:
            if self.signal_bin_version == 'prod':
                uuid = self.driver.execute_script('return window.reduxStore.getState().items.uuid_id')
                password = self.driver.execute_script('return window.reduxStore.getState().items.password')
            else:
                uuid = self.driver.execute_script('return window.SignalDebug.getReduxState().items.uuid_id')
                password = self.driver.execute_script('return window.SignalDebug.getReduxState().items.password')
        except JavascriptException as e:
            pass

        return uuid, password

    def close(self):
        self.cb_msg('Closing Signal Desktop')
        self.driver.quit()

    def launch_signal_desktop(self):
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

        if self.signal_bin_version == 'prod':
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
        self.cb_msg(f'Signal Desktop is using chrome version {major_version}')
        
        chromedriver_path, local_chromedriver_version = self.get_local_chromedriver(chromedriver_download_dir=self.chromedriver_download_dir)
        if chromedriver_path and local_chromedriver_version == major_version:
            self.cb_msg(f'Found chromedriver version {local_chromedriver_version}, skip downloading')
        else:
            chromedriver_path = self.download_chromedriver(major_version, chromedriver_download_dir=self.chromedriver_download_dir)

        self.cb_msg('Killing all Signal Desktop processes')
        self.killall_signal()

        self.cb_msg('Starting Signal Desktop with Selenium')
        self.launch_signal(signal_bin_path, signal_user_data_dir, chromedriver_path)