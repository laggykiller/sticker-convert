# Viber スタンプのダウンロード
sticker-convert は、スタンプパックの共有リンクから Viber スタンプをダウンロードできます。

# Viber スタンプのアップロード
Viber スタンプをアップロードするには、Viber 認証データが必要です。このデータは、Viber デスクトップアプリケーションから自動的に取得できます。
1. Viber デスクトップをインストールします。
2. Viber デスクトップにログインします。
3. sticker-convert で、「生成」ボタン (GUI の場合) または `--viber-get-auth` (CLI の場合) を押します。

注意:
- 認証データを取得する際、Viber デスクトップは一度閉じ、起動し、再び閉じられます。
- 認証データの取得には 1 分ほどかかる場合があります。
- macOS では SIP を無効にする必要があり、ユーザーパスワードの入力を求められる場合があります。
- Viber デスクトップの非標準インストールでは、`--viber-bin-path` を使用して Viber デスクトップ アプリケーションの場所を指定できます。
- `m_token`、`m_ts`、`member_id` が必要です。
- `m_ts` は、`m_token` が生成された時点の Unix タイムスタンプです。
- `m_token` は 13800 秒 (230 分) 後に有効期限が切れます。

# 参考資料
詳細については、https://help.viber.com/hc/en-us/articles/9204828903837-Use-and-create-stickers-on-Rakuten-Viber をご覧ください。