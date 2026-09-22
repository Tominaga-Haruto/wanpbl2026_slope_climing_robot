
# 指示書 実験06: その場旋回を直す学習（2本並走）と、評価のハングの切り分け（WRS機）

> 作成 2026-09-17 午後。実験05 停止点5a（`tools\\logs\\REPORT_exp05_stop5a.md`）を受けて。同じ WRS チャットに続けて貼る。
> 判断の経緯は `chats/2026-09-17_exp04-stop4-review.md` の追記。
> ユーザーの要望: コントローラーは「旋回ボタン（その場で回る）」と「並進ボタン（向きを変えずに前後左右）」を分けたい。今の「下がりながら回る」動きもあってよいが、それしかできないのは困る。合格ラインは「自然な動きになるなら」で Cowork に一任。

```
# 指示: 停止点5a の講評と、実験06（その場旋回を直す学習 2本 ＋ ハングの切り分け。停止点6a・6b・6c）

停止点5a ありがとう。その場旋回の指令が全体の 0.38% しか出ていないこと、足上げ報酬の判定が並進だけ（rewards.py:40）なのを行番号つきで出してくれたので、直す場所が決まった。
前の指示（instructions/inactive/wrs_training_operator_instruction.md の掟、実験03〜05 の「更新」と「やらないこと」）はすべて有効。起動は _launch.ps1 / _eval.ps1 / _play.ps1。GPU はユーザー了承済み（期限なし）。開始時に nvidia-smi で他人の計算プロセスがあれば、何も起動せず報告して止まる。

## 報告書への指摘（先に直す）
- T0-1 の報酬の表は、コードの既定値に見える。G_real_peak / H_eff13p5 は B_combined と同じ起動行（feet_air_time w0・feet_air_time_biped w0.25・track_lin_vel_xy_exp の std 0.35）で学習しているはず。「env.yaml でも確認」と書いてあるが、表の weight 2.0 / 0.0 と std 0.5 はそれと合わない。
  → H0-1 で、G_real_peak と H_eff13p5 の run フォルダの params\\env.yaml から rewards の全項（weight と params）を読み直して表を出し直す。コードの値は別の列にする。
- 結論（足上げ報酬の判定が並進だけ）は、feet_air_time と feet_air_time_biped の両方が [:, :2] なので変わらない。変わるのは「weight 2.0 の唯一の足上げ報酬」という大きさの記述。

## ユーザーの要望から決めたこと
- 実機のコントローラーは次の2つを分ける。学習でも両方を明示的に出す。
  - 旋回ボタン: 指令 (0, 0, wz)
  - 並進ボタン: 指令 (vx, vy, 0)
- 変えるのは、足上げ報酬の判定と、指令の出し方の2つ。track_ang_vel_z_exp の weight・std、アクチュエータ、地形は変えない（効きを切り分けるため）。
- 土台は H_eff13p5（デプロイの第一候補）と同じ起動行。

## H0 ハングの切り分け（最初に。30 分まで。何も直さない・消さない）
- H0-0 いま走っている D4 のリトライ（env 8）が 10 分進んでいなければ止める。これ以上リトライしない。止めたあと Get-Process python, kit* で残りのプロセスが無いことを確認し、あれば PID・起動時刻・コマンドラインを報告する（勝手に止めない。自分が起動したものだけ止める）。
- H0-1 上の「報告書への指摘」の表の出し直し（GPU なし）。
- H0-2 対照: 完走した実績のある p6_2_basevel_dropout.py（D3 と同じ引数・同じ env 数）を今もう一度起動する。env の構築が通るかだけ見ればよい（「Base environment:」が出たら止めてよい）。
  - 通る → スクリプト側の差が疑わしい。t0_3_s6_diag.py・p6_1_footpitch.py と、p6_2_basevel_dropout.py・dump_golden.py の env cfg の作り方の差分（センサ、debug_vis、初期姿勢の上書き、メッシュの読み出し、rendering、headless 引数など）を行番号つきで一覧にする。
  - 通らない → 環境側。Kit のログ（ハングした回の最終 100 行。場所は reference/wrs_pc_environment.md、無ければ %USERPROFILE%\\.nvidia-omniverse\\logs 以下を探す）と、ハング中のプロセスの CPU 使用率を報告する。
- H0-3 どちらでも、T0-3 と D4 はこの指示では再実行しない。

## J0 コードの変更（.bak を取ってから。既定値では今までと同じ挙動になるように）
J0-1 足上げ報酬の判定（my_robot_code\\rewards.py、.bak_yawgate）
- feet_air_time と feet_air_time_positive_biped に引数 yaw_gate: bool = False を足す。
- yaw_gate=True のときは「|(vx, vy)| > 0.1 または |wz| > 0.1」で報酬を出す。False のときは今と同じ。

J0-2 指令の出し方（まず grep で実物を確認してから書く）
- 先に、Isaac Lab 2.3.2 の UniformVelocityCommand（velocity_command.py）の _resample_command と _update_command、is_heading_env・is_standing_env の扱いを行番号つきで読む。
- UniformVelocityCommand を継承したクラスと、その cfg を作る。cfg に3つ足す（既定はどれも今と同じ挙動）:
  - rel_turn_in_place_envs: float = 0.0
  - turn_in_place_wz_range: tuple = (0.3, 1.0)
  - rel_translate_only_envs: float = 0.0
- _resample_command で、親の処理のあとに、選んだ env を上書きする:
  - rel_turn_in_place_envs の割合の env: vx = vy = 0、wz = ±U(turn_in_place_wz_range)（符号は半々）、is_heading_env = False、is_standing_env = False
  - rel_translate_only_envs の割合の env（その場旋回に選ばれなかった中から）: wz = 0、is_heading_env = False
- _update_command が heading env の wz を計算し直し、standing env を 0 にするので、上の2種類の env が上書きされないことを確認する。
- 置き場所: 既存のハードリンク済みファイル（rough_env_cfg.py など、rewards.py と同じ仕組みで Isaac Lab 側から見えるもの）に入れる。新しいファイルが必要になるなら、作る前に止まって報告する（ハードリンクの組が増えるため）。
- rough_env_cfg.py の commands.base_velocity を新しい cfg に差し替える。3つの値は既定のまま（0.0）。

J0-3 確認
- 64 env / 20 iter で起動（J_turn の起動行で）。params\\env.yaml で yaw_gate と3つの値が反映されているか確認する。
- T0-2 と同じ集計（action 0、64 env、1000 step）を新しい指令で出す。その場旋回・並進だけ・歩きながら旋回・立ち止まりの4つの割合。
- diff、ハードリンク5組の Get-FileHash とリンク数、commit（push しない）。

## J 本番（2本同時、4096 env、seed 1、noise_std_type=log）
共通: H_eff13p5 とまったく同じ起動行（run フォルダの params から写す。起動行を報告に貼る）に、次を足す:
- 足上げ報酬のうち weight が 0 でない項に yaw_gate=true（H0-1 の表で確認した方。両方 0 でなければ両方）
- env.commands.base_velocity.rel_turn_in_place_envs=0.2
- env.commands.base_velocity.rel_translate_only_envs=0.15
- rel_heading_envs 0.5・rel_standing_envs 0.02・指令のレンジはそのまま

1. J_turn_resume: H_eff13p5 の model_2999.pt から再開して +1500 iter（F_BtoRough と同じ再開のやり方。--max_iterations は追加 iter 数）
2. J_turn_scratch: 一から 3000 iter

起動の順番: H0 と J0 が終わってから起動する。評価は学習と並べて 64 env で回してよいが、env の構築が 10 分進まなければ止め、リトライせず「学習が終わってから回す」に回す。

## 評価（measure_crab.py。S10・S11 を足す。既存の指標は変えない）
- シナリオを足す: S10 (0, 0, +1.0)、S11 (0, 0, +0.2)（どちらも参考）
- S6 / S9 / S10 / S11 で、胴体の水平速度 |(vx, vy)| の平均と、左右の足の滞空時間・10 s あたりの歩数を必ず出す
- タイミング: J_turn_resume は +500 / +1000 / +1499、J_turn_scratch は 1000 / 2000 / 2999。比較のため H_eff13p5@2999 の S1〜S11 も1回

判定（Cowork が決めた。変えないこと。境界付近は数値をそのまま出す）
- その場旋回 合格: S6 と S9 で、yaw rate の符号が指令と同じ、|yaw rate| ≥ 0.25、S6 と S9 の大きさの比が 0.5〜2、|(vx, vy)| の平均 ≤ 0.10（下がりながら回るのは不合格）、転倒率 ≤ 5%、左右とも足を上げている（歩数 > 0）
- 既存の基準（立ち往生・カニ歩き・転倒・トルク・小旋回）を落とさない。S1 の v_x ≥ 0.35 と、S1 の FFE の RMS が H_eff13p5 から大きく増えていないか（数値を並べる）
- S6 の HR の |computed torque| の p95 と飽和率

## 【停止点6a】H0・J0 が終わり、2本を起動して iter 30 まで進んだら報告（学習は回したまま、止まらずに評価へ進んでよい）
- H0 の結果（対照が通ったか、差分の一覧、残りのプロセス）、出し直した報酬の表
- J0 の diff、UniformVelocityCommand の該当行、新しい指令での4つの割合、commit のハッシュ
- 2本の起動行、秒/iter、終わる見込み時刻
- 想定外（上書きが効かない、64 env テストが落ちる、対照もハングする）は止まって報告。この場合は学習を起動しない。

## 【停止点6b】J_turn_resume の +1499 の評価が終わったら報告（J_turn_scratch は回したまま）
- 冒頭3行: その場旋回の判定、既存基準を落としていないか、足の運び（歩数・滞空・|(vx, vy)|）
- H_eff13p5@2999 / J_turn_resume の +500 / +1000 / +1499 を S1〜S11 で並べた表
- 学習ログの正規化 error_vel_yaw と error_vel_xy の推移

## 【停止点6c】J_turn_scratch の 2999 の評価が終わったら報告して止まる
- 6b と同じ形で J_turn_scratch の 1000 / 2000 / 2999
- その場旋回に合格した中で、S1 の成績とトルクが一番良いチェックポイントを1つ推す。規則と違う推し方をするなら理由を並べる
- 推したチェックポイントの ONNX 書き出しと verify_onnx.py、SHA256
- 頑健性の評価（P1 の条件 1・3・4・6・8・9・10・16 と速度 0）は、ユーザーが推しを了承してから別に指示する。ここではやらない

## やらないこと
- track_ang_vel_z_exp の weight・std、アクチュエータ、地形の変更
- push、削除、pip / conda でのインストール
推測で直さない。想定外は止まって報告。報告書は tools\\logs\\REPORT_exp06_stop6a.md / stop6b.md / stop6c.md。
```
