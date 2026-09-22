# claude/ — 道しるべ

> **これは索引ではなく道しるべ。ここで読むのを止めて、下の4つだけ読む。**
> 旧・大索引（〜2026-09-22、チャット索引つき）は `legacy/README_index_legacy.md` に保全した。開始時には読まない。

## 新しいセッションが読むもの（これで全部）

1. リポジトリ直下の **`AGENTS.md`** ── 掟と開始手順
2. **`PROJECT.md`** ── 目的・機械・文書構造・読む順番・更新ルール
3. **`CONTEXT.md`** ── 現在地。**いま有効な引き継ぎ書を冒頭で名指しする**
4. その名指された **`handoffs/YYYY-MM-DD_....md`** ── 次にやること

合計およそ1万字。**それ以外は最初に読まない。**

## 途中で必要になったら

| 欲しいもの | 入口 |
|---|---|
| ハードウェア・CAN・関節・原点 | `domains/hardware/README.md` |
| 方策・学習・評価 | `domains/policy/README.md` |
| コントローラー | `domains/controller/README.md` |
| デプロイの段取り | `domains/deployment/README.md` |
| 実機・評価の実行手順 | `procedures/README.md` |
| ある結論の根拠 | `reports/` |
| 過去のやり取り | `chats/` |
| 旧来の巨大な入口文書 | `legacy/` |

## 毎チャット必ず

終わる前に `chats/YYYY-MM-DD_内容.md` を1ファイル作る。**索引への追記は不要**（ファイル名と `git log` が索引）。`CONTEXT.md` と次の引き継ぎ書も同じcommitで更新する。更新のしかた（書き換えか追記か）は `PROJECT.md` の「文書の更新ルール」。
