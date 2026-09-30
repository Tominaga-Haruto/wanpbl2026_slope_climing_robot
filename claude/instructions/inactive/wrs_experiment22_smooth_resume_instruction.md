# WRS 実験22: X21 の2本を「なめらかさ強め・参照の振り足弱め」で再開＋動画を何度でも撮れる再生スクリプト

作成 2026-09-30 14:50（14:00 版を差し替え。CLI には未投入だった）。**新しい CLI チャットに「CLI に渡すもの」のブロックだけを貼る。**
X21a_ref_upright は 2100 iter、X21b_ref_hpose は 2000 iter で止めた（本人）。本人の目視:
- X21a: 前へ歩くが、胴が上下に弾む。
- X21b: 上下動はほぼ無いが、振り足を「一度空中で止めて、もう一度前へ出す」二段階で出す。
- 動画（mp4）は速くかくかく、再生の画面ではゆっくりに見える。→ 画面の再生は実時間より遅く描いているだけで、方策の速さは同じ（推定）。
  mp4 は 50 fps の実時間。

見立て: 参照の振り足（X21 の ref_joint_pos）は、足をその場で真上に上げ下げする形で、前へ運ぶ成分が無い
（順運動学で前後の移動 0 mm）。方策は「参照どおり真上に上げる → 前へ出す」を別々にやるので二段階になる（推定）。
歩き方はもう覚えたので、参照の重みを 2.0 → 0.5 に下げて、自分で前へ運ぶ余地を与える。あわせて、なめらかさの罰を 10 倍。
- action_rate_l2: −0.01 → −0.1、joint_acc_l2: −2.5e-8 → −2.5e-7、ref_joint_pos: 2.0 → 0.5
- 2本とも、それぞれの親の最後の checkpoint から、同じ上書きで 2000 iter 追加。
判定は再開から +300 / +600 iter。歩かなくなったら action_rate −0.05 で同じ親からやり直す。

## CLI に渡すもの

```
# 依頼: 実験22。X21 の2本を報酬の上書きで再開する学習コマンドを渡し、そのあと動画を何度でも撮れる再生スクリプトを作る

## このプロンプトの前提
- 新しいチャット。このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。
- 長時間の学習をバックグラウンドで回さない。本番の学習はユーザーが別々の PowerShell で前景実行する。
- **既存のコード・cfg・play.py を変えない。** 学習の条件は起動行の Hydra の上書きだけ。新しく作ってよいのは
  tools\runs\x22_video.py だけ。何も削除しない。pip しない。git の commit・push をしない。動いている学習を止めない。
- 推測で直さない。上書きのキー名・API 名が違うときは Isaac Lab のソースと env.yaml を見て同じ意味に直すのはよい（報告に書く）。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\（run フォルダ）
- 学習・再生は train.py / play.py を直接呼ぶ。起動行の形（_preload_h5py_and_run.py 経由、conda activate、
  OMNI_KIT_ACCEPT_EULA、agent.policy.noise_std_type=log）は tools\logs\run_X18h_bold_from_c.txt の先頭と同じ。
  これは resume の例でもある（--resume、--load_run、--checkpoint）。
- タスク: X21a は Skyentific-Poclegs-GaitRef-v0（再生用 GaitRef-Play-v0）、X21b は Skyentific-Poclegs-GaitRefH-v0（GaitRefH-Play-v0）。
  観測は 44 次元（最後の2つが 0.7 s 周期の時計の sin・cos）。制御は 50 Hz（step_dt 0.02 s）。
- GPU は RTX 3090 Ti が1枚。

## S0 親を確かめる（数分）
- run フォルダ名が *_X21a_ref_upright・*_X21b_ref_hpose（複数あれば一番新しい）の model_*.pt の最大番号を親の checkpoint とする
  （2100 と 2000 のはず）。学習プロセスがまだ checkpoint を書いていたら止まって報告。
- TensorBoard（EventAccumulator）で各親の最後の iter の Episode_Reward/action_rate_l2・joint_acc_l2・ref_joint_pos・
  track_lin_vel_xy_exp・gait_contact・lin_vel_z_l2 と Train/mean_episode_length を表に（再開後との比較の基準）。

## S1 スモーク（各 64 env・5 iter、親から resume）
- run名 TEST_X22a（GaitRef-v0、親 X21a）・TEST_X22b（GaitRefH-v0、親 X21b）。上書き:
  env.rewards.action_rate_l2.weight=-0.1 env.rewards.joint_acc_l2.weight=-2.5e-07 env.rewards.ref_joint_pos.weight=0.5
- 確かめる: checkpoint を読めたログの行、iter が親の続きから始まる、env.yaml に上の3つの値、gait_contact 2.0 が残っている、観測 44。
- **合格したら、ここで学習コマンドを先に出す**（ユーザーがすぐ起動できるように）。そのあと S2 に進む:
  別々の PowerShell、train.py を直接、親から resume、seed 1、num_envs 4096、max_iterations 2000（追加分）、save_interval 100、
  noise_std_type=log、entropy_coef 0.005、--device cuda:0、上の3つの上書き。run名 X22a_smooth_upright / X22b_smooth_hpose。
  先頭に nvidia-smi の1行と「1本目の 1〜2 iter 後に nvidia-smi で空きを見て2本目」。実行フォルダ付き・プレースホルダ無し・1行版。

## S2 動画スクリプト tools\runs\x22_video.py（学習と並行でよい。1 env だけ使う）
play.py を手本に、次を満たす再生スクリプトを新規に書く（play.py 自体は変えない）:
- 引数: --task（Play の方）、--run（run フォルダ名、部分一致可）、--checkpoint（model_XXXX.pt）、--mode stand_walk|random、
  --vx（stand_walk 用、既定 0.3）、--seconds（既定 12）、--seed（既定 0）、--headless、--video（付けると mp4 を撮る）。
- num_envs 1。カメラは env 0 のロボットを追う（cfg の viewer.env_index を 0 にする）。押し・外乱なし。
- 速度指令は毎 step スクリプトが直接書く（指令の自動の再抽選と heading 制御は止める）:
  - stand_walk: 最初の 2 s は 0（立って止まっている所から映る）、そのあと vx・vy 0・wz 0。
  - random: 3 s ごとに学習と同じ範囲（vx −0.2〜0.6、vy ±0.1、wz ±0.3）から --seed で抽選。いつ何を出したかをログに残す。
- 時計の観測はエピソードの経過時間から出るので、リセットは最初の1回だけにする（途中で転んだらそこで終了してよい）。
- **上書きしない保存**: 出力フォルダ（run フォルダ）\videos\x22\ に、
  <checkpoint>_<mode>_vx<vx>_seed<seed>_<YYYYMMDD_HHMMSS>.mp4 と同じ名前の .csv を作る。
- csv に毎 step: 時刻、指令 vx/vy/wz、胴の x/y/z と前後・左右の速度と yaw 角速度、両足の接地（0/1）、両足の足首の点の x/z、
  10 関節の角度、行動。
- 終わったら要約を表示: 胴の z の振れ幅（p95−p5、mm）、1 秒あたりの歩数、指令ありの区間の平均の前後・左右の速度と yaw 角速度、
  両足同時に浮いた時間の割合、**振り足の前後の速さが振りの途中でいったん 0 付近（< 0.05 m/s）に落ちた回数の割合**
  （二段階の足の出し方の指標）、転倒したか。
- 動作確認: 親 X21a（2100）と X21b（2000）で stand_walk と random（seed 0）を各1回、--video 付きで撮る。
  要約の表を出す（これが X22 と比べる基準になる）。

## 報告（これで止まる。短く）
1. 冒頭3行: 親の checkpoint、S1 の合否（学習コマンドは S1 の直後に出したものを再掲）、S2 の要約の比較（X21a と X21b の
   胴の z の振れ幅と二段階の割合）。
2. S0・S1・S2 の表、直した書き方、新しく作ったファイル。
3. **動画・再生のコマンド**（x22_video.py を使う。実行フォルダ付き・1行版）:
   - X22a / X22b の stand_walk（vx 0.3、例 model_「親+300」.pt）と random（seed 0、1、2 の3本）。
   - checkpoint の番号・seed・vx を変えるだけで何度でも撮れる形。mp4 と csv ができるフォルダの絶対パス。
   - 画面で見たいとき用に --video と --headless を外した形も1本。
4. 学習中に見る値: action_rate_l2・joint_acc_l2 は 0 に近づく、track_lin_vel_xy_exp と gait_contact は親から大きく下がらない、
   mean_episode_length が下がらない。track_lin_vel_xy_exp が親の半分以下に落ち続けたら立往生の兆し。
```
