# 実験07: 評価スクリプトのハング原因特定と、その場旋回の詳細診断

2026-09-17夜。学習はせず診断のみ(K0〜K4)。詳細な生ログ・全表は`tools/logs/REPORT_exp07_stop7.md`(git管理外)。

## 背景

実験05/06以来、`t0_3_s6_diag.py`と`p6_1_footpitch.py`がKit起動直後に毎回ハングし、
一度も完走していなかった(`p6_2_basevel_dropout.py`は同種の構造で常に成功)。
実験06終了時点でコード上の差分(import順・argparse・AppLauncher引数)からは原因不明のままだった。

## K1: ハング原因の特定と修正

`tools/k1_bisect.py`(`p6_2_basevel_dropout.py`の骨組みを土台に、疑わしい要素を`--stage`で1つずつ
足していく切り分けスクリプト)で、env=16・単独実行・各10分までの上限で総当たりした結果:

| stage | 内容 | 結果 |
|---|---|---|
| 1 | env作成→即close(1回) | 成功(2.2s) |
| 2 | env作成→close→**2つ目のenv作成** | **ハング**(1つ目は成功、2つ目は`ManagerBasedRLEnv`構築中に無応答) |
| 3〜10 | 単一env内での全操作(Runner構築・reset・step・contact_sensor/reward_mgr取得・pxr走査・event override・resetを跨いだdefault_joint_pos書き換え・t0_3の全シナリオ約1800ステップの完全再現) | 全て成功 |

**結論**: 原因は「同一プロセス(同一`simulation_app`)内で`ManagerBasedRLEnv`をcloseして
2つ目を作り直す」ことのみ。単一env内でどれだけ複雑な処理をしても問題は起きない。
`t0_3_s6_diag.py`は2 checkpoint分をループしてenvを2回作っており、`p6_1_footpitch.py`は
Part1/Part2×2/Part3でenvを最大4回作っていたため、どちらも必ずハングしていた。

**修正**: 両スクリプトを「1プロセス=1env」に分割(`.bak_k1_multienv_split`にバックアップ)。
- `t0_3_s6_diag.py`: `--load_run`/`--checkpoint`必須引数化。1回の起動で1 checkpoint分のみ処理。
  2回起動する`tools/runs/run_t0_3_both.ps1`を追加。
- `p6_1_footpitch.py`: `--part {1,2,3}`に分割(Part2は追加で`--run_name`)。Part1がFFEキャリブレーション
  結果を`--calib_json`に書き出し、Part2/Part3が読み戻す。4回(Part2は2回)起動する
  `tools/runs/run_p6_1_all.ps1`を追加。

両方とも修正後に実際に動作確認済み(K2・K4として本番実行、下記)。

## K2: その場旋回で何が起きているか

新規`tools/k2_turn_diag.py`(1プロセス1env、64env)で H_eff13p5@2999 / J_turn_scratch@1000 /
J_turn_scratch@2999 を S1・S3・S6・S9で測定。

- **yaw rateは3 checkpoint全て0.01〜0.07 rad/s**(判定基準`|yaw rate|≥0.25`に対し未達、実験06の結論と一致)。
- **立脚足の滑り(yaw角速度)はS6/S9(0.07〜0.09 rad/s)の方がS1歩行時(0.33〜0.45 rad/s)より小さい。**
  「滑って回れない」のではなく、そもそも滑るほど強く踏み込んでいない。
- **HR関節角はS6/S9でS1/S3より大きく動く**(|角|p95が0.18〜0.66、S1/S3は0.05〜0.18)が、
  **HRトルクは全scenario・全checkpointでp95 0.6〜2.3 N・m**にとどまる。
- K2で報告した「HR飽和率0.0000」は`robot.data.joint_effort_limits`(PhysXソルバー側の値、
  実際は1e9=無制限)を参照していたための誤り。K3で確認した実効上限は53 N・m(下記)で、
  実際の使用率は2〜4%程度、全く飽和していない。
- 報酬内訳: `track_lin_vel_xy_exp`はS3/S6/S9で0.997〜1.000(ほぼ満点)、
  `track_ang_vel_z_exp`はS3の0.496〜0.500に対しS6/S9で0.188〜0.235と明確に低い。

## K3: 旋回可能トルクの実測

新規`tools/k3_torque_ramp.py`(H_eff13p5@2999、S3、方策動作中、32env)。胴体に world z軸まわりの
外力トルクを0→10 N・mまで1 N・m/sで漸増(`Articulation.set_external_force_and_torque(...,
is_global=True)`、非推奨API だが動作は正常。cfgは変更せず本スクリプト内のみで適用)。

| 項目 | 値 |
|---|---|
| 胴体yaw角速度が0.2rad/sを超えたトルク | 中央値5.740、範囲[0.020,7.460] N・m(32/32到達) |
| 立脚足のyaw角速度が0.2rad/sを超えたトルク(滑り出し) | 中央値2.760、範囲[0.020,4.440] N・m(32/32到達) |
| 転倒した時刻 | 中央値8.100、範囲[5.980,9.920] s(30/32が10秒以内に転倒) |
| 胴体z軸まわり慣性モーメント(全身、base原点基準、近似) | 0.21574 kg・m^2(全身質量10.1058kg) |
| HR effort_limit(actuatorオブジェクト実値、LL/LR) | 53.000/53.000 N・m |
| HR stiffness(actuatorオブジェクト実値、LL/LR) | 10.000/10.000 |

外力で強制的に回すと2.76〜5.74 N・m程度で足が滑り・胴体が回り始める。K2で見た方策自身のHRトルク
(p95 0.6〜2.3 N・m)はこれより小さい。**「物理的に回せない」のではなく、方策がその出力を
使おうとしていない**という見立てを補強する材料(ただし外力で強制的に回すケースと方策が
自発的にHRトルクを出すケースは異なるため、これだけでは断定できない)。

## K4: 足裏(P6-1、G_real_peak@2999)

- **Part1(FFE補正)**: 既定姿勢の足裏ピッチ-30°前後を打ち消すtheta_zero(+0.22〜0.23rad)を算出、
  URDF可動域内。ただし検証後の残差ピッチが約+27〜29°と、theta_zero適用前とほぼ同じ大きさで
  **符号反転**しており、単純な線形補正では足裏を水平にできない(非線形性が強い、または校正の限界)。
- **Part2(S3/S1立脚中の推定ソールピッチ)**: G_real_peak/H_eff13p5とも、S1立脚中の推定ピッチは
  -30°〜-84°と既定姿勢より傾いている場面が多く、方策は足裏を水平にする方向には使っていない。
- **Part3(補正姿勢でaction=0固定、2秒起立テスト)**: **転倒率1.0000(16/16全て転倒)**。
  FFE補正だけでは静的安定性は得られない(`project_handbook.md`の既存の結論と整合)。

## 未実施・積み残し

- 足裏の実測ピッチ(world頂点フィット)とPart2の線形写像推定値の直接比較検証
- HRトルクが実効上限の2〜4%しか使われない原因の直接分析(実験08 L0-1/L0-2で報酬側から着手)
- `docs/reference/eval_protocol.md`はS1-S6時点のまま、S7-S11とその場旋回基準の反映が未実施

## 関連ファイル

- `tools/k1_bisect.py`・`tools/k2_turn_diag.py`・`tools/k3_torque_ramp.py`(新規診断スクリプト)
- `tools/t0_3_s6_diag.py`・`tools/p6_1_footpitch.py`(1プロセス1envに修正)
- `tools/runs/run_t0_3_both.ps1`・`tools/runs/run_p6_1_all.ps1`(複数checkpoint/part起動ラッパー)
- `tools/logs/REPORT_exp07_stop7.md`(全数値・K1切り分け全stageの詳細、git管理外)
- commit: `e7a7924`
