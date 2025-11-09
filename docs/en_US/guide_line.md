# Downloading Line stickers
1. You may search for stickers from https://store.line.me/stickershop or https://store.line.me/emojishop
2. Copy the URL of the sticker pack to input url of sticker-convert

# Downloading "Message stickers" with custom text
1. Input your Message stickers url, start conversion
2. A message will pop up when downloading stickers, edit line-sticker-text.txt, then continue

# Downloading "Custom stickers" with custom text
This requires Line cookies.

## Method 1: Automatic
1. Login to store.line.me
2. Press on `Generate` button in sticker-convert GUI
3. Press on `Get cookies` button in the window (Format: `key_1=value_1;key_2=value_2`)
4. Input your Custom stickers url, start conversion
5. A message will pop up when downloading stickers, edit line-sticker-text.txt, then continue

NOTICE:
- Due to [recent updates](https://github.com/borisbabic/browser_cookie3/issues/180) to chrome browser, this might not work! You will have to use manual method in such cases.
- For best chance of success, use firefox.

## Method 2: Manual
1. Install `Get cookies.txt LOCALLY` extension on your browser
    - Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
    - Firefox: https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/
    - Github page: https://github.com/kairi003/Get-cookies.txt-LOCALLY
2. Login to store.line.me
3. Open `Get cookies.txt LOCALLY` extension, select `Export Format` to `JSON` and press `Copy`
4. Paste to `Line cookies` field in sticker-convert

# Uploading Line stickers
You need to manually submit sticker pack for approval before you can use in app.