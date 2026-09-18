
# 指示書 実験08: その場旋回の報酬を締める学習（WRS機、実験07 と同じチャットに貼る）

> 作成 2026-09-17 夜。停止点7（`tools\\logs\\REPORT_exp07_stop7.md`）を受けて。経緯は `chats/2026-09-17_exp04-stop4-review.md` の末尾。

```
# 指示: 停止点7 の講評と、実験08（その場旋回の報酬を締める学習 2本。停止点8a・8b）

停止点7 ありがとう。ハングの原因（同じプロセスで env を閉じて作り直すとハング）を特定したのは大きい。
wrs_new_chat_start.md の掟・作法はすべて有効。評価は 1プロセス1env で行う。

## 講評（Cowork の読みの訂正を含む）
- Cowork の第一候補「足裏の摩擦が足りず、立脚足が滑る」は外れ。S6 / S9 の立脚足の yaw 角速度は S1 より小さい。足が滑り出すトルク（中央値 2.76 N·m）に対して、HR は p95 で 0.6〜2.3 N·m しか使っていない。回れないのではなく、回ろうとしていない。
- 「止まっている方が総報酬が高い」は、回らない方策の報酬しか見ていないので、まだ示せていない。回るために足を踏むと罰がいくら増えるかが要る（L0-1）。
- K4: 足裏を平らにしても action 0 では 16/16 転倒。実機は吊り下ろしで始める前提のまま（条件16 は合格済み）。

## L0（GPU なし。既存のログと計算だけ。30 分まで）
L0-1 K2 の報酬の項ごとの 1 step 平均（weight 込み）を、全項について S1・S3・S6・S9 で並べる（H_eff13p5@2999、J_turn_scratch@1000、@2999）。罰の項の合計を S1 と S3 で比べ、「歩くと罰が 1 step あたりいくら増えるか」を1行で出す。
L0-2 計算: track_ang_vel_z_exp の std を 0.5 と 0.35 にしたとき、wz 指令 0.3 / 0.5 / 1.0 で「止まっているとき」と「完全に追従したとき」の 1 step の報酬（weight 0.5 と 1.0 の両方）。L0-1 の「歩くと増える罰」と並べる。
L0-3 ハングの原因と対策（1プロセス1env）、実験06・07 の結果を docs\\experiments\\ に正式に書く。commit（push しない）。

## L 本番（2本同時、4096 env、seed 1）
土台は J_turn_resume の起動行（yaw_gate=true、rel_turn_in_place_envs 0.2、rel_translate_only_envs 0.15 込み）。変えるのは track_ang_vel_z_exp だけ。
1. L_angstd: env.rewards.track_ang_vel_z_exp.params.std=0.35（weight 0.5 のまま）
2. L_angstd_w1: 同じく std=0.35、env.rewards.track_ang_vel_z_exp.weight=1.0
どちらも H_eff13p5 の model_2999.pt から --resume --load_run 2026-09-17_00-08-51_H_eff13p5 --checkpoint model_2999.pt で +1500 iter。
起動前の確認（64 env / 20 iter）:
- テスト run の params\\env.yaml を J_turn_resume の run と丸ごと diff する。差が track_ang_vel_z_exp の std・weight と、run ごとの値だけであること。
- ログに Loading model checkpoint が出て、iter が 3000 から始まること。
- std が上書きできない、など想定外があれば起動せず報告。

## 評価（measure_crab.py、S1〜S11、64 env、1プロセス1env）
- 各ランの +500 / +1000 / +1499 で行う。
- 判定は実験06 と同じ（その場旋回の合格ライン＋既存の基準）。
- S6 / S9 では、HR の computed torque の p95、立脚足の yaw 角速度、歩数も出す。

## 【停止点8a】L0 と2本の起動（iter 30）が終わったら短く報告（止まらずに評価へ進む）
- L0-1 の表と「歩くと増える罰」、L0-2 の表、起動行2本、diff の結果、終わる見込み

## 【停止点8b】両方の +1499 の評価が終わったら報告して止まる
- 冒頭3行: その場旋回の判定（2本）、既存基準の退行の有無、足の運び
- 表: H_eff13p5@2999 / J_turn_resume@4498 / L の2本 × 3 チェックポイント。S1・S3・S5・S6・S7・S8・S9 について、yaw・|(vx, vy)|・転倒率・歩数・FFE RMS
- 合格があれば一番良いチェックポイントを1つ推し、ONNX 書き出し・verify_onnx.py・SHA256
- チャットには冒頭3行・表・未実施だけを出す。詳細は tools\\logs\\REPORT_exp08_stop8b.md に

## やらないこと
track_ang_vel_z_exp 以外の報酬・指令・地形・アクチュエータの変更、push、削除、インストール。推測で直さない。想定外は止まって報告。
```
