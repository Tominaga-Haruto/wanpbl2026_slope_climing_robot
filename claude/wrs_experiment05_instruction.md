
# 指示書 実験05: デプロイ準備（両方の方策）と、その場旋回ができない原因の調査（WRS機）

> 作成 2026-09-17 午後。実験04 停止点4（`tools\\logs\\REPORT_exp04_stop4.md`）を受けて。実験04 と同じ WRS チャットに続けて貼る。
> 判断の経緯は `chats/2026-09-17_exp04-stop4-review.md`。
> ユーザー決定: デプロイには G_real_peak@2999 と H_eff13p5@2999 の両方を持っていく（実機は H_eff13p5 から）。GPU はずっと使ってよい。その場旋回ができないのはまずいので、デプロイ準備と並行して旋回を直しに行く。
> この指示では学習を起動しない。旋回を直す学習の変更は、停止点5a（原因の数値）を見て Cowork が決める。

```
# 指示: 停止点4 の講評と、実験05（デプロイ準備 D ＋ その場旋回の原因調べ T0。停止点5a・5b）

停止点4 ありがとう。ハングで止めて、推測でリトライしなかった判断は正しい。
前の指示（wrs_training_operator_instruction.md の掟、実験03・04 の「更新」と「やらないこと」）はすべて有効。起動は _launch.ps1 / _eval.ps1 / _play.ps1。
GPU の占有はユーザーが了承済み（今回は期限なし）。開始時に nvidia-smi で他人の計算プロセスがあれば、何も起動せず報告して止まる。

## 判断（ユーザー決定）
- デプロイには G_real_peak@2999 と H_eff13p5@2999 の両方を持っていく。実機は H_eff13p5 から試し、G_real_peak は予備。
  根拠: 共通の条件での不合格はどちらも3つ（G: damping ×0.5 の直進 yaw・damping ×2・速度 0／H_eff13p5: stiffness ×0.7 の転倒 6.2% = 64 体中 4 体・damping ×2・速度 0）。ゲインのずれは実機で換算係数を測れば指令側で合わせられるが、トルク側（条件4 で G は転倒 3.1%・FFE 飽和 40%、H_eff13p5 は 0%・23%）は測っても消えない。
- H_gainDR は候補から外す。ゲインのランダム化での再学習は今はしない（実機で Kd を測れば不要になるため）。
- その場旋回（S6 / S9）ができないのは、デプロイに困るとユーザーが判断。デプロイ準備と並行して直しに行く。今回はまず原因を数値で調べる（T0）。学習の変更は停止点5a の後に決める。

## 報告書への指摘
- 冒頭3行の推奨（G_real_peak）は、前に決めた選び方「不合格が同数ならトルクの低い方」と違っていた。規則と違う推奨をするときは、規則の結論と、違える理由を並べて書く。
- 1b93c48 の diff が報告に無い（指示では載せることになっていた）。D1 で出す。

## 進め方
- T0 と D1 から始める。GPU を使う評価は 64 env 以下で、同時に2本まで。学習はこの指示では起動しない。
- 評価を起動する前に nvidia-smi の GPU 使用率を記録する。env の構築が 10 分進まなければ、そのプロセスを止め、env 数を半分にして1回だけやり直す。それでも進まなければ止まって報告。
- T0 が終わった時点で停止点5a を報告する（D の残りは止めずに続けてよい）。D が全部終わったら停止点5b を報告して止まる。

## T0 その場旋回ができない原因（学習 cfg は変えない。読む・評価・計算だけ）
分かっている事実: どの run も S6 / S9（その場旋回 ±0.5 rad/s）で |yaw rate| 0.03 前後。S7 / S8（前進 0.5 ＋ 旋回 ±0.3）は合格。旋回の指令は学習中に十分出ていた（|wz 指令| > 0.2 が 77〜85%）。正規化 error_vel_yaw は iter 1600 以降じわじわ悪化する。

T0-1 実効値（__post_init__ と起動行の上書きの後の値。G_real_peak の run の params\\env.yaml と、コードの grep の両方で。ファイル名と行番号つき）
- track_ang_vel_z_exp と track_lin_vel_xy_exp の weight・std
- feet_air_time_biped と feet_air_time の関数本体を行ごと貼る。指令の大きさで報酬を掛けたり 0 にしたりする行があるか。あれば、その判定に使っているのが lin_vel_x / lin_vel_y だけか、ang_vel_z も入っているか
- ほかに指令の大きさで入り切りする項（stand_still 系など）を全部
- joint_deviation_hip の対象関節と weight、HR の動きを罰するほかの項（feet_slide など、足の yaw 方向の動きに効く項も）
- 指令: ranges（lin_vel_x / lin_vel_y / ang_vel_z / heading）、heading_command、heading_control_stiffness、rel_heading_envs、rel_standing_envs、resampling_time_range
- HR の関節リミット（URDF の値と、シムの soft limit のテンソル値）、HR グループの stiffness・damping・effort_limit

T0-2 学習時の指令の組み合わせ（64 env、学習と同じ指令 cfg・rel_heading_envs 0.5、action 0 で 1000 step、毎 step 記録）
- |(vx, vy)| < 0.1 かつ |wz| > 0.3 の割合（その場旋回の指令）
- |(vx, vy)| < 0.1 かつ |wz| ≤ 0.3 の割合（立ち止まりの指令）
- |(vx, vy)| ≥ 0.1 かつ |wz| > 0.3 の割合（歩きながら曲がる指令）
- 上の3つを、heading モードの env と wz を直接出す env に分けて

T0-3 S6 で何をしているか（H_eff13p5@2999 と G_real_peak@2999、64 env、S6・S1・S3 を並べる）
- 足を上げているか: 左右の足の接地率、1歩あたりの滞空時間、10 s あたりの歩数
- HR の関節角: 平均・範囲・|値| の p95（左右）。HR の computed torque の p95 と飽和率
- 報酬の項ごとの 1 step 平均（weight 込み）。reward manager の項ごとの値を記録する
- 接地中の足の yaw 方向の滑り（接地中の足リンクの world の yaw 角速度の平均と p95）

T0-4 計算だけ
- S6（wz 指令 0.5）で、yaw 0.03 のときと完全に追従したときの track_ang_vel_z_exp の 1 step の差（weight 込み）
- T0-1 で足上げの報酬が並進の指令でしか入らないと分かった場合、S6 の指令でその項がいくらになるか
- HR を ±0.2 rad 振ったときの joint_deviation_hip の 1 step の罰

## D デプロイ準備（G_real_peak@2999 と H_eff13p5@2999 の両方）
D1（GPU なし）
- git show 1b93c48 の diff（ファイルごと）
- H_gainDR と G_real_peak の学習ログ（TensorBoard）を iter 500 / 1000 / 1600 / 2400 / 2999 で並べる: Train/mean_reward、Train/mean_episode_length、正規化 error_vel_xy / error_vel_yaw、track_lin_vel_xy_exp・track_ang_vel_z_exp・足上げの報酬、Policy/mean_std。「学習中から歩いていなかった」のか「評価のときだけ止まる」のかを1行で判定。
D2 H_eff13p5@2999 の golden npz（P5-4 と同じ中身）→ tools\\logs\\golden_H_eff13p5_2999.npz と同名の .md。obs_contract.md に H_eff13p5 の節を足す: 観測の並び・次元・scale・clip が G_real_peak と同じかを項ごとに比べた表と、デプロイ用アクチュエータ表（テンソルから読んだ値で）。
D3 P6-2 を H_eff13p5@2999 で（G_real_peak と同じ条件。zero / hold × 0.1 / 0.2 / 0.5 / 1.0 / 2.0 s、途絶開始から 3 s の転倒率）。
D4 P6-1 のやり直し（前回ハング）。env は 16 から。
- 1（FFE を何 rad 足すと足裏の pitch が 0 か）と 3（その姿勢で action 0 で 2 s 立てるか、16 env の転倒率）は形状と既定姿勢で決まるので1回だけ
- 2（S3 と S1 の立脚中の足裏 pitch と FFE 角）は G_real_peak@2999 と H_eff13p5@2999 の両方

## 【停止点5a】T0 が終わったら報告（D は続けてよい）
- 冒頭3行: その場旋回ができない原因の候補を、数字で効きが大きい順に
- T0-1〜T0-4 の表と、関数の該当行
- 旋回を直す学習の変更案を2つまで。どの数字からそう言えるかをつける。起動はしない。
- D の進み具合と終わる見込みの時刻
- 報告書は tools\\logs\\REPORT_exp05_stop5a.md

## 【停止点5b】D が全部終わったら報告して止まる
- D1〜D4 の結果、未実施の項目、commit のハッシュ（push しない）
- 報告書は tools\\logs\\REPORT_exp05_stop5b.md

## やらないこと
- 学習の起動、報酬・指令・地形・アクチュエータの cfg の変更
- push、削除、pip / conda でのインストール
推測で直さない。想定外は止まって報告。
```
