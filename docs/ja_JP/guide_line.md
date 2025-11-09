# LINEスタンプのダウンロード
1. https://store.line.me/stickershop または https://store.line.me/emojishop からスタンプを検索できます。
2. スタンプパックのURLをコピーし、sticker-convertのURLを入力します。

# カスタムテキスト付き「メッセージスタンプ」のダウンロード
1. メッセージスタンプのURLを入力し、変換を開始します。
2. スタンプのダウンロード時にメッセージが表示されます。line-sticker-text.txtを編集して続行してください。

# カスタムテキスト付き「カスタムスタンプ」のダウンロード
このダウンロードにはLINEのCookieが必要です。

## 方法 1: 自動
1. store.line.me にログインします。
2. スタンプ変換 GUI の`生成`ボタンを押します。
3. ウィンドウ内の`Cookie を取得`ボタンを押します (形式: `key_1=value_1;key_2=value_2`)。
4. カスタムスタンプの URL を入力し、変換を開始します。
5. スタンプのダウンロード時にメッセージが表示されます。line-sticker-text.txt を編集して続行します。

注意:
- Chrome ブラウザの [最近のアップデート](https://github.com/borisbabic/browser_cookie3/issues/180) により、この方法が機能しない可能性があります。その場合は手動で設定する必要があります。
- 成功率を高めるには、Firefox を使用してください。

## 方法2：手動
1. ブラウザに`Get cookies.txt LOCALLY`拡張機能をインストールします。
    - Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
    - Firefox: https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/
    - Githubページ: https://github.com/kairi003/Get-cookies.txt-LOCALLY
2. store.line.meにログインします。
3. `Get cookies.txt LOCALLY`拡張機能を開き、`Export Format`」で`JSON`を選択し、`Copy`を押します。
4. Sticker-convertの`Line Cookies`欄に貼り付けます。

# LINEスタンプのアップロード
アプリで使用する前に、スタンプパックを手動で承認申請する必要があります。