# slope-climbing-robot

二足歩行ロボットを Isaac Lab ＋ RSL-RL で歩かせ、最終的に坂を登らせるプロジェクト。

**まず `project_handbook.md` を読むこと。** 現状・環境の注意点・結論・次にやることが全部そこにある。
この README は「どこに何があるか」の索引。

参考実装: Skyentific https://github.com/SkyentificGit/BipedalRobotSim

---

## 1. 読む順番

| 目的 | 見るファイル |
|---|---|
| **毎回最初に読む** | `project_handbook.md` |
| どこに何があるか | この README |
| 学習した方策を目で見たい | `docs/play_commands.md` |
| どの run が何だったか | `docs/runs.md` |
| 評価の条件と判定基準 | `docs/reference/eval_protocol.md` |
| 過去のチャットで何をしたか | `chats/` |

## 2. ディレクトリ構成

```
slope-climbing-robot/
├── README.md                 ← このファイル。索引
├── project_handbook.md       ← 現状と全体で必要な情報。毎回読む
├── my_robot_code/            ← 学習設定の実体（拡張側とハードリンク）
├── tools/                    ← スクリプト
├── docs/                     ← ドキュメント
├── chats/                    ← チャットごとの作業記録
├── onshape_export/           ← CAD からの書き出し・URDF・USD
└── references/               ← Skyentific 参考実装（外部 extension。git 管理外）
```

## 3. `my_robot_code/` — 学習設定

拡張側（`references/BipedalRobotSim/skyentific_poclegs/...`）と**ハードリンクで繋がっている 5 ファイル**。
片方を編集すればもう片方にも反映される。編集方法の注意は `project_handbook.md` の 2 章。

| ファイル | 中身 |
|---|---|
| `rough_env_cfg.py` | 地形・観測・報酬・イベント・カリキュラム・終了条件。**普段いじるのはここ** |
| `rewards.py` | 自作の報酬関数（`feet_air_time`、`feet_air_time_positive_biped`、`feet_slide`） |
| `curriculums.py` | 地形レベル・押し力・指令速度のカリキュラム |
| `rsl_rl_cfg.py` | PPO のハイパーパラメータ、`save_interval`、`experiment_name` |
| `skyentific_poclegs.py` | ロボットの ArticulationCfg（USD パス、初期姿勢、アクチュエータ） |
| `*.bak_*` | 各種バックアップ（git 管理外） |

## 4. `tools/` — スクリプト

| ファイル | 用途 |
|---|---|
| `measure_crab.py` | **固定の評価プロトコル。** 6 シナリオで速度追従・静止率・転倒率などを測る |
| `stance_check.py` | 初期姿勢の COM と足裏の支持多角形、action=0 で放置したときの転倒方向。`--stiffness_scale` で剛性診断 |
| `tb_extract.py` | TensorBoard のスカラーを指定 iter で抜き出す |
| `tb_norm_error.py` | `error_vel_xy` / `error_vel_yaw` をエピソード長で正規化して比較する |
| `runs/_launch.ps1` | 学習をバックグラウンド起動する |
| `runs/_eval.ps1` | `measure_crab.py` を起動する |
| `runs/_play.ps1` | 学習した方策を GUI で再生する |
| `runs/TEST_*.ps1` | 最初に書いた失敗版（EULA 変数なし）。`_launch.ps1` に置き換わった。git 管理外 |
| `logs/` | **生出力の置き場。`.gitignore` で除外されている。** 評価結果 `eval_*.md` / `.csv`、学習ログ `run_*.txt` など |
| その他（`diag_*.py`、`verify_*.py`、`view_*.png` など） | URDF/USD 化フェーズの診断ツールと確認画像 |

`tools/logs/` は git に入らないので、**残したい内容は `docs/` に書くこと。**

## 5. `docs/` — ドキュメント

| ファイル | 中身 |
|---|---|
| `play_commands.md` | **再生コマンド集。** どの run をどの地形で見ればよいかの一覧つき |
| `runs.md` | run フォルダの対応表と、各ランの起動行 |
| `setup_log.md` | 環境構築の履歴（Ubuntu 時代からの引き継ぎ含む）。トラブルと対処 |
| `remote_access.md` | リモート接続まわり |
| `reference/eval_protocol.md` | 評価環境・シナリオ・指標の定義・判定基準 |
| `reference/isaaclab_internals.md` | Isaac Lab 2.3.2 の内部仕様を grep で確かめた結果（metrics の式、`rel_heading_envs`、yaw フレーム版の報酬関数など） |
| `reference/terrain_level0.md` | 自作 `ROUGH_TERRAINS_CFG` の全パラメータと、レベル 0 で実際に何 cm の凹凸になるか |
| `reference/stance_and_stiffness.md` | 初期姿勢の COM・支持多角形と、stiffness 3 条件の転倒診断 |
| `reference/gpu_throughput.md` | 4096 env の秒/iter・VRAM・温度。何本まで並走できるか |
| `experiments/exp01_stop1_iter1600.md` | 実験01 の iter 1600 時点の報告 |
| `experiments/exp01_final.md` | 実験01 の最終報告（A と B、3000 iter） |
| `experiments/exp01_ablation_iter1000.md` | 実験01 の追加切り分け（iter 1000 時点）。**結論は後に撤回された** |
| `experiments/exp02_stop1.md` | 実験02 停止点1。C_flatonly の 2400 で結論が変わった回 |
| `experiments/exp02_stop2.md` | 実験02 停止点2。E_yawcmd と F_BtoRough |
| `experiments/exp06_turn_in_place.md` | 実験06。その場旋回(S6/S9)修正の全経緯と**失敗判定**。D1〜D3(実験04/05)もここに格納 |

## 6. `chats/` — チャットごとの作業記録

1 チャット 1 ファイル。そのチャットで何を指示され、何をやり、何が分かったかを書く。
チャットを切り替えるタイミングで必ず書く。

| ファイル | 内容 |
|---|---|
| `2026-09-16_exp01_exp02.md` | 実験01（立ち往生・カニ歩きの切り分け）と実験02（切り分けの仕上げ・seed 再現・旋回） |
| `2026-09-17_exp05_exp06.md` | 実験05（デプロイ準備・その場旋回の原因診断）と実験06（対策と評価。**失敗判定**） |

## 7. `onshape_export/` — CAD から機体まで

`myrobot_dummy/` に URDF・質量入れ・リンク改名のスクリプトとバックアップ。
USD（`*.usd`）と STL は `.gitignore` で除外。経緯は `docs/setup_log.md` の 2026-08-18 以降。

## 8. 更新のルール

- **何かあったとき、チャットを切り替えるときに `README.md` と `project_handbook.md` を更新する。**
- 細かい情報はその都度 `docs/` に md を作り、README の表に 1 行足す。
- チャットが終わるときに `chats/` に 1 ファイル書く。
- `tools/logs/` は生出力の置き場であって、記録の置き場ではない（git に入らないため）。
