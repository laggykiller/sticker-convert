# SignalのUUIDとPasswordの取得
Signal スタンプをアップロードするには、`UUID` と `Password` が必要です。
(注: 手動でアップロードしたくない場合は、Signal Desktop を使って手動でスタンプをアップロードすることもできます)

## 方法 1: 自動
`Generate` ボタン (GUI の場合) または `--signal-get-auth` (CLI の場合) を使用すると取得できます。

v2.7.0 以降では、Signal のベータ版以外からSignalのUUIDとPasswordを取得できます。

## 方法 2: 手動 (Signal Beta版を使用)
![/imgs/signal-uuid-password.png](/imgs/signal-uuid-password.png)

1. https://support.signal.org/hc/en-us/articles/360007318471-Signal-Beta から Signal Desktop Beta版をインストールします。
2. Signal Desktop をスマートフォンにリンクします。
3. Signal Desktop Beta版を起動します。
4. 上部のバーで、`表示 -> 開発者ツールの切り替え` (`View -> Toggle Developers tools`)を選択します。
5. コンソールを開きます。
    - コマンドをコピー＆ペーストする場合は、`allow pasting`と入力して Enter キーを押します。
    - `uuid` は、`window.SignalDebug.getReduxState().items.uuid_id` を実行した際の出力です。
    - `password` は、`window.SignalDebug.getReduxState().items.password` を実行した際の出力です。 

## 方法 3: 手動 (Signal Production を使用)
1. https://signal.org/en/download/ から Signal Desktop をインストールします。
2. Signal Desktop をスマートフォンとリンクします。
3. `--enable-dev-tools` フラグを付けて Signal Desktop を起動します。
4. 上部のバーで、`表示 -> 開発者ツールの切り替え` (`View -> Toggle Developers tools`)を選択します。
5. コンソールを開きます。
    - JavaScript コンテキストをtopからElectron Isolated Contextに変更します (下の動画を参照)。
    - コマンドをコピー＆ペーストする場合は、`allow pasting`と入力して Enter キーを押します。
    - `uuid` は、`window.reduxStore.getState().items.uuid_id` を実行した際の出力です。
    - `password` は、`window.reduxStore.getState().items.password` を実行した際の出力です。

https://github.com/signalstickers/signalstickers-client/assets/7778898/ca3f1fec-e908-49d9-88a8-e33d0ee9a453

参照
- https://github.com/teynav/signalApngSticker
- https://github.com/signalstickers/signalstickers-client
- https://github.com/signalstickers/signalstickers-client/issues/15
- https://github.com/signalstickers/signalstickers-client/issues/15#issuecomment-1474791031
