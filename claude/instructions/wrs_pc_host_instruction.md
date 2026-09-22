# 指示書: WRS共用PCに Isaac Lab 環境を作る（Claude Code 向け）

> 改訂 2026-09-15。**この文書は、WRS共用PC上で動く Claude Code に渡すためのもの。**
> 読み手の Claude Code は、このプロジェクトのこれまでの経緯を知らない前提で書いてある。**必要な情報はこの文書に全部入れてある。**

---

## 0. まず読むこと: あなたの状況

- **あなたが今動いているのは「WRS の共用 Windows デスクトップ」です。Alienware ではありません。**
  以前少しだけ Alienware（Ubuntu 機）で使われていた記憶や設定が残っていても、**それは別のマシンの話です。無視してください。** Alienware は 2026-09-13 に故障して使えなくなりました。
- **このPCは TA さんが主に使っている共用機です。** ユーザー（冨永 / GitHub: `Tominaga-Haruto`）は、使わせてもらっている立場です。**他の人の環境を壊さないことが、何より優先です。**
- ユーザーは TeamViewer で遠隔から操作しています。**TeamViewer は固定パスワードで接続できる設定済みなので、TeamViewer の設定には触らないでください。**

### 最初に打つ確認（自分がどのマシンにいるか確定させる）

```
powershell -Command \"hostname; (Get-CimInstance Win32_OperatingSystem).Caption; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv\"
```

**`Windows 11` と `NVIDIA GeForce RTX 3090 Ti` が出れば正しいマシンです。** 違うものが出たら作業を始めずにユーザーに報告してください。

> Claude Code の Bash ツールは Windows では Git Bash で動くことが多いです。**PowerShell 固有のコマンドは `powershell -Command \"...\"` で包んで実行してください。** パスは `D:\\Tominaga\\...` と `/d/Tominaga/...` の読み替えに注意。

---

## 1. ゴール

**このPCで、ユーザー専用の Isaac Lab 環境を作り、素の Isaac Lab で学習が回ることを確認する。** その上で、ユーザーのロボット学習コードを配置する。

完了条件（ここまでで止めて報告）:

1. `D:\\Tominaga\\` に専用の conda 環境・Isaac Sim 5.1・Isaac Lab ができている
2. Isaac Lab の同梱タスクで、**小さい学習（数 env・数 iter・headless）が完走する**
3. ユーザーのリポジトリと参考実装が clone され、自作コードが学習から読める位置に配置されている

**ユーザーのロボット本体のデータ（USD）はまだ無いので、ロボットでの学習はこの作業の範囲外です**（§7）。

---

## 2. ★ 共用PCの掟（必ず守る）

1. **新しく作るもの・書き込むものは `D:\\Tominaga\\` の中だけ。** このフォルダは**まだ存在しないので、あなたが作ります。**
2. **既存の環境には一切書き込まない。** 既に分かっているもの:
   ```
   C:\\Jerry\\IsaacLab              ← Jerry さんの環境
   D:\\IsaacLab                    ← Isaac Lab 2.3.2（持ち主不明。TA さんのものかもしれない）
   conda 環境: env_isaaclab / jerry_isaaclab / matsuuchi_env / matsuuchi_env_backup /
              pcnT / tf_1 / unitree_sim_env / wilor
   ```
   **読むのは可。使う・書き換える・削除するのは不可。**
3. **C ドライブに大きいものを置かない。** C: は空き約 41GB しかなく、埋まると全員の作業が止まる。**D: は空き約 550GB。**
   - conda 環境は **`-n 名前` ではなく `--prefix D:\\Tominaga\\envs\\...`** で作る（`-n` だと C: に入る）
   - **pip / conda のキャッシュも D: に向ける**（§4 段階2）。Isaac Sim は数十GBあり、既定のままだと C: のユーザーフォルダにキャッシュが溜まる
4. **Isaac Lab 公式手順の環境名 `env_isaaclab` は使わない。** 同名の他人の環境が既にある。公式手順をそのまま打つと壊す。
5. **システム全体の設定を変えない。** 次のものは**実行前に必ずユーザーに確認**する（ユーザーが TA さんに許可を取る）:
   - レジストリ・管理者権限が要る操作（長いパスの有効化など）
   - 電源・スリープ設定（**今回は変更しない。確認も不要**）
   - `git config --global`（**共用機なので、git 設定はリポジトリごとの `--local` にする**）
   - 環境変数のユーザー／システム単位での永続設定（`setx` など）。**その場限りの設定は可**
6. **他人のプロセスを止めない。** `python.exe` が走っていても、自分が起動したもの以外は触らない。
7. **GPU を長く使う前にユーザーに一言確認。** 動作確認の短い実行（数分）は可。
8. **ファイルを書き換える前は `.bak_変更内容` 形式でバックアップを取る**（例 `train.py.bak_taskimport`）。

---

## 3. 既存のインストール状況を調べる（読むだけ）

**作業を始める前に、今このPCに何がどこに入っているかを調べてユーザーに報告してください。** 過去の調査は1回だけで、見落としがあるかもしれません。

```
powershell -Command \"Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID,@{n='FreeGB';e={[math]::Round($_.FreeSpace/1GB,1)}},@{n='SizeGB';e={[math]::Round($_.Size/1GB,1)}}; Get-ChildItem D:\\ | Select-Object Name\"
```

```
conda env list
```

```
powershell -Command \"Get-ChildItem -Path C:\\,D:\\ -Filter isaaclab.bat -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Object FullName\"
```

```
powershell -Command \"Get-Content D:\\IsaacLab\\VERSION; git -C D:\\IsaacLab log -1 --oneline\"
```

C: のキャッシュの大きさ（Isaac Sim を入れると増える場所）:

```
powershell -Command \"'pip cache: {0:N1} GB' -f ((Get-ChildItem \\\"$env:LOCALAPPDATA\\pip\\cache\\\" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1GB); 'ov cache: {0:N1} GB' -f ((Get-ChildItem \\\"$env:LOCALAPPDATA\\ov\\\" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1GB)\"
```

Windows の長いパス対応（Isaac Sim の pip インストールで必要になることがある）:

```
powershell -Command \"Get-ItemProperty HKLM:\\SYSTEM\\CurrentControlSet\\Control\\FileSystem -Name LongPathsEnabled\"
```

**報告する内容:** ドライブ空き容量／conda 環境の一覧／Isaac Lab の場所とバージョン／C: のキャッシュ量／`LongPathsEnabled` の値（1 なら有効）。
**`D:\\Tominaga` が既にあった場合、`LongPathsEnabled` が 0 の場合は、そこで止めてユーザーに相談。**

---

## 4. 環境を作る

**進め方は「各段階で確認コマンドを打ち、期待通りの出力を見てから次へ」。** 期待と違えば、推測で直さずユーザーに報告する。

### 段階1: フォルダを作る

```
powershell -Command \"New-Item -ItemType Directory -Force -Path D:\\Tominaga\\envs,D:\\Tominaga\\cache\\pip,D:\\Tominaga\\cache\\conda | Out-Null; Get-ChildItem D:\\Tominaga | Select-Object Name\"
```

**確認: `envs` と `cache` が `D:\\Tominaga` の下に出ること。**

### 段階2: キャッシュを D: に向けて conda 環境を作る

**以降、pip / conda を使うシェルでは毎回この2つを設定する**（その場限り。永続設定はしない）:

```
PIP_CACHE_DIR=D:\\Tominaga\\cache\\pip
CONDA_PKGS_DIRS=D:\\Tominaga\\cache\\conda
```

環境作成（Python 3.11。Isaac Sim 5.1 の要件）:

```
conda create --prefix D:\\Tominaga\\envs\\isaac_env python=3.11 -y
```

**確認:** `D:\\Tominaga\\envs\\isaac_env\\python.exe` が存在し、`--version` が `3.11.x` を返すこと。

> Git Bash から `conda activate` がうまく効かない場合は、**`D:\\Tominaga\\envs\\isaac_env\\python.exe` をフルパスで呼ぶ**のが確実。以降の `python` はこの python を指す。
> **`pip` 単体は使わない。必ず `python -m pip`。** 別の Python の pip が呼ばれて、他人の環境や C: に入る事故を防ぐため。

```
D:\\Tominaga\\envs\\isaac_env\\python.exe -m pip install --upgrade pip
```

### 段階3: Isaac Lab を clone してバージョンを揃える

**この機体で既に動いている `D:\\IsaacLab` と同じ版（2.3.2 / `b4c3210247`）に揃える。** 他の人の環境と差が出ないようにするため。

```
git clone https://github.com/isaac-sim/IsaacLab.git D:\\Tominaga\\IsaacLab
git -C D:\\Tominaga\\IsaacLab checkout b4c3210247
```

**確認:** `D:\\Tominaga\\IsaacLab\\VERSION` が `2.3.2`。

### 段階4: Isaac Sim 5.1 と PyTorch を入れる（数十分・数十GB）

**★コマンドはこの文書を鵜呑みにせず、clone した Isaac Lab 同梱のインストール手順と照合してから実行する。**

```
powershell -Command \"Get-ChildItem D:\\Tominaga\\IsaacLab\\docs\\source\\setup\\installation -Recurse -Filter *.rst | Select-String -Pattern 'isaacsim\\[|torch==' | Select-Object Path,Line\"
```

2.3 系の手順では、おおむね次の形のはず（ドキュメントと食い違ったら**ドキュメント側を優先**し、差分をユーザーに報告）:

```
D:\\Tominaga\\envs\\isaac_env\\python.exe -m pip install \"isaacsim[all,extscache]==5.1.0\" --extra-index-url https://pypi.nvidia.com
D:\\Tominaga\\envs\\isaac_env\\python.exe -m pip install -U torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128
```

**確認（GPU が見えるか）:**

```
D:\\Tominaga\\envs\\isaac_env\\python.exe -c \"import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))\"
```

**`True` と `NVIDIA GeForce RTX 3090 Ti` が出れば合格。**

インストール中・後に C: の空きを §3 のコマンドで再確認し、**減り方が数GBを超えていたら報告**する。

### 段階5: Isaac Lab をインストール

```
cd D:\\Tominaga\\IsaacLab
isaaclab.bat --install
```

`isaaclab.bat` は有効な conda 環境の python を使う。**実行前に `D:\\Tominaga\\envs\\isaac_env` が有効（`python -c \"import sys; print(sys.executable)\"` がその環境を指す）ことを必ず確認する。** 他人の環境に入った状態で実行すると、その環境を書き換えてしまう。

Git Bash から `conda activate` が効かない場合は、cmd で「有効化 → 確認 → 実行」を1行にまとめる:

```
cmd /c \"set PIP_CACHE_DIR=D:\\Tominaga\\cache\\pip&& conda activate D:\\Tominaga\\envs\\isaac_env && where python && cd /d D:\\Tominaga\\IsaacLab && isaaclab.bat --install\"
```

**`where python` の1行目が `D:\\Tominaga\\envs\\isaac_env\\python.exe` であることを確認する。** 段階6以降の `isaaclab.bat` も同じ形で実行する。

### 段階6: 動作確認

**GUI は使わない。** TeamViewer 越しでは描画系が起動時に落ちることがある。**必ず `--headless`。**

```
cd D:\\Tominaga\\IsaacLab
isaaclab.bat -p scripts\\tutorials\\00_sim\\create_empty.py --headless
```

> **★このスクリプトは自分では終了しない**（中身が `while simulation_app.is_running(): sim.step()` の無限ループ）。**起動ログに `Simulation App Startup Complete` 相当が出たら成功なので、Ctrl+C で止める。** 放置すると GPU を使い続ける（2026-09-15 に約2時間回り続けた実例あり）。

通ったら、同梱タスクで短い学習（数分で終わる規模）:

```
isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\train.py --task Isaac-Velocity-Flat-Anymal-D-v0 --num_envs 64 --max_iterations 5 --headless
```

**確認:** iteration のログが5回分出て正常終了すること。**このときの VRAM 使用量と 1 iter の秒数を記録して報告。**
（学習ログは `D:\\Tominaga\\IsaacLab\\logs\\` に出る。）

**ここまで通れば「このPCで Isaac Lab が動く」が確定。** 以降でエラーが出たら、環境ではなくユーザーのコード側を疑える。

---

## 5. ユーザーのコードを配置する

### 段階7: リポジトリを clone

```
git clone https://github.com/Tominaga-Haruto/wanpbl2026_slope_climing_robot.git D:\\Tominaga\\slope-climbing-robot
git -C D:\\Tominaga\\slope-climbing-robot branch -a
```

- **GitHub 上のデフォルトは `main`**（`master` は存在しない。2026-09-15 確認）。 `fix/falling-down-end-condition` は過去の良い状態の記録なので**消さない**。
- **確認:** `my_robot_code\\` に次の5ファイルがあること:
  `rough_env_cfg.py` / `skyentific_poclegs.py` / `curriculums.py` / `rewards.py` / `rsl_rl_cfg.py`
- **git 設定はこのリポジトリ限定（`--local`）で。** `--global` は使わない。
- **改行コード:** `git -C D:\\Tominaga\\slope-climbing-robot config --local core.autocrlf` を確認して報告。**ユーザーの指示があるまで commit / push しない。**
- 公開リポジトリなので、**API キー・パスワード・`.env` は絶対にコミットしない。**

### 段階8: 参考実装（Skyentific の BipedalRobotSim）を clone

ユーザーのコードは、Skyentific 氏の二足ロボット学習リポジトリ **BipedalRobotSim**（ロボット名 PocLegs、タスク ID `Velocity-Rough-Skyentific-Poclegs-v0`）を土台にしている。**このリポジトリは `.gitignore` 除外なので、ユーザーのリポジトリには入っていない。**

- URL: **https://github.com/SkyentificGit/BipedalRobotSim** （ユーザー確認済み）
- clone 先: `D:\\Tominaga\\slope-climbing-robot\\references\\BipedalRobotSim`

```
git clone https://github.com/SkyentificGit/BipedalRobotSim.git D:\\Tominaga\\slope-climbing-robot\\references\\BipedalRobotSim
git -C D:\\Tominaga\\slope-climbing-robot\\references\\BipedalRobotSim log -1 --oneline
```

**確認:** clone が成功し、最新 commit が1行表示されること。

### 段階9: 自作5ファイルを参考実装の中から読めるようにする

元のマシン（Linux）では、参考実装の中にある5ファイルを削除し、代わりに `my_robot_code\\` の実体を指す **symlink** を置いていた。こうすると `my_robot_code\\` を編集するだけで学習に反映され、Git 管理も親リポジトリ側でできる。

**Windows で symlink を作るには管理者権限か開発者モードが要るので、代わりにハードリンクを使う。** 同じドライブ内なら権限不要で、「実体は1つ」という性質は同じ。

1. **まず、参考実装の中で5ファイルがどこにあるかを実測する**（推測でパスを決めない）:
   ```
   powershell -Command \"Get-ChildItem D:\\Tominaga\\slope-climbing-robot\\references\\BipedalRobotSim -Recurse -Include rough_env_cfg.py,skyentific_poclegs.py,curriculums.py,rewards.py,rsl_rl_cfg.py | Select-Object FullName\"
   ```
2. **見つかった場所と対応をユーザーに提示して了承を得る。**
3. 各ファイルについて: 元ファイルを `.bak_original` にリネーム → ハードリンクを作る:
   ```
   cmd /c mklink /H \"参考実装側のフルパス\" \"D:\\Tominaga\\slope-climbing-robot\\my_robot_code\\ファイル名\"
   ```
   （「参考実装側のフルパス」「ファイル名」は手順1で実測した実名に置き換えた完成形で実行する。）
4. **確認:** 片方の中身を表示してもう片方と一致すること（`fc` か `Get-FileHash` で比較）。

> **注意:** エディタによっては保存時にファイルを作り直し、ハードリンクが切れる。切れていないかは `Get-FileHash` で両者を比べれば分かる。ユーザーに一言伝えておく。

### 段階10: 参考実装を Python から import できるようにする

参考実装に `setup.py` / `pyproject.toml` があれば、**isaac_env の python で** editable インストールする:

```
D:\\Tominaga\\envs\\isaac_env\\python.exe -m pip install -e \"D:\\Tominaga\\slope-climbing-robot\\references\\BipedalRobotSim\\setup.py があるフォルダ\"
```

- **既知の罠:** 古い `setup.py` が `torch==2.5.1` などを固定していて、入れると torch がダウングレードされたことがある。**実行前に `setup.py` の `install_requires` を読み、torch 等の固定があればユーザーに報告**（元のマシンでは `install_requires=[]` にして `--no-deps` で入れた）。
- 実行後、段階4の torch 確認コマンドをもう一度打って、torch の版と CUDA が変わっていないこと。

### 段階11: タスク登録の1行を足す

IsaacLab の `train.py` は、参考実装のタスクを自動では読み込まない。**`D:\\Tominaga\\IsaacLab` は自分専用の clone なので、ここは編集してよい。**

```
D:\\Tominaga\\IsaacLab\\scripts\\reinforcement_learning\\rsl_rl\\train.py
D:\\Tominaga\\IsaacLab\\scripts\\reinforcement_learning\\rsl_rl\\play.py
```

の両方で、`import isaaclab_tasks` の近くに次の1行を追加する（`.bak_taskimport` を取ってから）:

```python
import skyentific_poclegs  # noqa: F401
```

**確認:** 差分を表示してユーザーに見せる。

---

## 6. ★ 既知の Isaac Lab のバグ（参考実装側）

参考実装は古い Isaac Lab 向けに書かれている。ユーザーの `my_robot_code\\curriculums.py` は修正済みだが、**同様の API 変更エラーが他でも出る可能性がある。**

- 例: 旧 API `_term_dones[\"...\"]` → 現行は `get_term(\"...\")`
- **エラーが出たら、推測で直さず、`D:\\Tominaga\\IsaacLab\\source` を grep して現行 API を確認してから、原因と修正案をユーザーに報告する。**

---

## 7. この作業の範囲外（やらないこと）

- **ロボットでの学習（`Velocity-Rough-Skyentific-Poclegs-v0`）は、まだ回せない。** ロボットの形状データ（USD・STL）は `.gitignore` 除外で GitHub に無く、元データは壊れた Alienware の中にある。さらにロボットの構造に修正が入ったため、**Onshape（CAD）から再エクスポートして作り直す予定。** これは別の指示書で行う。
  - 段階11まで終えたら、試しに `--num_envs 16 --max_iterations 1 --headless` で起動し、**「USD が見つからない」系のエラーで止まるなら、それは正常（想定内）**として報告する。それ以外のエラー（import エラー、タスク未登録など）は段階9〜11の問題なので原因を報告。
- Onshape の API キーの設定。**API キーやパスワードをユーザーにチャットへ貼らせない。**
- 長時間の本番学習。
- TeamViewer・電源・Windows Update の設定変更。

---

## 8. 最後にユーザーへ報告すること

以下を短くまとめて報告してください。**長いログは貼らず、要点だけ。**

| 項目 | 内容 |
|---|---|
| 既存環境の調査結果 | §3 の結果（特に `D:\\IsaacLab` の版、C: キャッシュ量、LongPathsEnabled） |
| 作ったもの | `D:\\Tominaga\\` 以下のフォルダと容量 |
| バージョン | Python / Isaac Sim / Isaac Lab（commit）/ torch / CUDA 可否 |
| 動作確認 | 同梱タスク学習の完走可否、VRAM 使用量、秒/iter |
| リポジトリ | 現在のブランチ、`core.autocrlf` の値、BipedalRobotSim の commit |
| リンク | 5ファイルのハードリンク対応表と一致確認の結果 |
| C: の空き | 作業前 → 作業後 |
| 詰まった点・未解決 | あれば |
| ユーザーの許可が要ること | 長いパス有効化など、止まっているもの |

**連絡のコツ:** ユーザーはターミナルの長文を読むのが得意ではありません。エラーは要点を日本語で訳し、次にやることを1〜2個に絞って伝えてください。コマンドを見せるときは、どのフォルダで実行するかを明示し、`<名前>` のような山括弧のプレースホルダは使わず、実際の名前を埋めた1行の完成形で出してください。
