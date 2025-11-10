# sticker-convert
### [ [English](/README.md) | [繁體中文](/docs/zh_TW/README.md) | [简体中文](/docs/zh_CN/README.md) | [日本語](/docs/ja_JP/README.md) ]

![/imgs/banner.png](https://socialify.git.ci/laggykiller/sticker-convert/image?description=1&font=Inter&logo=https%3A%2F%2Fgithub.com%2Flaggykiller%2Fsticker-convert%2Fblob%2Fmaster%2Fsrc%2Fsticker_convert%2Fresources%2Fappicon.png%3Fraw%3Dtrue&name=1&owner=1&theme=Dark)
![/imgs/screenshot](/imgs/screenshot.png)

- 一個用於建立、下載、轉換+壓縮並上傳即時通訊應用程式的貼圖的 Python 腳本。
- 提供圖形使用者介面 (GUI) 和命令列介面 (CLI)，可在 Windows、macOS 和 Linux 系統上運作。
- 目前支援 Signal、Telegram、WhatsApp（建立 .wastickers 檔案）、Line（僅下載）、Kakao（僅下載）、Naver Band（僅下載）、OGQ（僅下載）、Viber、Discord（僅下載）和 iMessage（建立 Xcode 貼紙包專案）。
- 支援靜態和動態貼紙，並支援透明度。

## 下載
- [預編譯版本](https://github.com/laggykiller/sticker-convert/releases)，適用於 Windows、macOS 和 Linux（AppImage 格式）。
    - Windows：解壓縮下載的檔案並執行 `sticker-convert.exe`，或下載 msi 檔案進行安裝。
    - macOS：解壓縮下載的文件，首次使用時按住 Ctrl 鍵並點擊 `hold_control_and_click_open_me.command` 打開，之後使用 `sticker-convert.app` 打開。
    - Linux：
        - AppImage：使用 `chmod +x` 指令為下載的 AppImage 檔案新增權限並執行。
        - Zip：解壓縮並執行 `sticker-convert.bin`。
        - [AUR 套件](https://aur.archlinux.org/packages/sticker-convert)：`makepkg -si`
- [pip 套件](https://pypi.org/project/sticker-convert/)：`pip install sticker-convert`。使用 `sticker-convert` 或 `python -m sticker_convert` 啟動。
- [Docker 映像](https://hub.docker.com/r/laggykiller/sticker-convert) 用於在 Linux 上運行。
- [無需下載，在 Google Colab 中試用](https://colab.research.google.com/github/laggykiller/sticker-convert/blob/master/sticker_convert_colab.ipynb)（需要 Google 帳戶），程式碼在 Google 伺服器上運行，結果從 Google 雲端硬碟取得。但是，速度可能比在您的電腦上運行慢。 （如果不轉換為 .apng 格式，每個檔案大約需要 15 秒；如果轉換為 .apng 格式，則每個檔案大約需要 1 分鐘。）

## 目錄
- [兼容性](#兼容性)
- [使用説明 (GUI)](#使用説明-gui)
- [使用説明 (CLI)](#使用説明-cli)
- [使用説明 (Docker)](#使用説明-docker)
- [直接執行Python腳本及編譯](#直接執行Python腳本及編譯)
- [常見問題](#常見問題)
    - [平台特定指南 (例如: 取得憑證)](#平台特定指南-例如-取得憑證)
    - [轉換速度慢](#轉換速度慢)
    - [記憶體不足/系統凍結](#記憶體不足系統凍結)
    - [macOS提示程式來自未知開發者](#macOS提示程式來自未知開發者)
    - [我想上傳stickers_output中尚未上傳的貼紙](#我想上傳stickers_output中尚未上傳的貼紙)
    - [憑證存放在哪裡? ](#憑證存放在哪裡)
    - [power和steps是什麼意思?](#power和steps是什麼意思)
- [未來計畫](#未來計畫)
- [鳴謝](#鳴謝)
- [免責聲明](#免責聲明)

## 兼容性
| 應用程式                               | ⬇️ 下載                         | ⬆️ 上載                                       |
| ------------------------------------- | --------------------------------| --------------------------------------------- |
| [Signal](/docs/zh_TW/guide_signal.md)     | ✅                              | ✅ (需要`uuid`&`password`或手動上傳)           |
| [Telegram](/docs/zh_TW/guide_telegram.md) | ✅ (需要`token`或telethon)      | ✅ (需要`token`&`user_id`或telethon或手動上傳) |
| [WhatsApp](/docs/zh_TW/guide_whatsapp.md) | ⭕ (以安卓或網頁版)              | ⭕ (創建`.wastickers`, 以Sticker Maker輸入)   |
| [Line](/docs/zh_TW/guide_line.md)         | ✅                              | 🚫 (需要人工審核)                             |
| [Kakao](/docs/zh_TW/guide_kakao.md)       | ✅ (需要'auth_token'下載動態貼圖) | 🚫 (需要人工審核)                            |
| [Band](/docs/zh_TW/guide_band.md)         | ✅                              | 🚫 (需要人工審核)                             |
| [OGQ](/docs/zh_TW/guide_ogq.md)           | ✅                              | 🚫 (需要人工審核)                             |
| [Viber](/docs/zh_TW/guide_viber.md)       | ✅                              | ✅ (需要`viber_auth`)                        |
| [Discord](/docs/zh_TW/guide_discord.md)   | ✅ (需要`token`)                | 🚫                                           |
| [iMessage](/docs/zh_TW/guide_imessage.md) | 🚫                              | ⭕ (創建Xcode貼圖包專案以作側載)               |

✅ = 支援 ⭕ = 部分支援 🚫 = 不支援

- Signal
    - 下載: 支援 (例：`https://signal.art/addstickers/#pack_id=xxxxx&pack_key=xxxxx`)
    - 上載: 支援
        - 如果要在此程式裏上載貼圖包，`uuid`和`password`是必要的。請參考常見問題。
        - 另一選擇是用Signal桌面版手動上載此程式製作出來的貼圖檔。
- Telegram
    - 下載: 支援貼圖和自訂表情符號 (例：`https://telegram.me/addstickers/xxxxx`)，但需要bot token或使用Telethon
    - 上載: 支援貼圖和自訂表情符號，但需要bot token和user_id或使用Telethon。你亦可以手動上載此程式製作出來的貼圖檔。
- WhatsApp
    - 下載：您需要手動尋找貼圖包/從手機或 WhatsApp 網頁版提取。請參閱 [/docs/zh_TW/guide_whatsapp.md](/docs/zh_TW/guide_whatsapp.md)。
    - 上傳：程式可以建立 .wastickers 文件，然後可以透過第三方應用程式「Sticker Maker」將其匯入 WhatsApp（本倉庫作者與 Sticker Maker 無任何關聯）。請參閱常見問題。
- Line
    - 下載: 支援 (例：`https://store.line.me/stickershop/product/1234/en`或`line://shop/detail/1234`或`1234`)
        - 官方網站搜尋：https://store.line.me/stickershop
        - 在非官方網站上搜尋（包括區域鎖定和過期的套件）：http://www.line-stickers.com/
        - 欲了解更多資訊：https://github.com/doubleplusc/Line-sticker-downloader
    - 上傳：不支援。您需要手動提交貼紙包以獲得批准才能在應用程式中使用。
- Kakao
    - 下載: 支援 (例：`https://e.kakao.com/t/xxxxx`或`https://emoticon.kakao.com/items/xxxxx`或`4404400`). 有點複雜，請參照[/docs/zh_TW/guide_kakao.md](/docs/zh_TW/guide_kakao.md)
    - 上載: 不支援。你需要手動上傳貼圖包作檢核以在程式裏使用。
- Band
    - 下載: 支援 (例：`https://www.band.us/sticker/xxxx`或`2535`)。有關如何取得分享連結，請參照[/docs/zh_TW/guide_band.md](/docs/zh_TW/guide_band.md)
    - 上載: 不支援。你需要手動上傳貼圖包作檢核以在程式裏使用。
- OGQ
    - 下載: 支援 (例：`https://ogqmarket.naver.com/artworks/sticker/detail?artworkId=xxxxx`)
    - 上載: 不支援。你需要手動上傳貼圖包作檢核以在程式裏使用。
- Viber
    - 下載: 支援 (例：`https://stickers.viber.com/pages/example`或`https://stickers.viber.com/pages/custom-sticker-packs/example`)
    - 上載: 支援。上載Viber貼圖時需要Viber認證資料。認證資料可在Viber桌面版中自動取得。
- Discord
    - 下載: 支援 (例：`https://discord.com/channels/169256939211980800/@home`或`169256939211980800`)，但需要user token。
    - 上載: 不支援
- iMessage
    - 下載: 不支援
    - 上載: 此程式可以創建Xcode貼圖包專案以作編譯和側載。

## 使用説明 (GUI)
1. 執行`sticker-convert.exe`、`sticker-convert.app`或`python3 src/sticker-convert.py`
2. 選擇輸入來源
    - 如要下載，請輸入URL地址（如適用）
    - 如果您使用本機文件，請選擇輸入目錄。預設為程式所在目錄下的名為「stickers_input」的資料夾。請將要轉換的檔案放入該目錄。
3. 選擇壓縮選項。如果不確定，請從選項選單中選擇預設值。
4. 如果您只想下載文件，請勾選「不壓縮」。
5. 選擇輸出選項和輸出目錄。
6. 輸入貼紙包的標題和作者。
7. 如果您想從 Telegram 下載/上傳貼紙，或從 Signal 上傳貼紙，請輸入憑證（更多信息，請參閱“兼容性”和“常見問題解答”部分）。
8. 按下「開始」按鈕。

## 使用説明 (CLI)
如要使用CLI模式，請輸入任何參數

```
usage: sticker-convert.py [-h] [--version] [--no-confirm] [--no-progress] [--custom-presets CUSTOM_PRESETS]
                          [--lang {en_US,ja_JP,zh_CN,zh_TW}] [--input-dir INPUT_DIR]
                          [--download-auto DOWNLOAD_AUTO | --download-signal DOWNLOAD_SIGNAL | --download-telegram DOWNLOAD_TELEGRAM | --download-telegram-telethon DOWNLOAD_TELEGRAM_TELETHON | --download-line DOWNLOAD_LINE | --download-kakao DOWNLOAD_KAKAO | --download-band DOWNLOAD_BAND | --download-ogq DOWNLOAD_OGQ | --download-viber DOWNLOAD_VIBER | --download-discord DOWNLOAD_DISCORD | --download-discord-emoji DOWNLOAD_DISCORD_EMOJI]
                          [--output-dir OUTPUT_DIR] [--author AUTHOR] [--title TITLE]
                          [--export-signal | --export-telegram | --export-telegram-emoji | --export-telegram-telethon | --export-telegram-emoji-telethon | --export-viber | --export-whatsapp | --export-imessage]
                          [--no-compress]
                          [--preset {auto,signal,telegram,telegram_emoji,whatsapp,line,kakao,band,ogq,viber,discord,discord_emoji,imessage_small,imessage_medium,imessage_large,custom}]
                          [--steps STEPS] [--processes PROCESSES] [--fps-min FPS_MIN] [--fps-max FPS_MAX]
                          [--fps-power FPS_POWER] [--res-min RES_MIN] [--res-max RES_MAX] [--res-w-min RES_W_MIN]
                          [--res-w-max RES_W_MAX] [--res-h-min RES_H_MIN] [--res-h-max RES_H_MAX]
                          [--res-power RES_POWER] [--res-snap-pow2] [--no-res-snap-pow2] [--quality-min QUALITY_MIN]
                          [--quality-max QUALITY_MAX] [--quality-power QUALITY_POWER] [--color-min COLOR_MIN]
                          [--color-max COLOR_MAX] [--color-power COLOR_POWER] [--duration-min DURATION_MIN]
                          [--duration-max DURATION_MAX] [--padding-percent PADDING_PERCENT] [--bg-color BG_COLOR]
                          [--vid-size-max VID_SIZE_MAX] [--img-size-max IMG_SIZE_MAX] [--vid-format VID_FORMAT]
                          [--img-format IMG_FORMAT] [--fake-vid] [--no-fake-vid] [--scale-filter SCALE_FILTER]
                          [--quantize-method QUANTIZE_METHOD] [--cache-dir CACHE_DIR] [--chromium-path CHROMIUM_PATH]
                          [--default-emoji DEFAULT_EMOJI] [--signal-uuid SIGNAL_UUID]
                          [--signal-password SIGNAL_PASSWORD] [--signal-get-auth] [--telegram-token TELEGRAM_TOKEN]
                          [--telegram-userid TELEGRAM_USERID] [--telethon-setup] [--kakao-auth-token KAKAO_AUTH_TOKEN]
                          [--kakao-get-auth-android-login] [--kakao-get-auth-desktop-memdump]
                          [--kakao-get-auth-desktop-login] [--kakao-bin-path KAKAO_BIN_PATH]
                          [--kakao-username KAKAO_USERNAME] [--kakao-password KAKAO_PASSWORD]
                          [--kakao-country-code KAKAO_COUNTRY_CODE] [--kakao-phone-number KAKAO_PHONE_NUMBER]
                          [--kakao-device-uuid KAKAO_DEVICE_UUID] [--line-get-auth] [--line-cookies LINE_COOKIES]
                          [--viber-auth VIBER_AUTH] [--viber-get-auth VIBER_GET_AUTH]
                          [--viber-bin-path VIBER_BIN_PATH] [--discord-get-auth] [--discord-token DISCORD_TOKEN]
                          [--save-cred]

sticker-convert的CLI

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --no-confirm          不要訊問任何問題。
  --no-progress         不要在文字界面顯示進度計。
  --custom-presets CUSTOM_PRESETS
                        選擇一個自訂的compression.json檔案，
                        請參考compression.json的格式，
                        請注意如果'custom_preset.json'若存在於設定值路徑，它將會被載入。
  --lang {en_US,ja_JP,zh_CN,zh_TW}
                        選擇語言(預設為系統語言)。

輸入選項:
  --input-dir INPUT_DIR
                        選擇輸入路徑。
  --download-auto DOWNLOAD_AUTO
                        自動偵測URL類型並下載
                        (支援輸入來源: Signal, Telegram, Line, Kakao, Naver Band, OGQ, Viber, Discord)
  --download-signal DOWNLOAD_SIGNAL
                        從URL下載Signal貼圖
                        (例子: https://signal.art/addstickers/#pack_id=xxxxx&pack_key=xxxxx)
  --download-telegram DOWNLOAD_TELEGRAM
                        從URL下載Telegram貼圖
                        (例子: https://telegram.me/addstickers/xxxxx
                         OR https://telegram.me/addemoji/xxxxx)
  --download-telegram-telethon DOWNLOAD_TELEGRAM_TELETHON
                        從URL以Telethon下載Telegram貼圖
                        (例子: https://telegram.me/addstickers/xxxxx
                         OR https://telegram.me/addemoji/xxxxx)
  --download-line DOWNLOAD_LINE
                        從URL/ID下載Line貼圖
                        (例子: https://store.line.me/stickershop/product/1234/en
                         OR https://line.me/S/sticker/1234/?lang=en OR line://shop/detail/1234 OR 1234)
  --download-kakao DOWNLOAD_KAKAO
                        從URL/ID下載Kakao貼圖
                        (例子: https://e.kakao.com/t/xxxxx 
                        OR https://emoticon.kakao.com/items/xxxxx OR 4404400)
  --download-band DOWNLOAD_BAND
                        從URL/ID下載Naver Band貼圖
                        (例子: https://www.band.us/sticker/xxxx OR 2535)
  --download-ogq DOWNLOAD_OGQ
                        從URL下載OGQ貼圖
                        (Example: https://ogqmarket.naver.com/artworks/sticker/detail?artworkId=xxxxx)
  --download-viber DOWNLOAD_VIBER
                        從URL下載Viber貼圖
                        (例子: https://stickers.viber.com/pages/example
                        OR https://stickers.viber.com/pages/custom-sticker-packs/example)
  --download-discord DOWNLOAD_DISCORD
                        從頻道URL/ID下載Discord貼圖
                        (例子: https://discord.com/channels/169256939211980800/@home
                        OR 169256939211980800)
  --download-discord-emoji DOWNLOAD_DISCORD_EMOJI
                        從頻道URL/ID下載Discord表情
                        (例子: https://discord.com/channels/169256939211980800/@home
                        OR 169256939211980800)

輸出選項:
  --output-dir OUTPUT_DIR
                        選擇輸出路徑。
  --author AUTHOR       設定表情包的作者。
  --title TITLE         設定表情包的名稱。
  --export-signal       上載至Signal
  --export-telegram     上載至Telegram
  --export-telegram-emoji
                        上載至Telegram (Custom emoji)
  --export-telegram-telethon
                        以Telethon上載至Telegram *不建議，但可使連結結尾不含_by_xxxbot*
  --export-telegram-emoji-telethon
                        以Telethon上載至Telegram (自訂表情符號) *不建議，但可使連結結尾不含_by_xxxbot*
  --export-viber        上載至Viber
  --export-whatsapp     創建 .wastickers檔案以供上載至WhatsApp
  --export-imessage     創建Xcode專案以供輸入至iMessage

壓縮選項:
  --no-compress         不要壓縮檔案，適用於只下載貼圖。
  --preset {auto,signal,telegram,telegram_emoji,whatsapp,line,kakao,band,ogq,viber,discord,discord_emoji,imessage_small,imessage_medium,imessage_large,custom}
                        套用壓縮的預設值。
  --steps STEPS         設定最少與最大值之間的分割數。
                        數值越大 = 較慢但生成的檔案更接近檔案大小限制。
  --processes PROCESSES
                        設定進程數量。預設為系統邏輯處理器數量的一半。
                        數量越大 = 壓縮較快但更耗用更多資源。
  --fps-min FPS_MIN     設定最少幀率。
  --fps-max FPS_MAX     設定最大幀率。
  --fps-power FPS_POWER
                        可設定為-1至正無限。倍數越少 = 更重視該變量值，儘可能保持該變量值更大。
  --res-min RES_MIN     設定最低的解像度。
  --res-max RES_MAX     設定最高的解像度。
  --res-w-min RES_W_MIN
                        設定最低的闊度。
  --res-w-max RES_W_MAX
                        設定最高的闊度。
  --res-h-min RES_H_MIN
                        設定最低的高度。
  --res-h-max RES_H_MAX
                        設定最高的高度。
  --res-power RES_POWER
                        可設定為-1至正無限。倍數越少 = 更重視該變量值，儘可能保持該變量值更大。
  --res-snap-pow2       將解像度數值約至最近的2次方數 (1,2,4,8,16,...).
                        若最少與最大的解像度數值之間不存在任何2次方數，此選項會被忽略。
  --no-res-snap-pow2    禁用res_snap_pow2
  --quality-min QUALITY_MIN
                        設定最低的質量。
  --quality-max QUALITY_MAX
                        設定最高的質量。
  --quality-power QUALITY_POWER
                        可設定為-1至正無限。倍數越少 = 更重視該變量值，儘可能保持該變量值更大。
  --color-min COLOR_MIN
                        設定最少顏色數量（只適用於png及apng檔案）。
  --color-max COLOR_MAX
                        設定最大顏色數量（只適用於png及apng檔案）。
  --color-power COLOR_POWER
                        可設定為-1至正無限。倍數越少 = 更重視該變量值，儘可能保持該變量值更大。
  --duration-min DURATION_MIN
                        設定最少的動畫長度限制（毫秒）。
  --duration-max DURATION_MAX
                        設定最大的動畫長度限制（毫秒）。
  --padding-percent PADDING_PERCENT
                        設定邊界佔用百分比。
  --bg-color BG_COLOR   設定自訂背景顏色（以rrggbbaa為格式）。
                        例子: 00ff0000是透明值0的綠色.
                        預設為若影像明亮則背景顏色設為黑色，若影像黑暗則背景顏色設為白色。
                        注意: 若檔案格式支援透明色，將不會看到背景顏色。
  --vid-size-max VID_SIZE_MAX
                        設定最大動畫檔案大小。
  --img-size-max IMG_SIZE_MAX
                        設定最大圖片檔案大小。
  --vid-format VID_FORMAT
                        設定動畫檔案格式。
  --img-format IMG_FORMAT
                        設定圖片檔案格式。
  --fake-vid            將圖片轉換（假扮）成動畫。
                        下列情況可以應用:
                        (1) 動畫檔案的大小限制大於圖片；
                        (2) 混合圖片和動畫於同一表情包。
  --no-fake-vid         禁用fake_vid
  --scale-filter SCALE_FILTER
                        設定縮放濾鏡。預設為bicubic。可使用值為：
                        - nearest = 使用最近像素（適用於像素風影像）
                        - box = 與nearest相似，但下採樣更好
                        - bilinear = 線性插值
                        - hamming = 與bilinear相似，但下採樣更好
                        - bicubic = 三次樣條插值
                        - lanczos = 高質素的下採樣濾鏡
  --quantize-method QUANTIZE_METHOD
                        設定量化方式。預設為imagequant。可選擇：
                        - imagequant = 速度+ 壓縮度+ 質素++++ 支援RGBA
                        - fastoctree = 速度++ 壓縮度++++ 質素+ 支援RGBA
                        - maxcoverage = 速度+++ 壓縮度+++ 質素++ 不支援RGBA
                        - mediancut = 速度++++ 壓縮度++ 質素+++ 不支援RGBA
                        - none = 禁止量子化，檔案大
                        質素低會令影像看起來一格格。
  --cache-dir CACHE_DIR
                        設定自訂快存路徑。
                        可用於除錯，或設定cache_dir於快取記憶體以加速轉換速度。
  --chromium-path CHROMIUM_PATH
                        設定（基於）Chromium/Chrome瀏覽器的路徑。
                        需用於轉換SVG檔案。
                        留空白以自動偵測。
  --default-emoji DEFAULT_EMOJI
                        設定上載Signal和Telegram貼圖包的預設顏文字。

認證選項:
  --signal-uuid SIGNAL_UUID
                        設定Signal uuid。需用於上載Signal貼圖。
  --signal-password SIGNAL_PASSWORD
                        設定Signal password。需用於上載Signal貼圖。
  --signal-get-auth     產生Signal uuid和password。
  --telegram-token TELEGRAM_TOKEN
                        設定Telegram token。需用於上載和下載Telegram貼圖。
  --telegram-userid TELEGRAM_USERID
                        設定Telegram user_id (從真實賬戶，而非機械人帳戶)n。需用於上載和下載Telegram貼圖。
  --telethon-setup      設定Telethon
  --kakao-auth-token KAKAO_AUTH_TOKEN
                        設定Kakao auth_token。需用於從 https://e.kakao.com/t/xxxxx 上載和下載動態貼圖。
  --kakao-get-auth-android-login
                        透過模擬登入Kakao安卓版取得auth_token。需要Kakao使用者名稱、密碼、國家代碼和電話號碼。
  --kakao-get-auth-desktop-memdump
                        透過memdump從已安裝的Kakao桌面版中取得 Kakao auth_token。
  --kakao-get-auth-desktop-login
                        透過模擬登入Kakao桌面版取得auth_token。需要Kakao使用者名稱、密碼。
  --kakao-bin-path KAKAO_BIN_PATH
                        設定Kakao桌面版路徑以開啟程式並取得auth_token。
                        適用於免安裝版。
  --kakao-username KAKAO_USERNAME
                        設定Kakao使用者名，即註冊Kakao帳戶時使用的電子郵件地址或電話號碼
                        範例：+447700900142
                        需用於模擬安卓/桌面版登入以取得Kakao auth_token。
  --kakao-password KAKAO_PASSWORD
                        設定Kakao帳戶密碼。
                        需用於模擬安卓/桌面版登入以取得Kakao auth_token。
  --kakao-country-code KAKAO_COUNTRY_CODE
                        設定Kakao國際電話區號。
                        範例: 82 (韓國), 44 (英國), 1 (美國).
                        需用於模擬安卓版登入以取得Kakao auth_token。
  --kakao-phone-number KAKAO_PHONE_NUMBER
                        設定Kakao電話號碼 (與Kakao帳號連結的電話號碼)
                        不要輸入國際電話區號
                        範例: 7700900142
                        用於收/發短信.
                        需用於模擬安卓版登入以取得Kakao auth_token。
  --kakao-device-uuid KAKAO_DEVICE_UUID
                        設定Kakao device uuid以登入桌面版。預設為真實device uuid。
                        選填，以模擬桌面版登入以取得Kakao auth_token。
  --line-get-auth       從瀏覽器取得Line cookies, 以用於製作訊息貼圖。
  --line-cookies LINE_COOKIES
                        設定Line cookies, 以用於製作訊息貼圖。
  --viber-auth VIBER_AUTH
                        設定Viber身份驗證數據。
                        用於上載Viber貼圖。
  --viber-get-auth VIBER_GET_AUTH
                        產生Viber身份驗證數據。
  --viber-bin-path VIBER_BIN_PATH
                        指明Viber桌面版程式路徑。
                        可用於免安裝版。
  --discord-get-auth    取得Discord token。
  --discord-token DISCORD_TOKEN
                        設定Discord token。用於下載Discord貼圖和表情。
  --save-cred           儲存身份驗證數據。
```

如要直接執行Python 腳本，請執行`src/sticker-convert.py`

如以pip安裝，請執行`sticker-convert`或`python -m sticker_convert`

如在macOS中執行，請執行`sticker-convert.app/Contents/MacOS/sticker-convert-cli`

例子:

只下載一個來源

`sticker-convert --download-signal <url> --no-compress`

轉換本機檔案到Signal兼容貼圖檔案

`sticker-convert --input-dir ./custom-input --output-dir ./custom-output --preset signal`

`sticker-convert --preset signal`

轉換Signal貼圖到Telegram並上載

`sticker-convert --download-signal <url> --export-telegram --telegram-token <你的_bot_token> --telegram-userid <你的_userid_here> --save-cred`

轉換本機檔案到多個格式並輸出

`sticker-convert --export-telegram --export-signal`

轉換本機檔案到自定義格式

`sticker-convert --fps-min 3 --fps-max 30 --quality-min 30 --quality-max 90 --res-min 512 --res-max 512 --steps 10 --vid-size-max 500000 --img-size-max 500000 --vid-format .apng --img-format .png`

提示：使用CLI以一個命令轉換多個貼圖！

下列例子轉換兩個Line貼圖包到Signal，Telegram和WhatsApp
```
sticker-convert --no-confirm --download-auto https://store.line.me/stickershop/product/1/en --export-signal
sticker-convert --no-confirm --export-telegram
sticker-convert --no-confirm --export-whatsapp

sticker-convert --no-confirm --download-line https://store.line.me/stickershop/product/2/en --preset signal --export-signal
sticker-convert --no-confirm --preset telegram --export-telegram
sticker-convert --no-confirm --preset whatsapp --export-whatsapp
```

請留意轉換結果可在export-result中查閲

## 使用説明 (Docker)
![/imgs/screenshot-docker-gui.png](/imgs/screenshot-docker-gui.png)

下載
```
# 選項1: 從Dockerhub
## 完整版
docker pull laggykiller/sticker-convert:latest
## 沒有多語言, Signal 桌面版, Viber 桌面版, Kakao 桌面版, Chromium
docker pull laggykiller/sticker-convert:latest-min-gui
## 沒有多語言, Signal 桌面版, Viber 桌面版, Kakao 桌面版, Chromium；只有CLI
docker pull laggykiller/sticker-convert:latest-min-cli

# 選項2: 從ghcr
## 完整版
docker pull ghcr.io/laggykiller/sticker-convert:latest
## 沒有多語言, Signal 桌面版, Viber 桌面版, Kakao 桌面版, Chromium
docker pull ghcr.io/laggykiller/sticker-convert:latest-min-gui
## 沒有多語言, Signal 桌面版, Viber 桌面版, Kakao 桌面版, Chromium；只有CLI
docker pull ghcr.io/laggykiller/sticker-convert:latest-min-cli
```

執行（GUI）
```
docker run -d -it --name sticker-convert \
    -v /path/to/your/stickers_input:/app/stickers_input \
    -v /path/to/your/stickers_output:/app/stickers_output \
    -p 5800:5800 \ # Port for Web UI
    -p 5900:5900 \ # Optional for VNC
    laggykiller/sticker-convert:latest
```

執行（CLI）
```
docker run -d -it --name sticker-convert \
    -v /path/to/your/stickers_input:/app/stickers_input \
    -v /path/to/your/stickers_output:/app/stickers_output \
    laggykiller/sticker-convert:latest \
    python3 /app/sticker-convert.py --help
```

你亦可以使用docker-compose.yml
```
docker compose up
```

建構
```
docker build --tag sticker-convert:latest --target full .
docker build --tag sticker-convert:latest-min-cli --target min-cli .
docker build --tag sticker-convert:latest-min-gui --target min-gui .
```

請留意GUI版本是基於https://github.com/jlesage/docker-baseimage-gui.
若要開啓GUI，請在運行docker image的電腦以瀏覽器到訪`localhost:5800`
另一方法是以VNC軟件連接`localhost:5900`

## 直接執行Python腳本及編譯
請參照 [/docs/zh_TW/COMPILING.md](/docs/zh_TW/COMPILING.md)

## 常見問題

### 平台特定指南 (例如: 取得憑證)
- [Signal](/docs/zh_TW/guide_signal.md)
- [Telegram](/docs/zh_TW/guide_telegram.md)
- [WhatsApp](/docs/zh_TW/guide_whatsapp.md)
- [Line](/docs/zh_TW/guide_line.md)
- [Kakao](/docs/zh_TW/guide_kakao.md)
- [Viber](/docs/zh_TW/guide_viber.md)
- [Discord](/docs/zh_TW/guide_discord.md)
- [iMessage](/docs/zh_TW/guide_imessage.md)

### 轉換速度慢
試試以下建議：
- 增加進程數（`--processes`）
    - 但增加進程數超過預設值實際上可能會降低速度
- 減少步驟數（`--steps`）
    - 但減少過多步驟可能會導致品質下降

### 記憶體不足/系統凍結
嘗試減少進程數（`--processes`）

### macOS提示程式來自未知開發者
要成為認證開發者，我需要每年向蘋果支付 99 美元。

有兩種方法可以繞過這個問題：

1. 永久方法：在執行 `sticker-convert` 之前，打開終端機並執行 `sudo spctl --master-disable` 指令。
2. 臨時方法：在解壓縮下載的 zip 檔案之前，開啟終端並執行 `xattr -d com.apple.quarantine ./downloads/sticker-convert-macos.zip` 指令。

如果 macOS 仍然對某些二進位檔案（例如 apngasm）發出警告，請前往`系統偏好設定 > 安全性與隱私`，然後點擊每個檔案`仍然開啟`。

請訪問此頁面了解更多：https://disable-gatekeeper.github.io/

### 我想上傳stickers_output中尚未上傳的貼紙
CLI：執行命令時新增參數 `--no-compress --export-xxxxx`
GUI：選擇`從本機路徑`作為輸入來源，勾選`不壓縮`複選框，並選擇`上載至xxxxx`作為輸出選項。

### 憑證存放在哪裡? 
憑證儲存在 creds.json 檔案中。

預設情況下，它應該位於程式運行所在的相同目錄下。

但是，如果目錄不可寫入（例如，在 macOS 中安裝到 `/Applications`，或在 Linux 中安裝到 `/usr/local/bin`），則 `creds.json` 檔案將儲存在下列位置：
- Windows：`%APPDATA%/sticker-convert/creds.json`
- 其他：`~/.config/sticker-convert/creds.json`

### power和steps是什麼意思?
這是使用二分法尋找最優壓縮設定。 `power` 參數允許數值「偏向」一側（負值會使sticker-convert嘗試更多較大的值；`power` 設定為 1 會使 sticker-convert將其嘗試次數均勻地分配在最小值和最大值之間；`power`大於 1 會使sticker-convert嘗試更多較小的值）。

為了說明這一點，讓我們來看看 `--steps 16 --fps-min 5 --fps-max 30 --fps-power 3.0` 的作用。

1. 我們會從 `8/16`（16 步中的第 8 步）開始，這是中間點。
2. 我們將使用冪運算計算一個因子：`(8/16)^3.0 = 0.125`
3. 幀率 (fps) 的設定公式為 `round((max - min) * step / steps * factor + min)`，即 `round((16-1) * 8 / 16 * 0.125 + 5) = round(5.9375) = 6`。這意味著幀率將設定為 6。
4. 如果檔案大小太小，我們將嘗試 `4/16`（16 步中的第 4 步，即 0 到 8 的中間值）。否則，我們將嘗試 `10/16`（16 步中的第 10 步，即 8 到 16 的中間值）。
5. 重複步驟 1-3。

## 未來計畫
請參閲[/docs/TODO.md](/docs/TODO.md)

## 鳴謝
- Signal 和 Telegram 貼紙資訊：https://github.com/teynav/signalApngSticker
- Line 和 Kakao 貼圖資訊：https://github.com/star-39/moe-sticker-bot
- Line 貼圖資訊：https://github.com/doubleplusc/Line-sticker-downloader
- Kakao 動態貼圖資訊：https://gist.github.com/chitacan/9802668
- Kakao 動態貼圖的下載與解密：https://github.com/blluv/KakaoTalkEmoticonDownloader
- 尋找瀏覽器執行檔路徑：https://github.com/roniemartinez/browsers
- 應用程式圖示來自 [Icons8](https://icons8.com/)
- 橫幅由 [GitHub Socialify](https://socialify.git.ci/) 生成
- Windows 系統上的免費程式碼簽署由 [SignPath.io](https://about.signpath.io/) 提供由 [SignPath Foundation](https://signpath.org/) 頒發的憑證

## 免責聲明
- 本代碼庫作者與 Signal、Telegram、WhatsApp、Line、Kakao、Naver Band、OGQ、Viber、Discord、iMessage 或 Sticker Maker 沒有任何關聯。
- 本代碼庫作者對因使用本倉庫而產生的任何法律後果和損失概不負責。
