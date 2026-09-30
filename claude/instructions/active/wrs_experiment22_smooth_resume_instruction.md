# WRS 実験22: X21a・X21b を、動きをなめらかにする罰を強めて再開する2本（X22a・X22b）

作成 2026-09-30 14:00。X21a_ref_upright・X21b_ref_hpose は約 1200 iter で、まっすぐ歩けるが動きがかくかくしていた（本人の目視）。本人がどちらも止めた。
コードは変えない。起動行の Hydra の上書きだけで、次の2つを 10 倍にする。
- `action_rate_l2`: −0.01 → **−0.1**（前の step との行動の差²）
- `joint_acc_l2`: −2.5e-8 → **−2.5e-7**（関節の加速度²）

他の報酬（参照の振り足 2.0 など）は X21 のまま。2本とも、それぞれの親の最新の checkpoint から同じ設定で再開する。
判定: 再開から +300 iter と +600 iter で、vx 0.3 固定の再生と動画を見る。
- かくかくが減って、歩き続けている → 当たり。その姿勢の方を送信器へ。
- 歩かなくなった（立往生） → 罰が強すぎ。action_rate −0.05 で同じ親からやり直す（起動行の数字を変えるだけ）。
終わったらこのファイルを `../inactive/` へ移す。

## CLI に渡すもの

```
# 依頼: 実験22。X21 の2本を、なめらかさの罰を強めて再開する。確認して、学習・再生・動画のコマンドを渡して止まる

## このプロンプトの前提
- このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。
- 長時間の学習をバックグラウンドで回さない。やってよいのは下の S0〜S2（各数分）だけ。本番の学習・再生・動画は
  ユーザーが別々の PowerShell で前景実行する。
- **コードも cfg も変えない。** 条件は起動行の Hydra の上書きだけで作る。何も削除しない。pip しない。git の commit・push をしない。
  動いている学習のプロセスを止めない（ユーザーが止める）。
- 推測で直さない。上書きのキー名が違う・効かないときは、Isaac Lab のソースと env.yaml を見て同じ意味の書き方に直すのはよい。
  直した箇所は報告。コードの変更が要るなら止まって報告。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\（run フォルダ）
- 学習・再生は train.py / play.py を直接呼ぶ。起動行の形（_preload_h5py_and_run.py 経由、conda activate、
  OMNI_KIT_ACCEPT_EULA、agent.policy.noise_std_type=log）は tools\logs\run_X18h_bold_from_c.txt の先頭と同じ。
  これは resume の例でもある（--resume、--load_run、--checkpoint）。
- タスク: X21a は Skyentific-Poclegs-GaitRef-v0（再生は GaitRef-Play-v0）、X21b は Skyentific-Poclegs-GaitRefH-v0（GaitRefH-Play-v0）。
  どちらも観測 44 次元。
- GPU は RTX 3090 Ti が1枚。

## S0 親を確かめる
- run フォルダ名が *_X21a_ref_upright と *_X21b_ref_hpose のもの（複数あれば一番新しい）を探し、それぞれ保存されている
  model_*.pt の最大番号を親の checkpoint とする。フォルダ名・checkpoint・最終更新時刻を報告。
- 学習プロセスがまだ動いていて checkpoint が増え続けているなら、止まって「ユーザーが止めてから」と報告。
- TensorBoard のイベントファイルを読み（tensorboard の EventAccumulator）、各親の最後の iter で
  Episode_Reward/action_rate_l2、joint_acc_l2、ref_joint_pos、track_lin_vel_xy_exp、gait_contact と
  Train/mean_episode_length を表に（再開後と比べるための基準）。

## S1 スモーク（各 64 env・5 iter、親から resume）
- run名 TEST_X22a（GaitRef-v0、親 X21a）・TEST_X22b（GaitRefH-v0、親 X21b）。起動行に次の上書きを付ける:
  env.rewards.action_rate_l2.weight=-0.1 env.rewards.joint_acc_l2.weight=-2.5e-07
- 確かめて表に: checkpoint を読めたログの行、iter 番号が親の続きから始まるか、env.yaml の action_rate_l2 が −0.1・
  joint_acc_l2 が −2.5e-07、ref_joint_pos 2.0 と gait_contact 2.0 が残っていること、観測 44。
- TEST_ run は消さない。

## S2 再生・動画の起動行を試す
- TEST_X22a の最後の checkpoint で、報告 4・5 の形のコマンドを短く（動画は --video_length 100）1回ずつ走らせ、
  指令の固定（vx 0.3）が効くか・mp4 がどこにできるかを確かめる。

## 報告（これで止まる。短く）
1. 冒頭3行: 親の checkpoint 2つ、S1・S2 の合否、進めてよいか。
2. S0 の表（基準の値）、S1 の表、直した書き方。
3. **ユーザーが前景で打つ学習コマンド2本**（別々の PowerShell、train.py を直接、親から resume、seed 1、num_envs 4096、
   max_iterations 2000（再開からの追加分）、save_interval 100、noise_std_type=log、entropy_coef 0.005、--device cuda:0、
   上の2つの上書き）。run名 X22a_smooth_upright（親 X21a）/ X22b_smooth_hpose（親 X21b）。先頭に nvidia-smi の1行。
   「1本目を起動して 1〜2 iter 進んだら nvidia-smi で空きを見て、学習1本分より多ければ2本目を起動」と書き添える。
   実行フォルダ付き・プレースホルダ無し・改行なしの1行版。
4. **再生コマンド2本**（GaitRef-Play-v0 / GaitRefH-Play-v0、X22 の run フォルダ、checkpoint のファイル名だけ差し替えればよい形。
   例は「親の番号 + 300」の model。指令を固定: env.commands.base_velocity.ranges.lin_vel_x=[0.3,0.3]、lin_vel_y=[0.0,0.0]、
   ang_vel_z=[0.0,0.0]、heading_command=false、rel_standing_envs=0.0）。
   あわせて**比較用に親（X21a・X21b の最後の checkpoint）を同じ条件で再生するコマンド2本**。
5. **動画コマンド2本**（4 と同じ指令、--video --video_length 500 --headless、--num_envs 4、例は「親の番号 + 600」）と、
   mp4 ができるフォルダの絶対パス。
6. 見る値: Episode_Reward/action_rate_l2 と joint_acc_l2 は 0 に近づく（絶対値が小さくなる）、ref_joint_pos と
   track_lin_vel_xy_exp は親の値から大きく下がらない、Train/mean_episode_length が下がらない。
   track_lin_vel_xy_exp が親の半分以下に落ち続けたら立往生の兆し、と書き添える。
```
