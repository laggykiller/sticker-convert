import os
import zipfile

try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system('pip3 install beautifulsoup4')
    from bs4 import BeautifulSoup

try:
    import requests
except ImportError:
    os.system('pip3 install requests')
    import requests

soup = BeautifulSoup(requests.get("https://imagemagick.org/archive/binaries").text, "html.parser")

for x in soup.find_all("a", href=True):
    file = x['href']
    if file.startswith('ImageMagick-7') and file.endswith('portable-Q16-x64.zip'):
        url = 'https://imagemagick.org/archive/binaries/' + file
        break

with open(file, 'wb+') as f:
    f.write(requests.get(url).content)

with zipfile.ZipFile(file, 'r') as zip_ref:
    zip_ref.extractall()

os.remove(file)