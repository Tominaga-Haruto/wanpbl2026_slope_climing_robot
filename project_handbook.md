# project_handbook

**このファイルは毎回最初に読む。** 他のドキュメントはここから必要なときだけ見に行く。
何かあったとき、チャットを切り替えるときに更新する。

最終更新: 2026-09-16（実験02 停止点2 の直後）

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

### 旋回（未解決）

- **学習中、旋回速度指令が一度も出ていなかった。** `rel_heading_envs=1.0`（親クラスの既定）なので
  全 env が heading 追従になり、サンプルした `ang_vel_z` は `_update_command` で毎ステップ上書きされて捨てられる。
- `rel_heading_envs=0.5` にしても S6（指令 0.5 rad/s）への応答は +0.063 止まり。**解決しなかった。**
- 逆に F_BtoRough は**指令と無関係に勝手に回る**（前進指令で yaw rate +0.324 rad/s＝10 s で約 186°）。
- 未検証の有力候補: いまの `track_ang_vel_z_exp` は base フレームの `root_ang_vel_b[:,2]` を、
  `track_lin_vel_xy_exp` は roll/pitch 込みの base フレームを使っている。
  Isaac Lab 同梱の G1/H1 は `track_ang_vel_z_world_exp` と `track_lin_vel_xy_yaw_frame_exp`（yaw のみ）を使う。
  **引数の並びが同じなので `func` の差し替えだけで試せる。**

### 初期姿勢

- **公称姿勢は静的に安定ではない。** action=0 で放置すると 64/64 が +x（前）へ 29 cm 動きながら
  pitch +73° で倒れる。
- **PD 剛性不足ではない。** stiffness を 4 倍にしても転倒率は 64/64 のままで、変位はむしろ増える。
  膝の沈みは元々 2.7° しかない（`docs/reference/stance_and_stiffness.md`）。
- COM は支持多角形の中（前余裕 6.6 cm / 後余裕 11.5 cm）にあるのに倒れる。
  足裏が全面接地していないか、接地時の沈み込み（base 高さ 0.3758 → 0.3613 m）で姿勢が変わるあたりが次の疑い先。**未調査。**
- 前進と後退の獲得順序が非対称（後退が先）。前倒れを押し返す動作の副産物として後退がただで手に入る、
  という仮説はあるが未検証。

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

評価プロトコルの全体は `docs/reference/eval_protocol.md`。

## 6. 現状のベスト

| 用途 | run / checkpoint |
|---|---|
| 平地で真っ直ぐ歩く | `2026-09-16_05-15-41_B_combined` / `model_2999.pt` |
| 凹凸地形を登る | `2026-09-16_13-40-37_F_BtoRough` / `model_4498.pt`（ただし円を描く） |

見る方法は `docs/play_commands.md`。

## 7. 次にやる候補

1. **yaw の報酬関数を G1/H1 と同じものに差し替える。**
   `track_ang_vel_z_exp` → `track_ang_vel_z_world_exp`、
   `track_lin_vel_xy_exp` → `track_lin_vel_xy_yaw_frame_exp`。引数の並びが同じなので `func` だけ替えればよい。
   F の「勝手に回る」と E の「指令で回らない」が同じ原因なら、これ 1 本で両方説明がつく。
2. **F_BtoRough をそのまま延長する。** terrain_levels はまだ 4.69 で上昇中、time_out も 0.50 まで来ている。
   あと 1500〜3000 iter で頭打ちになるかを見れば「rough を最後まで登れるか」が分かる。候補 1 と直交する。

## 8. やらないと決めていること

- アクチュエータ（effort・friction・グループ分け・ゲイン）は変えない
- 指令レンジ（`lin_vel_x` / `lin_vel_y` / `ang_vel_z`）は変えない
- 走っているランの cfg は途中で変えない
- 判定基準は変えない
- 何も削除しない
- push はユーザーが行う（AI 側は commit まで）

## 9. git

- リポジトリ: `D:\Tominaga\slope-climbing-robot`、ブランチ `main`
- remote: `https://github.com/Tominaga-Haruto/wanpbl2026_slope_climing_robot.git`
- 最新 commit: `6c80638`（評価基盤と `feet_air_time_biped` の追加、8 ファイル）
- **未 push。** push は下の 1 行:

```powershell
cd D:\Tominaga\slope-climbing-robot; git push origin main
```

- `.gitignore` で `logs/` と `**/logs/` が除外されているので、**`tools/logs/` の生出力は git に入らない**。
  残したい内容は `docs/` 以下に置くこと。
