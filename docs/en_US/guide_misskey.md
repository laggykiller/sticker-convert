# Downloading Misskey custom emojis
Only Misskey URL required, token not necessary.

# Uploading Misskey custom emojis
If token not given, a zip file with `meta.json` would be generated, which the zip file
can be used for bulk uploading custom emojis by yourself.

If token given, sticker-convert would attempt to upload the generated zip file. If
zip file upload failed, sticker-convert would attempt to upload emojis one-by-one.

# Getting token

## Method 1: Automatic
1. Install Chrome browser
2. Input Misskey URL
3. Press on `Generate` button in sticker-convert GUI
4. Press on `Get token` button in the window and login to Misskey

## Method 2: Manual
1. Login to Misskey on browser
2. Open DevTool by pressing `F12`
3. In `Console`, enter `JSON.parse(localStorage.getItem("account")).token`, then press `Enter`
4. The result returned is the token

# Custom emojis naming
Custom emojis are downloaded and uploaded in the format of `<category>-<name>.<extension>`

Example 1: A custom emoji with name `:cat:` in category `lol` is `lol-cat.png`
Example 2: A custom emoji with name `:dog:` without category is `dog.png`