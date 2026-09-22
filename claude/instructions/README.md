# instructions/

WRS学習機・デプロイ作業に渡す**指示書**。1件＝1作業単位。

```
instructions/
  active/     まだ実行中・これから実行する指示書
  inactive/   終わった・置き換えられた・廃止された指示書（読まない）
```

- 開始時には読まない。`CONTEXT.md` か `handoffs/active/` が名指ししたものだけ読む。
- 実機を触る手順は `procedures/` にある。ここは主に学習機・準備作業側。
- **終わった指示書は、終わったと判断したエージェントがその場で `git mv instructions/active/<名前>.md instructions/inactive/` する。** ユーザーに頼まない。同じ commit で `CONTEXT.md` のリンクを直す。
- 消さない。`inactive/` に移すだけ。ファイル名の日付と番号が履歴である。
- **WRS機の CLI に渡す指示は、リポジトリ直下 `AGENTS.md` の「WRS機 CLI の運用」に従って書く**（自己完結・コンテキストを読ませない・長時間処理はユーザーが前景で回す）。
- 2026-09-23 以前の文書には移動前のパス（`instructions/<名前>.md`）が残っている。ファイル名で `active/` か `inactive/` を探せばよい。
