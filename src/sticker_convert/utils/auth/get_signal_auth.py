#!/usr/bin/env python3
import os
import io
import json
import shutil
import stat
import platform
import zipfile
import string
import webbrowser
from typing import Optional, Generator

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import JavascriptException

from ..files.run_bin import RunBin # type: ignore
from ..files.dir_utils import DirUtils # type: ignore

# https://stackoverflow.com/a/17197027
def strings(filename: str, min: int = 4) -> Generator[str, None, None]:
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
    def __init__(self, signal_bin_version: str = 'beta', cb_msg=print, cb_ask_str=input):
        chromedriver_download_dir = os.path.join(DirUtils.get_config_dir(), 'bin')
        os.makedirs(chromedriver_download_dir, exist_ok=True)

        self.signal_bin_version = signal_bin_version
        self.chromedriver_download_dir = chromedriver_download_dir

        self.cb_ask_str = cb_ask_str
        self.cb_msg = cb_msg

        self.launch_signal_desktop()

    def download_signal_desktop(self, download_url: str, signal_bin_path: str):
        webbrowser.open(download_url)

        self.cb_msg(download_url)

        prompt = 'Signal Desktop not detected.\n'
        prompt += 'Download and install Signal Desktop BETA version\n'
        prompt += 'After installation, quit Signal Desktop before continuing'
        while not (os.path.isfile(signal_bin_path) or shutil.which(signal_bin_path)):
            if self.cb_ask_str != input:
                self.cb_ask_str(prompt, initialvalue=download_url, cli_show_initialvalue=False)
            else:
                input(prompt)

    def get_signal_chromedriver_version(self, electron_bin_path: str) -> Optional[str]:
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

        return None
    
    def get_local_chromedriver(self, chromedriver_download_dir: str) -> tuple[Optional[str], Optional[str]]:
        local_chromedriver_version = None
        if platform.system() == 'Windows':
            chromedriver_name = 'chromedriver.exe'
        else:
            chromedriver_name = 'chromedriver'
        chromedriver_path = os.path.abspath(os.path.join(chromedriver_download_dir, chromedriver_name))
        if not os.path.isfile(chromedriver_path):
            chromedriver_path = shutil.which('chromedriver') # type: ignore[assignment]

        if chromedriver_path:
            output_str = RunBin.run_cmd(cmd_list=[chromedriver_path, '-v'], silence=True)
            local_chromedriver_version = output_str.split(' ')[1].split('.', 1)[0]
        else:
            local_chromedriver_version = None
        
        return chromedriver_path, local_chromedriver_version
    
    def download_chromedriver(self, major_version: str, chromedriver_download_dir: str = '') -> str:
        if platform.system() == 'Windows':
            chromedriver_platform = 'win32'
            if '64' in platform.architecture()[0]:
                chromedriver_platform_new = 'win64'
            else:
                chromedriver_platform_new = 'win32'
        elif platform.system() == 'Darwin':
            if platform.processor().lower() == 'arm64':
                chromedriver_platform = 'mac_arm64'
                chromedriver_platform_new = 'mac-arm64'
            else:
                chromedriver_platform = 'mac64'
                chromedriver_platform_new = 'mac-x64'
        else:
            chromedriver_platform = 'linux64'
            chromedriver_platform_new = 'linux64'

        chromedriver_url = None
        chromedriver_version_url = f'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}'
        r = requests.get(chromedriver_version_url)
        if r.ok:
            new_chrome = False
            chromedriver_version = r.text
            chromedriver_url = f'https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_{chromedriver_platform}.zip'
        else:
            new_chrome = True
            r = requests.get('https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json')
            versions_dict = json.loads(r.text)
            chromedriver_list = versions_dict \
                .get('milestones', {}) \
                .get(major_version, {}) \
                .get('downloads', {}) \
                .get('chromedriver', {})
        
            chromedriver_url = None
            for i in chromedriver_list:
                if i.get('platform') == chromedriver_platform_new:
                    chromedriver_url = i.get('url')
        
        if not chromedriver_url:
            return ''

        if platform.system() == 'Windows':
            chromedriver_name = 'chromedriver.exe'
        else:
            chromedriver_name = 'chromedriver'

        if new_chrome:
            chromedriver_zip_path = f'chromedriver-{chromedriver_platform_new}/{chromedriver_name}'
        else:
            chromedriver_zip_path = chromedriver_name
        
        chromedriver_path = os.path.abspath(os.path.join(chromedriver_download_dir, chromedriver_name))

        with io.BytesIO() as f:
            f.write(requests.get(chromedriver_url).content) # type: ignore[arg-type]
            with zipfile.ZipFile(f, 'r') as z, open(chromedriver_path, 'wb+') as g:
                g.write(z.read(chromedriver_zip_path))

        if platform.system() != 'Windows':
            st = os.stat(chromedriver_path)
            os.chmod(chromedriver_path, st.st_mode | stat.S_IEXEC)
        
        return chromedriver_path
    
    def killall_signal(self):
        if platform.system() == 'Windows':
            os.system('taskkill /F /im "Signal.exe"')
            os.system('taskkill /F /im "Signal Beta.exe"')
        else:
            RunBin.run_cmd(cmd_list=['killall', 'signal-desktop'], silence=True)
            RunBin.run_cmd(cmd_list=['killall', 'signal-desktop-beta'], silence=True)
    
    def launch_signal(self, signal_bin_path: str, signal_user_data_dir: str, chromedriver_path: str):
        options = webdriver.ChromeOptions()
        options.binary_location = signal_bin_path
        options.add_argument(f"user-data-dir={signal_user_data_dir}")
        options.add_argument('no-sandbox')
        service = Service(executable_path=chromedriver_path)

        self.driver = webdriver.Chrome(options=options, service=service)

    def get_cred(self) -> tuple[Optional[str], Optional[str]]:
        # https://stackoverflow.com/a/73456344
        uuid, password = None, None
        try:
            if self.signal_bin_version == 'prod':
                uuid = self.driver.execute_script('return window.reduxStore.getState().items.uuid_id')
                password = self.driver.execute_script('return window.reduxStore.getState().items.password')
            else:
                uuid = self.driver.execute_script('return window.SignalDebug.getReduxState().items.uuid_id')
                password = self.driver.execute_script('return window.SignalDebug.getReduxState().items.password')
        except JavascriptException:
            pass

        return uuid, password

    def close(self):
        self.cb_msg('Closing Signal Desktop')
        self.driver.quit()

    def launch_signal_desktop(self):
        if platform.system() == 'Windows':
            signal_bin_path_prod = os.path.expandvars("%localappdata%/Programs/signal-desktop/Signal.exe")
            signal_bin_path_beta = os.path.expandvars("%localappdata%/Programs/signal-desktop-beta/Signal Beta.exe")
            signal_user_data_dir_prod = os.path.abspath(os.path.expandvars('%appdata%/Signal'))
            signal_user_data_dir_beta = os.path.abspath(os.path.expandvars('%appdata%/Signal Beta'))
            electron_bin_path_prod = signal_bin_path_prod
            electron_bin_path_beta = signal_bin_path_beta
        elif platform.system() == 'Darwin':
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
        if major_version:
            self.cb_msg(f'Signal Desktop is using chrome version {major_version}')
        else:
            self.cb_msg('Unable to determine Signal Desktop chrome version')
            return
        
        chromedriver_path, local_chromedriver_version = self.get_local_chromedriver(chromedriver_download_dir=self.chromedriver_download_dir)
        if chromedriver_path and local_chromedriver_version == major_version:
            self.cb_msg(f'Found chromedriver version {local_chromedriver_version}, skip downloading')
        else:
            chromedriver_path = self.download_chromedriver(major_version, chromedriver_download_dir=self.chromedriver_download_dir)
            if chromedriver_path == '':
                self.cb_msg('Unable to download suitable chromedriver')
                return

        self.cb_msg('Killing all Signal Desktop processes')
        self.killall_signal()

        self.cb_msg('Starting Signal Desktop with Selenium')
        self.launch_signal(signal_bin_path, signal_user_data_dir, chromedriver_path)