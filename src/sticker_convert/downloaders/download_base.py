#!/usr/bin/env python3
import requests

class DownloadBase:
    def __init__(self, url, out_dir, opt_cred=None, cb_msg=print, cb_msg_block=input, cb_bar=None):
        self.url = url
        self.out_dir = out_dir
        self.opt_cred = opt_cred
        self.cb_msg = cb_msg
        self.cb_msg_block = cb_msg_block
        self.cb_bar = cb_bar
    
    def download_multiple_files(self, targets, retries=3, **kwargs):
        # targets format: [(url1, dest2), (url2, dest2), ...]
        if self.cb_bar:
            self.cb_bar(set_progress_mode='determinate', steps=len(targets))

        for url, dest in targets:
            self.download_file(url, dest, retries, show_progress=False, **kwargs)

            if self.cb_bar:
                self.cb_bar(update_bar=True)

    def download_file(self, url, dest=None, retries=3, show_progress=True, **kwargs):
        result = b''
        chunk_size = 102400

        for retry in range(retries):
            try:
                response = requests.get(url, stream=True, **kwargs)
                total_length = int(response.headers.get('content-length'))

                if response.status_code != 200:
                    return False
                else:
                    self.cb_msg(f'Downloading {url}')

                if self.cb_bar and show_progress:
                    self.cb_bar(set_progress_mode='determinate', steps=(total_length/chunk_size) + 1)

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        result += chunk
                        if self.cb_bar and show_progress:
                            self.cb_bar(update_bar=True)
                
                break
            except requests.exceptions.RequestException:
                self.cb_msg(f'Cannot download {url} (tried {retry+1}/{retries} times)')
        
        if not result:
            return False
        elif dest:
            with open(dest, 'wb+') as f:
                f.write(result)
            self.cb_msg(f'Downloaded {url}')
            return True
        else:    
            return result