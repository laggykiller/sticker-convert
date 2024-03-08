# Getting signal uuid and password
`uuid` and `password` are needed for uploading Signal stickers.
(Note: If you don't want to do this, you can still upload stickers manually by Signal Desktop)

## Method 1: Automatic
You can get them easily with `Generate` button (In GUI) or `--signal-get-auth` (In CLI)

Since v2.7.0, you can get Signal uuid and password from non-beta version of Signal.

If you are using custom Signal installation such as portapps, you need to specify Signal
data directory (`--signal-data-dir` In CLI). Choose the `data` directory of your Signal
portable installation.

## Method 2: Manual
![../imgs/signal-uuid-password.png](../imgs/signal-uuid-password.png)

1. Install Signal Desktop BETA VERSION from https://support.signal.org/hc/en-us/articles/360007318471-Signal-Beta
2. Link Signal Desktop with your phone
3. Launch Signal Desktop BETA VERSION
4. On the top bar, go to `View -> Toggle Developers tools`
5. Open console
    - If you want to copy-paste commands, type `allow pasting` and press enter first
    - `uuid` is the output of running: `window.SignalDebug.getReduxState().items.uuid_id`
    - `password` is the output of running: `window.SignalDebug.getReduxState().items.password`

Reference
- https://github.com/teynav/signalApngSticker
- https://github.com/signalstickers/signalstickers-client
- https://github.com/signalstickers/signalstickers-client/issues/15
