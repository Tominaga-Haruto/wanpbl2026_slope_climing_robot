# 次チャットへの指示書 — Isaac Lab debugging #11（2026-09-19）

## 役割・最優先規約

- 目標は平地での実機デプロイ。WRS機の Codex は利用可能で、ユーザーは長時間のGPU利用を許可している。
- 最初に **`README.md` → `project_handbook.md` → `handover.md` → この文書** の順で読む。恒久的な運用規約は `project_handbook.md` A1/A5、これは今回だけの実験指示である。
- WRS機の既存cloneを使い、別cloneは作らない。開始時にgit statusが空でなければpullも学習も始めず、差分を報告する。
- 共用PCなので他人のプロセスを止めない。`D:\\Tominaga\\`の外へ書かない。pip/conda install、Isaac Lab/Sim・conda環境/extscacheの変更・削除はしない。
- 学習前に `nvidia-smi`、`where.exe python`、`python -c "import h5py"` を確認する。h5py単体は通っている。playのDLL衝突には実在する `tools\\runs\\_preload_h5py_and_run.py` を使い、中身を読んでから使う。
- 全学習・再生・評価は平地にする。既定の`Velocity-Rough-...` / `...-Play-v0`はrough。平地の正確なHydra上書きは既存の平地runと`params\\env.yaml`から確認し、推測でキー名を書かない。

## 現在地

- 直進の第一候補は `H_eff13p5@2999`、予備は `G_real_peak@2999`。
- P2/P3は平地上書きなしでterrain level 4.714 / 5.075まで上がった。平地のgain DR比較として不成立であり、重みを再開元・候補・平地評価に使わない。
- 旋回は L_angstd_w1@4000/4200だけに一時的な合格があり、連続300 iter・頑健性を満たさなかった。N_w1_seed2は合格ゼロ、N_w1p5は4400の単発合格。

## 最初の停止点: 同期と実在確認

1. `D:\\Tominaga\\slope-climbing-robot`で`git status --short`、`git remote -v`、`git log -3 --oneline`を確認する。cleanなら`git pull --ff-only origin main`を行い、最新commitを報告する。差分があれば更新せず報告する。
2. `D:\\Tominaga\\IsaacLab`で`tools\\runs`、`_preload_h5py_and_run.py`、平地評価/学習スクリプト、H/L/Jのrunの`params\\env.yaml`と`agent.yaml`を読む。
3. H_eff13p5@2999、L_angstd_w1@4000、J_turn_resumeの実run名とcheckpointを確認する。L/Jがなければrun名一覧だけを報告して止まる。
4. H_eff13p5@2999を16 env・平地で短時間再生し、自然な前進か、静止・転倒・不自然歩容かを記録する。再生は学習と同時に行わない。

## 実験11: 平地2本の並列学習

起動前に両方を64 env / 20 iterでテストする。元runとの`params\\env.yaml` / `agent.yaml`のdiffを取り、flat=1.0・その他=0.0、noise_std_type=log、再開元、各ラン固有の上書きを確認する。意図しない差分があれば本番を起動しない。

### F1: 直進の平地 gain DR

- run名 `F1_flat_gainDR_seed2`。H_eff13p5@2999から再開、seed 2、4096 env、追加1500 iter。
- 変更は狭いactuator gain DRだけ: stiffness x0.85〜1.15、damping x0.8〜1.25。
- 旋回用yaw_gate・純旋回比率・yaw報酬の変更は入れない。
- 狙いはHのstiffness x0.7での転倒6.2%を、平地歩容を壊さず下げること。

### T1: 旋回の平地学習

- run名 `T1_turn35_flat_seed1`。H_eff13p5@2999から再開、seed 1、4096 env、追加1500 iter。
- L_angstd_w1の実際の起動行を土台にする: yaw_gate=true、yaw追従std=0.35・weight=1.0、translate-only比率0.15を保つ。
- 変更は純旋回指令比率だけをLの0.20から0.35へ上げること。実際のHydra key・既存値はJ/Lのparamsから確認する。
- gain DRは入れない。直進頑健化と旋回の変更を混ぜない。

## 起動・監視・評価

- 起動行はWRS側Codexが実在するプリロード起動スクリプトとparamsから組み立てる。`cd`、conda有効化、Python確認、EULA、平地上書き、noise_std_type=log、run名、再開元、checkpointを省略しない完成形にする。
- 起動後iter 30でcheckpoint loading・flat上書き・秒/iter・VRAM・GPU温度を確認する。NaN、noise std<0.05、設定差分、Hydra errorならそのrunだけ止め、末尾30行とdiffを報告する。
- F1はS1〜S11、S1の関節RMS/最大/飽和率、c06、Hに無い不合格をH@2999と比較する。
- T1はS6/S9を256 env・評価seed 2回で評価し、S1/S7/S8、転倒、|(vx,vy)|、左右比、歩数、FFE RMSも出す。

## 採用規則と停止点

- F1を候補にするのは、既存平地基準、c06転倒率≤5%、Hに無い不合格なし、自然な歩容を満たす場合だけ。
- T1を候補にするのは、S6/S9で|yaw|≥0.25、符号一致、|(vx,vy)|≤0.10、転倒≤5%、左右比0.5〜2、既存基準の退行なしを評価2回とも連続300 iter以上で満たす場合だけ。
- どちらも基準を満たさなければ第三ランを勝手に始めない。全runの表・動画/再生所見・原因仮説を記録して停止する。
- 終了時に`training_runs.md`、`docs\\experiments\\`または`tools\\logs\\REPORT_exp11.md`、`chats/`を更新する。コード・文書だけをcommitし、pushはユーザーへ確認する。
