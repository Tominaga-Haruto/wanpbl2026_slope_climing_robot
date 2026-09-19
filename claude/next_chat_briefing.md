# 次チャットへの指示書 — このノートPCの Isaac Lab debugging #11（2026-09-19）

## このチャットの役割

- ここは**ノートPC側の講評・判断チャット**である。WRS側には既に稼働中のCodexがあり、ユーザーが明示して「WRS側の新しいチャット」を求めない限り、新しいWRSチャットを作らない。
- 最初に `README.md`、`project_handbook.md`、`handover.md`、この文書の順で読む。恒久規約は `project_handbook.md` A1/A5 が正本で、この文書へ運用規約を足さない。
- WRS側Codexには、必要な作業を既存チャットへの追記として渡す。実行結果を受けて、このチャットで採点・次の判断を行う。

## 現在地

- 直進の第一候補は H_eff13p5@2999、予備は G_real_peak@2999。
- P2_gainDR_seed2 / P3_stiffonly は平地上書きを欠き、terrain level 4.714 / 5.075 のrough地形で学習した。平地候補・再開元に使わない。
- WRS側の既存cloneには、`README.md` / `project_handbook.md` の削除と多数の未追跡ファイルがある。WRS側Codexに既存cloneを安全に整理・同期させる。二重cloneは作らない。未追跡の`references/`・生成物・バックアップは勝手に削除・追加しない。

## 最初にWRS側の既存Codexへ渡す指示

WRS側Codexへ次を送る。Git同期までをWRS側Codexが行う。

```text
既存の `D:\Tominaga\slope-climbing-robot` を安全にGit管理してください。二重cloneは禁止です。

1. `git remote -v` と `git branch --show-current` で、originがこのプロジェクトのGitHub remote、branchがmainであることを確認する。違えば変更せず報告して止まる。
2. `git status --short`、`git diff -- README.md project_handbook.md`、`git ls-files README.md project_handbook.md` を読み、削除された追跡docsがローカル編集ではなく、旧cloneの未整理状態であることを確認する。
3. 確認できた場合、追跡されている削除docsだけを `git restore --source=HEAD -- README.md project_handbook.md` で戻す。`references/`、onshape_exportのbak、toolsの生成物など未追跡物は削除・add・stashしない。
4. `git fetch origin` の後、`git pull --ff-only origin main` で同期する。競合・fast-forward不能・未追跡ファイル衝突があれば、何も上書きせず停止して原因を報告する。
5. 同期後に `git status --short`、`git log -3 --oneline`、`git rev-parse HEAD` を確認する。未追跡物だけが残る状態を目標にする。
6. Git同期後、`AGENTS.md`、`claude/README.md`、`claude/project_handbook.md`、`claude/handover.md`、`claude/next_chat_briefing.md`を読んでから学習へ進む。

学習を起動する前に、各runについて平地16 envの再生コマンドをユーザーへ先に提示してください。実在するプリロード起動方法・平地上書きから作り、学習中/終了後にそのrunの最新保存済みcheckpointを自動選択する完成コマンドにします。学習終了後は、採用した固定checkpoint名を埋めた再生コマンドも必ず提示してください。
```

## Git状態の判断後に行う学習案（まだWRSへ送らない）

ユーザーがWRS cloneの扱いを決め、平地用起動方法を既存スクリプト・paramsから確認できた後に限り、長時間GPU許可を使って次の2本を並列実行する。

1. F1: H_eff13p5@2999から、平地、seed 2、stiffness x0.85〜1.15・damping x0.8〜1.25だけを加えた直進gain DR。
2. T1: H_eff13p5@2999から、L_angstd_w1の実設定を基準に、平地、std=0.35、yaw報酬weight=1.0、yaw_gate、translate-only比率0.15を保ち、純旋回比率だけ0.20→0.35にする旋回学習。

両方とも64 env / 20 iterで、平地上書き・noise_std_type=log・再開元・意図した差分だけを`params\\env.yaml` / `agent.yaml`で確認してから4096 envへ進む。F1はc06転倒率≤5%かつ既存平地基準、T1は評価2回とも連続300 iterの旋回合格を満たした場合だけ候補にする。第三ランは勝手に始めない。

本番を起動したWRS側Codexは、iteration 30後に各runの実測秒/iter、残りiteration、予想終了時刻、そこからの残り時間を必ず報告する。並列時はrunごとに計算し、遅い方の終了時刻を全体の終了見込みとして併記する。

## このチャットの終了時

- WRS側のGit状態と実行結果を `training_runs.md` / 該当report / `chats/` に記録する。
- 次のチャットへの指示書を更新するのは、ユーザーがこのノートPC側で「次へ移る」と明示した時だけ。
