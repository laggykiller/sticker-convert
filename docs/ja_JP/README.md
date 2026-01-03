# sticker-convert
### [ [English](/README.md) | [繁體中文](/docs/zh_TW/README.md) | [简体中文](/docs/zh_CN/README.md) | [日本語](/docs/ja_JP/README.md) ]

![/imgs/banner.png](https://socialify.git.ci/laggykiller/sticker-convert/image?description=1&font=Inter&logo=https%3A%2F%2Fgithub.com%2Flaggykiller%2Fsticker-convert%2Fblob%2Fmaster%2Fsrc%2Fsticker_convert%2Fresources%2Fappicon.png%3Fraw%3Dtrue&name=1&owner=1&theme=Dark)
![/imgs/screenshot](/imgs/screenshot.png)

- 複数のインスタントメッセージングアプリケーションからスタンプを作成、ダウンロード、変換+圧縮、アップロードするためのPythonスクリプトです。
- Windows、MacOS、Linuxで動作するGUIとCLIを備えています。
- 現在、Signal、Telegram、WhatsApp（.wastickersを作成）、Line（ダウンロードのみ）、Kakao（ダウンロードのみ）、Naver Band（ダウンロードのみ）、OGQ（ダウンロードのみ）、Viber、Discord（ダウンロードのみ）、iMessage（Xcodeスタンプパックプロジェクトを作成）をサポートしています。
- 画像スタンプと動画スタンプをサポートし、透明度もサポートしています。

## ダウンロード
- [実行ファイル]：Windows、MacOS、Linux（AppImage形式）バージョンあり(https://github.com/laggykiller/sticker-convert/releases)。
- Windows：ダウンロードしたファイルを展開し、`sticker-convert.exe`を実行する；又はインストール用のmsiファイルをダウンロードしてください。
- MacOS：ダウンロードしたファイルを展開し、Ctrlキーを押しながら`hold_control_and_click_open_me.command`（初回のみ）を開いてください。次回からは`sticker-convert.app`を実行してください。
- Linux：
    - AppImage：ダウンロードしたAppImageを`chmod +x`で実行してください。
    - Zip：展開し、`sticker-convert.bin`を実行してください。
    - [AURパッケージ](https://aur.archlinux.org/packages/sticker-convert): `makepkg -si`
- [pipパッケージ](https://pypi.org/project/sticker-convert/): `pip install sticker-convert` `sticker-convert` または `python -m sticker_convert` で起動します。
- [Docker イメージ](https://hub.docker.com/r/laggykiller/sticker-convert) をLinuxに使用できます。
- [Google Colab](https://colab.research.google.com/github/laggykiller/sticker-convert/blob/master/sticker_convert_colab.ipynb) でダウンロードせずに試す(Google アカウントが必要です)。Google サーバー上でコードを実行し、Google ドライブから結果を取得します。ただし、パソコンで実行するよりも遅くなる可能性があります。(.apng に変換しない場合はファイルあたり約 15 秒、.apng に変換する場合はファイルあたり約 1 分)

## 目録
- [適合性](#適合性)
- [使い方 (GUI)](#使い方-GUI)
- [使い方 (CLI)](#使い方-CLI)
- [使い方 (Docker)](#使い方-Docker)
- [Pythonスクリプトの直接実行とコンパイル](#Pythonスクリプトの直接実行とコンパイル)
- [よくある質問](#よくある質問)
    - [プラットフォーム固有のガイド (例: 認証情報の取得)](#プラットフォーム固有のガイド-例-認証情報の取得)
    - [変換が遅い](#変換が遅い)
    - [RAM不足/システムがフリーズする](#RAM不足システムがフリーズする)
    - [macOSが開発元不明のプログラムに関するエラーメッセージを表示する](#macOSが開発元不明のプログラムに関するエラーメッセージを表示する)
    - [stickers_outputにある、まだアップロードされていないスタンプをアップロードしたい](#stickers_outputにあるまだアップロードされていないスタンプをアップロードしたい)
    - [認証情報はどこに保存されますか？](#認証情報はどこに保存されますか)
    - [powerとstepsとはどういう意味ですか？](#powerとstepsとはどういう意味ですか)
- [今後の計画](#今後の計画)
- [クレジット](#クレジット)
- [免責事項](#免責事項)

## 適合性
| アプリ                                   | ⬇️ ダウンロード                               | ⬆️ アップロード                                        |
| ---------------------------------------- | ----------------------------------------------| ---------------------------------------------------- |
| [Signal](/docs/ja_JP/guide_signal.md)        | ✅                                           | ✅ (`uuid`と`password`が必要；又は自分で)              |
| [Telegram](/docs/ja_JP/guide_telegram.md)    | ✅ (`token`又はtelethonが必要)                | ✅ (`token`と`user_id`又はtelethonが必要；又は自分で)  |
| [WhatsApp](/docs/ja_JP/guide_whatsapp.md)    | ⭕ (AndroidまたはWhatsApp Webで)              | ⭕ (`.wastickers`を創建、Sticker Makerで入力)         |
| [Line](/docs/ja_JP/guide_line.md)            | ✅                                           | 🚫 (人工審査が必要)                                   |
| [Kakao](/docs/ja_JP/guide_kakao.md)          | ✅ (動画スタンプは'auth_token'が必要) | 🚫 (人工審査が必要)                                   |
| [Band](/docs/ja_JP/guide_band.md)            | ✅                                           | 🚫 (人工審査が必要)                                   |
| [OGQ](/docs/ja_JP/guide_ogq.md)              | ✅                                           | 🚫 (人工審査が必要)                                   |
| [Viber](/docs/ja_JP/guide_viber.md)          | ✅                                           | ✅ (`viber_auth`が必要)                              |
| [Discord](/docs/ja_JP/guide_discord.md)      | ✅ (`token`が必要)                            | 🚫                                                  |
| [iMessage](/docs/ja_JP/guide_imessage.md)    | 🚫                                           | ⭕ (サイドロードのためにXcodeスタンププロジェクトを創建) |

✅ = 対応 ⭕ = 部分的に対応 🚫 = 非対応

- Signal
    - ダウンロード：対応 (例：`https://signal.art/addstickers/#pack_id=xxxxx&pack_key=xxxxx`)
    - アップロード：対応
        - プログラムでパックを自動アップロードするには、`uuid` と `password` が必要です。詳細はFAQをご覧ください。
        - または、Signal Desktopを使用して、このプログラムの出力から手動でアップロードし、スタンプパックを作成することもできます。
- Telegram
    - ダウンロード：スタンプとカスタム絵文字の両方で対応しています(例：`https://telegram.me/addstickers/xxxxx`)。ただし、bot tokenまたはTelethonの設定が必要です。
    - アップロード：スタンプとカスタム絵文字の両方で対応していますが、bot tokenとuser_idまたはTelethonの設定が必要です。または、このプログラムの出力から手動でアップロードし、スタンプパックを作成することもできます。
- WhatsApp
    - ダウンロード：携帯電話またはWhatsApp Webから、手動でスタンプパックを探すか、抽出する必要があります。詳細は[/docs/ja_JP/guide_whatsapp.md](/docs/ja_JP/guide_whatsapp.md)をご覧ください。
    - アップロード：このプログラムは.wastickersファイルを作成でき、サードパーティ製アプリ「Sticker Maker」を介してWhatsAppにインポートできます（このリポジトリの作者はSticker Makerとは一切関係ありません）。詳細は"よくある質問"をご覧ください。
- Line
    - ダウンロード：対応（例：`https://store.line.me/stickershop/product/1234/en` または `line://shop/detail/1234` または `1234`）
        - 公式サイトで検索：https://store.line.me/stickershop
        - 非公式サイトで検索（地域ロックや期限切れのパックを含む）：http://www.line-stickers.com/
        - 詳細は https://github.com/doubleplusc/Line-sticker-downloader をご覧ください。
    - アップロード：未対応。アプリで使用する前に、スタンプパックを手動で承認申請する必要があります。
- Kakao
    - ダウンロード：対応（例：`https://e.kakao.com/t/xxxxx` または `https://emoticon.kakao.com/items/xxxxx` または `4404400`）。手順は少し複雑なので、[/docs/ja_JP/guide_kakao.md](/docs/ja_JP/guide_kakao.md) をご覧ください。
    - アップロード：非対応。アプリで使用する前に、スタンプパックを手動で承認申請する必要があります。
- Band
    - ダウンロード：対応（例：`https://www.band.us/sticker/xxxx` または `2535`）。共有リンクの取得方法については、[/docs/ja_JP/guide_band.md](/docs/ja_JP/guide_band.md) をご覧ください。
    - アップロード：非対応。アプリで使用する前に、スタンプパックを手動で承認申請する必要があります。
- OGQ
    - ダウンロード：対応（例：https://ogqmarket.naver.com/artworks/sticker/detail?artworkId=xxxxx）
    - アップロード：非対応。アプリで使用する前に、スタンプパックを手動で承認申請する必要があります。
- Viber
    - ダウンロード：対応（例：https://stickers.viber.com/pages/example または https://stickers.viber.com/pages/custom-sticker-packs/example）
    - アップロード：非対応。ViberスタンプをアップロードするにはViber認証データが必要です。認証データはViberデスクトップアプリケーションから自動的に取得できます。
- Discord
    - ダウンロード：対応（例：https://discord.com/channels/169256939211980800/@home または 169256939211980800）ですが、ユーザートークンが必要です。
    - アップロード: 非対応。
- iMessage
    - ダウンロード: 非対応。
    - アップロード: このプログラムはiMessageスタンプパック用のXcodeプロジェクトを作成でき、Xcodeを使用してコンパイルおよびサイドロードできます。

## 使い方 (GUI)
1. `sticker-convert.exe`、`sticker-convert.app`、または `python3 src/sticker-convert.py` を実行します。
2. 入力元を選択します。
    - ダウンロードする場合は、ダウンロード元のURLアドレスを入力します（該当する場合）。
    - ローカルファイルを使用する場合は、入力ディレクトリを選択します。デフォルトでは、プログラムと同じディレクトリにある「stickers_input」というフォルダが作成されます。変換したいファイルをそのディレクトリに配置します。
3. 圧縮オプションを選択します。不明な場合は、オプションメニューからプリセットを選択してください。
4. ファイルをダウンロードするだけの場合は、「圧縮なし」にチェックを入れます。
5. 出力オプションと出力ディレクトリを選択します。
6. スタンプパックのタイトルと作成者を入力します。
7. Telegramからダウンロード/アップロードする場合、またはSignalからアップロードする場合は、認証情報を入力します（詳細は「適合性」と「よくある質問」セクションをご覧ください）。
8. 「開始」を押します。

## 使い方 (CLI)
CLIモードで実行するには、引数を渡します

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

sticker-convertのCLI

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --no-confirm          質問しません。
  --no-progress         CLI にプログレスバーを表示しません。
  --custom-presets CUSTOM_PRESETS
                        カスタム圧縮プリセットを含むJSONファイルを指定します。
                        形式については、compression.jsonを参照してください。
                        存在する場合は、configディレクトリの'custom_preset.json'が自動的に読み込まれます。
  --lang {en_US,ja_JP,zh_CN,zh_TW}
                        言語の選択（システム言語をデフォルトにする）。

輸入オプション:
  --input-dir INPUT_DIR
                        入力ディレクトリを指定します。
  --download-auto DOWNLOAD_AUTO
                        URLタイプを自動検出とダウンロード
                        (サポートされている入力ソース: Signal, Telegram, Line, Kakao, Naver Band, OGQ, Viber, Discord)
  --download-signal DOWNLOAD_SIGNAL
                        入力としてURLからSignalスタンプをダウンロードする
                        (例: https://signal.art/addstickers/#pack_id=xxxxx&pack_key=xxxxx)
  --download-telegram DOWNLOAD_TELEGRAM
                        入力としてURLからTelegramスタンプをダウンロードする
                        (例: https://telegram.me/addstickers/xxxxx
                         OR https://telegram.me/addemoji/xxxxx)
  --download-telegram-telethon DOWNLOAD_TELEGRAM_TELETHON
                        Telethonを使って入力としてURLからTelegramスタンプをダウンロードする
                        (例: https://telegram.me/addstickers/xxxxx
                         OR https://telegram.me/addemoji/xxxxx)
  --download-line DOWNLOAD_LINE
                        入力としてURL/IDからLineスタンプをダウンロードする
                        (例: https://store.line.me/stickershop/product/1234/en
                         OR https://line.me/S/sticker/1234/?lang=en OR line://shop/detail/1234 OR 1234)
  --download-kakao DOWNLOAD_KAKAO
                        入力としてURL/IDからKakaoスタンプをダウンロードする
                        (例: https://e.kakao.com/t/xxxxx 
                        OR https://emoticon.kakao.com/items/xxxxx OR 4404400)
  --download-band DOWNLOAD_BAND
                        入力としてURL/IDからNaver Bandスタンプをダウンロードする
                        (例: https://www.band.us/sticker/xxxx OR 2535)
  --download-ogq DOWNLOAD_OGQ
                        入力としてURLからOGQスタンプをダウンロードする
                        (例: https://ogqmarket.naver.com/artworks/sticker/detail?artworkId=xxxxx)
  --download-viber DOWNLOAD_VIBER
                        入力としてURL/IDからViberスタンプをダウンロードする
                        (例: https://stickers.viber.com/pages/example
                        OR https://stickers.viber.com/pages/custom-sticker-packs/example)
  --download-discord DOWNLOAD_DISCORD
                        入力としてURL/IDからDiscordスタンプをダウンロードする
                        (例: https://discord.com/channels/169256939211980800/@home
                        OR 169256939211980800)
  --download-discord-emoji DOWNLOAD_DISCORD_EMOJI
                        入力としてURL/IDからDiscord顔文字をダウンロードする
                        (例: https://discord.com/channels/169256939211980800/@home
                        OR 169256939211980800)

輸出オプション:
  --output-dir OUTPUT_DIR
                        出力ディレクトリを指定します。
  --author AUTHOR       作成したスタンプパックの作成者を設定します。
  --title TITLE         作成したスタンプパックの名前を設定します。
  --export-signal       Signalにアップロードする
  --export-telegram     Telegramにアップロードする
  --export-telegram-emoji
                        Telegramにアップロードする (カスタム絵文字)
  --export-telegram-telethon
                        Telethonを使ってTelegramにアップロードする *推奨されませんが、_by_xxxbotで終わらないリンクを制作出来る*
  --export-telegram-emoji-telethon
                        Telethonを使ってTelegramにアップロードする (カスタム絵文字) *推奨されませんが、_by_xxxbotで終わらないリンクを制作出来る*
  --export-viber        Viberにアップロードする
  --export-whatsapp     .wastickersファイルに圧縮する、そしてWhatsAppにアップロードする
  --export-imessage     iMessageにインポートするためのXcodeプロジェクトを作成する

圧縮オプション:
  --no-compress         ファイルを圧縮しません。スタンプのダウンロードのみに便利です。
  --preset {auto,signal,telegram,telegram_emoji,whatsapp,line,kakao,band,ogq,viber,discord,discord_emoji,imessage_small,imessage_medium,imessage_large,custom}
                        圧縮プリセットを適用します。
  --steps STEPS         最小設定と最大設定の間の分割数を設定します。ステップ数が多いほど圧縮速度は遅くなりますが、指定されたファイルサイズ制限に近づきます。
  --processes PROCESSES
                        プロセス数を設定します。デフォルトでは、システム内の論理プロセッサの半分になります。プロセス数が多いほど圧縮速度は速くなりますが、消費リソースは多くなります。
  --fps-min FPS_MIN     最小出力fpsを設定します。
  --fps-max FPS_MAX     最大出力fpsを設定します。
  --fps-power FPS_POWER
                        -1から正の無限大の間です。べき乗値が小さいほどパラメータの重要性が高まり、高い値を維持するように努め、犠牲にしないようにします。
  --res-min RES_MIN     最小の幅と高さを設定します。
  --res-max RES_MAX     最大の幅と高さを設定します。
  --res-w-min RES_W_MIN
                        最小幅さを設定します。
  --res-w-max RES_W_MAX
                        最大幅さを設定します。
  --res-h-min RES_H_MIN
                        最小高さを設定します。
  --res-h-max RES_H_MAX
                        最大高さを設定します。
  --res-power RES_POWER
                        -1から正の無限大までの範囲です。べき乗が低いほどパラメータの重要性が増し、犠牲にならないようにしてします。
  --res-snap-pow2       解像度を最も近い2のべき乗（1、2、4、8、16、...）にスナップします。
                        最小解像度と最大解像度の間に2のべき乗が存在しない場合は無視されます。
  --no-res-snap-pow2    res_snap_pow2を無効にします。
  --quality-min QUALITY_MIN
                        最低品質を設定します。
  --quality-max QUALITY_MAX
                        最高品質を設定します。
  --quality-power QUALITY_POWER
                        -1から正の無限大までの範囲です。べき乗が低いほどパラメータの重要性が増し、犠牲にならないようにしてします。
  --color-min COLOR_MIN
                        最小色数を設定します（apngとapngへの変換のみ）。
  --color-max COLOR_MAX
                        最大色数を設定します（apngとapngへの変換のみ）。
  --color-power COLOR_POWER
                        -1から正の無限大までの範囲です。べき乗が低いほどパラメータの重要性が増し、犠牲にならないようにしてします。
  --duration-min DURATION_MIN
                        最小出力時間（ミリ秒単位）を設定します。
  --duration-max DURATION_MAX
                        最大出力時間（ミリ秒単位）を設定します。
  --padding-percent PADDING_PERCENT
                        パディングとして使用するスペースの割合を設定します。
  --bg-color BG_COLOR   rrggbbaa 形式でカスタム背景色を設定します。
                        例: アルファ値が0の緑は00ff0000です。
                        設定されていない場合、画像が明るい場合は背景色が自動的に黒に、暗い場合は白に設定されます。
                        注: 出力形式が透明化をサポートしている場合、背景色は表示されません。
  --vid-size-max VID_SIZE_MAX
                        動画スタンプの最大ファイルサイズ制限を設定します。
  --img-size-max IMG_SIZE_MAX
                        静止スタンプの最大ファイルサイズ制限を設定します。
  --vid-format VID_FORMAT
                        入力が動画の場合のファイル形式を設定します。
  --img-format IMG_FORMAT
                        入力が静止の場合のファイル形式を設定します。
  --fake-vid            画像を動画に変換（偽装）します。
                        次の場合に役立ちます:
                        (1) 動画のサイズ制限が画像より大きい場合;
                        (2) 画像と動画を同じパックに混在させる場合。
  --no-fake-vid         fake_vid を無効にする
  --scale-filter SCALE_FILTER
                        スケールフィルターを設定します。デフォルトはバイキュービックです。有効なオプションは次のとおりです:
                        - near = 最近傍法を使用（ピクセルアートに適しています）
                        - box = near 法に似ていますが、ダウンスケーリングが優れています
                        - bilinear = 線形補間
                        - hamming = バイリニア法に似ていますが、ダウンスケーリングが優れています
                        - bicubic = 3次スプライン補間
                        - lanczos = 高品質のダウンサンプリングフィルター
  --quantize-method QUANTIZE_METHOD
                        画像の量子化方法を設定します。デフォルトはimagequantです。有効なオプションは次のとおりです:
                        - imagequant = 速度+圧縮+品質++++ RGBA対応
                        - fastoctree = 速度++、圧縮++++ 品質+ RGBA対応
                        - maxcoverage = 速度+++、圧縮+++ 品質++ RGBA未対応
                        - mediancut = 速度++++ 圧縮++ 品質+++ RGBA未対応
                        - none = 画像の量子化を行わず、結果として画像サイズが大きくなります
                        品質を低くすると画像が粗くなります
  --cache-dir CACHE_DIR
                        カスタムキャッシュディレクトリを設定します。
                        デバッグに便利です。また、cache_dirがRAMディスク上にある場合は変換速度が向上します。
  --chromium-path CHROMIUM_PATH
                        Chromium(ベース)/Chromeブラウザのパスを設定します。
                        SVGファイルからの変換に必須です。
                        自動検出するには空白のままにしてください
  --default-emoji DEFAULT_EMOJI
                        SignalおよびTelegramスタンプパックのアップロード時のデフォルトの絵文字を設定します。

認証情報オプション:
  --signal-uuid SIGNAL_UUID
                        Signal UUIDを設定します。Signalスタンプのアップロードに必要です。
  --signal-password SIGNAL_PASSWORD
                        Signalパスワードを設定します。Signalスタンプのアップロードに必要です。
  --signal-get-auth     Signal UUIDとパスワードを生成します。
  --telegram-token TELEGRAM_TOKEN
                        Telegramトークンを設定します。Telegramスタンプのアップロードとダウンロードに必要です。
  --telegram-userid TELEGRAM_USERID
                        TelegramユーザーIDを設定します（ボットアカウントではなく、実際のアカウントから）。Telegramスタンプのアップロードに必要です。
  --telethon-setup      Telethonをセットアップします。
  --kakao-auth-token KAKAO_AUTH_TOKEN
                        Kakao auth_tokenを設定します。https://e.kakao.com/t/xxxxx から動画スタンプをダウンロードするのに必要です。
  --kakao-get-auth-android-login
                        AndroidからのログインをシミュレートしてKakao auth_tokenを取得します。 Kakaoのユーザー名、パスワード、国番号、電話番号が必要です。
  --kakao-get-auth-desktop-memdump
                        インストール済みのKakaoデスクトップアプリケーションからmemdumpを使用してKakaoの認証トークンを取得します。
  --kakao-get-auth-desktop-login
                        デスクトップアプリケーションからのログインをシミュレートして、Kakaoの認証トークンを取得します。Kakaoのユーザー名とパスワードが必要です。
  --kakao-bin-path KAKAO_BIN_PATH
                        Kakaoデスクトップアプリケーションの起動と認証トークン取得のためのパスを設定します。
                        ポータブルインストールに便利です。
  --kakao-username KAKAO_USERNAME
                        Kakaoアカウントのサインアップに使用したメールアドレスまたは電話番号のKakaoユーザー名を設定します。
                        例: +447700900142
                        Android/デスクトップログインをシミュレートしてKakaoの認証トークンを取得するために必要です。
  --kakao-password KAKAO_PASSWORD
                        Kakaoパスワード（Kakaoアカウントのパスワード）を設定します。
                        必須Android/デスクトップログインをシミュレートしてKakao auth_tokenを取得します。
  --kakao-country-code KAKAO_COUNTRY_CODE
                        Kakaoの携帯電話の国コードを設定します。
                        例：82（韓国）、44（イギリス）、1（アメリカ）。
                        AndroidログインをシミュレートしてKakao auth_tokenを取得するために必須です。
  --kakao-phone-number KAKAO_PHONE_NUMBER
                        Kakaoの電話番号（Kakaoアカウントに関連付けられた電話番号）を設定します。
                        国コードは入力しないでください。
                        例：7700900142
                        SMSによる確認コードの送受信に使用します。
                        AndroidログインをシミュレートしてKakao auth_tokenを取得するために必須です。
  --kakao-device-uuid KAKAO_DEVICE_UUID
                        デスクトップログイン用のKakaoデバイスUUIDを設定します。デフォルトは実際のデバイスUUIDです。
                        デスクトップログインをシミュレートしてKakao auth_tokenを取得する場合はオプションです。
  --line-get-auth       ブラウザからLine Cookieを取得します。これはメッセージスタンプの作成に必要です。
  --line-cookies LINE_COOKIES
                        Line Cookieを設定します。これはメッセージスタンプの作成に必要です。
  --viber-auth VIBER_AUTH
                        Viber認証データを設定します。Viberスタンプのアップロードに必要です。
  --viber-get-auth VIBER_GET_AUTH
                        Viber認証データを生成します。
  --viber-bin-path VIBER_BIN_PATH
                        Viberデスクトップアプリケーションの場所を指定します。これはポータブルインストールに便利です。
  --discord-get-auth    Discordトークンを取得します。
  --discord-token DISCORD_TOKEN
                        Discordトークンを設定します。Discordスタンプと絵文字のダウンロードに必要です。
  --save-cred           認証情報を保存します。
```

Pythonスクリプトを直接実行する場合は、`src/sticker-convert.py`を実行してください。

pipでインストールした場合は、`sticker-convert`または`python -m sticker_convert`を実行してください。

macOSの場合は、`sticker-convert.app/Contents/MacOS/sticker-convert-cli`を実行してください。

例:

ソースからダウンロードのみ

`sticker-convert --download-signal <url> --no-compress`

ローカルファイルをSignal対応スタンプに変換する

`sticker-convert --input-dir ./custom-input --output-dir ./custom-output --preset signal`

`sticker-convert --preset signal`

SignalをTelegramスタンプに変換してTelegramにアップロードする

`sticker-convert --download-signal <url> --export-telegram --telegram-token <your_bot_token_here> --telegram-userid <your_userid_here> --save-cred`

ローカルファイルを複数の形式に変換してエクスポートする

`sticker-convert --export-telegram --export-signal`

ローカルファイルをカスタムフォーマットに変換する

`sticker-convert --fps-min 3 --fps-max 30 --quality-min 30 --quality-max 90 --res-min 512 --res-max 512 --steps 10 --vid-size-max 500000 --img-size-max 500000 --vid-format .apng --img-format .png`

ヒント: CLI を使えば、複数のスタンプを一括変換できます。操作は一切不要です。

以下の例では、2 つの LINE スタンプパックを Signal、Telegram、WhatsApp に一括変換しています。
```
sticker-convert --no-confirm --download-auto https://store.line.me/stickershop/product/1/en --export-signal
sticker-convert --no-confirm --export-telegram
sticker-convert --no-confirm --export-whatsapp

sticker-convert --no-confirm --download-line https://store.line.me/stickershop/product/2/en --preset signal --export-signal
sticker-convert --no-confirm --preset telegram --export-telegram
sticker-convert --no-confirm --preset whatsapp --export-whatsapp
```

変換結果はexport-result.txtで確認できます。

## 使い方 (Docker)
![/imgs/screenshot-docker-gui.png](/imgs/screenshot-docker-gui.png)

ダウンロード
```
# 選択 1: Dockerhubから
## 完全版
docker pull laggykiller/sticker-convert:latest
## 翻訳、Signalデスクトップ版、Viberデスクトップ版、Kakaoデスクトップ版、Chromiumなし
docker pull laggykiller/sticker-convert:latest-min-gui
## 翻訳、Signalデスクトップ版、Viberデスクトップ版、Kakaoデスクトップ版、Chromiumなし；CLIだけ
docker pull laggykiller/sticker-convert:latest-min-cli

# 選択 2: ghcrから
## 完全版
docker pull ghcr.io/laggykiller/sticker-convert:latest
## 翻訳、Signalデスクトップ版、Viberデスクトップ版、Kakaoデスクトップ版、Chromiumなし
docker pull ghcr.io/laggykiller/sticker-convert:latest-min-gui
## 翻訳、Signalデスクトップ版、Viberデスクトップ版、Kakaoデスクトップ版、Chromiumなし；CLIだけ
docker pull ghcr.io/laggykiller/sticker-convert:latest-min-cli
```

実行 (GUI)
```
docker run -d -it --name sticker-convert \
    -v /path/to/your/stickers_input:/app/stickers_input \
    -v /path/to/your/stickers_output:/app/stickers_output \
    -p 5800:5800 \ # Port for Web UI
    -p 5900:5900 \ # Optional for VNC
    laggykiller/sticker-convert:latest
```

実行 (CLI)
```
docker run -d -it --name sticker-convert \
    -v /path/to/your/stickers_input:/app/stickers_input \
    -v /path/to/your/stickers_output:/app/stickers_output \
    laggykiller/sticker-convert:latest \
    python3 /app/sticker-convert.py --help
```

docker-compose.ymlも使いできます
```
docker compose up
```

構築
```
docker build --tag sticker-convert:latest --target full .
docker build --tag sticker-convert:latest-min-cli --target min-cli .
docker build --tag sticker-convert:latest-min-gui --target min-gui .
```

GUIバージョンは https://github.com/jlesage/docker-baseimage-gui に基づいていることに注意してください。
GUIを開くには、Dockerイメージを実行しているマシンでブラウザを使用して `localhost:5800` にアクセスしてください。
または、VNCプログラムを使用して `localhost:5900` にアクセスしてください。

## Pythonスクリプトの直接実行とコンパイル
[docs/ja_JP/COMPILING.md](/docs/ja_JP/COMPILING.md)を参照してください

## よくある質問

### プラットフォーム固有のガイド (例: 認証情報の取得)
- [Signal](/docs/ja_JP/guide_signal.md)
- [Telegram](/docs/ja_JP/guide_telegram.md)
- [WhatsApp](/docs/ja_JP/guide_whatsapp.md)
- [Line](/docs/ja_JP/guide_line.md)
- [Kakao](/docs/ja_JP/guide_kakao.md)
- [Viber](/docs/ja_JP/guide_viber.md)
- [Discord](/docs/ja_JP/guide_discord.md)
- [iMessage](/docs/ja_JP/guide_imessage.md)

### 変換が遅い
以下のヒントをお試しください:
- プロセス数を増やす (`--processes`)
    - ただし、デフォルト値より大きくすると、実際には遅くなる可能性があります
- ステップ数を減らす (`--steps`)
    - ただし、小さくしすぎると品質が低下する可能性があります

### RAM不足/システムがフリーズする
プロセス数を減らす (`--processes`)

### macOSが開発元不明のプログラムに関するエラーメッセージを表示する
開発者として認められるには、Apple に毎年 99 ドルを支払う必要があります。

この問題を回避する方法は 2 つあります。
1. 永続的: ターミナルを開き、`sticker-convert` を実行する前に `sudo spctl --master-disable` を実行します。
2. 一時的: ターミナルを開き、ダウンロードした zip ファイルを展開する前に `xattr -d com.apple.quarantine ./Downloads/sticker-convert-macos.zip` を実行します。

もしmacOSが個々のバイナリ (例: apngasm) についてエラーメッセージを表示する場合は、`システム環境設定 > セキュリティとプライバシー`に移動し、各ファイルに対して`このまま開く`を押します。

詳細については、こちらのページをご覧ください: https://disable-gatekeeper.github.io/

### stickers_outputにある、まだアップロードされていないスタンプをアップロードしたい
CLI: `--no-compress --export-xxxxx` で実行します。

GUI: 入力ソースとして`ローカルディレクトリから`を選択し、`圧縮なし`にチェックを入れ、出力オプションとして`xxxxx にアップロードする`を選択します。

### 認証情報はどこに保存されますか？
認証情報は creds.json に保存されます。

デフォルトでは、プログラムを実行するディレクトリと同じディレクトリに保存されます。

ただし、そのディレクトリが書き込み不可の場合（例：macOS では `/Applications`、Linux では `/usr/local/bin` にインストールした場合）、`creds.json` は次の場所に保存されます。
- Windows: `%APPDATA%/sticker-convert/creds.json`
- その他: `~/.config/sticker-convert/creds.json`

### powerとstepsとはどういう意味ですか？
これは最適な圧縮設定を探すための二分法です。`power` は、値を片側に「偏らせる」方法を提供します（負の power を指定すると、sticker-convert はより大きな値を試します。power を 1 に設定すると、sticker-convert は試行を最小値と最大値の間で均等に分散します。power を 1 より大きい値に設定すると、sticker-convert はより小さな値を試します）。

例として、`--steps 16 --fps-min 5 --fps-max 30 --fps-power 3.0` の動作を見てみましょう。
1. 中間点である `8/16`（16 ステップ中 8 ステップ目）から開始します。
2. べき乗を使って係数を計算します: `(8/16)^3.0 = 0.125`
3. fps設定は`round((max - min) * step / steps * factor + min)`で、`round((16-1) * 8 / 16 * 0.125 + 5) = round(5.9375) = 6`となります。つまり、fpsは6に設定されます。
4. ファイルサイズが小さすぎる場合は、`4/16`（16ステップ中4ステップ、0から8の中間点）を試します。それ以外の場合は、`10/16`（16ステップ中10ステップ、8から16の中間点）を試します。
5. 1～3を繰り返します。

## 今後の計画
[/docs/TODO.md](/docs/TODO.md)を参照してください

## クレジット
- SignalとTelegramのスタンプに関する情報: https://github.com/teynav/signalApngSticker
- LineとKakaoのスタンプに関する情報: https://github.com/star-39/moe-sticker-bot
- Lineスタンプに関する情報: https://github.com/doubleplusc/Line-sticker-downloader
- Kakao動画スタンプに関する情報: https://gist.github.com/chitacan/9802668
- Kakao動画スタンプのダウンロードと復号化: https://github.com/blluv/KakaoTalkEmoticonDownloader
- ブラウザの実行パスの検索: https://github.com/roniemartinez/browsers
- アプリケーションアイコンは[Icons8](https://icons8.com/)から取得
- バナーは[GitHub Socialify](https://socialify.git.ci/)から生成
- Windowsでの無料コード署名は以下から提供されています[SignPath.io](https://about.signpath.io/)、[SignPath Foundation](https://signpath.org/) による証明書

## 免責事項
- このリポジトリの作成者は、Signal、Telegram、WhatsApp、Line、Kakao、Naver Band、OGQ、Viber、Discord、iMessage、Sticker Makerとは一切関係ありません。
- このリポジトリの作成者は、このリポジトリの使用によって生じた法的結果や損失について一切責任を負いません。
