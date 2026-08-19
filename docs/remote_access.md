# リモートアクセス設定

## TeamViewer
- 設定日: 2026-07-17
- TeamViewer バージョン: 15.79.4 (DEB)
- デスクトップ TeamViewer ID: (ここに9-10桁)
- 固定パスワード: (別途管理 / パスワードマネージャ推奨)
- セッション: X11 (WaylandEnable=false in /etc/gdm3/custom.conf)
- 自動ログイン: 有効 / 無効 ← どちらにしたか記入

## 接続手順
1. ノートPC の TeamViewer を起動
2. パートナーID に上記IDを入力 → 接続
3. パスワード入力

## 注意
- Wayland に戻ると画面が真っ暗になる
- Isaac Sim の3Dビューポートは TeamViewer だと重い → Omniverse Streaming 推奨
