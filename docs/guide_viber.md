# Downloading Viber stickers
sticker-convert supports downloading viber stickers from share link of sticker pack.

# Uploading Viber stickers
Viber authentication data required for uploading Viber stickers, which could be fetched
from Viber Desktop application automatically:
1. Install Viber Desktop
2. Login to Viber Desktop
3. In sticker-convert, press `Generate` button (In GUI) or `--viber-get-auth` (In CLI)

Notice:
- Viber Desktop would be closed, launched and closed again when getting auth data.
- It may take a minute to get auth data.
- On macOS, you need to disable SIP and will be asked for user password.
- For atypical installation of Viber Desktop, you may specify Viber Desktop application
location by using `--viber-bin-path`.
- `m_token`, `m_ts` and `member_id` are required.
- `m_ts` is the unix timestamp when `m_token` is generated.
- `m_token` expires after 13800 seconds (230 minutes).

# References
For more info, please refer to https://help.viber.com/hc/en-us/articles/9204828903837-Use-and-create-stickers-on-Rakuten-Viber