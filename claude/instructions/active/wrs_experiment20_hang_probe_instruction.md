# WRS 実験20 続き4: シーン作成で止まる場所を特定する（2026-09-30）

作成 2026-09-30。前提は `wrs_experiment20_gait_clock_instruction.md`（X20 本体と「続き」〜「続き3」）。
2026-09-27 05:55、地面を生成器に替えた後の S1（GaitFull-Play-v0）が 2 時間以上シーン作成から進まず、CLI が停止した。
同じ大きさの生成器（10×20、0.1 m）は rough の学習で何度も普通に作れているので、「タイル生成が重い」ではなく
別の場所（Nucleus の読み込み待ちなど）で止まっていると見ている。**下のブロックを新しい CLI チャットにそのまま貼る。**
終わったら、このファイルと X20 本体の指示書を `../inactive/` へ移すかどうかを、結果を見て決める。

```
# 依頼: 実験20 続き4。X20 の環境作成が止まる場所を特定する（直すのは条件つき）

## このプロンプトの前提
- このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。
- 1 回の起動は最長 3 分で打ち切る（下の見張りを必ず付ける）。学習をバックグラウンドで回さない。
- pip で何も入れない。git の commit・push はしない。Nucleus・Kit・Isaac Sim の設定ファイルは触らない。
  ファイルを削除しない（自分が作った診断用スクリプトとログは残してよい）。
- stand_env_cfg.py はハードリンク（D:\Tominaga\slope-climbing-robot\my_robot_code\stand_env_cfg.py と、
  references\ 以下の config\skyentific_poclegs\stand_env_cfg.py）。**Edit ツールで書き換えない**（2026-09-27 に
  それでリンクが切れた）。書き換えるときは python で open(path, "r+") → seek(0)・write・truncate。
  先に .bak_20260930_hangprobe を取り、書いたあと `fsutil hardlink list` で2つのパスが両方出ることを確かめる。
- 推測で直さない。直してよいのは下の「直してよい条件」に当てはまるときだけ。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、
  python D:\Tominaga\envs\isaac_env\python.exe、GPU RTX 3090 Ti 1 枚。
- 起動行の形は tools\logs\run_X18h_bold_from_c.txt の先頭と同じ（_preload_h5py_and_run.py 経由、conda activate、
  OMNI_KIT_ACCEPT_EULA）。再生は D:\Tominaga\IsaacLab の scripts\reinforcement_learning\rsl_rl\play.py、
  学習は同じ場所の train.py。
- X20 のタスク: Skyentific-Poclegs-GaitFull-v0 / -GaitFull-Play-v0 / -GaitMod-v0 / -GaitMod-Play-v0
  （stand_env_cfg.py 末尾の「X20」節、__init__.py に登録済み）。
- 2026-09-27 に入れた変更（_X20BaseEnvCfg の __post_init__）: 地面を terrain_type="generator"
  （MeshPlaneTerrainCfg だけ、10×20、size 8×8、border 20、use_cache=False）、visual_material を
  PreviewSurfaceCfg、sky_light の texture_file を None、commands.base_velocity.debug_vis=False。
  理由: plane が Nucleus（S3）の Grid/default_environment.usd を開けなくなった（9/25 までは動いた）。
  その後、矢印 Props/UIElements/arrow_x.usd も Nucleus で落ちた。

## P0 状態の確認（起動しない）
1. 動いたままの python.exe / kit.exe が残っていないか（Get-CimInstance Win32_Process で CommandLine も）。
   コマンドラインに play.py・train.py と GaitFull・GaitMod・X20 を含むものが残っていれば、PID と
   CommandLine を記録してから Stop-Process する。それ以外のプロセスは止めない。nvidia-smi の1行を記録。
2. `fsutil hardlink list` で stand_env_cfg.py の2つのパスが出るか。X20 節と上の 2026-09-27 の変更が入っているか
   （該当行を行番号つきで引用）。
3. Nucleus の到達: Test-NetConnection omniverse-content-production.s3-us-west-2.amazonaws.com -Port 443 と、
   Invoke-WebRequest -Method Head で「isaaclab.utils.assets の ISAAC_NUCLEUS_DIR を python で print した値」＋
   /Environments/Grid/default_environment.usd の結果（URL そのもの、ステータス、かかった時間）。URL を手で組み立てない。プロキシの環境変数（HTTP_PROXY・HTTPS_PROXY・NO_PROXY）の有無。

## P1 見張りつきで起動する仕組み
tools\runs\_hang_probe.py を新しく作る（既存ファイルは変えない）。中身:
- faulthandler.dump_traceback_later(60, repeat=True, file=ログ) で 60 秒ごとに全スレッドの Python スタックを
  tools\logs\hangprobe_<名前>_<時刻>.txt に書く。
- 残りの引数をそのまま _preload_h5py_and_run.py に渡して runpy で実行する（起動の形を変えない）。
PowerShell 側は Start-Process で起動し、180 秒で終わっていなければ Stop-Process -Force（子の kit.exe も）。
各起動の標準出力・標準エラーもファイルに残す。あわせて、その回の Kit のログ（Isaac Sim のログフォルダで
いちばん新しい kit_*.log）の最後の 60 行を保存する。

## P2 切り分け（全部 --headless、--num_envs 16、play.py、checkpoint なしで作れるなら作るところまで）
play.py が checkpoint を要求して止まるなら、代わりに scripts\environments\zero_agent.py（無ければ
random_agent.py）で同じタスクを起動する。どちらを使ったか報告する。
- R1: Skyentific-Poclegs-GaitFull-Play-v0（止まる本体）。
- R2: rough の既存タスク（_train_foreground.ps1 が使っているタスク名）。9/27 以前に普通に作れていたもの。
- R3: R1 に Hydra の上書きで地面の生成器を最小にしたもの:
  env.scene.terrain.terrain_generator.num_rows=1 env.scene.terrain.terrain_generator.num_cols=1
  env.scene.terrain.terrain_generator.border_width=5.0
  （上書きが通らないなら、そう報告して飛ばす）。
- R4: R1 に --kit_args で Nucleus を切った起動が作れるなら試す（Isaac Sim 5.1 のソースで該当する設定名を確かめて
  から。見つからなければ飛ばす。推測の設定名を入れない）。
各回について表に: 起動から「シーン作成が終わった」（最初の step、または env の観測の形が出る）までの秒数、
止まった場合は最後の Python スタックのいちばん深い isaaclab / omni / pxr のフレーム（ファイル:行・関数名）と、
Kit ログの最後の意味のある行（URL・http・timeout・Downloading・Resolving を含む行は全部）。

## 直してよい条件
- 止まっている場所が、見た目だけのアセット（素材・スカイ・マーカー・矢印・テクスチャ・MDL）の Nucleus URL の
  読み込みだと、スタックかログで特定できたときだけ、_X20BaseEnvCfg の __post_init__ でその項目を
  無効にしてよい（上の書き換え方で）。直したら R1 をもう一度見張りつきで起動し、作れることを確かめる。
- 物理に関わる項目（地面の形・摩擦・ロボットの USD・接触センサー）や、原因が1か所に決まらないときは直さずに止まる。
- 原因が X20 に限らず R2 でも止まるなら、直さずに止まる（H などの古いタスクも同じ影響を受けるため、本人が判断する）。

## 作れたら（直した場合も、最初から作れた場合も）: 前回の S1・S2 の続き
- S1（GaitFull-Play-v0、16 env、行動 0、押しなし）: リセット直後の ll_ffe・lr_ffe のボディ原点の z の中央値を
  FOOT_Z_STAND として mm で丸め、stand_env_cfg.py の FOOT_Z_STAND = 0.075 を書き換える（上の書き換え方で）。
  FEET_ORDERED・FEET_BODIES_ORDERED の body_ids が ["ll_ffe", "lr_ffe"] の順か（センサー側・ロボット側）。
  50 step 回して gait_contact_match・flight_phase・swing_clearance_deficit・feet_air_time_single・
  stand_still_pose が NaN を出さず、contact_match が 0〜1。
- S2（各 64 env・10 iter、ゼロから、train.py）: TEST_X20a（GaitFull-v0、観測 44 次元＝最後の2つが時計の sin・cos）、
  TEST_X20b（GaitMod-v0、観測 42 次元）。env.yaml の地面が generator・flat のみであることと、新しい報酬の項目が
  ログに出ることを確かめる。TEST_ run は消さない。

## 報告（これで止まる）
1. 冒頭3行: 止まっていた場所（ファイル:行・関数名、または URL）、それを示す根拠（スタック／Kit ログの行）、
   直したか・直していないか（直していない場合は候補の直し方を1つ）。
2. P0 の結果、P2 の表、変えたファイル（.bak の名前、fsutil の結果）。
3. 作れた場合だけ: S1 の FOOT_Z_STAND と足の順、S2 の合否（観測 44 / 42）、
   **ユーザーが前景で打つ学習コマンド2本**（別々の PowerShell、train.py を直接、ゼロから、seed 1、num_envs 4096、
   max_iterations 3000、save_interval 100、agent.policy.noise_std_type=log、entropy_coef 0.005、--device cuda:0、
   run名 X20a_gait_full / X20b_gait_mod）。先頭に nvidia-smi の1行と「1本目が 1〜2 iter 進んだら nvidia-smi で
   空きを見て、学習1本分より多ければ2本目を起動」。実行フォルダつき・プレースホルダなし・改行なしの1行版。
   再生コマンド2本（GaitFull-Play-v0 / GaitMod-Play-v0、checkpoint 名 model_500.pt を差し替えるだけの形）。
```
