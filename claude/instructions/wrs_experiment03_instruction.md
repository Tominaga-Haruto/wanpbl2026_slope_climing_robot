# 指示書 実験03: 実機準拠アクチュエータで平地を一から学習＋デプロイ準備（WRS機・新しいチャット）

> 作成 2026-09-16 15時、**改訂 2026-09-16 夕（実験02 停止点2の結果とユーザー決定を反映）**。**WRS機の Claude Code を新しいチャットにして、①`instructions/wrs_training_operator_instruction.md` の全文 → §8 の確認が終わったら ②下のコードブロック、の順に貼る。**
> 背景: ゴールを「平地」に変更（坂は後回し）。AK80-9 の実機トルクを超えた設定（effort 20〜30 N·m）で学習した方策はデプロイに使えないので、実機準拠のアクチュエータで一から学習し直す。根拠は `reference/actuator_params.md`、経緯は `chats/2026-09-16_goal-flat-real-actuator.md` と `chats/2026-09-16_exp03-criteria-and-turning.md`。
> **改訂点:** ①デプロイの合格基準（トルク: S1 で RMS ≤ 定格・最大 ≤ ピーク、飽和率と切る前トルクを併記／旋回: 小旋回 S7・S8 で判定）を追加 ②P0 を実験02完了後の内容に ③P1-3 に S7〜S9 と computed torque・S3（立ち）④P1-4 に左右対称性 ⑤P1-5 旋回が出ない件の材料（報酬実効値・heading モードの指令分布・罰と取り分の比）⑥P3 で並走の実測（プロセスごと VRAM・RAM・CPU）⑦play の起動行を報告させる ⑧占有見込みを約5時間に。⑨（REPORT_exp02_stop2.md 本文を読んで追記）P1-4 に足裏接地の時間変化、左右対称性は参考扱いに（S1 yaw の符号がランで違う）、P1-5 に E の error_vel_yaw がほぼ改善しなかった件。

```
# 指示: 実験03 実機準拠アクチュエータで平地を一から学習 ＋ デプロイ準備

最初に貼った指示書（instructions/wrs_training_operator_instruction.md）の掟・作法はすべて有効。ただし §3〜§6 の一部は古いので、下の「更新」を優先すること。
ユーザーは今日このあと約5時間、この GPU を学習で占有することを了承済み。開始時に nvidia-smi で他人の計算プロセスがあれば、何も起動せず報告して止まる。

## 更新（指示書 instructions/wrs_training_operator_instruction.md から変わったこと）
- 最新コミットは 6c80638（評価スクリプト・weight 0 の feet_air_time_biped 項など）。コードは 08-21 版ではない。
- 学習・評価の起動には環境変数 OMNI_KIT_ACCEPT_EULA=YES が要る。起動スクリプトの雛形は tools\\runs\\_launch.ps1 と tools\\runs\\_eval.ps1。
- terrain_type=plane は使えない（S3 の既定 USD を取りに行って落ちる）。平地は sub_terrains の proportion を flat=1.0・他 0.0 に上書きして作る。
- 学習ログの error_vel_xy / error_vel_yaw はエピソード長に比例する。比べるときは 正規化値 = 生値 × 500 / Train/mean_episode_length（tools\\tb_norm_error.py）。「0.3 以下＝歩けている」の目安は使わない。
- 評価は tools\\measure_crab.py（平地・固定指令・64 env・2 s 捨てて 10 s）。カニ歩き・立ち往生・転倒の判定基準は tools\\logs\\REPORT_exp01_final.md と同じ。
- これまでの経緯は tools\\logs\\ の REPORT_exp01_final.md / REPORT_ablation.md / REPORT_exp02_stop1.md / REPORT_exp02_stop2.md / P3a_stiffness.md / stance_check.md / P1_findings.md にある。最初に目を通すこと。
- 実験02 は完了済み（E_yawcmd 2000、F_BtoRough +1500。GPU は空いている）。
- ゴールは平地（坂は後回し）。目的は「実機に載せられる方策」。

## デプロイの合格基準（ユーザー決定 2026-09-16。あなたが変えないこと。境界付近は数値をそのまま出す）
- トルク: S1 で関節ごとに RMS ≤ 定格（AK10-9 = 18、AK80-9 = 9 N·m）、かつ最大 ≤ ピーク（AK10-9 = 53、AK80-9 = 18 N·m ＝MIT 上限）。
  注意: シムの applied torque は effort_limit で切られるので「最大 ≤ ピーク」は自動で満たされる。だから飽和率（applied が effort_limit の 95% 以上の時間割合）と、切る前の computed torque の p95・最大も必ず併記する。
- 旋回: 大きな旋回は不要、小さな旋回でよい。ただし実機で向きを保つには小さな yaw 指令に従う必要がある。
  S7 (0.5, 0, +0.3) と S8 (0.5, 0, −0.3) で、yaw rate 平均の符号が指令と同じ、かつ |yaw rate 平均| ≥ 0.15 rad/s、かつ S7 と S8 の大きさの比が 0.5〜2 なら「小旋回 合格」。S1 の |yaw rate| ≤ 0.10 は既存の基準のまま。

## P0 引き継ぎ確認（読むだけ）
1. git log -3 --format=\"%h %ad %s\" --date=iso と git status --short。
2. 学習プロセスが残っていないこと（nvidia-smi）。
3. REPORT_exp02_stop2.md から E_yawcmd の S6 と F_BtoRough の S1 yaw rate の結論を1行ずつ報告に書く。

## P1 デプロイ準備（GPU は短時間・64 env 以下。学習コードは変えない）
1. 方策の書き出し: play.py を B_combined の model_2999.pt で headless・動画なしで起動し、run フォルダの exported\\ に policy.pt と policy.onnx ができるか確認（できたらすぐ閉じてよい）。ファイルサイズと時刻。onnxruntime か onnx が isaac_env に既に入っていれば入出力の形を表示（無ければ入れない。報告だけ）。
   通った play の起動行を、動画なし版と動画あり版（--video --video_length 500、16 env）の2本、実名を埋めた PowerShell の1行で報告に書く（ユーザーが自分で見るため。動画あり版は実行しなくてよい）。
2. 観測・行動の契約を書き出す（新規 tools\\dump_contract.py → tools\\logs\\obs_contract.md）。env を 1〜4 env で作って、実物の manager から:
   - sim.dt、decimation、制御周期 [Hz]
   - policy 観測の項の順番、各項の次元・scale・clip・学習時ノイズ、関節系の項が使う関節名の並び、合計次元
   - action 項: 関節名の並び、scale、offset（＝既定関節角の値）、clip
   - 既定関節角（init_state.joint_pos）の値を関節名つきで
   - velocity_commands 項の中身（lin_vel_x, lin_vel_y, ang_vel_z の順か、heading かどうか）
   - 指令の設定: ranges（lin_vel_x / lin_vel_y / ang_vel_z / heading）、heading_command、heading_control_stiffness、rel_heading_envs、rel_standing_envs、resampling_time_range
3. measure_crab.py の拡張（評価スクリプトの変更なので可。既存の指標と S1〜S6 は変えない）:
   - シナリオ追加: S7 (0.5, 0, +0.3) / S8 (0.5, 0, −0.3) / S9 (0, 0, −0.5)
   - 関節ごとの指標: |applied torque| の p95・最大・10 s の RMS、|computed torque|（effort_limit で切る前）の p95・最大、飽和率（applied ≥ effort_limit の 95%）、|関節速度| の p95・最大
   - B_combined の 2999 で S1〜S9 を一度走らせる。関節（HR/HAA/HFE/KFE/FFE、左右平均と左右の大きい方）ごとに、S1 / S2 / S3（立ち）の表を、実機値（定格・ピーク・MIT 上限・無負荷速度）の列と並べて作る（B は旧アクチュエータ設定。どれだけ実機を超えていたかの記録）。
   実機値: AK10-9（HR・HAA・KFE）定格 18 / ピーク 53 / MIT トルク上限 54 N·m、無負荷 33.5 rad/s。AK80-9（HFE・FFE）定格 9 / ピーク 22 / MIT トルク上限 18 N·m、無負荷 59.7 rad/s。
4. 立っていられない件の続き（stance_check.py、action 0。P3a で stiffness 4 倍でも倒れることは確認済み）。まず、この試験で reset_robot_joints（関節角 0.5〜1.5 倍）・reset_base の速度ランダム化・push が本当に切れているかを cfg で確認して報告。そのうえで:
   - 関節をほぼ固定（全グループ stiffness 1000 / damping 50）: それでも前に倒れるなら、関節ではなく形状・接地・重心の問題
   - 足の衝突形状の種類（convex hull / 三角メッシュ / 近似の種類）と、初期姿勢で地面に接している点の数と x 範囲
   - 足裏の接地の時間変化: 0 / 0.1 / 0.5 s で、左右の足それぞれの接触点の数・x 範囲・法線力の合計と、base 高さ（P3a で 0.3758 → 0.3613 m と 1.45 cm 沈んでいる）。COM は支持多角形の前端から 6.6 cm 内側なのに倒れるので、「足裏が線や点でしか接地していない」「沈み込みで姿勢が変わる」のどちらかを数値で切り分ける
   - 左右の対称性（参考）: 左右の対応リンクごとの質量と COM（base 座標、y は符号を反転して比較）、全身 COM の y。S1 の yaw rate は B +0.021 / E −0.023 / F +0.324 とランで符号が違うので、方策側の要因が主の可能性が高い。機体の左右差が無いことの確認として出すだけでよい
   これは診断だけ。学習 cfg は変えない。
5. 旋回が出ない件の材料（読むだけ・短時間。学習 cfg は変えない）:
   - 報酬: track_ang_vel_z_exp の weight・std、track_lin_vel_xy_exp の weight・std、joint_deviation_hip の対象関節（.*HR が入っているか）と weight、そのほか HR の動きを罰する項があれば全部（rough_env_cfg.py の __post_init__ の上書き後の実効値で）
   - 指令の分布: 64 env 以下で env を作り、学習時と同じ指令 cfg で rel_heading_envs=1.0 と 0.5 のそれぞれについて、env を進めて（action 0 でよい、200 step）ang_vel_z 指令を記録し、|ang_vel_z 指令| > 0.2 rad/s の割合と平均 |ang_vel_z 指令| を出す。heading モードで yaw 指令が実際にどれだけ出ていたかを数値で確かめるため
   - HR を 0.1 rad 振ったときに joint_deviation_hip が 1 step あたりいくら罰になるか、yaw 0.3 rad/s を完全に追従したときの track_ang_vel_z_exp の 1 step あたりの取り分との比（計算だけ）
   - 参考: E_yawcmd は旋回指令を半分の env に入れても正規化 error_vel_yaw が 0.313 → 0.298 しか下がっていない（REPORT_exp02_stop2.md 2-3）。指令が出ていても yaw の追従が学習上ほとんど得にならない、という読みと矛盾しないかを上の数値で確かめる

## P2 アクチュエータを実機準拠にする（my_robot_code\\skyentific_poclegs.py）
- .bak_real_actuator を取ってから、open(r+) 方式で actuators を関節ごとの5グループに組み直す。DelayedPDActuatorCfg・delay・stiffness・damping・velocity_limit は今の値のまま（変えるのは下の表の列だけ）。
  | グループ | 関節 | 機種 | effort_limit | armature | friction |
  |---|---|---|---|---|---|
  | hr | .*HR | AK10-9 | 53.0 | 8.116e-3 | 0.37 |
  | haa | .*HAA | AK10-9 | 53.0 | 8.116e-3 | 0.37 |
  | hfe | .*HFE | AK80-9 | 18.0 | 9.77e-3 | 0.22 |
  | kfe | .*KFE | AK10-9 | 53.0 | 8.116e-3 | 0.37 |
  | ffe | .*FFE | AK80-9 | 18.0 | 9.77e-3 | 0.22 |
  - stiffness は今の値（HFE は旧 kfe グループの値＝15、ほかは各グループの今の値）。damping 1.5。
  - effort_limit の既定は「ピーク（AK10-9 は 53、AK80-9 は MIT のトルク上限 18）」。定格版は起動行の上書きで作る（P3）。
  - 各行にコメントで出どころ（reference/actuator_params.md の §3、AK10-9 の friction 0.37 と armature は未実測の暫定値）を書く。
- diff → ハードリンク5組の Get-FileHash とリンク数。
- 64 env / 20 iter で G_real_peak と G_real_rated の起動行を1本ずつ通す。env 作成後に robot.actuators の各グループの joint_names・effort_limit・armature・friction・stiffness・damping を実際のテンソルから表示して、表どおりか（定格版は上書きが効いているか）確認。
- 通ったら commit（push はしない。measure_crab.py・dump_contract.py・skyentific_poclegs.py などコードだけ）。コミットメッセージ案と、ユーザーが PowerShell で打つ push の1行（実行フォルダ付き）を表示。

## P1・P2 で想定外が無ければ、止まらずに P3 を起動してよい（報告は起動後にまとめて1回）
想定外の例: play.py で exported ができない（→ P3 は進めてよい、報告に書く）、P1-4 / P1-5 が途中で詰まる（→ 30 分で打ち切って P3 へ進んでよい、報告に書く）、アクチュエータのテンソルが表と違う・上書きが効かない（→ 止まって報告）、64 env テストが落ちる（→ 止まって報告）。

## P3 本番（2本同時、4096 env、--max_iterations 3000、--seed 1）
共通: B_combined と同じ（平地＝proportion 方式、noise_std_type=log、feet_air_time_biped w0.25、feet_air_time w0、track_lin_vel_xy_exp の std 0.35）＋ env.commands.base_velocity.rel_heading_envs=0.5。指令レンジ・報酬は既定のまま（旋回の報酬はこの実験では変えない）。一から（--resume なし）。
1. G_real_peak（--run_name G_real_peak）: 上の共通だけ（effort は AK10 53（ピーク）/ AK80 18（MIT 上限））
2. G_real_rated（--run_name G_real_rated）: 共通 ＋ effort_limit を定格に上書き（hr / haa / kfe = 18.0、hfe / ffe = 9.0）
- 起動直後の iter 確認、params\\env.yaml で上書きの反映確認。
- 両方が iter 30 進んだら: 各ランの秒/iter、終了見込み時刻（評価込み）、nvidia-smi --query-compute-apps=pid,used_memory --format=csv のプロセスごと VRAM、GPU 全体の VRAM、ホスト RAM の使用量と総量（Get-CimInstance Win32_OperatingSystem の TotalVisibleMemorySize / FreePhysicalMemory）、論理 CPU 数と CPU 使用率。
- iter 1000 / 1600 / 2400 / 2999 で measure_crab.py（S1〜S9、関節ごとのトルク・速度の指標込み）。
- 監視は今までどおり。どちらかが iter 1600 の評価で S1 静止率 100% でも止めない（C_flatonly は 2400 で歩き出した）。

## 【停止点】両方の 2999 の評価が終わったら報告して止まる
- 冒頭: 2本それぞれ「カニ歩き・立ち往生・転倒・トルク・小旋回」の判定1行（上の基準で機械的に）
- P0 の結論2行、P1 の結果（exported の有無と play の起動行2本、obs_contract.md の要約: 観測の合計次元と並び、制御周期、action の scale と関節順、指令の設定）
- トルク表: B@2999 / G_real_peak@2999 / G_real_rated@2999 を並べる（S1 と S3、関節ごと applied の RMS・p95・最大、computed の p95・最大、飽和率、関節速度 p95・最大、実機値の列つき）
- P1-4 の診断結果、P1-5 の結果（報酬の実効値、指令分布の2条件の数値、罰と取り分の比）
- 評価の表（B@2999 / G_real_peak / G_real_rated × S1〜S9、iter 1000 / 1600 / 2400 / 2999 の S1・S2・S6・S7・S8）
- 正規化 error_vel_xy / error_vel_yaw（500 / 1000 / 1600 / 2400 / 2999）
- 並走の実測（プロセスごと VRAM、ホスト RAM、CPU）
- 所見3行以内、次の候補1〜2個（小旋回が不合格なら、P1-5 の数値に基づく次の一手を1つ。報酬関数の world 版への差し替えは平地では base 版とほぼ同じ値になるので、候補にするなら理由を数値で示す）

## やらないこと
- 報酬・指令レンジ・地形・stiffness / damping は変えない
- push はしない（ユーザーが行う）。何も削除しない
- pip で何かを入れない（onnx / onnxruntime も。無ければ報告だけ）
```

---

## 続き（2026-09-16 夜）: P2 の 64 env テストで train.py が h5py の DLL エラーで停止 → 切り分けの指示

WRS 報告の要点: P1-1〜P1-3 完了（policy.onnx 入力 [1,42]・出力 [1,10]、50 Hz、action scale 0.5、**B@2999 は S7 +0.354 / S8 −0.307 で小旋回合格**）。P2 のコード変更後、train.py だけが `ImportError: DLL load failed while importing _errors`（h5py）で4回とも落ちる。play.py / dump_contract.py は動く。同じ頃ユーザーが別ターミナルで play の動画版を起動していた。`reference/actuator_params.md` はリポジトリ外（Cowork 文書）。

```
# 指示: 実験03 の続き（train.py の h5py クラッシュの切り分け → 通れば P3）

報告ありがとう。回答と次の指示。

## 回答
1. reference/actuator_params.md はリポジトリの外（ユーザーの Cowork プロジェクトの文書）にある。探さなくてよい。コメントの出どころは「reference/actuator_params.md §3（Cowork プロジェクト文書・リポジトリ外）、AK10-9 の friction 0.37 と armature は未実測の暫定値」に書き換えてよい。数値は指示書の値で正しい。
2. ユーザーは、あなたの作業中に別ターミナルで play.py の動画版を起動していた。別プロセスの DLL 読み込みが他のプロセスを直接壊すことは通常ないが、そのとき Kit の拡張やキャッシュが追加・更新された可能性はある。これも疑いに入れて切り分ける。
3. S7 / S8 の結果（B で +0.354 / −0.307）は重要な発見。旋回の優先度は下がったので、P1-5 は「報酬の実効値」と「指令分布」だけでよい（罰と取り分の比の計算は省略可）。

## Q1 h5py クラッシュの切り分け（最大 40 分。pip / conda で何も入れない・消さない・更新しない）
今日 13:40 には E_yawcmd / F_BtoRough の train.py が動いていた。そのあと何が変わったかを調べる。
1. 時系列: 今日 train.py が最後に成功した時刻、最初に h5py で落ちた時刻、ユーザーの play（動画版）の起動・終了時刻（ログ・プロセス・videos フォルダの時刻から分かる範囲で）。
2. 今日変わったもの（読むだけ）:
   - D:\\Tominaga\\envs\\isaac_env の中で、今日 12:00 以降に更新された *.dll / *.pyd / *.dist-info フォルダの一覧（パス・時刻）。特に h5py、hdf5、numpy、onnx、torch、tensordict。
   - conda list --revisions の最後の数件。python -m pip show tensordict と torchaudio の版（既知の落とし穴）。
   - onnx 1.22.0 がいつ入ったか（dist-info の時刻）。
   - isaac_env の isaacsim の extscache と C:\\Users\\WRS\\AppData\\Local\\ov\\data\\exts\\v2\\ で、今日 12:00 以降に作られたフォルダ。
3. 起動方法の差: 今日成功した起動（tools\\runs\\_launch.ps1 と E_yawcmd の ps1。conda activate ＋ isaaclab.bat -p）と、今回落ちた起動（python.exe 直叩き / Bash）で、PATH の中身を比べる。PATH 上にある hdf5*.dll をすべて列挙（where.exe hdf5.dll と Get-ChildItem で isaac_env\\Library\\bin・h5py フォルダ・isaacsim / kit 配下を検索）。
4. 再現テスト（64 env / 20 iter）:
   a. 今日成功したのと同じ起動方法（_launch.ps1 経由、conda activate ＋ isaaclab.bat -p）で、B_combined と同じ上書きの起動行を --run_name TEST_h5py_launch で。skyentific_poclegs.py は P2 の編集後のまま。
   b. a が落ちたら、P2 の編集を一時的に戻して同じ起動: skyentific_poclegs.py.bak_real_actuator の中身を open(r+) 方式で書き戻す → ハッシュとリンク数確認 → 起動 → 結果に関わらず P2 の中身を open(r+) で戻す → ハッシュとリンク数確認。
5. 判断:
   - a が通ったら（原因は起動方法）: 以後は必ず _launch.ps1 方式で起動する。G_real_peak / G_real_rated の 64 env / 20 iter をその方式で通し、アクチュエータのテンソル確認（P2 のとおり）→ commit（push しない）→ 止まらずに P3 を起動してよい。報告は P3 起動後にまとめて1回。
   - a が落ちて b が通ったら: P2 の編集が原因。diff を見て原因の行を特定し、直さずに止まって報告。
   - a も b も落ちたら: Q2 の結果を添えて止まって報告。直す案は書くだけで、実行しない。

## Q2 GPU を使う学習と重ならない範囲で P1-4 / P1-5 を進める
- P1-4 は指示書どおり全部。
- P1-5 は「報酬の実効値」と「指令分布（rel_heading_envs 1.0 / 0.5）」だけ。
- Q1 と同時に GPU を使わない。どちらかが終わってから次へ。
- P3 を起動した場合、P1-4 / P1-5 は P3 と並行して 64 env 以下で行ってよい（VRAM の空き 4 GB 以上のとき）。

## 追加の注意
- 報告の play の起動行について: 動画版は --headless を付けること（TeamViewer 越しは GUI が落ちる）。また Play-v0 タスクは既定だと rough 地形になるので、B（平地で学習）を見るときは sub_terrains の proportion を flat=1.0・他 0.0 に上書きする。上書きを含めた完成形の1行を、次の報告に書き直して載せる。
- P3 を起動する場合、起動時刻と終了見込み時刻（評価込み）を報告の冒頭に書く。

## やらないこと
- 報酬・指令レンジ・地形・stiffness / damping は変えない
- pip / conda で入れる・消す・更新するを一切しない
- Isaac Lab 本体、isaacsim、extscache のファイルを変更しない
- push はしない。何も削除しない
```
