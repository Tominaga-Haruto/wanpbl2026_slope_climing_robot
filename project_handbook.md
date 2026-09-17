# project_handbook

**このファイルは毎回最初に読む。** 他のドキュメントはここから必要なときだけ見に行く。
何かあったとき、チャットを切り替えるときに更新する。

最終更新: 2026-09-17（実験06 その場旋回修正の失敗判定の直後）

---

## 1. このプロジェクトは何か

二足歩行ロボット（Skyentific PocLegs をベースに自作した 10 関節・約 10 kg の機体）を
Isaac Lab ＋ RSL-RL で歩かせる。**最終目的は坂を登らせること。**
いまは「平地で真っ直ぐ歩く」と「凹凸地形を登る」の段階。

## 2. 環境（ここを間違えると何も動かない）

| 項目 | 値 |
|---|---|
| GPU | RTX 3090 Ti 24 GB（研究室の共用機。**起動前に `nvidia-smi` で他人のプロセスを確認する**） |
| OS | Windows 11、PowerShell |
| Python | `D:\Tominaga\envs\isaac_env\python.exe`（conda, 3.11.16） |
| **Isaac Lab の実体** | **`D:\Tominaga\IsaacLab`**（editable install の参照先、`train.py` に skyentific import パッチ入り） |
| 紛らわしいもの | `D:\IsaacLab` も存在するが**別物**。読んでも実際に動いているコードではない |
| 自作拡張 | `D:\Tominaga\slope-climbing-robot\references\BipedalRobotSim\skyentific_poclegs\` |
| 学習ログ | `D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\` |
| 登録タスク | `Velocity-Rough-Skyentific-Poclegs-v0` と `-Play-v0` の 2 つだけ（Flat タスクは無い） |

### 必ず守ること

1. **headless 起動には `$env:OMNI_KIT_ACCEPT_EULA="YES"` が要る。**
   無いと EULA プロンプトの入力待ちで `Unable to bootstrap inner kit kernel: EOF when reading a line` で死ぬ。
2. **学習・評価・再生はすべて `D:\Tominaga\IsaacLab` を作業ディレクトリにする。** ログのルートが CWD 相対。
3. **`my_robot_code\*.py` は拡張側の実体とハードリンクで繋がっている（5 組）。**
   編集は `open(r+)` 方式（読んで seek(0) して write して truncate）で行い、
   編集後に `Get-FileHash` の一致と `fsutil hardlink list` のリンク数 2 を必ず確認する。
   ファイルを作り直す書き方をするとリンクが切れて拡張側に反映されなくなる。
4. **`terrain_type="plane"` は使えない。** 全面 flat の generator で代用する（詳細は
   `docs/reference/eval_protocol.md`）。
5. **`--max_iterations` は「追加 iter 数」**。resume では通算ではない。
6. 学習は 4096 env で **2 本並走が上限**。3 本目は合計スループットが +5% しか増えず、
   既存の 2 本が 50% 遅くなるので割に合わない（`docs/reference/gpu_throughput.md`）。

## 3. いま分かっていること（結論）

### 立ち往生（指令を出しても一歩も動かない）

- **原因は地形。平地にするだけで解消する。** 報酬や std の変更は不要だった。
- rough 地形では 3000 iter 回しても前進を獲得しない（A も C_noflat も）。後退だけは 2999 で出る。
- レベル 0 でも env の 20 % は **6 cm のランダム凹凸**の上にいる。`random_uniform_terrain` は
  difficulty を無視するので、カリキュラムを下げてもこのタイルだけは常に最大荒さ
  （`docs/reference/terrain_level0.md`）。歩行時の遊脚高さ 9〜13 cm と同オーダー。
- **`max_init_terrain_level` を上げるのは逆効果**（レベル 0 が最易、`None` は全レベル一様抽選）。
- 報酬・std の変更は「歩き出す時期」を早めるだけ（B は iter 1000、C_flatonly は 2400）。

### 平地 → rough への移行

- **平地で歩けるようにしてから rough に移すと、地形カリキュラムが上がる。**
  F_BtoRough で terrain_levels 0.98 → 4.69（全 10 レベル中）、まだ上昇中。
- 平地の歩行能力は失わない（破滅的忘却なし）。

### 旋回・その場旋回（実験06 まで — 未解決、対策も失敗）

- **並進しながらの旋回（歩きながら曲がる）**: `rel_heading_envs=0.5` にしても S6 応答は +0.063 止まり。
- **その場旋回（S6/S9、並進ゼロで wz だけ）— 実験05/06 で本格着手、実験06 で対策も失敗と判定。**
  原因は特定できた: `feet_air_time`/`feet_air_time_biped` の足上げ報酬が
  `torch.norm(command[:,:2])>0.1`（並進のみ）でゲートされ wz を見ていない上、
  `rel_heading_envs=1.0`（親クラス既定）のせいで学習中にその場旋回コマンドが 0.38% しか
  出現していなかった。`yaw_gate` オプション（両ゲートの OR 化）と `TurnAwareVelocityCommand`
  （その場旋回/並進のみのコマンド carve-out、既定 20%/15%）で対策し、コマンド出現率は
  19.95% まで上がったが、**S6/S9 の実測 yaw rate は resume・scratch 系 6 本＋比較用
  H_eff13p5@2999 の計 7 本すべてで判定基準（`|yaw rate|≥0.25`）に届かなかった**
  （観測された最大値は 0.12。しかも学習が進むほど値は縮む方向 — 詳細
  `docs/experiments/exp06_turn_in_place.md`）。
  **`track_ang_vel_z_exp` の重み/std・アクチュエータ・地形は変えない制約下では未解決。**
- 逆に F_BtoRough は**指令と無関係に勝手に回る**（前進指令で yaw rate +0.324 rad/s＝10 s で約 186°）。
- 未検証の有力候補（実験01/02 から積み残し、実験06 の仮説とも合流）:
  1. その場旋回専用の追従報酬を新設し、大きい wz 指令だけに重みを乗せる
     （`track_ang_vel_z_exp` 自体は変えない）。
  2. `rel_turn_in_place_envs` を上げる／`turn_in_place_wz_range` を S6/S9 相当（0.5 付近）に寄せる。
  3.（制約を外す前提）いまの `track_ang_vel_z_exp` は base フレームの `root_ang_vel_b[:,2]` を、
     `track_lin_vel_xy_exp` は roll/pitch 込みの base フレームを使っている。
     Isaac Lab 同梱の G1/H1 は `track_ang_vel_z_world_exp` と `track_lin_vel_xy_yaw_frame_exp`
     （yaw のみ）を使う。**引数の並びが同じなので `func` の差し替えだけで試せる。**
     もしくは std を縮めて大きい wz への感度を上げる。

### 初期姿勢

- **公称姿勢は静的に安定ではない。** action=0 で放置すると 64/64 が +x（前）へ 29 cm 動きながら
  pitch +73° で倒れる。
- **PD 剛性不足ではない。** stiffness を 4 倍にしても転倒率は 64/64 のままで、変位はむしろ増える。
  膝の沈みは元々 2.7° しかない（`docs/reference/stance_and_stiffness.md`）。
- COM は支持多角形の中（前余裕 6.6 cm / 後余裕 11.5 cm）にあるのに倒れる。
  足裏が全面接地していないか、接地時の沈み込み（base 高さ 0.3758 → 0.3613 m）で姿勢が変わるあたりが次の疑い先。**未調査。**
- 前進と後退の獲得順序が非対称（後退が先）。前倒れを押し返す動作の副産物として後退がただで手に入る、
  という仮説はあるが未検証。

### 実機アクチュエータ・デプロイ候補（実験03〜05）

- **実機準拠アクチュエータに移行済み。** hr/haa/kfe は AK80-9 相当（effort_limit=53.0）、
  hfe/ffe は AK10-9 相当（effort_limit=13.5、`H_eff13p5` 系列の由来）。5グループ化
  （commit `664105a`）。実機変換係数（stiffness/damping/friction/velocity_limit/delay）込みの
  全表は `tools/logs/obs_contract.md`。
- **h5py と `isaacsim.sensors.rtx` の同梱DLLが衝突してクラッシュする問題を特定・回避済み**
  （commit `0a434a7`）。評価・学習スクリプトは `_preload_h5py_and_run.py` 経由で起動する
  （先に import することでDLL初期化の勝ち負けを固定する）。
- **デプロイ候補は `G_real_peak`（トルク寄り）と `H_eff13p5`（ゲイン寄り）の2本。**
  実験04の頑健性スイープ（P1〜P6、アクチュエータgain/damping/delay誤差・base_lin_vel途絶・
  吊り下ろし試験など）で両方とも条件4本中3本が共通で不合格だったが、原因の質が違う
  （G はトルク飽和系、H はゲイン系）。ゲイン誤差は実機で変換係数を測れば補正できるが、
  トルク誤差はできないため、**両方を実機で試す方針**（H_eff13p5を先に）。
  `H_gainDR`（アクチュエータgain domain randomization版）は候補から除外
  （noise_std_type設定漏れで学習中一貫して歩いていなかったことが判明。詳細下記D1）。
- **その場旋回ができないことがデプロイのブロッカーと判定 → 実験05/06 で対応 → 失敗。**
  上の「旋回・その場旋回」節と `docs/experiments/exp06_turn_in_place.md` を参照。
  **現時点でその場旋回ができるチェックポイントは存在しない。** G_real_peak/H_eff13p5 は
  「並進はできるがその場旋回はできない」状態のまま。
- `docs/reference/eval_protocol.md` は S1-S6 時点の記述のまま。S7-S11 とその場旋回の判定基準
  （下の5章）は未反映。**次のチャットで更新推奨。**
  `tools/logs/obs_contract.md`（観測契約・実機actuatorテーブル・golden dataset比較）と
  `docs/experiments/exp06_turn_in_place.md`（D1/D2/D3も格納）が現状の一次情報。
  前者はgit管理外（`tools/logs/`）なので、**消えると困る数値は`docs/`側へ転記が望ましい**
  （未実施）。

## 4. 数値を読むときの注意

**`error_vel_xy` / `error_vel_yaw` は生値のまま比べてはいけない。**
毎ステップ「誤差 ÷ (resampling_time_range[1] / step_dt)」＝「誤差 ÷ 500」を積算した値なので、
エピソード長に比例して大きくなる（`velocity_command.py:114-124`）。

```
正規化値（1 ステップあたりの平均誤差） = 生値 × 500 / Train/mean_episode_length
```

`tools/tb_norm_error.py` がこれを計算する。20 s 完走（1000 ステップ）なら生値は平均誤差の 2 倍。

**立ち往生している方策の「進行方向角」は無意味。** 10 s の正味変位がほぼ 0 なので。
静止率が 100 % ならカニ歩き判定が「有」でも実態は立ち往生のほう。

## 5. 判定基準（事前に決めた暫定値。勝手に変えない）

- **カニ歩き無し**: S1・S2 の両方で `|v_y| ≤ 0.05`、`|v_y − cmd_y| ≤ 0.10`、`|yaw rate| ≤ 0.10`、
  進行方向角 ±10° 以内。かつ S5 で `v_y ≥ +0.15`
- **立ち往生無し**: S1 で静止率 ≤ 5% かつ `v_x ≥ 0.35`、S2 で静止率 ≤ 5%
- **転倒合格**: S1 の転倒率 ≤ 5%
- 参考: 正規化 error_vel_xy ≤ 0.3
- **その場旋回合格（実験06、Cowork固定・変更禁止）**: S6・S9 両方で yaw 符号が指令と一致、
  両方 `|yaw rate| ≥ 0.25`、比率 `|S6|/|S9|` が [0.5, 2]、`|(vx,vy)|` 平均 ≤ 0.10、転倒率 ≤ 5%、
  両足とも実際に着地(landings>0)。**実験06 時点でこれに達したチェックポイントは無い**
  （最大観測値 0.12、詳細 `docs/experiments/exp06_turn_in_place.md`）。

評価プロトコルの全体は `docs/reference/eval_protocol.md`（S1-S6 まで。S7-S11 は未反映、上記参照）。

## 6. 現状のベスト

| 用途 | run / checkpoint |
|---|---|
| 平地で真っ直ぐ歩く | `2026-09-16_05-15-41_B_combined` / `model_2999.pt` |
| 凹凸地形を登る | `2026-09-16_13-40-37_F_BtoRough` / `model_4498.pt`（ただし円を描く） |
| 実機デプロイ候補（並進のみ、旋回不可） | `G_real_peak` と `H_eff13p5` の `model_2999.pt`（両方試す。H_eff13p5を先に） |

見る方法は `docs/play_commands.md`。**実機用の各種テーブルは `tools/logs/obs_contract.md`。**

## 7. 次にやる候補

実験06 で「その場旋回はデプロイのブロッカー」「yaw_gate＋コマンド分布変更だけでは不十分」と
分かった。次の一手（優先度未定、次のチャットでユーザーと相談）:

1. **その場旋回専用の追従報酬を新設する。** 大きい `wz` 指令だけに重みを乗せる項を追加し、
   既存の `track_ang_vel_z_exp` 自体（重み・std）は変えない制約を保ったまま試す。
2. **`rel_turn_in_place_envs` を上げる／`turn_in_place_wz_range` を S6/S9 相当（0.5 付近）に寄せる。**
   いまは 0.2 / (0.3, 1.0) で出現率 19.95%。単純に頻度・強度を上げて再挑戦する案。
3.（制約を外す前提）**yaw の報酬関数を G1/H1 と同じものに差し替える。**
   `track_ang_vel_z_exp` → `track_ang_vel_z_world_exp`、
   `track_lin_vel_xy_exp` → `track_lin_vel_xy_yaw_frame_exp`。引数の並びが同じなので `func` だけ
   替えればよい。または std を縮めて大きい wz への感度を上げる。
4. **ハングの原因切り分けを再開する。** `t0_3_s6_diag.py`/`p6_1_footpitch.py` が毎回ハングする件
   （`p6_2_basevel_dropout.py` は毎回成功）。コード差分では説明がつかなかった
   （`docs/experiments/exp06_turn_in_place.md` 5章）。学習が全部終わって GPU が空いている今が
   再現・切り分けの適期。
5. **F_BtoRough をそのまま延長する。** terrain_levels はまだ 4.69 で上昇中、time_out も 0.50 まで
   来ている。あと 1500〜3000 iter で頭打ちになるかを見れば「rough を最後まで登れるか」が分かる。

## 8. やらないと決めていること

- アクチュエータ（effort・friction・グループ分け・ゲイン）は変えない
  （実験03で実機準拠に変えたのは承認済みの変更。**その後は**変えない、の意味）
- 指令レンジ（`lin_vel_x` / `lin_vel_y` / `ang_vel_z`）は変えない
- `track_ang_vel_z_exp` の重み・std は変えない（実験06、旋回の原因切り分けのため。
  7章の候補3はこの制約を外す前提の案なので、着手前にユーザーに確認する）
- 地形（terrain）は変えない（実験06時点）
- 走っているランの cfg は途中で変えない
- 判定基準は変えない（5章、Cowork固定）
- 何も削除しない
- pip / conda のインストール・削除・更新はしない
- push はユーザーが行う（AI 側は commit まで）
- 「推測で直さない。想定外は止まって報告。」— 実験05以降、毎回の指示に明記される原則

## 9. git

- リポジトリ: `D:\Tominaga\slope-climbing-robot`、ブランチ `main`
- remote: `https://github.com/Tominaga-Haruto/wanpbl2026_slope_climing_robot.git`
- 最新 commit: `8ea9b54`（`dump_baseline_env_yaml.py` 追加。実験06 J0/評価基盤拡張の一連）
- **未 push。** push は下の 1 行:

```powershell
cd D:\Tominaga\slope-climbing-robot; git push origin main
```

- `.gitignore` で `logs/` と `**/logs/` が除外されているので、**`tools/logs/` の生出力は git に入らない**。
  残したい内容は `docs/` 以下に置くこと。
