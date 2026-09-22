# claude/ — 全エージェント共通の文書領域

Claude専用ではない。Codexもここを正本として読み書きする。

**開始時に読むのはこの4つだけ**（合計 約1万字）。

1. リポジトリ直下の `../AGENTS.md`
2. `PROJECT.md` ── 基本情報と、下のフォルダの地図
3. `CONTEXT.md` ── 現在地。いま有効な引き継ぎ書を冒頭で名指しする
4. その名指された `handoffs/YYYY-MM-DD_....md`

これ以外は最初に読まない。必要になった時だけ `PROJECT.md` の表から1本ずつ取りに行く。

| フォルダ | 中身 | 開始時 |
|---|---|---|
| `handoffs/` | 次の担当への引き継ぎ書（有効な1本はCONTEXT.mdが名指し） | 名指された1本だけ |
| `procedures/` | 実機・評価の実行手順 | × |
| `instructions/` | WRS機・デプロイ作業への指示書 | × |
| `reference/` | 数値・環境・コード構造の正本 | × |
| `domains/` | 分野ごとの入口（hardware / policy / controller / deployment） | × |
| `reports/` | 結論の根拠。追記のみ | × |
| `chats/` | 過去の会話。1チャット1ファイル。追記のみ | × |
| `archive/` | 役目を終えた引き継ぎ・briefing・生ログ | × |
| `legacy/` | 旧来の巨大な入口文書 | × |

直下にファイルを増やさないこと。ルールは `PROJECT.md`「文書の更新ルール」。
