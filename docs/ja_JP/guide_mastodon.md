# Mastodonカスタム絵文字のダウンロード
MastodonのURLのみが必要で、Cookieは不要です。

# Mastodonカスタム絵文字のアップロード
Cookieが指定されていない場合、`.tar.gz`ファイルが生成されます。このファイルは、`toolctl`を使用してMastodonに一括アップロードする際に使用できます。

Cookieが指定されている場合、sticker-convertは絵文字をMastodonにアップロードしようとします。


# クッキーの取得

## 方法 1: 自動
1. Chrome ブラウザをインストールします。
2. Mastodon の URL を入力します。
3. sticker-convert GUI の「生成」ボタンをクリックします。
4. ウィンドウの「クッキーを取得」ボタンをクリックし、Mastodon にログインします。

## 方法 2: 手動
1. ブラウザに`Get cookies.txt LOCALLY`拡張機能をインストールします。
    - Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
    - Firefox: https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/
    - Githubページ: https://github.com/kairi003/Get-cookies.txt-LOCALLY
2. Mastodonにログインします。
3. `Get cookies.txt LOCALLY`拡張機能を開き、`_session_id`の値をコピーします。
4. sticker-convertの`Mastodon cookies`フィールドに貼り付けてください。

# カスタム絵文字の命名規則
カスタム絵文字は、`<カテゴリ>-<名前>.<拡張子>`の形式でダウンロードおよびアップロードされます。

例1：カテゴリ`lol`に属する名前`:cat:`のカスタム絵文字は、`lol-cat.png`となります。
例2：未分類のカスタム絵文字`:dog:`は`dog.png`となります。