# Downloading Mastodon custom emojis
Only Mastodon URL required, cookies not necessary.

# Uploading Mastodon custom emojis
If cookies not given, a `.tar.gz` file would be generated, which could be used for
bulk uploading to Mastodon using `toolctl`.

If cookies given, sticker-convert would attempt to upload emojis to Mastodon.

# Getting cookies

## Method 1: Automatic
1. Install Chrome browser
2. Input Mastodon URL
3. Press on `Generate` button in sticker-convert GUI
4. Press on `Get cookies` button in the window and login to Mastodon

## Method 2: Manual
1. Install `Get cookies.txt LOCALLY` extension on your browser
    - Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
    - Firefox: https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/
    - Github page: https://github.com/kairi003/Get-cookies.txt-LOCALLY
2. Login to Mastodon
3. Open `Get cookies.txt LOCALLY` extension, copy value of `_session_id`
4. Paste to `Mastodon cookies` field in sticker-convert

# Custom emojis naming
Custom emojis are downloaded and uploaded in the format of `<category>-<name>.<extension>`

Example 1: A custom emoji with name `:cat:` in category `lol` is `lol-cat.png`
Example 2: A custom emoji with name `:dog:` without category is `dog.png`