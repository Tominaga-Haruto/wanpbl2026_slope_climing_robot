# WRS機 CLI 側の整理: コンテキストはプロンプトで渡し、ローカルには「動かすのに要るもの」だけ置く

作成 2026-09-23。WRS機の CLI の**新しいチャット**に、下のコードブロックをそのまま貼る。実験12の学習が走っていない時間にやる。
方針は `../../../AGENTS.md` の「WRS機 CLI の運用」。終わったらこのファイルを `../inactive/` へ移す。

**方針についての補足（ノートPC側チャットの意見）:** 「ローカルには何も置かない」はほぼ賛成。ただし2つは残す。
(1) コード（学習・再生・評価のスクリプト、ハードリンクされた cfg）。これが無いと毎回プロンプトに手順を書くことになり、かえって長くなる。
(2) 20行程度の「このPCの不変条件」。noise_std_type の入れ忘れ、h5py の DLL 競合、ハードリンク、同名上書きは実際に事故が起きたので、プロンプトの書き漏れで再発させない。
経緯・現在地・候補の評価のような**変わる情報**は WRS 機には置かない。

```
# 依頼: このPC（WRS機）の CLI 環境を「実行専用」に整理する

## このプロンプトの前提
- このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書は「中身を読んで従う」対象ではない。
  今回は整理の対象として一覧を取るだけ。
- 何も削除しない。移動は D:\Tominaga\_wrs_archive\20260923\ へのコピー後に元を移す形で、元の相対パスを保つ。
- 動いている train.py / play.py があれば何もせず止まって報告。
- git の commit・push はしない（このPCの作業ツリーは同期を止めてある）。.git には触らない。
- 学習・評価は起動しない。

## 目標の形
このPCに残すのは次だけ。
1. 動かすためのコード: tools\runs\*.ps1、tools\runs\_preload_h5py_and_run.py、tools\*.py（measure_crab.py など評価・診断）、
   tools\eval_slope\（あれば）、my_robot_code\*.py（IsaacLab 側とハードリンク。絶対に移動・置換しない）、
   onshape_export\ と assets（USD/URDF）、IsaacLab 本体と logs\rsl_rl\（重み）、tools\logs\（実行ログ）。
2. このPCの不変条件を書いた短いファイル1つ（20行以内）。CLI が自動で読む場所に置く
   （Codex なら C:\Users\WRS\.codex\AGENTS.md、Claude Code なら C:\Users\WRS\.claude\CLAUDE.md。使っている方だけ）。
3. それ以外の文書（経緯、現在地、引き継ぎ、指示書、報告書、チャット記録、古い README／ハンドブック、
   作業フォルダ直下の AGENTS.md・CLAUDE.md・claude\ など）は _wrs_archive へ移す。

## R0 棚卸し（読み取りのみ。終わったら止まって報告）
1. 次の場所の .md / .txt 文書と CLI 設定を一覧にする（パス、サイズ、更新日時）:
   D:\Tominaga\slope-climbing-robot 以下（logs\ と .git\ を除く）、C:\Users\WRS\.codex\、C:\Users\WRS\.claude\
   （CLAUDE.md、settings、projects\*\memory など自動で読まれるもの）。
2. 各ファイルを「残す（コード・データ）」「不変条件へ要約して移す」「アーカイブへ移す」に分類した表。
   自動で読み込まれるもの（AGENTS.md、CLAUDE.md、メモリ）は印を付ける。
3. my_robot_code\*.py のハードリンク数とハッシュ（IsaacLab 側と一致しているか）。
4. 不変条件ファイルの草案（20行以内）。入れる候補:
   - パス: 作業フォルダ、IsaacLab、python、run 保存先、tools\logs
   - 学習は tools\runs\_train_foreground.ps1 で前景、再生は tools\runs\_play.ps1。_launch.ps1（バックグラウンド）は使わない
   - agent.policy.noise_std_type を必ず指定（ほぼ全 run が log。H_gainDR だけ scalar）
   - h5py を先読みする _preload_h5py_and_run.py 経由でないと DLL 競合で落ちる。conda activate も必須
   - my_robot_code\*.py はハードリンク。編集は open(r+) で中身だけ書き換え、置換・移動しない
   - cfg は書き換えず Hydra 上書きで条件を作る。スクリプト修正は .bak_日付_内容 を取り、既定挙動を変えない
   - CSV・ログ・run名は毎回変える（同名上書きの事故あり）
   - 何も削除しない。pip install しない。長時間処理はバックグラウンドで回さず、ユーザーに前景コマンドを渡して止まる
   - 依頼はプロンプトに全部書いてある。それ以外の文書を読みに行かない
5. 移動計画（どこからどこへ、何ファイル）。

## R1 実行（ユーザーが「R1 やって」と言ってから）
- R0 の計画どおりにアーカイブへ移す。元の相対パスを保つ。移したら件数とハッシュ照合。
- 不変条件ファイルを置く。既存があれば .bak_20260923_refactor を取ってから置き換える。
- 確認: _play.ps1 と _train_foreground.ps1 が参照するパスがすべて残っている（Test-Path の一覧）。
  my_robot_code のハードリンク数・ハッシュが R0 と同じ。

## 報告
R0: 冒頭3行（文書の数、自動で読まれるもの、移す量）、分類表、不変条件の草案、移動計画。ここで止まる。
R1: 移した件数、照合結果、Test-Path の結果、不変条件ファイルの全文。
```
