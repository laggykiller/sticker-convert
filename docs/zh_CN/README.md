# sticker-convert
### [ [English](/README.md) | [繁體中文](/docs/zh_TW/README.md) | [简体中文](/docs/zh_CN/README.md) | [日本語](/docs/ja_JP/README.md) ]

![/imgs/banner.png](https://socialify.git.ci/laggykiller/sticker-convert/image?description=1&font=Inter&logo=https%3A%2F%2Fgithub.com%2Flaggykiller%2Fsticker-convert%2Fblob%2Fmaster%2Fsrc%2Fsticker_convert%2Fresources%2Fappicon.png%3Fraw%3Dtrue&name=1&owner=1&theme=Dark)
![/imgs/screenshot](/imgs/screenshot.png)

- 一个用于建立、下载、转换+压缩并上传即时通讯应用程式的貼图的 Python 脚本。
- 提供图形使用者介面 (GUI) 和命令列介面 (CLI)，可在 Windows、macOS 和 Linux 系统上运作。
- 目前支援 Signal、Telegram、WhatsApp（建立 .wastickers 档案）、Line（仅下载）、Kakao（仅下载）、Naver Band（仅下载）、OGQ（仅下载）、Viber、Discord（仅下载）和 iMessage（建立 Xcode 貼纸包专案）。
- 支援静态和动态貼纸，并支援透明度。

## 下载
- [预编译版本](https://github.com/laggykiller/sticker-convert/releases)，适用于 Windows、macOS 和 Linux（AppImage 格式）。
    - Windows：解压缩下载的档案并执行 `sticker-convert.exe`，或下载 msi 档案进行安装。
    - macOS：解压缩下载的文件，首次开启 `first_launch.command`。如果无法打开，请不要点击“移到废纸篓”，而是点击“完成”。然后开启「系统偏好设定」（或较新版本的 macOS 系统中的「系统设定」），前往「隐私权与安全性」。在「一般」标签页中，您应该会看到一条关于 `first_launch.command` 被封锁的讯息，点击「强制打开」即可执行 `first_launch.command`。之后您就可以直接开启 `sticker-convert.app` 了。
    - Linux：
        - AppImage：使用 `chmod +x` 指令为下载的 AppImage 档案新增权限并执行。
        - Zip：解压缩并执行 `sticker-convert.bin`。
        - [AUR 套件](https://aur.archlinux.org/packages/sticker-convert)：`makepkg -si`
        - 注意：sticker-convert 是用 glibc 2.17 编译的，因此需要 Debian 8+ / Ubuntu 13.10 / Fedora 19+ / CentOS/RHEL 7+。
- [pip 套件](https://pypi.org/project/sticker-convert/)：`pip install sticker-convert`。使用 `sticker-convert` 或 `python -m sticker_convert` 启动。
- [Docker 映像](https://hub.docker.com/r/laggykiller/sticker-convert) 用于在 Linux 上运行。
- [无需下载，在 Google Colab 中试用](https://colab.research.google.com/github/laggykiller/sticker-convert/blob/master/sticker_convert_colab.ipynb)（需要 Google 帐户），程式码在 Google 伺服器上运行，结果从 Google 云端硬碟取得。但是，速度可能比在您的电脑上运行慢。 （如果不转换为 .apng 格式，每个档案大约需要 15 秒；如果转换为 .apng 格式，则每个档案大约需要 1 分钟。）

## 目录
- [兼容性](#兼容性)
- [使用説明 (GUI)](#使用説明-gui)
- [使用説明 (CLI)](#使用説明-cli)
- [使用説明 (Docker)](#使用説明-docker)
- [直接执行Python脚本及编译](#直接执行Python脚本及编译)
- [常见问题](#常见问题)
    - [平台特定指南 (例如: 取得凭证)](#平台特定指南-例如-取得凭证)
    - [转换速度慢](#转换速度慢)
    - [记忆体不足/系统冻结](#记忆体不足系统冻结)
    - [macOS提示程式来自未知开发者](#macOS提示程式来自未知开发者)
    - [我想上传stickers_output中尚未上传的貼纸](#我想上传stickers_output中尚未上传的貼纸)
    - [凭证存放在哪里? ](#凭证存放在哪里)
    - [power和steps是什么意思?](#power和steps是什么意思)
- [未来计画](#未来计画)
- [鸣谢](#鸣谢)
- [免责声明](#免责声明)

## 兼容性
| 应用程式                               | ⬇️ 下载                         | ⬆️ 上载                                       |
| ------------------------------------- | --------------------------------| --------------------------------------------- |
| [Signal](/docs/zh_CN/guide_signal.md)     | ✅                              | ✅ (需要`uuid`&`password`或手动上传)           |
| [Telegram](/docs/zh_CN/guide_telegram.md) | ✅ (需要`token`或telethon)      | ✅ (需要`token`&`user_id`或telethon或手动上传) |
| [WhatsApp](/docs/zh_CN/guide_whatsapp.md) | ⭕ (以安卓或网页版)              | ⭕ (创建`.wastickers`, 以Sticker Maker输入)   |
| [Line](/docs/zh_CN/guide_line.md)         | ✅                              | 🚫 (需要人工审核)                             |
| [Kakao](/docs/zh_CN/guide_kakao.md)       | ✅ (需要'auth_token'下载动态貼图) | 🚫 (需要人工审核)                            |
| [Band](/docs/zh_CN/guide_band.md)         | ✅                              | 🚫 (需要人工审核)                             |
| [OGQ](/docs/zh_CN/guide_ogq.md)           | ✅                              | 🚫 (需要人工审核)                             |
| [Viber](/docs/zh_CN/guide_viber.md)       | ✅                              | ✅ (需要`viber_auth`)                        |
| [Discord](/docs/zh_CN/guide_discord.md)   | ✅ (需要`token`)                | 🚫                                           |
| [iMessage](/docs/zh_CN/guide_imessage.md) | 🚫                              | ⭕ (创建Xcode貼图包专案以作侧载)               |

✅ = 支援 ⭕ = 部分支援 🚫 = 不支援

- Signal
    - 下载: 支援 (例：`https://signal.art/addstickers/#pack_id=xxxxx&pack_key=xxxxx`)
    - 上载: 支援
        - 如果要在此程式裏上载貼图包，`uuid`和`password`是必要的。请参考常见问题。
        - 另一选择是用Signal桌面版手动上载此程式制作出来的貼图档。
- Telegram
    - 下载: 支援貼图和自订表情符号 (例：`https://telegram.me/addstickers/xxxxx`)，但需要bot token或使用Telethon
    - 上载: 支援貼图和自订表情符号，但需要bot token和user_id或使用Telethon。你亦可以手动上载此程式制作出来的貼图档。
- WhatsApp
    - 下载：您需要手动寻找贴图包/从手机或 WhatsApp 网页版提取。请参阅 [/docs/zh_TW/guide_whatsapp.md](/docs/zh_TW/guide_whatsapp.md)。
    - 上传：程式可以建立 .wastickers 文件，然后可以透过第三方应用程式「Sticker Maker」将其汇入 WhatsApp（本仓库作者与 Sticker Maker 无任何关联）。请参阅常见问题。
- Line
    - 下载: 支援 (例：`https://store.line.me/stickershop/product/1234/en`或`line://shop/detail/1234`或`1234`)
        - 官方网站搜寻：https://store.line.me/stickershop
        - 在非官方网站上搜寻（包括区域锁定和过期的套件）：http://www.line-stickers.com/
        - 欲了解更多资讯：https://github.com/doubleplusc/Line-sticker-downloader
    - 上传：不支援。您需要手动提交贴纸包以获得批准才能在应用程式中使用。
- Kakao
    - 下载: 支援 (例：`https://e.kakao.com/t/xxxxx`或`https://emoticon.kakao.com/items/xxxxx`或`4404400`). 有点复杂，请参照[/docs/zh_CN/guide_kakao.md](/docs/zh_CN/guide_kakao.md)
    - 上载: 不支援。你需要手动上传貼图包作检核以在程式裏使用。
- Band
    - 下载: 支援 (例：`https://www.band.us/sticker/xxxx`或`2535`)。有关如何取得分享连结，请参照[/docs/zh_CN/guide_band.md](/docs/zh_CN/guide_band.md)
    - 上载: 不支援。你需要手动上传貼图包作检核以在程式裏使用。
- OGQ
    - 下载: 支援 (例：`https://ogqmarket.naver.com/artworks/sticker/detail?artworkId=xxxxx`)
    - 上载: 不支援。你需要手动上传貼图包作检核以在程式裏使用。
- Viber
    - 下载: 支援 (例：`https://stickers.viber.com/pages/example`或`https://stickers.viber.com/pages/custom-sticker-packs/example`)
    - 上载: 支援。上载Viber貼图时需要Viber认证资料。认证资料可在Viber桌面版中自动取得。
- Discord
    - 下载: 支援 (例：`https://discord.com/channels/169256939211980800/@home`或`169256939211980800`)，但需要user token。
    - 上载: 不支援
- iMessage
    - 下载: 不支援
    - 上载: 此程式可以创建Xcode貼图包专案以作编译和侧载。

## 使用説明 (GUI)
1. 执行`sticker-convert.exe`、`sticker-convert.app`或`python3 src/sticker-convert.py`
2. 选择输入来源
    - 如要下载，请输入URL地址（如适用）
    - 如果您使用本机文件，请选择输入目录。预设为程式所在目录下的名为「stickers_input」的资料夹。请将要转换的档案放入该目录。
3. 选择压缩选项。如果不确定，请从选项选单中选择预设值。
4. 如果您只想下载文件，请勾选「不压缩」。
5. 选择输出选项和输出目录。
6. 输入貼纸包的标题和作者。
7. 如果您想从 Telegram 下载/上传貼纸，或从 Signal 上传貼纸，请输入凭证（更多信息，请参阅“兼容性”和“常见问题解答”部分）。
8. 按下「开始」按钮。

## 使用説明 (CLI)
如要使用CLI模式，请输入任何参数

```
usage: sticker-convert.py [-h] [--version] [--no-confirm] [--no-progress]
                          [--custom-presets CUSTOM_PRESETS]
                          [--lang {en_US,ja_JP,zh_CN,zh_TW}]
                          [--input-dir INPUT_DIR]
                          [--download-auto DOWNLOAD_AUTO | --download-signal DOWNLOAD_SIGNAL | --download-telegram DOWNLOAD_TELEGRAM | --download-telegram-telethon DOWNLOAD_TELEGRAM_TELETHON | --download-line DOWNLOAD_LINE | --download-kakao DOWNLOAD_KAKAO | --download-band DOWNLOAD_BAND | --download-ogq DOWNLOAD_OGQ | --download-viber DOWNLOAD_VIBER | --download-discord DOWNLOAD_DISCORD | --download-discord-emoji DOWNLOAD_DISCORD_EMOJI]
                          [--output-dir OUTPUT_DIR] [--author AUTHOR]
                          [--title TITLE]
                          [--export-signal | --export-telegram | --export-telegram-emoji | --export-telegram-telethon | --export-telegram-emoji-telethon | --export-viber | --export-whatsapp | --export-imessage]
                          [--no-compress]
                          [--preset {auto,signal,telegram,telegram_emoji,whatsapp,line,kakao,band,ogq,viber,discord,discord_emoji,imessage_small,imessage_medium,imessage_large,custom}]
                          [--steps STEPS] [--processes PROCESSES]
                          [--fps-min FPS_MIN] [--fps-max FPS_MAX]
                          [--fps-power FPS_POWER] [--res-min RES_MIN]
                          [--res-max RES_MAX] [--res-w-min RES_W_MIN]
                          [--res-w-max RES_W_MAX] [--res-h-min RES_H_MIN]
                          [--res-h-max RES_H_MAX] [--res-power RES_POWER]
                          [--res-snap-pow2] [--no-res-snap-pow2]
                          [--quality-min QUALITY_MIN] [--quality-max QUALITY_MAX]
                          [--quality-power QUALITY_POWER] [--color-min COLOR_MIN]
                          [--color-max COLOR_MAX] [--color-power COLOR_POWER]
                          [--duration-min DURATION_MIN]
                          [--duration-max DURATION_MAX] [--duration-spoof]
                          [--padding-percent PADDING_PERCENT] [--bg-color BG_COLOR]
                          [--vid-size-max VID_SIZE_MAX]
                          [--img-size-max IMG_SIZE_MAX] [--vid-format VID_FORMAT]
                          [--img-format IMG_FORMAT] [--fake-vid] [--no-fake-vid]
                          [--scale-filter SCALE_FILTER]
                          [--quantize-method QUANTIZE_METHOD]
                          [--cache-dir CACHE_DIR] [--chromium-path CHROMIUM_PATH]
                          [--default-emoji DEFAULT_EMOJI]
                          [--signal-uuid SIGNAL_UUID]
                          [--signal-password SIGNAL_PASSWORD] [--signal-get-auth]
                          [--telegram-token TELEGRAM_TOKEN]
                          [--telegram-userid TELEGRAM_USERID] [--telethon-setup]
                          [--kakao-auth-token KAKAO_AUTH_TOKEN]
                          [--kakao-get-auth-android-login]
                          [--kakao-get-auth-desktop-memdump]
                          [--kakao-get-auth-desktop-login]
                          [--kakao-bin-path KAKAO_BIN_PATH]
                          [--kakao-username KAKAO_USERNAME]
                          [--kakao-password KAKAO_PASSWORD]
                          [--kakao-country-code KAKAO_COUNTRY_CODE]
                          [--kakao-phone-number KAKAO_PHONE_NUMBER]
                          [--kakao-device-uuid KAKAO_DEVICE_UUID] [--line-get-auth]
                          [--line-cookies LINE_COOKIES] [--viber-auth VIBER_AUTH]
                          [--viber-get-auth VIBER_GET_AUTH]
                          [--viber-bin-path VIBER_BIN_PATH] [--discord-get-auth]
                          [--discord-token DISCORD_TOKEN] [--save-cred]

sticker-convert的CLI

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --no-confirm          不要讯问任何问题。
  --no-progress         不要在文字界面显示进度计。
  --custom-presets CUSTOM_PRESETS
                        选择一个自订的compression.json档案，
                        请参考compression.json的格式，
                        请注意如果'custom_preset.json'若存在于设定值路径，它将会被载入。
  --lang {en_US,ja_JP,zh_CN,zh_TW}
                        选择语言 (预设为系统语言)。

输入选项:
  --input-dir INPUT_DIR
                        选择输入路径。
  --download-auto DOWNLOAD_AUTO
                        自动侦测URL类型并下载
                        (支援输入来源: Signal, Telegram, Line, Kakao, Naver Band, OGQ, Viber, Discord)
  --download-signal DOWNLOAD_SIGNAL
                        从URL下载Signal贴图
                        (例子: https://signal.art/addstickers/#pack_id=xxxxx&pack_key=xxxxx)
  --download-telegram DOWNLOAD_TELEGRAM
                        从URL下载Telegram贴图
                        (例子: https://telegram.me/addstickers/xxxxx
                         OR https://telegram.me/addemoji/xxxxx)
  --download-telegram-telethon DOWNLOAD_TELEGRAM_TELETHON
                        从URL以Telethon下载Telegram贴图
                        (例子: https://telegram.me/addstickers/xxxxx
                         OR https://telegram.me/addemoji/xxxxx)
  --download-line DOWNLOAD_LINE
                        从URL/ID下载Line贴图
                        (例子: https://store.line.me/stickershop/product/1234/en
                         OR https://line.me/S/sticker/1234/?lang=en OR line://shop/detail/1234 OR 1234)
  --download-kakao DOWNLOAD_KAKAO
                        从URL/ID下载Kakao贴图
                        (例子: https://e.kakao.com/t/xxxxx 
                        OR https://emoticon.kakao.com/items/xxxxx OR 4404400)
  --download-band DOWNLOAD_BAND
                        从URL/ID下载Naver Band贴图
                        (例子: https://www.band.us/sticker/xxxx OR 2535)
  --download-ogq DOWNLOAD_OGQ
                        从URL下载OGQ贴图
                        (Example: https://ogqmarket.naver.com/artworks/sticker/detail?artworkId=xxxxx)
  --download-viber DOWNLOAD_VIBER
                        从URL下载Viber贴图
                        (例子: https://stickers.viber.com/pages/example
                        OR https://stickers.viber.com/pages/custom-sticker-packs/example)
  --download-discord DOWNLOAD_DISCORD
                        从频道URL/ID下载Discord贴图
                        (例子: https://discord.com/channels/169256939211980800/@home
                        OR 169256939211980800)
  --download-discord-emoji DOWNLOAD_DISCORD_EMOJI
                        从频道URL/ID下载Discord表情
                        (例子: https://discord.com/channels/169256939211980800/@home
                        OR 169256939211980800)

输出选项:
  --output-dir OUTPUT_DIR
                        选择输出路径。
  --author AUTHOR       设定表情包的作者。
  --title TITLE         设定表情包的名称。
  --export-signal       上载至Signal
  --export-telegram     上载至Telegram
  --export-telegram-emoji
                        上载至Telegram (Custom emoji)
  --export-telegram-telethon
                        以Telethon上载至Telegram *不建议，但可使连结结尾不含_by_xxxbot*
  --export-telegram-emoji-telethon
                        以Telethon上载至Telegram (自订表情符号) *不建议，但可使连结结尾不含_by_xxxbot*
  --export-viber        上载至Viber
  --export-whatsapp     创建 .wastickers档案以供上载至WhatsApp
  --export-imessage     创建Xcode专案以供输入至iMessage

压缩选项:
  --no-compress         不要压缩档案，适用于只下载貼图。
  --preset {auto,signal,telegram,telegram_emoji,whatsapp,line,kakao,band,ogq,viber,discord,discord_emoji,imessage_small,imessage_medium,imessage_large,custom}
                        套用压缩的预设值。
  --steps STEPS         设定最少与最大值之间的分割数。
                        数值越大 = 较慢但生成的档案更接近档案大小限制。
  --processes PROCESSES
                        设定进程数量。预设为系统逻辑处理器数量的一半。
                        数量越大 = 压缩较快但更耗用更多资源。
  --fps-min FPS_MIN     设定最少帧率。
  --fps-max FPS_MAX     设定最大帧率。
  --fps-power FPS_POWER
                        可设定为-1至正无限。倍数越少 = 更重视该变量值，尽可能保持该变量值更大。
  --res-min RES_MIN     设定最低的解像度。
  --res-max RES_MAX     设定最高的解像度。
  --res-w-min RES_W_MIN
                        设定最低的阔度。
  --res-w-max RES_W_MAX
                        设定最高的阔度。
  --res-h-min RES_H_MIN
                        设定最低的高度。
  --res-h-max RES_H_MAX
                        设定最高的高度。
  --res-power RES_POWER
                        可设定为-1至正无限。倍数越少 = 更重视该变量值，尽可能保持该变量值更大。
  --res-snap-pow2       将解像度数值约至最近的2次方数 (1,2,4,8,16,...).
                        若最少与最大的解像度数值之间不存在任何2次方数，此选项会被忽略。
  --no-res-snap-pow2    禁用res_snap_pow2
  --quality-min QUALITY_MIN
                        设定最低的质量。
  --quality-max QUALITY_MAX
                        设定最高的质量。
  --quality-power QUALITY_POWER
                        可设定为-1至正无限。倍数越少 = 更重视该变量值，尽可能保持该变量值更大。
  --color-min COLOR_MIN
                        设定最少颜色数量（只适用于png及apng档案）。
  --color-max COLOR_MAX
                        设定最大颜色数量（只适用于png及apng档案）。
  --color-power COLOR_POWER
                        可设定为-1至正无限。倍数越少 = 更重视该变量值，尽可能保持该变量值更大。
  --duration-min DURATION_MIN
                        设定最少的动画长度限制（毫秒）。
  --duration-max DURATION_MAX
                        设定最大的动画长度限制（毫秒）。
  --duration-spoof      允许将 Matroska 影片（mkv/webm）的播放时长伪造在一定范围内。 
                        可用于上传时长超过 3 秒的影片贴纸到 Telegram，但未来可能不再支援。
  --padding-percent PADDING_PERCENT
                        设定边界占用百分比。
  --bg-color BG_COLOR   设定自订背景颜色（以rrggbbaa为格式）。
                        例子: 00ff0000是透明值0的绿色.
                        预设为若影像明亮则背景颜色设为黑色，若影像黑暗则背景颜色设为白色。
                        注意: 若档案格式支援透明色，将不会看到背景颜色。
  --vid-size-max VID_SIZE_MAX
                        设定最大动画档案大小。
  --img-size-max IMG_SIZE_MAX
                        设定最大图片档案大小。
  --vid-format VID_FORMAT
                        设定动画档案格式。
  --img-format IMG_FORMAT
                        设定图片档案格式。
  --fake-vid            将图片转换（假扮）成动画。
                        下列情况可以应用:
                        (1) 动画档案的大小限制大于图片；
                        (2) 混合图片和动画于同一表情包。
  --no-fake-vid         禁用fake_vid
  --scale-filter SCALE_FILTER
                        设定缩放滤镜。预设为bicubic。可使用值为：
                        - nearest = 使用最近像素（适用于像素风影像）
                        - box = 与nearest相似，但下采样更好
                        - bilinear = 线性插值
                        - hamming = 与bilinear相似，但下采样更好
                        - bicubic = 三次样条插值
                        - lanczos = 高质素的下采样滤镜
  --quantize-method QUANTIZE_METHOD
                        设定量化方式。预设为imagequant。可选择：
                        - imagequant = 速度+ 压缩度+ 质素++++ 支援RGBA
                        - fastoctree = 速度++ 压缩度++++ 质素+ 支援RGBA
                        - maxcoverage = 速度+++ 压缩度+++ 质素++ 不支援RGBA
                        - mediancut = 速度++++ 压缩度++ 质素+++ 不支援RGBA
                        - none = 禁止量子化，档案大
                        质素低会令影像看起来一格格。
  --cache-dir CACHE_DIR
                        设定自订快存路径。
                        可用于除错，或设定cache_dir于快取记忆体以加速转换速度。
  --chromium-path CHROMIUM_PATH
                        设定（基于）Chromium/Chrome浏覽器的路径。
                        需用于转换SVG档案。
                        留空白以自动侦测。
  --default-emoji DEFAULT_EMOJI
                        设定上载Signal和Telegram貼图包的预设颜文字。

认证选项:
  --signal-uuid SIGNAL_UUID
                        设定Signal uuid。需用于上载Signal貼图。
  --signal-password SIGNAL_PASSWORD
                        设定Signal password。需用于上载Signal貼图。
  --signal-get-auth     产生Signal uuid和password。
  --telegram-token TELEGRAM_TOKEN
                        设定Telegram token。需用于上载和下载Telegram貼图。
  --telegram-userid TELEGRAM_USERID
                        设定Telegram user_id (从真实账户，而非机械人帐户)n。需用于上载和下载Telegram貼图。
  --telethon-setup      设定Telethon
  --kakao-auth-token KAKAO_AUTH_TOKEN
                        设定Kakao auth_token。需用于从 https://e.kakao.com/t/xxxxx 上载和下载动态貼图。
  --kakao-get-auth-android-login
                        透过模拟登入Kakao安卓版取得auth_token。需要Kakao使用者名称、密码、国家代码和电话号码。
  --kakao-get-auth-desktop-memdump
                        透过memdump从已安装的Kakao桌面版中取得 Kakao auth_token。
  --kakao-get-auth-desktop-login
                        透过模拟登入Kakao桌面版取得auth_token。需要Kakao使用者名称、密码。
  --kakao-bin-path KAKAO_BIN_PATH
                        设定Kakao桌面版路径以开启程式并取得auth_token。
                        适用于免安装版。
  --kakao-username KAKAO_USERNAME
                        设定Kakao使用者名，即注册Kakao帐户时使用的电子邮件地址或电话号码
                        范例：+447700900142
                        需用于模拟安卓/桌面版登入以取得Kakao auth_token。
  --kakao-password KAKAO_PASSWORD
                        设定Kakao帐户密码。
                        需用于模拟安卓/桌面版登入以取得Kakao auth_token。
  --kakao-country-code KAKAO_COUNTRY_CODE
                        设定Kakao国际电话区号。
                        范例: 82 (韩国), 44 (英国), 1 (美国).
                        需用于模拟安卓版登入以取得Kakao auth_token。
  --kakao-phone-number KAKAO_PHONE_NUMBER
                        设定Kakao电话号码 (与Kakao帐号连结的电话号码)
                        不要输入国际电话区号
                        范例: 7700900142
                        用于收/发短信.
                        需用于模拟安卓版登入以取得Kakao auth_token。
  --kakao-device-uuid KAKAO_DEVICE_UUID
                        设定Kakao device uuid以登入桌面版。预设为真实device uuid。
                        选填，以模拟桌面版登入以取得Kakao auth_token。
  --line-get-auth       从浏覽器取得Line cookies, 以用于制作讯息貼图。
  --line-cookies LINE_COOKIES
                        设定Line cookies, 以用于制作讯息貼图。
  --viber-auth VIBER_AUTH
                        设定Viber身份验证数据。
                        用于上载Viber貼图。
  --viber-get-auth VIBER_GET_AUTH
                        产生Viber身份验证数据。
  --viber-bin-path VIBER_BIN_PATH
                        指明Viber桌面版程式路径。
                        可用于免安装版。
  --discord-get-auth    取得Discord token。
  --discord-token DISCORD_TOKEN
                        设定Discord token。用于下载Discord貼图和表情。
  --save-cred           储存身份验证数据。
```

如要直接执行Python 脚本，请执行`src/sticker-convert.py`

如以pip安装，请执行`sticker-convert`或`python -m sticker_convert`

如在macOS中执行，请执行`sticker-convert.app/Contents/MacOS/sticker-convert-cli`

例子:

只下载一个来源

`sticker-convert --download-signal <url> --no-compress`

转换本机档案到Signal兼容貼图档案

`sticker-convert --input-dir ./custom-input --output-dir ./custom-output --preset signal`

`sticker-convert --preset signal`

转换Signal貼图到Telegram并上载

`sticker-convert --download-signal <url> --export-telegram --telegram-token <your_bot_token_here> --telegram-userid <your_userid_here> --save-cred`

转换本机档案到多个格式并输出

`sticker-convert --export-telegram --export-signal`

转换本机档案到自定义格式

`sticker-convert --fps-min 3 --fps-max 30 --quality-min 30 --quality-max 90 --res-min 512 --res-max 512 --steps 10 --vid-size-max 500000 --img-size-max 500000 --vid-format .apng --img-format .png`

提示：使用CLI以一个命令转换多个貼图！

下列例子转换两个Line貼图包到Signal，Telegram和WhatsApp
```
sticker-convert --no-confirm --download-auto https://store.line.me/stickershop/product/1/en --export-signal
sticker-convert --no-confirm --export-telegram
sticker-convert --no-confirm --export-whatsapp

sticker-convert --no-confirm --download-line https://store.line.me/stickershop/product/2/en --preset signal --export-signal
sticker-convert --no-confirm --preset telegram --export-telegram
sticker-convert --no-confirm --preset whatsapp --export-whatsapp
```

请留意转换结果可在export-result中查閲

## 使用説明 (Docker)
![/imgs/screenshot-docker-gui.png](/imgs/screenshot-docker-gui.png)

下载
```
# 选项1: 从Dockerhub
## 完整版
docker pull laggykiller/sticker-convert:latest
## 没有多语言, Signal 桌面版, Viber 桌面版, Kakao 桌面版, Chromium
docker pull laggykiller/sticker-convert:latest-min-gui
## 没有多语言, Signal 桌面版, Viber 桌面版, Kakao 桌面版, Chromium；只有CLI
docker pull laggykiller/sticker-convert:latest-min-cli

# 选项2: 从ghcr
## 完整版
docker pull ghcr.io/laggykiller/sticker-convert:latest
## 没有多语言, Signal 桌面版, Viber 桌面版, Kakao 桌面版, Chromium
docker pull ghcr.io/laggykiller/sticker-convert:latest-min-gui
## 没有多语言, Signal 桌面版, Viber 桌面版, Kakao 桌面版, Chromium；只有CLI
docker pull ghcr.io/laggykiller/sticker-convert:latest-min-cli
```

执行（GUI）
```
docker run -d -it --name sticker-convert \
    -v /path/to/your/stickers_input:/app/stickers_input \
    -v /path/to/your/stickers_output:/app/stickers_output \
    -p 5800:5800 \ # Port for Web UI
    -p 5900:5900 \ # Optional for VNC
    laggykiller/sticker-convert:latest
```

执行（CLI）
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

建构
```
docker build --tag sticker-convert:latest --target full .
docker build --tag sticker-convert:latest-min-cli --target min-cli .
docker build --tag sticker-convert:latest-min-gui --target min-gui .
```

请留意GUI版本是基于https://github.com/jlesage/docker-baseimage-gui.
若要开啓GUI，请在运行docker image的电脑以浏覽器到访`localhost:5800`
另一方法是以VNC软件连接`localhost:5900`

## 直接执行Python脚本及编译
请参照 [/docs/zh_CN/COMPILING.md](/docs/zh_CN/COMPILING.md)

## 常见问题

### 平台特定指南 (例如: 取得凭证)
- [Signal](/docs/zh_CN/guide_signal.md)
- [Telegram](/docs/zh_CN/guide_telegram.md)
- [WhatsApp](/docs/zh_CN/guide_whatsapp.md)
- [Line](/docs/zh_CN/guide_line.md)
- [Kakao](/docs/zh_CN/guide_kakao.md)
- [Viber](/docs/zh_CN/guide_viber.md)
- [Discord](/docs/zh_CN/guide_discord.md)
- [iMessage](/docs/zh_CN/guide_imessage.md)

### 转换速度慢
试试以下建议：
- 增加进程数（`--processes`）
    - 但增加进程数超过预设值实际上可能会降低速度
- 减少步骤数（`--steps`）
    - 但减少过多步骤可能会导致品质下降

### 记忆体不足/系统冻结
尝试减少进程数（`--processes`）

### macOS提示程式来自未知开发者
要成为认证开发者，我需要每年向苹果支付 99 美元。

有两种方法可以绕过这个问题：

1. 永久方法：在执行 `sticker-convert` 之前，打开终端机并执行 `sudo spctl --master-disable` 指令。
2. 临时方法：在解压缩下载的 zip 档案之前，开启终端并执行 `xattr -d com.apple.quarantine ./downloads/sticker-convert-macos.zip` 指令。

如果 macOS 仍然对某些二进位档案（例如 apngasm）发出警告，请前往`系统偏好设定 > 安全性与隐私`，然后点击每个档案`仍然开启`。

请访问此页面了解更多：https://disable-gatekeeper.github.io/

### 我想上传stickers_output中尚未上传的貼纸
CLI：执行命令时新增参数 `--no-compress --export-xxxxx`
GUI：选择`从本机路径`作为输入来源，勾选`不压缩`复选框，并选择`上载至xxxxx`作为输出选项。

### 凭证存放在哪里? 
凭证储存在 creds.json 档案中。

预设情况下，它应该位于程式运行所在的相同目录下。

但是，如果目录不可写入（例如，在 macOS 中安装到 `/Applications`，或在 Linux 中安装到 `/usr/local/bin`），则 `creds.json` 档案将储存在下列位置：
- Windows：`%APPDATA%/sticker-convert/creds.json`
- 其他：`~/.config/sticker-convert/creds.json`

### power和steps是什么意思?
这是使用二分法寻找最优压缩设定。 `power` 参数允许数值「偏向」一侧（负值会使sticker-convert尝试更多较大的值；`power` 设定为 1 会使 sticker-convert将其尝试次数均匀地分配在最小值和最大值之间；`power`大于 1 会使sticker-convert尝试更多较小的值）。

为了说明这一点，让我们来看看 `--steps 16 --fps-min 5 --fps-max 30 --fps-power 3.0` 的作用。

1. 我们会从 `8/16`（16 步中的第 8 步）开始，这是中间点。
2. 我们将使用幂运算计算一个因子：`(8/16)^3.0 = 0.125`
3. 帧率 (fps) 的设定公式为 `round((max - min) * step / steps * factor + min)`，即 `round((16-1) * 8 / 16 * 0.125 + 5) = round(5.9375) = 6`。这意味着帧率将设定为 6。
4. 如果档案大小太小，我们将尝试 `4/16`（16 步中的第 4 步，即 0 到 8 的中间值）。否则，我们将尝试 `10/16`（16 步中的第 10 步，即 8 到 16 的中间值）。
5. 重复步骤 1-3。

## 未来计画
请参閲[/docs/TODO.md](/docs/TODO.md)

## 鸣谢
- Signal 和 Telegram 貼纸资讯：https://github.com/teynav/signalApngSticker
- Line 和 Kakao 貼图资讯：https://github.com/star-39/moe-sticker-bot
- Line 貼图资讯：https://github.com/doubleplusc/Line-sticker-downloader
- Kakao 动态貼图资讯：https://gist.github.com/chitacan/9802668
- Kakao 动态貼图的下载与解密：https://github.com/blluv/KakaoTalkEmoticonDownloader
- 寻找浏覽器执行档路径：https://github.com/roniemartinez/browsers
- 应用程式图示来自 [Icons8](https://icons8.com/)
- 横幅由 [GitHub Socialify](https://socialify.git.ci/) 生成
- Windows 系统上的免费程式码签署由 [SignPath.io](https://about.signpath.io/) 提供由 [SignPath Foundation](https://signpath.org/) 颁发的凭证

## 免责声明
- 本代码库作者与 Signal、Telegram、WhatsApp、Line、Kakao、Naver Band、OGQ、Viber、Discord、iMessage 或 Sticker Maker 没有任何关联。
- 本代码库作者对因使用本仓库而产生的任何法律后果和损失概不负责。
