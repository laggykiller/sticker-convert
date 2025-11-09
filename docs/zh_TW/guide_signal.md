# 取得 Signal UUID 和密碼
上傳 Signal 貼紙需要 `uuid` 和 `password`。
（注意：如果您不想這樣做，仍然可以透過 Signal Desktop 手動上傳貼圖。）

## 方法 1：自動取得
您可以使用「生成」按鈕（在圖形介面中）或 `--signal-get-auth` 命令（在命令列介面中）取得它們。

自 v2.7.0 起，您可以從 Signal 的非測試版中取得 Signal UUID 和密碼。

## 方法二：手動（使用 Signal Beta 版）
![../imgs/signal-uuid-password.png](../imgs/signal-uuid-password.png)

1. 從 https://support.signal.org/hc/en-us/articles/360007318471-Signal-Beta 安裝Signal Desktop Beta版
2. 將 Signal Desktop 與您的手機連接
3. 啟動 Signal Desktop Beta 版
4. 在頂部功能表列中，前往“檢視 (View) -> 切換開發者工具 (Toggle Developers tools)”
5. 開啟控制台 (Console)
    - 如果您想複製貼上命令，請先輸入`allow pasting`並按回車鍵
    - `uuid` 是執行下列程式碼的輸出：`window.SignalDebug.getReduxState().items.uuid_id`
    - `password` 是執行下列程式碼的輸出：`window.SignalDebug.getReduxState().items.password`

## 方法三：手動（使用 Signal Production）
1. 從 https://signal.org/en/download/ 安裝 Signal Desktop
2. 將 Signal Desktop 與您的手機連接
3. 使用 `--enable-dev-tools` 參數啟動 Signal Desktop
4. 在頂部功能表列中，前往“檢視 (View) -> 切換開發者工具 (Toggle Developers tools)”
5. 開啟控制台 (Console)
    - 將 JavaScript context從Top變更為 Electron Isolated Context（請參閱下方影片）
    - 若您想複製貼上指令，請先輸入`allow pasting`並按下回車鍵
    - `uuid` 是執行下列程式碼的輸出：`window.reduxStore.getState().items.uuid_id`
    - `password` 是執行下列程式碼的輸出：`window.reduxStore.getState().items.password`

https://github.com/signalstickers/signalstickers-client/assets/7778898/ca3f1fec-e908-49d9-88a8-e33d0ee9a453

參考資料
- https://github.com/teynav/signalApngSticker
- https://github.com/signalstickers/signalstickers-client
- https://github.com/signalstickers/signalstickers-client/issues/15
- https://github.com/signalstickers/signalstickers-client/issues/15#issuecomment-1474791031
