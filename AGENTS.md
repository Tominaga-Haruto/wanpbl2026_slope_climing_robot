# 坂登坂ロボット

目的は平地での実機デプロイ。GitHub `main` とリポジトリ内の `claude/` が正本であり、`claude/` はClaude専用ではなく全エージェント共通の文書領域である。

## 開始手順

1. `git status --short`で他PCの未整理変更を把握し、上書きしない。
2. `claude/PROJECT.md`、`claude/CONTEXT.md`、そして`CONTEXT.md`が冒頭で名指しする`claude/handoffs/`の引き継ぎ書を順に読む。この4つで全部である。
3. それ以外は最初に読まない。必要になった時だけ`claude/PROJECT.md`の表から1本ずつ取りに行く。古い`README.md`・`project_handbook.md`・`next_chat_*`・`chats/`は、明示的に参照されたときだけ読む。

## 不変のルール

- 機械固有の役割は`~/.codex/AGENTS.md`に従う。役割外の実行はしない。
- 数値・配線・関節符号は推測せず、該当する正本を確認する。
- 実機モーターは、ユーザーが明示して安全条件を確認した場合だけ操作する。1モーター→片脚→全身の順を崩さない。
- 重み・モデル・生ログ・鍵をGitに入れない。ローカル実行時のログは報告書へ要約し、絶対パスと時刻を残す。
- 基本情報は`claude/PROJECT.md`、現在地は`claude/CONTEXT.md`、次の担当への指示は`claude/handoffs/`（日付＋内容の名前。有効な1本はCONTEXT.mdが名指しする）、詳細資料は`claude/domains/`と`claude/procedures/`、根拠は`claude/reports/`、過去の会話履歴は`claude/chats/`に置く。更新のしかたは`claude/PROJECT.md`の「文書の更新ルール」に従う。
- 作業結果は対象を絞ってcommit/pushし、現在地またはアクティブ引き継ぎを同じ変更に更新する。
