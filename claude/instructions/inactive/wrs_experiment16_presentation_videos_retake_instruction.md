# WRS 実験16: 発表用シム動画の撮り直し（足首の自然な候補探し・引きの画・30 秒・10 場面）

作成 2026-09-24。発表（2026-09-25）用。実験15（`../inactive/wrs_experiment15_presentation_videos_instruction.md`）の撮り直し。
変えた理由（ユーザーの目視）: B@25000 は足首（FFE）をほぼ回しきった姿勢で歩く／画が寄りすぎ／ロボットが密集／15 s では短い。
シムの関節可動域は URDF で全関節 ±π のまま（`../../reference/robot_model_conventions.md` §4）。つまり足首を回しきっても何も止めない。
終わったらこのファイルを `../inactive/` へ移す。

```
# 依頼: 発表用シム動画の撮り直し（10 場面）。足首が自然な方策を探してから撮る

## このプロンプトの前提
- このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。必要な情報はすべてここに書いた。
- やってよいこと: ファイルの確認、短い評価（動画なし）、動画撮影（1本 30 s 程度）。学習は起動しない。
- 撮影・評価は tools\record_fixed_cmd.py（前回あなたが作ったもの）を使う。このスクリプトには下の「スクリプトの追加」を
  入れてよい（先に .bak_20260924_retake を取る。既定値では前回と同じ動作のままにする）。
  既存ファイル（play.py、measure_crab.py、_play.ps1、_eval.ps1、my_robot_code\*.py、references\ 以下）は変更しない。
  my_robot_code\*.py は IsaacLab 側とハードリンクなので、移動・置換しない。
- 何も削除しない（前回の動画・_TRIAL も残す）。pip で何も入れない。git の commit・push はしない。
- 「import できない」など構造だけが理由の問題は、必要な部分を出典コメント付きで複製して進めてよい。止まるのは、
  直しを1回入れても落ちるとき、指令が固定されないとき、mp4 が出ないときだけ。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\<run名>
- 前回の起動の形（これを写す）:
  & "C:\Users\WRS\miniconda3\shell\condabin\conda-hook.ps1" | Out-Null ; conda activate "D:\Tominaga\envs\isaac_env" ; Push-Location "D:\Tominaga\IsaacLab" ; D:\Tominaga\envs\isaac_env\python.exe D:\Tominaga\slope-climbing-robot\tools\runs\_preload_h5py_and_run.py D:\Tominaga\slope-climbing-robot\tools\record_fixed_cmd.py --load_run 2026-09-21_02-17-13_B_direct_wz_turn_H20000 --checkpoint model_25000.pt --num_envs 16 --terrain flat --cmd 0.5 0.0 0.0 --scene_name V1_flat --video --video_length 750 ; Pop-Location
- 出力は Start-Process -RedirectStandardOutput / -RedirectStandardError で取る（*> は stdout が消えた）。
- 出力先（新規）: D:\Tominaga\slope-climbing-robot\tools\videos_presentation_20260924_v2\

## スクリプトの追加（record_fixed_cmd.py）
1. カメラ: --cam_mode {follow, world}。follow は viewer の origin_type を asset_root にして対象ロボット（--cam_env、既定 0）を
   追いかける。--cam_eye x y z と --cam_lookat x y z（follow では対象ロボットからの相対、world では世界座標）。
   follow の既定は eye (3.0, -5.0, 2.0)・lookat (0, 0, 0.3)（前回より十分に引いた斜め横。ロボット全身と足元の地面が入ること）。
   --resolution 1920 1080（viewer の resolution を上書き）。
2. 長さ: --episode_s（env の episode_length_s を上書き。既定は env のまま）。30 s 撮るときは 40 を渡し、撮影中に
   タイムアウトのリセットが入らないようにする。転倒による終了はそのまま。
3. 密集対策: --tiles_rows R --tiles_cols C --tile_size S（terrain_generator の num_rows・num_cols・size を上書き）。
   num_envs を C 以下、R=1 にして、1 体につき 1 タイルになるようにする。flat は 3 体・タイル 12 m、坂は 3 体・タイル 32 m
   （逆ピラミッドの中心から上り斜面が 15 m 続くように）、でこぼこは 3 体・タイル 24 m を既定の使い方とする。
   1 体 1 タイルにならない（env の原点が重なる）場合は、env の原点を読んで報告し、num_envs を減らして合わせる。
4. 記録の追加（.txt と stdout）: 関節ごと（左右 × HR/HAA/HFE/KFE/FFE）の角度 [deg] の 平均・5 %・95 %・最小・最大、
   関節角が URDF の可動域（env から読んだ soft limit）の 90 % を超えた時間の割合、
   胴体の横速度（胴体座標）の平均と、進行方向と胴体の向きのずれの平均 [deg]、前進速度の平均。
   そのロボット（env）の実際の関節の可動域（articulation の joint_pos_limits と soft_joint_pos_limits）を1回だけ表示する。
5. 1 回の起動で 1 場面（前回と同じ）。

## P0 足首の基準と候補探し（動画なし、1 条件ずつ）
- 基準: H_eff13p5@2999（run 2026-09-17_00-08-51_H_eff13p5、model_2999.pt）。ユーザーが目視で「足首は自然」と判断した方策。
  平地・(0.4, 0, 0)・30 s で回し、左右 FFE の 5 %〜95 % の範囲を「基準範囲」とする。
- 合格: FFE の 5 %・95 % が「基準範囲 ±15°」に収まり、かつ FFE の 95 % の |角度| が 60° 以下。
- 候補（実在確認してから。無い保存点は実在する最も近い点）:
  | run | checkpoint | ねらい |
  |---|---|---|
  | 2026-09-21_02-17-13_B_direct_wz_turn_H20000 | model_20000・21000・22000・23000 | 足首が回りきる前の点があるか |
  | A_auto_heading_world_H20000（実名確認） | model_23000 | 坂 10°で転倒 0 |
  | 2026-09-18_22-14-07_P2_gainDR_seed2 | model_4000 | 坂 10°で転倒 0、足の滑り最小 |
  | P3_stiffonly（実名確認） | model_6000 | 坂 10°で転倒 0 |
  | 2026-09-16_13-40-37_F_BtoRough | 最終保存点 | rough で学習、平地歩行を保持 |
  | T_turn35_w1_extend_18000（実名確認） | model_11000 | 平地学習で最も坂を登る |
  | 2026-09-17_21-18-22_L_angstd_w1 | model_4000 | その場旋回に合格した H 派生 |
  | H_eff13p5_extend_20000（実名確認） | model_19998 | H の延長 |
  | 2026-09-21_02-17-13_B_direct_wz_turn_H20000 | model_25000 | 比較用（前回の主役） |
- 手順: 全候補を 平地・(0.4, 0, 0)・30 s・3 体 で回し、足首の合否を出す。
  足首に合格した候補だけ、坂 10°（slope 0.176）と でこぼこ 6 cm（noise 0.06）を (0.4, 0, 0)・30 s で回す。
  旋回（(0, 0, +0.5) と (0.3, 0, +0.4)）も、足首に合格した候補だけ平地で回す。
- 場面ごとの採用: 転倒 0 かつ足首合格の中で、指令への追従（前進速度、または yaw 速度）が最も良いもの。
  足首に合格する候補が1つも無い場面は、B@25000 で撮り、報告でそう明記する。
- P0 は評価だけで、合計 90 分を超えそうなら、候補表の下から削って時間内に収める（削ったものを報告に書く）。

## P1 撮影（10 場面。長さ 30 s、1920×1080、step_dt は env.yaml から確認して 30 s 分の step 数にする）
ファイル名は tools\videos_presentation_20260924_v2\ に <番号>_<場面>_<run短縮名>_<ckpt>.mp4。
| 番号 | 場面 | 方策 | 地形・体数 | 指令 (vx,vy,wz) | カメラ |
|---|---|---|---|---|---|
| 01 | 4096 体の同時シミュレーション | H_eff13p5 の model_400 前後（歩こうとしてぎこちない頃）と model_2999 の2本 | flat、4096 体。タイルを 64×64・2.5 m にして格子状に並べる | (0.4, 0, 0) | world。全体が入る高い俯瞰、eye (-60, -60, 45)・lookat (80, 80, 0) を起点に、格子全体が画面に入るよう調整。長さ 20 s |
| 02 | 立ち往生 | 2026-09-16_05-14-59_A_base0821 の model_2999（全シナリオで静止 100% だった run） | flat、3 体 | (0.4, 0, 0) | follow 既定 |
| 03 | カニ歩き（URDF を直す前） | 下の注を参照 | flat、3 体 | (0.4, 0, 0) | follow 既定。横流れが分かるよう、真上寄り eye (0, -4, 5) も1本 |
| 04 | 改善後（まっすぐ前へ） | H_eff13p5@2999 | 02・03 と同じ地形・体数・カメラ | (0.4, 0, 0) | 02 と同じ |
| 05 | 平地を前進 | P0 で採用した方策（無ければ H_eff13p5@2999） | flat、3 体 | (0.3, 0, 0) と (0.4, 0, 0) の2本 | follow 既定 |
| 06 | 坂 10° | P0 で採用 | slope 0.176、3 体、タイル 32 m | (0.4, 0, 0) | follow。坂の傾きが分かる真横寄り eye (0, -6, 1.5) |
| 07 | 坂 15°（あれば） | P0 で採用 | slope 0.268、同上 | (0.4, 0, 0) | 06 と同じ。転倒するなら撮らなくてよい |
| 08 | でこぼこ 6 cm | P0 で採用 | noise 0.06、3 体、タイル 24 m | (0.4, 0, 0) | follow 既定 |
| 09 | その場で旋回 | P0 で採用 | flat、3 体 | (0, 0, +0.5) | follow。eye (2.5, -2.5, 2.0) |
| 10 | 歩きながら旋回 | P0 で採用 | flat、3 体、タイル 16 m | (0.3, 0, +0.4) | world。円が全部入る固定の俯瞰（対象ロボットの初期位置の上、高さ 6 m 程度）|
- 03 の注（カニ歩き）: URDF を直す前（2026-09-16 より前、旧機体）の run の動画が欲しい。
  1. まず、2026-09-16 より前の run フォルダの videos\ と、tools\ 以下に、既存の mp4 があるか探す。あれば一覧（パス・日時・長さ）を報告し、
     一番それらしいものを 03 としてコピーする（撮り直さない）。
  2. 無ければ、旧機体の USD が今も残っていて、その run の params\env.yaml が指している asset で再生できる場合に限り、それで撮る。
     今の機体の USD に旧 run の重みを載せて撮るのは禁止（別のロボットになるので「直す前」の証拠にならない）。
  3. どちらも無理なら、今の機体で横流れが最も大きかった 2026-09-16_13-40-10_E_yawcmd の model_1999 を (0.4, 0, 0) で撮り、
     報告で「URDF 修正後でも残った軽いカニ歩き（直す前の映像ではない）」と明記する。横速度と向きのずれの数値も添える。
- 01 について: これは学習そのものの録画ではなく、学習途中の保存点を 4096 体で再生したもの。報告の表にそう書く。
  4096 体で描画が重すぎて落ちる・極端に遅いときは 1024 体（32×32）に下げて、そう書く。

## 報告（これで止まる）
1. 冒頭3行: 撮れた場面／撮れなかった場面、足首に合格した候補（無ければ「無し、B@25000 で撮った」）、動画フォルダ。
2. 実際の関節の可動域（env から読んだ値。全関節 ±180° のままか）。
3. P0 の表: 候補 × 場面 × 転倒率・前進速度または yaw 速度・横速度・向きのずれ・FFE（左右）の 5 %/95 %/最大・足首の合否。
   基準（H@2999）の行を先頭に置く。
4. P1 の表: 番号 × ファイル名 × run@ckpt × 条件 × 数値。03 はどの方法（既存の動画／旧 USD／E_yawcmd）で用意したか。
5. 撮り直し用の起動行（場面ごとに PowerShell の1行、実名入り、山括弧なし。--load_run・--checkpoint・--cmd・--terrain・
   カメラ引数を差し替えるだけで撮れる形）。
6. record_fixed_cmd.py の .bak との diff。
```
