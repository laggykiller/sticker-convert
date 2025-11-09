# 取得 Signal UUID 和密码
上传 Signal 貼纸需要 `uuid` 和 `password`。
（注意：如果您不想这样做，仍然可以透过 Signal Desktop 手动上传貼图。）

## 方法 1：自动取得
您可以使用`生成`按钮（在图形介面中）或 `--signal-get-auth` 命令（在命令列介面中）取得它们。

自 v2.7.0 起，您可以从 Signal 的非测试版中取得 Signal UUID 和密码。

## 方法二：手动（使用 Signal Beta 版）
![../imgs/signal-uuid-password.png](../imgs/signal-uuid-password.png)

1. 从 https://support.signal.org/hc/en-us/articles/360007318471-Signal-Beta 安装Signal Desktop Beta版
2. 将 Signal Desktop 与您的手机连接
3. 启动 Signal Desktop Beta 版
4. 在顶部功能表列中，前往“检视 (View) -> 切换开发者工具 (Toggle Developers tools)”
5. 开启控制台 (Console)
    - 如果您想复制貼上命令，请先输入`allow pasting`并按回车键
    - `uuid` 是执行下列程式码的输出：`window.SignalDebug.getReduxState().items.uuid_id`
    - `password` 是执行下列程式码的输出：`window.SignalDebug.getReduxState().items.password`

## 方法三：手动（使用 Signal Production）
1. 从 https://signal.org/en/download/ 安装 Signal Desktop
2. 将 Signal Desktop 与您的手机连接
3. 使用 `--enable-dev-tools` 参数启动 Signal Desktop
4. 在顶部功能表列中，前往“检视 (View) -> 切换开发者工具 (Toggle Developers tools)”
5. 开启控制台 (Console)
    - 将 JavaScript context从Top变更为 Electron Isolated Context（请参阅下方影片）
    - 若您想复制貼上指令，请先输入`allow pasting`并按下回车键
    - `uuid` 是执行下列程式码的输出：`window.reduxStore.getState().items.uuid_id`
    - `password` 是执行下列程式码的输出：`window.reduxStore.getState().items.password`

https://github.com/signalstickers/signalstickers-client/assets/7778898/ca3f1fec-e908-49d9-88a8-e33d0ee9a453

参考资料
- https://github.com/teynav/signalApngSticker
- https://github.com/signalstickers/signalstickers-client
- https://github.com/signalstickers/signalstickers-client/issues/15
- https://github.com/signalstickers/signalstickers-client/issues/15#issuecomment-1474791031
