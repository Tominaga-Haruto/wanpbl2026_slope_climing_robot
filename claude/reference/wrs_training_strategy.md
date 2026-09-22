# WRS機での学習戦略（再エクスポート後）

> **これは何:** 再エクスポートで機体が正しくなった WRS機で、「次にどう学習を回すか」の方針。2026-09-15 作成、**2026-09-16 に棚卸し結果と機体の座標修正を反映して改訂。**
> **前提:** WRS機のコードは **08-21 版＋機体修正（`6ede75b`）**。9月に Alienware で入れた変更は入っていない。
> **★この文書は方針のたたき台。** 実際の実験計画は、学習戦略のチャット（`archive/next_chat_briefing.md`）でユーザーと決める。

---

## 0. 前提の整理

### 0-1. ★ 2026-09-16 に分かったこと: 過去の学習は機体が横を向いていた可能性が高い

- **base の +X（Isaac Lab の「前」）がロボットの横方向だった。** 08-21 版 URDF でも同じ（`reference/robot_model_conventions.md`、手順書 B2）。
- さらに**関節軸の符号が食い違い、初期姿勢が 22 cm 非対称**だった。
- **→ 9月の「カニ歩き」「前進限定化」「報酬の重み上げ」は、この機体に対する反応だった可能性がある。** 当時の因果分析（「非対称が原因・前進限定が引き金・重みが増幅」）は、**base の向きという交絡を含んでいた。**
- **したがって: 9月の変更をそのまま戻さない。** 機体と無関係に正しい構造的な対策（クラッシュ対策など）だけを入れ、**行動に効く調整（報酬・指令）は新しい機体で症状を見てから決める。**

### 0-2. Kp/Kd は「速さを決めるつまみ」ではない

- `stiffness`/`damping` は **PD ゲイン**（実機 MIT の Kp/Kd に対応）。
- ゲインが決めるのは「方策が出した目標角に**どう追従するか**」。**脚を速く振りたいのは方策**なので、ゲインだけで「速すぎる」は直らない。
- 9/08 の実測では要求トルクが `damping × 関節速度` に支配されていた（壊れた機体での値）。**damping を上げるほど要求トルクが増えて飽和が悪化する**うえ、実機の実効 Kd の天井は **2.4**（指令 Kd × 0.48）。
- **→ Kp/Kd は「実機で再現できる範囲の現実的な値に決めて、ほぼ固定＋ランダム化」する対象。速さは報酬・指令・アクチュエータの物理で抑える。**

---

## 1. 08-21 版コードの棚卸し（2026-09-16、WRS機の実物・行番号付きで確認）

### 1-1. `rsl_rl_cfg.py`

| 項目 | 08-21 版の値 | 9月版（Alienware、参考） |
|---|---|---|
| `noise_std_type` | **無し（＝scalar）** | \"log\" |
| `clip_actions` | **無し** | 6.0 |
| `init_noise_std` | 1.0 | 1.5 |
| `entropy_coef` | 0.005 | 0.002 |
| `learning_rate` | 1.0e-3 | 1.0e-3（adaptive） |
| `num_steps_per_env` | 24 | 24 |
| `max_iterations` | 30000（Rough）／15000（Flat） | — |

### 1-2. `rough_env_cfg.py`

- **terminations:** `base_contact`（body=`base`, threshold=1.0）／**`bad_orientation` あり、limit_angle=1.3**（9月版は 0.8）／`time_out`
- **commands:** **このファイルは指令に触れていない＝Isaac Lab 2.3.2 の親クラス既定**: `lin_vel_x=(-1,1)` / `lin_vel_y=(-1,1)` / `ang_vel_z=(-1,1)` / `heading=(-π,π)` / `heading_command=True` / `heading_control_stiffness=0.5` / `rel_standing_envs=0.02` / `rel_heading_envs=1.0` / `resampling_time_range=(10,10)`（ソースで確認）
- **rewards（実効値）:** track_lin_vel_xy_exp 1.0 / track_ang_vel_z_exp 0.5 / lin_vel_z_l2 −2.0 / ang_vel_xy_l2 −0.05 / joint_torques_l2 −1e-5 / action_rate_l2 −0.01 / feet_air_time 2.0（0.2〜0.5 s、`.*ffe`）/ feet_slide −0.25 / undesired_contacts −1.0 / joint_deviation_hip −0.1 / joint_deviation_knee −0.01 / flat_orientation_l2 **−0.5（`__post_init__`）** / dof_pos_limits **−1.0（`__post_init__`）**
- **curriculum:** terrain_levels（params 無し）／push_force_levels（max_velocity [3,3]、interval 200 iter、starting 1500 iter、昇降格あり）／command_vel（max_velocity [−1.5, 3.0]、interval 200 iter、starting 5000 iter、**昇格のみ**）
- **terrain:** 自作 ROUGH_TERRAINS_CFG（8×8 m、10 行×20 列）: flat 0.3 / hf_pyramid_slope 0.1 / _inv 0.1（slope_range 0〜0.4）/ stairs 0.05 / stairs_inv 0.05 / wave 0.2 / random_rough 0.2
- **events:** add_base_mass（`base`, −1〜+1 kg）／push_robot（±0.5 m/s、10〜15 s ごと）／armature と friction のランダム化あり／**アクチュエータゲインのランダム化は無し**
- **observations:** base_lin_vel → base_ang_vel → projected_gravity → velocity_commands → hip_pos → kfe_pos → ffe_pos → joint_vel → actions（height_scan は `__post_init__` で None）。noise: lin ±0.1 / ang ±0.2 / gravity ±0.05 / hip ±0.03 / kfe ±0.05 / ffe ±0.08 / joint_vel ±1.5
- **名前の一致:** `.*ffe` / `.*hfe` / `.*haa` / `base`（リンク）、`.*HR` / `.*HAA` / `.*KFE`（関節）は新しい URDF と一致。
- **未確認（新チャットで grep）:** `sim.dt` / `decimation`（→ 制御周期と dt）、`episode_length_s`、action の `scale` と `use_default_offset`、`feet_slide` / `undesired_contacts` の body 名の詳細

### 1-3. `curriculums.py`
- `modify_command_velocity`: **降格ロジック無し**（報酬が閾値を超えたときだけ範囲を ±0.5 広げる）。
- `modify_push_force`: 昇格・降格の両方あり。

### 1-4. `skyentific_poclegs.py`（2026-09-16 の機体修正を含む）

- `init_state.pos` z = **0.375776**、joint_pos: HR 0 / **HAA 0** / HFE −0.1745 / KFE 0.3491 / FFE −0.1745
- actuators（全部 `DelayedPDActuatorCfg`、delay 0〜4 step）:

| グループ | 関節 | effort | velocity | stiffness | damping | armature | friction |
|---|---|---|---|---|---|---|---|
| hr | `.*HR` | 24 | 23 | 10 | 1.5 | 6.9e-5×81 | 0.02 |
| haa | `.*HAA` | 30 | 15 | 15 | 1.5 | 9.4e-5×81 | 0.02 |
| kfe | **`.*HFE`, `.*KFE`** | 30 | 20 | 15 | 1.5 | 1.5e-4×81 | 0.02 |
| ffe | `.*FFE` | 20 | 23 | 10 | 1.5 | 6.9e-5×81 | 0.02 |

### 1-5. Isaac Lab 側
- `mdp.randomize_actuator_gains` あり（`envs/mdp/events.py:541`）、`DCMotorCfg` あり（`actuators/actuator_pd_cfg.py:42`）。どちらも未使用。

### 1-6. URDF の limit（学習に効くもの）
- velocity 15〜23 rad/s（USD に入り物理側で効く。**過去の学習は 10 rad/s 上限だった**）／lower・upper ±π（`dof_pos_limits` は実質無効）／effort は効かない。

---

## 2. 9月の変更の仕分け（2026-09-16 改訂）

| 9月の変更 | 扱い | 理由 |
|---|---|---|
| `noise_std_type=\"log\"` | **入れる** | 機体と無関係なクラッシュの根本対策。挙動への影響は小さい |
| `clip_actions` | 入れる候補 | 物理破綻の予防。値は Isaac Lab の既定例を確認して決める |
| `command_vel` の降格ロジック | 入れる候補 | 一方通行だと立ち往生の一因。ただし starting が 5000 iter なので初期の実験には効かない |
| アクチュエータのグループ分け（HFE を AK80-9 側へ） | **入れる** | 実機と対応させる前提。挙動は変わるので実験の段取りで扱う |
| effort / armature / friction の実機値 | 段階的に | 「軽やかすぎる」の一因の可能性。ただし一度に変えると切り分けできない |
| `stance_timeout` | 保留 | 足上げの問題が新しい機体でも出るか見てから |
| 前進限定（heading 固定・lin_vel_y=0） | **入れない** | 横向きの機体への対症療法だった可能性。副作用も大きかった |
| 報酬 weight の引き上げ（track_lin 2.5 / track_ang 2.0 等） | **入れない** | 立ち止まりの給料を 12 倍にした。因果実験でも劣化を確認 |
| `bad_orientation` 0.8 rad | 保留 | 08-21 版の 1.3 rad で様子を見る。坂で見直す |
| `joint_vel_out_of_manual_limit` 60 rad/s | 保留 | URDF の velocity limit が効くようになったので必要性を再評価 |

---

## 3. 実験の段取り（たたき台）

### 段階0: 「横向きの機体」仮説の確認（最小変更）

**問い: base の前後を直した機体で、08-21 版に近い設定でもカニ歩きは出るか。**

- 変更: `noise_std_type=\"log\"` **だけ**（クラッシュで実験が壊れないように）
- 地形・報酬・指令・アクチュエータは 08-21 版のまま
- 4096 env、1500〜3000 iter。**同時に 4096 env の基準値（秒/iter・VRAM・温度）を取る**
- 見る指標: `error_vel_xy`、`error_vel_yaw`、`terrain_levels`、**胴体座標の残差 `v_y − cmd_y`**（診断スクリプトで play から計測）、終了理由の内訳、録画
- **比較対象:** 過去の 08-21 版での学習結果（`fix/falling-down-end-condition` 当時の記録、`chats/` と handover の数値）。**機体以外の差（velocity limit 10 → 15〜23、初期姿勢、スポーン高さ）もあるので、完全な同一条件ではない**ことを明記して解釈する

### 段階1: ベースライン（平地オンリー・1500 iter）

変数を減らして「正しい機体が普通に歩くか」を詰める。

- 地形: `flat` のみ（一時構成）
- アクチュエータ: HFE を AK80-9 グループへ分離、effort=定格（AK10 18 / AK80 9）、armature=実測/計算値、friction=AK80 0.22・AK10 暫定 0.37
- 指令: Isaac Lab 既定寄り（§4）
- ゲイン: 下の2〜3条件だけ比較

| 条件 | stiffness | damping | 狙い |
|---|---|---|---|
| A | 見本値（10〜15） | 1.0〜1.5 | 基準 |
| B | 25 前後 | 1.0 | 摩擦の不感帯を減らす（実機 MIT も Kp 20〜60 が普通） |
| C | 25 前後 | 0.5 | damping 項の飽和を減らす |

**見る指標:** `error_vel_xy`、Episode 長・`time_out` 比率、**関節速度の分布**、**トルクの内訳（`stiffness×誤差` と `damping×速度`）**、**effort 上限への張り付き率（p95）**、横流れの残差。

### 段階2: 「速すぎる」を抑える（効きそうな順・1つずつ）

1. **アクチュエータの物理を現実に寄せる** ── effort 定格化。`DCMotorCfg` で `velocity_limit`＋`saturation_effort`（AK10 33.5 / AK80 59.7 rad/s）
2. **指令速度の上限を下げる** ── `lin_vel_x` 上限 0.5 程度から。`command_vel` カリキュラムで伸ばす
3. **動きの罰を足す** ── `joint_vel_l2` / `joint_acc_l2` を小さく。`action_rate_l2` を −0.01 → −0.02〜−0.05
4. **歩容の周期を長くする** ── `feet_air_time` の窓を 0.3〜0.6 s 側へ、dense 版の検討
5. **（必要なら）action scale を下げる**

**ロバスト化:** `randomize_actuator_gains` で stiffness/damping を ±20〜30%。

---

## 4. 指令（heading）の方針

**結論: heading 固定（前進限定）はやめ、`heading_command=True` のまま heading は全周ランダム（08-21 版＝Isaac Lab 既定がすでにそう）。**

- 固定した理由は「機体の左右非対称を表に出さないため」だった。**非対称も base の向きも解決済み。**
- 固定の副作用が大きかった: 立ち止まりの給料が激増、`lin_vel_x` 下限 0 で「静止」指令が混ぎました。
- **坂は向きを選ばない:** `pyramid_slope` は四方に坂がある。
- **実機で必要:** オペレーターが旋回指令で向きを直せないと困る。

案（崩れたら狭める）:
```
lin_vel_x = (-0.3, 0.6)   上限はカリキュラムで伸ばす（08-21 既定は (-1, 1)）
lin_vel_y = (-0.3, 0.3)   横は控えめ（既定は (-1, 1)）
heading   = (-3.14, 3.14)
rel_standing_envs は小さく（既定 0.02）
```

---

## 5. 段階3: 坂へ

1. 地形を `flat` ＋ `pyramid_slope`/`_inv` の2本立てに（階段・波・random_rough は外す）。`terrain_levels` に任せて slope_range を伸ばす
2. `flat_orientation_l2`（−0.5）を緩めて前傾を許す
3. `bad_orientation` の limit_angle を坂に合わせる（08-21 版は 1.3 rad）

---

## 6. 並行: デプロイ準備（学習の待ち時間にやる）

- `play.py` で `exported/policy.onnx` が出るか（WRS機での録画・play は未検証）
- 観測ベクトルの契約（順序・単位・`joint_pos_rel` の基準）を新しい joint 順で書き出す
- 制御周期と実機 50 Hz の整合
- 関節名 ↔ モーターID ↔ 符号の対応表（`reference/robot_model_conventions.md` を基準に）
