# 指示書 実験01: カニ歩き・立ち往生の切り分け（WRS機の Claude Code に貼る）

> 作成 2026-09-16。**WRS機の Claude Code の新チャットで、`instructions/wrs_training_operator_instruction.md` を貼って §8 の確認が終わった後に、下のコードブロックを丸ごと貼る。**
> 設計の根拠は `reference/crab_standstill_countermeasures.md`、ランの記録は `reference/training_runs.md`。

```
# 指示: 実験01 カニ歩き・立ち往生の切り分け（約6時間・GPU占有）

最初に貼った指示書（instructions/wrs_training_operator_instruction.md）の掟と作法はすべて有効。以下はその上での今回の作業。
ユーザーは今から約6時間、この GPU を学習で占有することを了承済み。ただし開始時に nvidia-smi で他人のプロセスが GPU を使っていたら、何も起動せず報告して止まること。

## 目的
- 問い1: base の前後を直した機体で、08-21 設定のままでもカニ歩き・立ち往生は消えるか（ラン A）
- 問い2: 効きそうな対策を複合した設定で消えるか（ラン B）
- A と B を同時に回し、iter 1600 で「固定の評価プロトコル」で判定する。その先の切り分けはユーザーが決める。

## 流れと停止点
P1 読むだけの確認 → P2 準備 → P3 64 env テスト → 【停止点1】 → P4 本番起動 → P5 監視 → 【停止点2: iter 1600】
P1〜P3 は止まらず続けてよい。ただし想定と違うことが出たら、その時点で止まって報告。推測で直さない。

## P1 読むだけの確認（ファイル名と行番号付きの表で）
1. sim.dt / decimation / episode_length_s（自作 rough_env_cfg.py と Isaac Lab の親クラスの両方）
2. actions の scale と use_default_offset
3. 報酬 feet_air_time / feet_slide / undesired_contacts が参照する body 名の正規表現と、新しい USD のリンク名に実際に何がマッチするか
4. 自作 rewards.py の feet_air_time_positive_biped の引数と中身（指令の大きさでゲートしているか）。Isaac Lab 同梱の同名関数の有無と差。Isaac Lab 同梱の G1 と H1 の locomotion velocity の env cfg で、足の滞空時間の報酬に使っている関数・weight・threshold
5. track_lin_vel_xy_exp の std（params の値）
6. Isaac Lab の RewardManager が weight 0.0 の項をどう扱うか（compute の実装）
7. mdp.base_lin_vel と track_lin_vel_xy_exp が使う速度が root の COM 速度か、リンク原点の速度か（articulation_data.py の root_lin_vel_b の定義）
8. 地形: max_init_terrain_level の値、自作 ROUGH_TERRAINS_CFG の階段の段差レンジ
9. タスク登録（config\\skyentific_poclegs\\__init__.py）の一覧。Flat タスクがあるか、あればその env cfg が Rough と何が違うか
10. train.py が --seed / --run_name を受けるか。Hydra の上書き（env.… / agent.…）が効く作りか
11. rsl_rl のバージョン、Isaac Lab に RslRlSymmetryCfg があるか（今回は使わない。次の準備）
12. 関節の内部順（名前の並び）
13. 初期姿勢での全身 COM の base 座標（特に y）。すぐ取れなければ省略可

## P2 準備（挙動を変えない変更だけ）
### 2-1 報酬項の追加（weight 0.0）
- my_robot_code\\rough_env_cfg.py の報酬クラスに、項 feet_air_time_biped を weight=0.0 で追加する。
- 関数は feet_air_time_positive_biped（自作 rewards.py 側。無ければ Isaac Lab 同梱）。params は既存の feet_air_time 項と同じ sensor・body 名（.*ffe）・command 名、threshold は P1-4 の G1 の値。
- 手順: rough_env_cfg.py.bak_add_airtime_biped を取る → open(r+) 方式で編集 → diff → ハードリンク5組の Get-FileHash 一致とリンク数 2。
- P1-6 で weight 0 の項も加算処理を通ると分かっても、値は 0 なので挙動は同じ。報告に書くだけでよい。

### 2-2 評価スクリプト D:\\Tominaga\\slope-climbing-robot\\tools\\measure_crab.py（新規）
play.py のチェックポイントの読み方を参考にして書く。
- 引数: --load_run（run フォルダ名）/ --checkpoint（例 model_1600.pt）/ --num_envs（既定 64）
- 評価環境（全ランで同じ。学習時の地形・報酬に依らない）: 平地（terrain_type plane）、観測ノイズ OFF、push などの外乱イベント OFF、指令の再サンプルなし、heading_command=False、rel_standing_envs=0。PLAY 用 cfg があれば土台にしてよい。
- シナリオ（毎回リセット、最初の 2 s を捨てて 10 s 計測）。(vx, vy, wz) で:
  S1 (0.5, 0, 0) / S2 (1.0, 0, 0) / S3 (0, 0, 0) / S4 (-0.3, 0, 0) / S5 (0, 0.3, 0) / S6 (0, 0, 0.5)
- 速度は「base の COM 速度を base の yaw だけで回した水平速度」（roll/pitch の揺れを混ぜない）。
- 指標（シナリオ × 指標の表）:
  v_x 平均 / v_y 平均（符号付き）/ |v_y − cmd_y| の平均 / yaw rate 平均（符号付き）/ 10 s の heading ずれ [deg] / 進行方向角 atan2(Δy, Δx) の平均 [deg]（計測開始時の base yaw 基準、S1・S2 のみ）/ 静止率（10 s 平均の水平速度 < 0.1 m/s の env の割合、S1・S2・S4・S5）/ 転倒率（計測中に終了した env の割合）/ LR_HR と LL_HR の平均角（符号付き）/ 左右の足の平均滞空時間 / 関節速度 |qd| の p95 / applied torque が effort_limit の 95% 以上の割合
- 出力: D:\\Tominaga\\slope-climbing-robot\\tools\\logs\\eval_（run フォルダ名）_（iter）.md と .csv
- 動作確認は 2026-09-16 のテスト起動の run で行う（数値の良し悪しは問わない）。env の command を実際に出力して、S1 で (0.5, 0, 0) に固定されていることを確認する。
- ついでに play.py の --video が動くかを1回だけ確認（--video_length 200、テスト run）。動かなければ深追いせず報告。

## P3 64 env / 20 iter テスト
- 下の P4 のラン A とラン B の起動行を、--num_envs 64 --max_iterations 20 に差し替えて1本ずつ通す。
- できた run フォルダの params\\env.yaml と params\\agent.yaml を開き、上書きが反映されているか確認: noise_std_type / terrain_type / terrain_generator / curriculum の terrain_levels / feet_air_time と feet_air_time_biped の weight / track_lin_vel_xy_exp の std。
- Hydra で null 指定が効かない等で落ちたら、代替案（Flat タスクがあればそれを使う等）を書いて止まる。

## 【停止点1】ここで報告して止まる
報告: P1 の表 / diff とハッシュ確認 / measure_crab.py の出力例 / params の反映確認 / 録画の可否 / P4 の起動行（実際の値を全部埋めた1行の完成形）。
ユーザーの「起動してよい」を待つ。

## P4 本番起動
共通: --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 4096 --max_iterations 3000 --headless env.commands.base_velocity.debug_vis=false agent.policy.noise_std_type=log --seed 1

- ラン A（--run_name A_base0821）: 共通だけ。地形・報酬・指令・アクチュエータは 08-21 版のまま。
- ラン B（--run_name B_combined）: 共通 ＋ 次の3系統
  - 平地: env.scene.terrain.terrain_type=plane env.scene.terrain.terrain_generator=null env.curriculum.terrain_levels=null
  - 足上げを dense に: env.rewards.feet_air_time.weight=0.0 env.rewards.feet_air_time_biped.weight=（P1-4 の G1 の weight）
  - 追従を厳しく: env.rewards.track_lin_vel_xy_exp.params.std=0.35
- ラン B2（--run_name B_combined_s2）: B と同じで --seed 2。下の条件を満たすときだけ。

起動の手順:
1. 各ランを D:\\Tominaga\\slope-climbing-robot\\tools\\runs\\（ラン名）.ps1 に書き、バックグラウンドで起動。ログは D:\\Tominaga\\slope-climbing-robot\\tools\\logs\\run_（ラン名）.txt。Claude Code のツールのタイムアウトで学習が止まらないようにする。
2. A を起動 → iter が 0 から始まり max 3000 に向かっていることを確認 → iter 30 まで待ち、秒/iter・VRAM・GPU 温度・使用率を記録。
3. B を起動 → 両方が iter 30 進んだ時点で、両方の秒/iter・VRAM・温度を記録。
4. B2 は次を全部満たすときだけ起動: その時点の VRAM 使用 ≤ 16 GB、GPU 温度 ≤ 80°C。起動して iter 30 進んだら、3本の (1 / 秒iter) の合計が、2本のときの合計より 10% 以上増えているか確認。増えていなければ B2 を止める。
5. どれかが落ちたら、他は止めずに、落ちたランのログ末尾の要点を記録して即報告。

## P5 監視
- 20〜30 分ごとにログ末尾: 落ちていないか / iter / Mean action noise std / VRAM / 温度。85°C 超が続いたら B2 → B の順に止めて報告。
- チェックポイント 1000 と 1600（save_interval の都合で無ければ最も近いもの）で measure_crab.py を実行。学習と同時になるので、VRAM の空きが 4 GB 以上のときだけ、64 env で。足りなければ待つ。
- TensorBoard のイベントファイルから iter 500 / 1000 / 1600 の値を抜き出す: Metrics/base_velocity/error_vel_xy / error_vel_yaw / Curriculum/terrain_levels（A のみ）/ Episode_Reward の全項目 / Episode_Termination の内訳 / Mean episode length / Mean action noise std。

## 【停止点2】全ランの 1600 のチェックポイントが出て評価が終わったら報告して止まる（学習は回したままでよい。止めるかはユーザーが決める）
報告の書式:
- 冒頭2行: A と B（と B2）それぞれ「カニ歩き: 有／無、立ち往生: 有／無、転倒: 合格／不合格」（下の基準で機械的に）
- 評価の表（S1〜S6 × 指標。A / B / B2 を横に並べる）
- 学習ログの表（iter 500 / 1000 / 1600）
- 4096 env の基準値（並走本数ごとの秒/iter・VRAM・温度）
- 所見は3行以内、次の候補は1〜2個

判定基準（事前に決めた暫定値。あなたが変えないこと。境界付近は数値をそのまま出す）:
- カニ歩き無し: S1 と S2 の両方で |v_y 平均| ≤ 0.05 m/s、|v_y − cmd_y| 平均 ≤ 0.10、|yaw rate 平均| ≤ 0.10 rad/s、進行方向角が ±10° 以内。かつ S5 で v_y 平均 ≥ +0.15
- 立ち往生無し: S1 で静止率 ≤ 5% かつ v_x 平均 ≥ 0.35、S2 で静止率 ≤ 5%
- 転倒合格: S1 の転倒率 ≤ 5%
- 参考: 学習ログの error_vel_xy ≤ 0.3

## やらないこと
- 走っているランの設定を途中で変えない。停止点2までコードを編集しない（次に起動するランが変わってしまう）
- アクチュエータ（effort・friction・グループ分け・ゲイン）には触らない
- 指令レンジは変えない
- commit / push はしない
- 他人のプロセスを止めない
```
