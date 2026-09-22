# 学習ランの記録（WRS機・2026-09-16 の機体以降）

> run ごとに1行。**2026-09-16 より前の run（旧機体）は無効なので載せない。** 設計の根拠と結果の解釈は `reference/crab_standstill_countermeasures.md`（§3 設計、§4 結果）。**用語（S1〜S9 など）の説明と経緯の読み物は `reference/wrs_training_history.md`。**
> 判定は `tools\\measure_crab.py`（平地・固定指令・64 env・2 s 捨てて 10 s）と、事前に決めた基準（同文書 §3）。**実験03 から小旋回（S7/S8）とトルク（S1 で RMS ≤ 定格、最大 ≤ ピーク、飽和率と computed torque 併記）を追加**（`archive/next_chat_briefing.md` §1a の決定）。
> **★学習ログの error_vel_xy / error_vel_yaw はエピソード長に比例する。正規化値 = 生値 × 500 / mean_episode_length で読む**（同 §4-2）。
> run フォルダの親: `D:\\Tominaga\\IsaacLab\\logs\\rsl_rl\\skyentific_poclegs_rough\\`
> **平地は `terrain_type=plane` が使えない（S3 の既定 USD を取りに行って落ちる）ので、sub_terrains の proportion を flat=1.0・他 0 に上書きして作る。**
> **起動は conda activate 込みの `tools\\runs\\_launch.ps1` / `_eval.ps1` / `_play.ps1`（python.exe 直叩きは h5py の DLL 競合で落ちる）。**
> **★起動行に `agent.policy.noise_std_type=log` を必ず入れる（H_gainDR で漏れた。再生・評価も同じ値でないと読み込めない）。**

## 実験01（2026-09-16 05:15〜、`instructions/wrs_experiment01_instruction.md`）

| ラン | run フォルダ | 変更（08-21 版からの差） | seed | iter | 判定（最終） | S1 v_x / S2 v_x / S4 v_x | S6 yaw rate | 正規化 err_xy | 所見 |
|---|---|---|---|---|---|---|---|---|---|
| A_base0821 | `2026-09-16_05-14-59_A_base0821` | log std | 1 | 3000 | **立ち往生**（全シナリオ静止 100%） | 0.00 / 0.00 / 0.00 | 0.00 | 0.77 | 足が一度も離れない。terrain_levels 0 のまま |
| B_combined | `2026-09-16_05-15-41_B_combined` | log std ＋ 平地 ＋ biped 足上げ w0.25 ＋ std 0.35 | 1 | 3000 | **全基準合格**（1600・2999。2400 は yaw rate 0.105 で外れる）。実験03 で S7/S8 小旋回も合格と判明 | 0.434 / 0.903 / −0.259 | 0.028 | 0.17 | その場旋回しない、滞空 0.07〜0.11 s（すり足?） |
| B_combined_s2 | `2026-09-16_05-32-13_B_combined_s2` | B と同じ | 2 | 30 | 評価対象外 | — | — | — | スループット +5.2% で規定どおり停止 |
| C_noflat | `2026-09-16_08-49-55_C_noflat` | B − 平地（rough） | 1 | 3000 | **立ち往生**（2999、後退のみ可） | — | 1000 時点 0.175 | 1000 時点 0.74 | rough は報酬/std を変えても歩かない |
| C_flatonly | `2026-09-16_08-50-17_C_flatonly` | A ＋ 平地 | 1 | 3000 | **立ち往生 無**（2400 で歩き出す）、カニ歩きは S1 進行方向角 −14.3° のみ外れ | 2400: 0.492 / 0.921 / −0.265 | — | 2999: 0.230 | 1600 までは後退のみ。平地だけで歩く |

## 実験02（2026-09-16 午後〜、`instructions/wrs_experiment02_instruction.md` の P3 を `instructions/wrs_experiment02_p3_instruction.md` で差し替え）

| ラン | run フォルダ | 変更 | seed | iter | 判定（最終） |
|---|---|---|---|---|---|
| E_yawcmd | `2026-09-16_13-40-10_E_yawcmd` | B ＋ rel_heading_envs 0.5 | 1 | 2000 | @1999: カニ歩き 有（S2 進行方向角 −18.3° のみ）／立ち往生 無／転倒 合格。S6 yaw rate +0.063（指令 0.5 の 1/8）。S1 0.461 / S2 0.962 / S5 v_y 0.310。正規化 err_xy は iter 1000 で 0.195（B 0.550） |
| F_BtoRough | `2026-09-16_13-40-37_F_BtoRough` | B@2999 から再開、地形だけ rough（08-21） | 1 | +1500 | @+1499: terrain_levels 0.98 → 4.69（上昇中）、平地歩行保持（S1 0.446 / S2 0.992、静止 0%）。**S1 yaw rate +0.103 → +0.162 → +0.324 で円を描く**。`--resume` の `--max_iterations` は追加 iter 数 |
| ~~D_noStd / D_noBiped / B_combined_s2~~ | | 中止（`reference/crab_standstill_countermeasures.md` §5-3） | | | |

- P3a（action 0、stiffness 1× / 2× / 4×）: **4倍でも 64/64 が前に転倒**、変位 0.289 → 0.337 m。膝の沈みは 2.7° で 2倍でほぼ 0。足首 9.2° は 4倍で 1.5 倍しか縮まない＝沈みではなく倒れ込み。**剛性不足の仮説は外れ。**

## 実験03（2026-09-16 17:28〜21:12、`instructions/wrs_experiment03_instruction.md`、報告 `tools\\logs\\REPORT_exp03_final.md`）

**実機準拠アクチュエータ（関節ごと5グループ、commit `664105a`）で一から学習。B 以前の方策（effort AK80 に 20〜30 N·m）はデプロイに使わない。** 評価に S7 (0.5,0,+0.3) / S8 (0.5,0,−0.3) / S9 (0,0,−0.5) と関節ごとトルク（applied・computed・飽和率）を追加。

| ラン | run フォルダ | 変更（B からの差） | effort（AK10 / AK80） | seed | iter | 判定（@2999） | S1 v_x / \\|v_y\\| / wz | S7 / S8 wz | FFE（S1）RMS / computed 最大 / 飽和率 | 正規化 err_xy（1000 / 2999） |
|---|---|---|---|---|---|---|---|---|---|---|
| B_combined（参考） | `2026-09-16_05-15-41_B_combined` | — | 24〜30 / 20〜30（旧） | 1 | 3000 | 小旋回 合格 | 0.434 / 0.035 / +0.021 | +0.354 / −0.307 | 6.7 / 35.2 / 0.00 | 0.550 / 0.174 |
| **G_real_peak** | `2026-09-16_17-28-46_G_real_peak` | 5グループ、armature 8.116e-3 / 9.77e-3、friction 0.37（暫定）/ 0.22、rel_heading_envs 0.5 | 53 / 18 | 1 | 3000 | **カニ歩き 有（S1 \\|v_y\\| 0.058・進行方向角 −13.9° の境界。@2400 は 0.004）**／立ち往生 無／転倒 合格／トルク 合格／小旋回 合格 | 0.462 / 0.058 / −0.023 | +0.283 / −0.327 | 7.0 / 21.4 / 0.00（applied 最大 18.0） | 0.210 / 0.180 |
| G_real_rated | `2026-09-16_17-29-30_G_real_rated` | 同上 | 18 / 9（定格） | 1 | 3000 | カニ歩き 無／立ち往生 無／転倒 合格／トルク 数値上合格（**FFE 飽和 20〜29%、computed 最大が MIT 上限 18 超**）／小旋回 合格 | 0.470 / 0.012 / +0.009 | +0.287 / −0.267 | 5.9 / 26.8 / 0.29 | 0.182 / 0.202 |

- 全チェックポイント（1000 / 1600 / 2400 / 2999）で転倒 0%・立ち往生 0%、S7 / S8 合格。S6（その場旋回）はどちらも 0.03 以下。
- **Cowork の判断: デプロイ候補は G_real_peak（2400 / 2999）。**（上限 18 が実機 MIT 上限と一致。rated は実機が 18 まで出すのでずれる）
- 正規化 error_vel_yaw は B / G とも iter 1600 以降じわじわ悪化（G_rated 0.311 → 0.448）。S7/S8 は保たれている。
- 指令分布（action 0、200 step）: rel_heading_envs 1.0 で |wz 指令|>0.2 が 85.4%（平均 0.698）、0.5 で 77.3%（0.558）＝旋回指令は十分出ていた。
- P1-4: stiffness 1000 / damping 50 でも 32/32 前に転倒。t=0 の接地は片足 0 点・片足 6 点。左右リンク質量は一致、反転比較の y が全5ペア −0.038〜−0.040 m ずれる（→ 実験04 で base 原点の横ずれ 2 cm と判明）。
- h5py の DLL 競合（conda activate 無しの python.exe 直叩きで発生）→ 起動スクリプトに conda activate（`0a434a7`）。measure_crab.py が Hydra の effort 上書きを評価で反映していなかった → `params\\env.yaml` から読む修正（`5f3a487`）。

## 実験04（2026-09-16 22:09〜、`instructions/wrs_experiment04_instruction.md` ＋ `instructions/wrs_experiment04_followup_instruction.md`、報告 `tools\\logs\\REPORT_exp04_stop2.md` / `REPORT_exp04_stop3.md`）

**G_real_peak の頑健性を評価だけで確かめ（16 条件）、保険の学習を3本。**

### 保険の学習

| ラン | run フォルダ | 変更（G_real_peak からの差） | seed | iter | 判定（@2999） | S1 v_x / \\|v_y\\| / wz | S5 v_y / 静止率 | FFE（S1）RMS / computed 最大 | 正規化 err_xy（1000 / 2999） |
|---|---|---|---|---|---|---|---|---|---|
| H_nolinvel | （00:08:40 起動。フォルダ名は WRS 報告参照） | 観測から base_lin_vel を外す（39 次元） | 1 | 3000 | **不採用。** 立ち往生 有（S1 v_x 0.315 < 0.35）／カニ歩き 有（S2 横残差、S5 ほぼ静止）／転倒 合格／トルク 合格／小旋回 合格 | 0.315 / 0.020 / −0.061 | 0.074 / 0.778 | 6.71 / 18.42 | 0.730 / 0.236 |
| H_eff13p5 | （00:08:51 起動） | AK80-9（hfe・ffe）の effort_limit 13.5 | 1 | 3000 | G_real_peak とほぼ同じ合否（カニ歩きは S1 進行方向角 −13.6° の境界のみ）／立ち往生 無／転倒 合格／トルク 合格／小旋回 合格。**頑健性は停止点4** | 0.421 / 0.023 / −0.035 | 0.331 / 0.000 | 5.97 / 18.01 | 0.172 / 0.182 |
| H_gainDR | `2026-09-17_07-55-38_H_gainDR` | randomize_actuator_gains（reset、stiffness ×0.7〜1.3、damping ×0.5〜2.0）。**★noise_std_type=scalar（起動行の漏れ。他は log）** | 1 | 3000 | **停止点4 で判定**（評価は scalar で読み込む） | | | | |

- H_nolinvel の頑健性（@2999）: 条件1・3・15 で v_x < 0.35、**stiffness ×0.7 で S1 転倒 100%**、遅延 4 step で S1 yaw 0.103 → 小旋回不合格、damping ×0.5 と吊り下ろしは合格。
- H_eff13p5 は学習時から上限 13.5 なので computed torque 自体が低い（G_real_peak を評価時だけ 13.5 に制限した場合は FFE 飽和 0.07）。

### G_real_peak の頑健性（評価だけ、2400 / 2999）

| 条件 | 2400 | 2999 |
|---|---|---|
| 1 基準 | OK | OK |
| 2・3 AK80 effort 13.5 / 12 | OK | OK |
| 4 AK80 effort 9.0 | NG（S1 転倒 6.3%、FFE 飽和 43%） | 境界 OK（3.1%） |
| 5 AK10 effort 36 | OK | OK |
| 6 stiffness ×0.7 | NG（転倒 9.4%） | 境界 OK（3.1%） |
| 7 stiffness ×1.3 | OK | OK |
| 8 damping ×0.5 | NG（小旋回、S1 yaw −0.125） | NG（同 −0.129） |
| 9 damping ×2.0 | **NG（転倒 100%）** | **NG（転倒 100%）** |
| 10・11 遅延 20 / 40 ms | OK | OK |
| 12 friction ×2、13 質量 +1 kg、14 地面摩擦 0.5、15 観測ノイズ | OK | OK |
| 16 吊り下ろし +5 cm | OK（転倒 0%） | OK（転倒 0%） |

- **条件9 は数値不安定ではない:** sim.dt 0.0025・decimation 8・遅延 step 2倍でも転倒 98.4%。damping×dt/armature は基準 0.92（AK10）/ 0.77（AK80）、×2 で 1.85 / 1.54。関節速度の符号反転率は増えない。
- **base_lin_vel への依存（@2999）:** 0 固定で S1 / S7 / S8 転倒 100%・S3 57.8%。バイアス (+0.1,0,0) で S1 v_x 0.359・転倒 0%。雑音 σ0.1、5 step（100 ms）ホールドはほぼ無影響。
- ONNX（`exported_2400\\` / `exported_2999\\`）は torch と最大誤差 1.1e-5（ランダム）/ 9.5e-7（実観測）で一致。正規化は Identity。H_nolinvel・H_eff13p5 の ONNX も PASS。
- 形状: 足裏平面（world、既定姿勢）pitch −30.4° / −29.4°。COM は base 座標 x −0.089、支持範囲 x −0.178〜−0.162（前に 73 mm）。股中点 y −0.0206 で鏡映した左右残差は y 1〜3 mm、遠位リンクで x 最大 11 mm。
- golden npz（`tools\\logs\\golden_G_real_peak_2999.npz`、`golden_H_nolinvel_2999.npz`）、`obs_contract.md` にデプロイ用アクチュエータ表。行動の clip 無し、|action| 最大は LL_FFE 2.86。
- commit（未 push）: `d4149ec`（停止点1）、`3382cf8`・`d8b2db3`（停止点3）。

### 停止点4（2026-09-17 13:00 まで、未着）

H_gainDR の評価、H_eff13p5 の頑健性、base_lin_vel の途絶の許容時間、足裏 −30° の出どころ → デプロイ方策を G_real_peak / H_eff13p5 / H_gainDR から1本に決める。

## 実験08・09と2026-09-18朝の確定結果

- `L_angstd_w1`: 角速度追従報酬を std 0.35、weight 1.0 に変更。`model_4000.pt` と
  `model_4200.pt` だけが256 env・評価seed 2回ともその場旋回基準に合格したが、連続幅は
  200 iterで、事前条件の300 iterに届かなかった。`model_4000.pt` は stiffness 0.7倍と
  base_lin_vel 0埋め0.2秒で、H_eff13p5に無い不合格も出した。
- `N_w1_seed2`: 同じ設定を学習seed 2で再実行し、3000から4498まで完走。保存点9個。
  3200以降の8点を256 env・評価seed 2回で評価したが、合格点はゼロ。S6最大は
  `model_4000.pt` の +0.171 rad/s。seed 1の一時的合格は再現しなかった。
- `N_w1p5` (`2026-09-18_00-44-35_N_w1p5`): weight 1.5、std 0.35、seed 1で
  3000から4498まで完走。`model_4400.pt` だけが評価seed 2回とも合格
  （S6 +0.280/+0.264、S9 -0.482/-0.483、転倒 0/0.8%）したが、1保存点だけなので
  連続300 iterの採用条件を満たさない。4498ではS6 +0.43 / S9 -0.23へ逆に振れた。
- 結論: その場旋回を実機候補には採用しない。直進の第一候補は
  `H_eff13p5@2999`、予備は `G_real_peak@2999` のまま。
- `P_gainDR_narrow`: H_eff13p5@2999から、stiffness 0.85〜1.15倍・damping
  0.8〜1.25倍で追加学習する直進頑健化。夜間は3069で停止し、保存済みは再開元の
  model_3000だけだった。次に実行・評価する対象。
- 仮デプロイパッケージ `D:\Tominaga\deploy_pkg\deploy_pkg_20260918.zip` は作成済み。
  H_eff13p5@2999 / G_real_peak@2999 / L_angstd_w1@4000 のONNX・PyTorch・golden npz・
  検証結果・観測契約・SHA256を含む。3方策の16 env短時間動画も生成確認済み。

## 実験10（2026-09-21/22、A/B@29997最終評価）

H `model_19998.pt`から平地4096 envで追加10000 iter。最終評価はflat・64 env・seed1234・外乱/ノイズなし・warmup 2 s+測定10 s。詳細は`reports/2026-09-22_exp10-autoturn-directturn-assessment.md`。

| ラン名 | 再開元 | 方式 | 共通条件 | 評価の主眼 |
|---|---|---|---|---|
| `A_auto_heading_world_H20000@29997` | H `model_19998.pt` | 世界速度目標と同じ方向へheadingを自動追従 | **不採用**。S2 yaw +0.483、S4 -0.198、S5 +0.082 rad/sと不要yawが混入 |
| `B_direct_wz_turn_H20000@29997` | H `model_19998.pt` | 純旋回38%、前進30%、歩行旋回30%、静止2%の明示 `(vx,vy,wz)` | **資格評価待ち**。S6 +0.445/S9 -0.310、転倒0だが64 env・1 seed・最終1点のみ |

次は再学習でなく、Bの29940〜29997周辺の保存点を256 env・2 seed・H同等頑健性で資格評価する。連続300 iter以上が合格し、既存基準を維持したときだけ中央のcheckpointを再エクスポートする。

**2026-09-22 夜間GPU枠:** 上の資格評価とは別に、B@29997から追加9000 iterを2本並走する。`B_continue_H30000`はB設定を完全維持する延長対照。`B_lateral10_H30000`は純旋回38%・静止2%を保持し、前進30→25%・歩行旋回30→25%として横移動10%を追加する。学習開始前に64 env/20 iterと実効paramsを確認し、ユーザーが前景PowerShellで本番を起動する。

## 4096 env の基準値（WRS機 RTX 3090 Ti、2026-09-16）

| 並走本数 | 秒/iter（各ラン） | 合計 it/s | VRAM 合計 | GPU 温度 |
|---|---|---|---|---|
| 1 | 約 2.2 | 0.45 | 8.1 GB | 54°C |
| 2 | 3.6〜4.2 | 0.528 | 13.0〜16.0 GB | 58〜61°C |
| 3 | 5.1〜6.0 | 0.556 | 17.6 GB | 61°C |

- VRAM はデスクトップ描画 約 4.3 GB 込み。評価（64 env）を同時に回すと +2.7 GB。
- 実験03 の2本並走: GPU 使用率 90〜91%、ホスト RAM 37.9 / 127.4 GB、論理 CPU 20・使用率 約 19%、3000 iter で 3h42m。**GPU 90% 超のとき新しい env の構築がハングしたことが1回ある**（env 数を下げてやり直すと通った）。
- **1024 env × 6 本は VRAM に入らない見込み**（Isaac Sim は1プロセス約 3 GB の固定費）。GPU 計算は飽和しているので本数を増やしても合計は伸びない。

## 過去の参考（テスト起動）

| run | 内容 | 結果 |
|---|---|---|
| 2026-09-16 テスト | 64 env / 20 iter、08-21 版＋機体修正 | 1.5〜2.3 s/iter、VRAM 7.4GB、iter19 bad_orientation 99.5% / base_contact 1.2% |
