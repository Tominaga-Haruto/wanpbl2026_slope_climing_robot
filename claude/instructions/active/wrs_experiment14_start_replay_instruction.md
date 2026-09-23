# WRS 実験14: 立った状態から方策を始めたとき、シムでは最初の 1 s に何が起きるか（実機との突き合わせ）

作成 2026-09-23。実機（D10-13C）では、まっすぐ立った状態から方策を始めると、0.2 s で体が前へ 9〜13°倒れ、FFE の最初の行動は +1.0〜1.2 だった。シムでも同じことが起きるのかを確かめる。ゲインの物理換算（Kt）と、関節の原点（CAD の姿勢）の2つの仮説を、条件を変えて見る。
根拠は `../../reports/2026-09-23_d10-13c_result_トルクと基準姿勢.md`。終わったらこのファイルを `../inactive/` へ移す。

```
# 依頼: 方策 H_eff13p5@2999 の「立ち始め 3 秒」をシムで再生して数字を取る（学習はしない）

## このプロンプトの前提
- このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない。
- 学習はしない。1 env・3 s の再生を 5 条件回すだけ（合わせて数分）。これは CLI が自分で実行してよい。
  10 分を超えそうなら止めて、ユーザーが前景で打つコマンドを渡す。
- cfg ファイル（my_robot_code\*.py、references\ 以下）は書き換えない・移動しない（IsaacLab 側とハードリンク）。
  新しいスクリプトを tools\replay_start.py として1本作るのはよい。既存スクリプトは直さない。
- 何も削除しない。pip で何も入れない。git の commit・push はしない。推測で直さない。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run: D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\2026-09-17_00-08-51_H_eff13p5、checkpoint model_2999.pt
- その run の params\env.yaml を正とする（HFE/FFE effort 13.5 が入っているはず。確認して報告に書く）。
- 再生の既存スクリプト tools\runs\_play.ps1 と、golden を作った measure_crab.py の env の作り方を参考にしてよい。

## 共通の条件（5 条件すべて）
- 1 env、平地（plane か、地形の難易度 0 の平らな区画）。
- ノイズなし（enable_corruption False）、押し（push_robot・base_external_force_torque）なし。
- リセット時の関節ランダム化を止める（reset_joints_by_scale の範囲を (1.0, 1.0)）。base の初期姿勢・速度のランダム化も 0。
- 質量・摩擦・armature の DR は既定値の中央（scale 1.0）に固定できるなら固定。できなければそのままにして報告。
- 指令は (0, 0, 0) に固定（resampling で変わらないように）。heading_command は False にしてよい。
- 開始から 150 step（3.0 s）を記録する。最初の step 0 の観測は、既定姿勢・静止のはず。

## 5 条件
| 条件 | 変えるもの | 何の仮説か |
|---|---|---|
| S0 | なし | 基準 |
| S1 | hfe・ffe の stiffness と damping を ×1.5、hr・haa・kfe を ×1.15 | 実機の物理トルクがシムより強い（Kt の仮説） |
| S2 | 全関節の friction ×3 | 実機の摩擦がシムの 1.7〜3.1 倍 |
| S3 | 初期関節角を LL(HFE,KFE,FFE)=(-7.1, +7.7, -0.6)°、LR=(-10.9, +12.8, -1.9)°、ほかは 0。方策へ入る観測はシムの通り | 実機の「まっすぐ」原点で既定姿勢を作ると、シムの関節角ではこの姿勢になる（原点の仮説） |
| S4 | S1 と S2 を両方 | 両方 |

S3 は、関節の初期角を init_state か reset イベントの上書きで入れる。胴の高さは足が床に着く程度に下げてよい（数 mm 浮いて落ちるのは可）。入れ方が分からなければ S3 だけ飛ばして報告。

## 記録と報告（tools\replay_start.py が CSV を1条件1本で書く。保存先 D:\Tominaga\slope-climbing-robot\tools\logs\replay_start\）
各 step: 時刻、projected_gravity（x,y,z）、pitch（atan2(gx, -gz) の度、+ が前）、base_lin_vel x、
10関節の joint_pos − default（度）、joint_vel（度/s）、action（生値）、applied_torque（N·m）。
関節の並び: LL_HR, LR_HR, LL_HAA, LR_HAA, LL_HFE, LR_HFE, LL_KFE, LR_KFE, LL_FFE, LR_FFE。

報告（これで止まる）:
1. 冒頭3行: S0 で最初の 0.5 s に前へ何度倒れたか。実機（0.2 s で +9〜+13°）にいちばん近い条件はどれか。
2. 表（条件ごと）: t = 0.1 / 0.2 / 0.3 / 0.5 / 1.0 / 3.0 s の pitch、0〜0.5 s の最大 pitch、step 0〜2 の LL_FFE・LR_FFE の action、
   0〜0.5 s の FFE・KFE の |applied_torque| 最大、3 s で倒れたか（pitch が ±45°を超えたか）、3 s の間に足踏みしたか（KFE の振れ幅）。
3. S0 の step 0 の観測 42 次元と action 10 次元をそのまま貼る（実機の最初の観測と比べるため）。
4. env.yaml から読んだ effort_limit・stiffness・damping・friction（5 グループ）と、実際にテンソルに入った値（S1・S2 で倍率が効いたか）。
5. ユーザーが自分で再実行するための 1 行コマンド（実行フォルダ明示、プレースホルダなし）。
```
