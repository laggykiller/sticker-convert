# Summary of downloading stickers in Kakao
| リンク                                                   | 動画スタンプをダウンロードするには認証トークンが必要ですか? |
| ------------------------------------------------------- | ------------------------------------------------------------------|
| "共有リンク": `https://emoticon.kakao.com/items/xxxxx`   | 必要 (推奨)                                                        |
| "ブラウザリンク": `https://e.kakao.com/t/xxxxx`          | 必要                                                               |
| "商品コード": `4404400`                                  | 必要ない (しかし手に入れる簡単な方法はない)                           |

- 動画スタンプのダウンロードにのみ auth_token が必要です。画像スタンプには必要ありません。
- 動画スタンプのダウンロードにおいて、`https://e.kakao.com/t/xxxxx` ではなく `https://emoticon.kakao.com/items/xxxxx` を使用すると、ダウンロードに失敗する可能性がわずかにあります。

## 共有リンクの取得方法
![/imgs/kakao-share.jpeg](/imgs/kakao-share.jpeg)

ウェブリンク (`https://e.kakao.com/t/xxxxx`) から見つけたスタンプパックをダウンロードするには、以下の手順に従ってください。
1. e.kakao.com で Kakao にログイン
2. ダウンロードしたいパックに「いいね！」する (ハートボタンを押す)
3. Kakao モバイルアプリでスタンプショップを開く -> 左上のハンバーガーメニューをタップ -> 「いいね！」して、気に入ったパックを見つける
4. モバイルアプリで共有リンクを取得し、sticker-convert を使用してパックをダウンロードする

## auth_token の取得方法
### 方法1：KakaoTalkデスクトップアプリケーションから認証トークンを取得する（推奨）
- `sticker-convert` は、KakaoTalkデスクトップアプリケーションから認証トークンを取得します。
- Linuxをお使いの場合は、wineを使用してWindows版をインストールできます。`winecfg` でWindowsバージョンを`Windows 10`に設定し（`winecfg -v win10`）、wine monoをインストールしてください。

GUI:
1. KakaoTalkデスクトップをダウンロードしてログインします。
2. Sticker-convert GUIの`生成する`ボタンを押します。
3. （オプション）KakaoTalkデスクトップをデフォルト以外の場所にインストールした場合は、`Kakaoアプリのパス`を指定できます。
4. `auth_tokenを取得する`ボタンを押して待機します。

CLI:
1. KakaoTalkデスクトップをダウンロードしてログインします。
2. 引数に`--kakao-get-auth-desktop`を追加します。
3. （オプション）KakaoTalkデスクトップをデフォルト以外の場所にインストールした場合は、`--kakao-bin-path <KAKAO_APP_PATH>`を追加します。
3. コマンドを実行します。

### 方法2：ログインをシミュレートしてauth_tokenを取得します。
- `sticker-convert`は、Android Kakaoアプリへのログインをシミュレートしてauth_tokenを取得します。
    - SMSで認証コードを送受信します。
    - 認証コードを受信する可能性が高いです。
    - 認証SMSを送信する必要がある場合は、認証コードの受信を何度もリクエストしました。
    - 既存のデバイスからログアウトされる可能性があります。
- auth_tokenは一定期間（約1週間）経過すると有効期限が切れます。有効期限が切れた場合は再生成してください。
- ログイン情報の説明
    - ユーザー名：Kakaoアカウントの登録に使用したメールアドレスまたは電話番号。（例：+447700900142）
    - パスワード：Kakaoアカウントのパスワード
    - 国コード：例：82（韓国）、44（英国）、1（米国）
    - 電話番号：Kakaoアカウントに関連付けられた電話番号。 SMS経由で認証コードを送受信するために使用します。

GUI:
1. 携帯電話でKakaoTalkアカウントを作成します。
2. スタンプ変換GUIの`生成`ボタンを押します。
3. ウィンドウにアカウントの詳細を入力します。
4. `ログインして認証トークンを取得`ボタンを押し、指示に従います。

CLI:
1. 携帯電話でKakaoTalkアカウントを作成します。
2. 引数として`--kakao-get-auth --kakao-username <ユーザー名> --kakao-password <パスワード> --kakao-country-code <国コード> --kakao-phone-number <電話番号>`を追加します。
- 注: 以前にユーザー名、パスワード、国コード、電話番号を保存している場合は、引数として追加しなくても構いません。
- 認証トークンとログイン情報を後で使用するために、`--save-cred`を追加することもできます。
3. コマンドを実行します。指示に従ってください。

### 方法3: 認証トークンを手動で取得するか、スタンプIDを取得する
ルート化されたAndroidデバイスから認証トークンを手動で取得できます（エミュレートされたAndroidデバイスで行うことをお勧めします）。

1. スマートフォンでKakaoTalkアカウントを作成します。
2. Android Studioをインストールし、エミュレートされたデバイスを作成します。デバイスにKakaoTalkをインストールします。
3. BurpSuiteをインストールします。
4. このガイドに従って、AndroidエミュレートされたデバイスをBurpSuiteに接続します。https://blog.yarsalabs.com/setting-up-burp-for-android-application-testing/
5. このガイドに従って、SSLピンニングをバイパスします。https://redfoxsec.com/blog/ssl-pinning-bypass-android-frida/
- このガイドに記載されている`cer.cer`には、手順4で作成した`burp-ca.crt`を使用します。
- `adb shell`、`su`、`/data/local/tmp/frida-server`を実行して起動します。 Android エミュレータ上の `frida-server`
- `frida-server` の実行中に `frida -U -f com.kakao.talk -l fridascript.js` を実行します。
6. KakaoTalk アプリケーションでスタンプを検索し、BurpSuite で HTTP 履歴を確認します。
- auth_token を取得するには、BurpSuite に表示されるリクエストのヘッダーから `Authorization` をコピーします。
- スタンプ ID を取得するには、`https://item.kakaocdn.net/dw/4404400.emot_001.webp` などの URL を探します。スタンプ ID は `4404400` です。

## 技術的な補足: 動画スタンプのデコード
webp および gif 形式のスタンプはデコードする必要があります。 Kakao Android アプリケーションの場合、`com/kakao/digitalitem/image/lib/ImageDecode.java` は `libdigitalitem_image_decoder.so` を呼び出します。

1. `nativeWebpImageResizeDecode()` または `nativeGifImageDecode()`
2. `webpDecode()` または `gifDecode()`
3. `decryptData()`
4. `cryptData()` は、LFSR と XOR によってスタンプをデコードします。

ご興味があれば、Kakao Android アプリケーションを `jadx` で逆コンパイルし、`libdigitalitem_image_decoder.so` を `ghidra` で逆コンパイルして学習することができます。

- Androidネイティブライブラリのリバースエンジニアリング: https://github.com/maddiestone/AndroidAppRE/blob/master/reversing_native_libs.md
- Kakao動画スタンプに関する情報: https://gist.github.com/chitacan/9802668
- Kakao動画スタンプのダウンロードと復号化: https://github.com/blluv/KakaoTalkEmoticonDownloader
- 共有リンクを使用してパックIDを取得する: https://github.com/star-39/moe-sticker-bot
