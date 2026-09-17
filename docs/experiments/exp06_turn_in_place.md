# 実験06: その場旋回(S6/S9)の修正 — 結果は失敗

2026-09-17。実験05で「その場旋回ができないことはデプロイのブロッカー」と判定し、原因診断(T0)と
対策(J0/J本番)を行った。**結論: 対策は効かなかった。** 判定基準に達したチェックポイントは
resume 3本・scratch 3本・比較用の H_eff13p5@2999 の計7本中 **0本**。

## 1. 原因診断（T0/H0）

- `feet_air_time`/`feet_air_time_biped` の足上げ報酬が `torch.norm(command[:, :2]) > 0.1`
  （並進成分のみ）でゲートされており、`command[:,2]`(wz) を一切見ていなかった。
  その場旋回コマンドは並進ゼロなのでゲートが開かず、足上げ報酬が常に0になる。
- 学習時の実際の重み（`params/env.yaml` から実測。コードのデフォルト値ではない）:
  `feet_air_time` weight=0.0（無効）、`feet_air_time_biped` weight=0.25（有効）、
  `track_lin_vel_xy_exp` std=0.35。両方とも同じ `command[:,:2]` ゲートを共有しているため、
  結論は上の重みで変わらない。
- T0-2で計測: 学習時にその場旋回コマンド（`|(vx,vy)|<0.1 & |wz|>0.3`）が出現した割合は **0.38%**
  （`rel_heading_envs=1.0`の親クラス既定により、サンプルした`ang_vel_z`のほとんどが
  `_update_command`のheading追従で毎ステップ上書きされていたため）。

## 2. 対策（J0）

`my_robot_code/rewards.py`・`rough_env_cfg.py`（commit `dd970bf`）:

1. `feet_air_time`/`feet_air_time_biped` に `yaw_gate: bool = False` を追加。
   `True` のとき `|(vx,vy)|>0.1 OR |wz|>0.1` でゲートを開く（既定 `False` は旧挙動のまま）。
2. `UniformVelocityCommand` のサブクラス `TurnAwareVelocityCommand` を追加し、
   `rel_turn_in_place_envs`（vx=vy=0, wz=±U(0.3,1.0)）と `rel_translate_only_envs`（wz=0）を
   carve-out。`_update_command` の heading/standing 上書きを塞ぐよう `is_heading_env`/
   `is_standing_env` を明示的に False にする。既定値0.0でノーオペ。
3. `track_ang_vel_z_exp` の重み・std、アクチュエータ、地形は**変更していない**（因果を切り分けるため）。

`t0_2_command_stats.py` で確認: `rel_turn_in_place_envs=0.2`/`rel_translate_only_envs=0.15` を
与えるとその場旋回コマンドの出現率が 0.38% → **19.95%**（目標20%相当）まで上がることを確認した。

## 3. 本番ラン

共通ベース = H_eff13p5 の実際の起動時 `params/env.yaml` を、ゼロオーバーライドの
ベースライン（`tools/dump_baseline_env_yaml.py`、`dump_yaml()`を直接使用）と丸ごとdiffして
再構成した起動行（地形flat化・`rel_heading_envs=0.5`・`debug_vis=false`込み。
G対H_eff13p5同士のdiffだけでは共通の上書きが見えないため、この方法をとった）。
+ `yaw_gate=true`（feet_air_time_biped）+ `rel_turn_in_place_envs=0.2` +
`rel_translate_only_envs=0.15`。

| run | 方式 | 最終iter | 学習時間 |
|---|---|---|---|
| `2026-09-17_15-22-38_J_turn_resume` | H_eff13p5@2999から`--resume --load_run --checkpoint`で+1500 | 4498 | 5912s |
| `2026-09-17_15-23-17_J_turn_scratch` | ゼロから3000 iter | 2999 | 完走 |

`--resume`はHydraの`agent.resume=true`オーバーライドでは効かない
（`cli_args.py:76-81`が`args_cli.resume`(store_trueなので常にNone以外)で無条件に上書きするため）。
トップレベル引数`--resume --load_run <name> --checkpoint <file>`で渡す方式が正しい
（F_BtoRoughと同じ）。ログの"Loading model checkpoint from:"・iter 2999からの再開・
entropy/action_stdが訓練済み値であることを確認済み。

## 4. 評価結果 — その場旋回は全チェックポイントで不合格

判定基準（Cowork固定・変更禁止）: S6/S9でyaw符号が指令と一致、両方`|yaw rate|≥0.25`、
比率`|S6|/|S9|`が[0.5,2]、`|(vx,vy)|`平均≤0.10、転倒率≤5%、両足とも実際に着地>0。

| run@iter | S6 yaw[rad/s] (cmd+0.5) | S9 yaw[rad/s] (cmd-0.5) | 判定 |
|---|---|---|---|
| H_eff13p5@2999（比較用、再測定） | +0.019 | -0.013 | **不合格**（想定通り） |
| J_turn_resume@model_3400（+401） | +0.021 | -0.052 | **不合格** |
| J_turn_resume@model_4000（+1001） | +0.029 | -0.019 | **不合格** |
| J_turn_resume@model_4498（+1499・最終） | +0.067 | -0.007 | **不合格**（S9符号ほぼノイズ） |
| J_turn_scratch@model_1000 | -0.002（符号逆転・微小） | -0.120 | **不合格** |
| J_turn_scratch@model_2000 | +0.018 | -0.064 | **不合格** |
| J_turn_scratch@model_2999（最終） | +0.014 | -0.007 | **不合格** |

**閾値0.25に対し、観測された最大値は0.12（scratch@1000のS9）。学習が進むほど値は縮む方向。**
S10（最強のその場旋回指令、wz=+1.0、参考用）でも同じ傾向: scratchのlandings/sが
iter2000の2.97→iter2999の0.67に**悪化**、yaw rateも0.434→0.074に縮小。
つまり「学習不足」ではなく、**学習が収束するにつれて足を止める方向に向かっている**。

### 仮説（未検証）

`track_ang_vel_z_exp`は指令`ang_vel_z`全域（大半は小さい値）に対するGaussian報酬で、
小さい`wz`は静止のままでも高い報酬が出る。大きい`wz`（S6/S9相当）だけを見た学習信号は
全体平均の中で希釈され、片や足を動かすと`action_rate_l2`・`joint_torques_l2`・
`flat_orientation_l2`等の罰則が増える。この差し引きで「回らずに立っている」方が
局所的に得、という仮説。`track_ang_vel_z_exp`の重み/stdを変えない制約下では検証できない
（次のチャットでの重要な分岐点: この制約を外すかどうかの判断が要る）。

### 既存判定基準への回帰は無い

- S1 `v_x`: H_eff13p5=0.423、resume=0.455/0.462/0.459、scratch=0.443/0.468/0.457。
  いずれも既存基準`≥0.35`を満たし、**むしろ改善**。
- 転倒率: S1-S9で全run 0.000（S10/S11は参考のみ、resume@4000でS10のみ0.047）。
- カニ歩き: S1/S2の`|v_y|`は全run 0.00-0.03、`|v_y-cmd_y|`は0.07-0.09台でH_eff13p5と同水準
  （新規の悪化ではない）。
- トルク飽和率（`torque>=95%limit`、S2）: H_eff13p5=0.023に対しresume=0.006-0.012（改善）、
  scratch=0.014-0.032（同水準〜やや悪化するがFFE専用のRMS指標ではなく全関節の飽和割合の
  代理指標であることに注意）。**FFEの直接のRMSはmeasure_crab.pyに実装が無く未測定（要追加）。**
- S6でのHR `|computed torque|` のp95・飽和割合は、現在の`measure_crab.py`には出力が無い
  （`|qd|`p95(角速度)と`torque_sat_frac`(全関節飽和割合)のみ）。**未測定、要追加計測。**

### training curve（TensorBoard正規化前の生値、参考）

| run@iter | track_ang_vel_z_exp | error_vel_yaw(生) | error_vel_xy(生) | mean_episode_length |
|---|---|---|---|---|
| resume@3000 | 0.0096 | 0.033 | 0.024 | 35（再開直後、まだ短い） |
| resume@3400 | 0.367 | 0.510 | 0.231 | 986 |
| resume@4498 | 0.378 | 0.478 | 0.234 | 991 |
| scratch@500 | 0.087 | 0.398 | 0.319 | 321 |
| scratch@2000 | 0.300 | 0.556 | 0.255 | 894 |
| scratch@2999 | 0.244 | 0.662 | 0.284 | 815 |

`track_ang_vel_z_exp`報酬は上がっているが、これは上の仮説通り小さい`wz`コマンドの改善であって
S6/S9のような大きい指令の追従ではないと考えられる（直接測定のS6/S9が裏付け）。

## 5. 結論と次のチャットへの判断材料

- **どのチェックポイントもデプロイ候補にしない。** ONNX書き出し・P1頑健性スイープは実施しない
  （実施前提の「合格チェックポイント」が存在しないため）。
- **`feet_air_time`のyaw_gateとコマンド分布の変更だけでは不十分**というのが今回はっきりした
  結論。次にやるなら候補は次の3つ（優先度は未決定、次のチャットでユーザーと相談）:
  1. その場旋回専用の追従報酬（`track_ang_vel_z_exp`とは別項）を新設し、大きい`wz`指令だけに
     重みを乗せる。既存の`track_ang_vel_z_exp`自体は変えない。
  2. `rel_turn_in_place_envs`をさらに上げる（0.2→0.4等）か、`turn_in_place_wz_range`の下限を
     0.5付近に寄せてS6/S9相当の指令頻度を増やす。
  3. （制約を外す前提の案）`track_ang_vel_z_exp`のstdを縮めて大きい`wz`への感度を上げる、
     または`track_ang_vel_z_world_exp`系への差し替え（実験01/02から積み残しの旋回改善候補と同根）。
- **ハングの切り分けは未解決のまま。** `t0_3_s6_diag.py`/`p6_1_footpitch.py`と
  `p6_2_basevel_dropout.py`をファイル全体・import順・AppLauncher引数・`.ps1`起動行まで
  diffしたが、コード上の差分は見つからなかった（cosmetic な引数名の違いのみ）。
  `pxr`/`UsdGeom`のimport位置も、以前成功した`shape_diag_p5_7.py`と同じ配置。
  再現性は高い（p6_2は3/3成功、t0_3とp6_1は毎回ハング）が原因不明。
  **学習が全て終わってGPUが空いている今が、再現・切り分けを再開する適期。**
- **D1/D2/D3（実験05から持ち越し）は本ドキュメントと`tools/logs/`に格納済み**（下記6章）。

## 6. 関連ファイル（`tools/logs/`、git管理外）

- D1: `diff_1b93c48_modified.txt`（scratchpad、noise_std_type修正のdiff。commit `1b93c48`）、
  `tb_H_gainDR_d1.md`/`tb_G_real_peak_d1.md`（TensorBoard比較。結論:
  H_gainDRは`track_lin_vel_xy_exp`が0.08〜0.13で頭打ち、`base_contact`終了率77-80%のまま、
  episode_lengthも390-430で改善せず — **学習中から一貫して歩いていなかった**。
  G_real_peakは同reward が0.13→0.64-0.76、base_contact終了率78%→10-42%、
  episode_length 492→800-930 — 明確に歩行を獲得している）。
- D2: `obs_contract.md`の「H_eff13p5用の節」— 42次元・観測順・scale/clipがG_real_peakと完全一致、
  actuatorの差はhfe/ffe effort_limit=13.5のみ。`|action|`p99/max表、joint_target範囲表も記載済み。
- D3: `P6_2_dropout_H_eff13p5_2999.md` — base_lin_vel途絶、zeroモードは0.1s安全(0%)・0.2sで1.56%・
  0.5s以上でほぼ100%、holdモードは0.5s安全(0%)・1.0sで26.56%・2.0sで70.31%。
- ハードリンク: 本番起動前に5組のリンク数・SHA256を再確認済み（Editツールで切れる問題は
  `project_handbook.md`2章に既に注意書きがあるため追記不要と判断。念のため次のチャットで
  「open(r+)方式」の徹底が実際に守られているか確認するとよい）。
