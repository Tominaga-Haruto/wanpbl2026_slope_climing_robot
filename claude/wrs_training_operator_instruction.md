# 指示書: WRS共用PCで学習を回す（WRS機の Claude Code・新しいチャット向け）

> 作成 2026-09-16。**この文書は、WRS共用PC上で動く Claude Code の新しいチャットに、最初に丸ごと貼るためのもの。**
> 読み手の Claude Code は、これまでの経緯を知らない前提で書いてある。**必要な情報はこの文書に全部入れた。**
> **この文書の役割は「作業の前提と作法」。** 何を実験するかの具体的な指示は、このあとユーザーが別途貼る（ユーザーは別のチャットで戦略を決めている）。**この文書を読んだら、§8 の最初の確認だけ行って報告し、次の指示を待つこと。**

---

## 0. あなたの状況

- **あなたが動いているのは WRS の共用 Windows 11 デスクトップ（`DESKTOP-MACG22A`、RTX 3090 Ti 24.5GB）です。** TA さんが主に使っている共用機で、ユーザー（冨永 / GitHub `Tominaga-Haruto`）は使わせてもらっている立場です。**他の人の環境を壊さないことが最優先です。**
- ユーザーは TeamViewer で遠隔から操作しています。TeamViewer の設定には触らないでください。
- **最初に確認:** `powershell -Command \"hostname; (Get-CimInstance Win32_OperatingSystem).Caption; nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv\"` → `DESKTOP-MACG22A`・`Windows 11`・`RTX 3090 Ti` でなければ作業を始めず報告。**GPU が他の人に使われていないか（使用率・メモリ）も見る。**
- Bash ツールは Git Bash のことが多い。**conda は PowerShell からしか使えません**（cmd には無い）。conda を使う処理は `powershell -Command \"...\"` で包むか、PowerShell スクリプト（.ps1）にして実行してください。

---

## 1. プロジェクトの概要（最小限）

- 機械学習（Isaac Lab + rsl_rl の PPO）で、自作の二足歩行ロボット（片脚5関節×2、総質量 10.1 kg）が坂を登る方策を作る。最終的に実機にデプロイする。
- タスク ID: **`Velocity-Rough-Skyentific-Poclegs-v0`**（Skyentific 氏の PocLegs 参考実装を土台に、ロボットを置き換えたもの）。
- **2026-09-16 にロボットのモデル（URDF/USD）を作り直した。** 旧モデルは「base の前（+X）がロボットの横を向いていた」「関節軸の符号が左右で食い違っていた」ことが判明し、修正済み。**それ以前の学習結果・チェックポイントは全部無効。** 過去に出ていた「カニ歩き（横に流れる歩き方）」が旧モデルのせいだった可能性があり、**それを確かめるのが当面の目的。**

---

## 2. ★ 共用PCの掟（必ず守る）

1. **書き込むのは `D:\\Tominaga\\` の中だけ。**
2. **既存の他人の環境には一切書き込まない:** `C:\\Jerry\\IsaacLab`、`D:\\IsaacLab`、conda 環境 `env_isaaclab` / `jerry_isaaclab` / `matsuuchi_env` / `matsuuchi_env_backup` / `pcnT` / `tf_1` / `unitree_sim_env` / `wilor`。読むのは可。
3. **C ドライブに大きいものを置かない**（空き約 43GB）。pip キャッシュは `D:\\Tominaga\\cache\\pip`。
4. **システム設定を変えない:** レジストリ、`setx`、`git config --global`、Windows の証明書ストア、Avast、電源設定。環境変数は**その場限り**。
5. **他人のプロセスを止めない。**
6. **GPU を数分以上使う前（本番学習など）は、必ずユーザーに確認する。** 64 env / 20 iter 程度の動作確認は可。
7. **ファイルを書き換える前は `.bak_変更内容` 形式でバックアップ**（例 `rsl_rl_cfg.py.bak_logstd`）。日付だけの名前にしない。
8. **`D:\\Tominaga` をリネームしない。**

---

## 3. 環境（構築済み・確定値）

| 項目 | 値 |
|---|---|
| Isaac 用 conda 環境 | `D:\\Tominaga\\envs\\isaac_env`（Python 3.11.16） |
| CAD 書き出し用 | `D:\\Tominaga\\envs\\onshape_env`（onshape-to-robot 1.8.3。今回は使わない） |
| Isaac Sim | 5.1.0（pip 版） |
| Isaac Lab | `D:\\Tominaga\\IsaacLab`（2.3.2 / `b4c3210247`）。`scripts\\reinforcement_learning\\rsl_rl\\train.py` と `play.py` に `import skyentific_poclegs  # noqa: F401` 追加済み |
| torch | 2.7.0+cu128 |
| tensordict | **0.7.0 固定**（最新版は Windows で access violation クラッシュ） |
| リポジトリ | `D:\\Tominaga\\slope-climbing-robot`（ブランチ `main`、最新 `6ede75b`） |
| 参考実装 | `D:\\Tominaga\\slope-climbing-robot\\references\\BipedalRobotSim`（editable インストール済み、git 除外） |
| 学習ログ | `D:\\Tominaga\\IsaacLab\\logs\\rsl_rl\\` の下 |

### 自作5ファイルとハードリンク

**編集対象は `D:\\Tominaga\\slope-climbing-robot\\my_robot_code\\` の5ファイル。** 参考実装側の同名ファイルとハードリンクになっていて、学習は参考実装側を読む。

| my_robot_code | 参考実装側（`references\\BipedalRobotSim\\skyentific_poclegs\\skyentific_poclegs\\` 以下） |
|---|---|
| `skyentific_poclegs.py`（アクチュエータ・初期姿勢・USD パス） | `assets\\skyentific_poclegs.py` |
| `rough_env_cfg.py`（報酬・終了・カリキュラム・地形・観測） | `tasks\\locomotion\\velocity\\config\\skyentific_poclegs\\rough_env_cfg.py` |
| `rsl_rl_cfg.py`（PPO） | `tasks\\locomotion\\velocity\\config\\skyentific_poclegs\\agents\\rsl_rl_cfg.py` |
| `curriculums.py` | `tasks\\locomotion\\velocity\\mdp\\curriculums.py` |
| `rewards.py` | `tasks\\locomotion\\velocity\\mdp\\rewards.py` |

- **★ハードリンクは、エディタの保存方式や git 操作（pull / checkout / stash）でファイルが作り直されると黙って切れる。** 切れると片方だけ古いまま学習が回る（エラーは出ない）。
- **編集は Python の `open(path, 'r+')` で読み→`seek(0)`→`write`→`truncate` の方式で行う**（ファイルを作り直さない）。
- **編集後と git 操作後は、5組すべて `Get-FileHash` で両側一致、リンク数 2 を確認する。**

### ロボットモデル（触らない。参考情報）

- USD: `...\\skyentific_poclegs\\assets\\robots\\myrobot_dummy\\robot.usd`（+ `configuration\\`）。URDF は `onshape_export\\myrobot_dummy\\robot_sim.urdf`（`tools\\postprocess_urdf.py` で生成）。
- **base 座標: +X 前 / +Y 左 / +Z 上。** 関節名 `LR_*`（右）/ `LL_*`（左）× `HR`（股ひねり）/ `HAA`（股横開き）/ `HFE`（股前後）/ `KFE`（膝）/ `FFE`（足首）。リンク名は小文字（`base`, `lr_ffe` など）。
- **関節の正の向き（左右とも同じ角度で鏡写しに動く）:** HR 正＝爪先が外、HAA 正＝足が外、HFE 負＝脚が前、KFE 正＝膝を曲げる、FFE 負＝爪先が上。
- 初期姿勢: HR 0 / HAA 0 / HFE −0.1745 / KFE 0.3491 / FFE −0.1745、スポーン高さ z=0.375776 m。
- **base の原点は胴体の中心ではない**（脚より約 9 cm 前、左右中心から約 2 cm）。速度を測るときは注意。
- URDF の関節 velocity limit（15〜23 rad/s）は学習の物理側で効く。effort は効かない（アクチュエータ設定の `effort_limit` が効く）。可動域は ±π（実質無制限）。
- **モデルを作り直す作業が必要になったら、止めてユーザーに報告**（手順が別にある）。

---

## 4. 現在のコードの状態（2026-09-16 に棚卸し済み）

**機体まわり以外は 2026-08-21 版。** 主な値:

- **PPO（`rsl_rl_cfg.py`）:** `noise_std_type` 無し（scalar）、`clip_actions` 無し、init_noise_std 1.0、entropy_coef 0.005、learning_rate 1e-3、num_steps_per_env 24、max_iterations 30000（コマンドラインの `--max_iterations` で上書きする）
- **指令:** `rough_env_cfg.py` では触っていない＝Isaac Lab 既定（lin_vel_x/y ±1、ang_vel_z ±1、heading ±π、heading_command True、rel_standing_envs 0.02、10 s ごとに再サンプル）
- **終了:** base_contact（base, threshold 1.0）/ bad_orientation（1.3 rad）/ time_out
- **報酬（実効）:** track_lin_vel_xy_exp 1.0 / track_ang_vel_z_exp 0.5 / lin_vel_z_l2 −2.0 / ang_vel_xy_l2 −0.05 / joint_torques_l2 −1e-5 / action_rate_l2 −0.01 / feet_air_time 2.0 / feet_slide −0.25 / undesired_contacts −1.0 / joint_deviation_hip −0.1 / joint_deviation_knee −0.01 / flat_orientation_l2 −0.5 / dof_pos_limits −1.0（最後の2つは `__post_init__` で上書き）
- **カリキュラム:** terrain_levels / push_force_levels（1500 iter〜）/ command_vel（5000 iter〜、昇格のみ）
- **地形:** flat 0.3 / pyramid_slope 0.1 / inv 0.1 / stairs 0.05 / stairs_inv 0.05 / wave 0.2 / random_rough 0.2
- **アクチュエータ（DelayedPD）:** hr（24 N·m, Kp 10）/ haa（30, 15）/ **kfe グループが HFE と KFE の両方**（30, 15）/ ffe（20, 10）、damping 1.5、friction 0.02
- **既知の弱点:** `noise_std_type` が scalar だと、長い学習の後半で `RuntimeError: normal expects all elements of std >= 0.0` で落ちることがある（std が負になる。`\"log\"` にすれば起きない）。

**★報酬の実効値はクラス定義ではなく `__post_init__` で上書きされていることがある。値を報告するときは両方を見る。**
**★文書に書いてある値を信じず、ファイルの実物（行番号付き）で確認してから作業・報告する。**

---

## 5. 毎回の起動と学習コマンド（PowerShell）

### 起動前チェック（毎回）
```
conda activate D:\\Tominaga\\envs\\isaac_env ; where.exe python ; python -m pip show tensordict
```
- `where.exe python` の1行目が `D:\\Tominaga\\envs\\isaac_env\\python.exe`
- tensordict が `0.7.0`
- `nvidia-smi` で他の人が GPU を使っていないか

### テスト起動（64 env / 20 iter。設定を変えたら毎回まずこれ）
```
conda activate D:\\Tominaga\\envs\\isaac_env ; cd D:\\Tominaga\\IsaacLab ; .\\isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 64 --max_iterations 20 --headless env.commands.base_velocity.debug_vis=false
```

### 本番学習（★実行前にユーザーの了承を取る）
```
conda activate D:\\Tominaga\\envs\\isaac_env ; cd D:\\Tominaga\\IsaacLab ; .\\isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 4096 --max_iterations 1500 --headless env.commands.base_velocity.debug_vis=false
```

- **★`env.commands.base_velocity.debug_vis=false` を必ず付ける。** 無いと速度指令の矢印アセット（S3 上の `arrow_x.usd`）の取得が 300 秒タイムアウトして落ちる。
- **★起動直後に iteration 番号が 0 から始まり、想定の max に向かっているか確認する。** 過去に iter 数の暴走（1500 のつもりが 15000）が起きている。
- **長い学習はバックグラウンドで実行し、ログをファイルに残す**（例: `Start-Process` や `*> D:\\Tominaga\\slope-climbing-robot\\tools\\logs\\run_名前.txt`）。定期的に末尾を確認し、落ちていないか見る。**Claude Code のツールのタイムアウトで学習が止まらないようにする。**
- 途中で止めるときは Ctrl+C（またはプロセスを止める）。**チェックポイントは 200 iter ごとに残る。**
- 4096 env での初回は、**秒/iter・VRAM・GPU 温度を記録して報告**（未測定の基準値）。

### 録画・再生（未検証。初回は動くか確認する）
```
conda activate D:\\Tominaga\\envs\\isaac_env ; cd D:\\Tominaga\\IsaacLab ; .\\isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\play.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 50 --headless --video --video_length 400 env.commands.base_velocity.debug_vis=false
```
- 既定では最新の run のチェックポイントを読む。特定の run は `--load_run` / `--checkpoint` で指定（引数名は `play.py --help` で確認）。
- 動画は run フォルダの `videos\\` に出る想定。`exported\\` に policy ファイルができるかも確認する。
- **学習中に play を同時に回さない**（GPU メモリ逼迫。共用機でもある）。
- GUI（`--headless` 無し）は使わない（TeamViewer 越しでは描画系が落ちることがある）。

---

## 6. ログの読み方と報告の書式

**Mean reward や episode 長だけで「歩けた」と判断しない**（棒立ちでも上がる）。

| 指標 | 歩けている | 棒立ち局所解 |
|---|---|---|
| `Metrics/base_velocity/error_vel_xy` | 0.3 以下 | 0.7 以上 |
| `Curriculum/terrain_levels` | 0 より上に動く | 0 に張り付く |
| `Episode_Reward/feet_air_time` | プラス | マイナス |

- **カニ歩き（横流れ）は、胴体座標の横速度から指令の横速度を引いた残差 `v_y − cmd_y` で測る。** 生の `v_y` は横指令がランダムな設定では意味が無い。
- `Episode_Termination/*` の内訳（base_contact / bad_orientation / time_out）、`Mean action noise std`（0.1 を切って下がり続けるのは危険信号）も見る。

**報告の書式（毎回）:**
- 冒頭に**結論を1〜2行**（通った／落ちた／何が分かった）
- 数値は表で。**長いログは貼らず要点だけ。** エラーは Traceback の要点を日本語で。
- 変更したファイルは diff の要点と `.bak` の名前、ハードリンクのハッシュ確認結果。
- run フォルダ名、iter 数、所要時間、秒/iter、VRAM。
- **次にやることの候補を1〜2個**に絞る（決めるのはユーザー）。
- **ユーザーはターミナルの長文を読むのが得意ではありません。** コマンドを見せるときは、どのフォルダで実行するかを明示し、`<名前>` のような山括弧のプレースホルダは使わず、実際の名前を埋めた1行の完成形で出してください。

---

## 7. 作業の作法

- **推測で直さない。** エラーや想定外の挙動が出たら、Isaac Lab 本体（`D:\\Tominaga\\IsaacLab\\source`）や rsl_rl を grep して現行の実装を確認し、**原因と修正案を報告して止まる。**
- **一度に1つだけ変える。** 変える → `.bak` → diff → 64 env / 20 iter → 報告 → 了承を得て本番。
- **Isaac Lab 本体は書き換えない**（train.py / play.py の import 1行は例外として追加済み）。
- **診断スクリプトは `D:\\Tominaga\\slope-climbing-robot\\tools\\` に .py として書く。** 複数行の Python をコマンドラインに直貼りしない。API キーやパスワードを出力しない。
- **成否は終了コードではなく成果物（ログ・ファイルの時刻）で判断する。** この機体では変換処理が失敗しても終了コード 0 を返した前例がある。
- **Git:**
  - ブランチは `main`。git 設定は `--local`（`--global` は使わない）。コミット著者は既存のコミットと同じ GitHub の noreply メール。
  - **commit / push はユーザーの指示があるまでしない。** commit 前に `git status --short` と `git diff --cached --stat` で `.env` / `*.usd` / `*.stl` / `*.part` / `*.bak*` / ログや動画が混ぎました。
  - **push は認証が要るので、ユーザーが PowerShell で自分で実行する。** あなたは実行する1行を表示して止まる。push 後は `git log -3 --format=\"%h %ad %s\" --date=iso origin/main` で反映を確認（あなたの Bash からの `git fetch` は証明書の設定が無いと失敗する）。
  - git 操作の後は必ずハードリンクのハッシュ確認。
- **証明書（Avast の HTTPS 検査）:** ネットに出る作業（pip / conda / git）が必要になったら、セッション限りで `PIP_CERT` / `CONDA_SSL_VERIFY` / `REQUESTS_CA_BUNDLE` を `D:\\Tominaga\\cache\\certs\\combined-ca-bundle.pem` に設定する。**パッケージの追加・更新は、tensordict が上がる恐れがあるので必ず事前にユーザーに確認。**
- **Omniverse のキャッシュは C: に溜まる**（`C:\\Users\\WRS\\AppData\\Local\\ov`）。長く使ったら C: の空きを報告。

---

## 8. 最初にやること（これだけやって報告し、指示を待つ）

1. §0 のマシン確認と GPU の使用状況
2. §5 の起動前チェック（python のパス、tensordict）
3. `git -C D:\\Tominaga\\slope-climbing-robot log -1 --format=\"%h %ad %s\" --date=short` と `git status --short`（最新が `6ede75b` か、未コミットの変更があるか）
4. ハードリンク5組の `Get-FileHash` 一致とリンク数
5. `D:\\Tominaga\\IsaacLab\\logs\\rsl_rl\\` にある run フォルダの一覧（名前と日時。2026-09-16 のテスト起動の run があるはず）
6. C: / D: の空き容量

**報告して止まってください。** 次に何をするかは、ユーザーが別のチャットで決めた指示を貼ります。
