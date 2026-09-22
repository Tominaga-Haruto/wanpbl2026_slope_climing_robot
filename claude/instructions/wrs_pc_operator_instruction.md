# 指示書: 新デスクトップ（WRS機）に Isaac Lab 環境を作る ── **操作する側**

> 作成 2026-09-14。**TeamViewer で繋いで操作する側（haruto、ノートPC）が読む文書。**
> デスクトップの前にいる人・持ち主が読む文書は `claude/wrs_pc_host_instruction.md`（別ファイル）。
>
> **この文書も鵜呑みにしない。** コマンドは実行前に出力を確認しながら進める（手順書 A1「推測で進めない」）。

---

## 0. この機体は何か（2026-09-14 実測）

Alienware が故障したため、**別のデスクトップを借りて柱Aを動かす。**

| 項目 | 値 | 判定 |
|---|---|---|
| GPU | **NVIDIA GeForce RTX 3090 Ti** | RT Coresあり。**Alienware の 4070 より上** |
| VRAM | **24,564 MiB（24.5GB）** | 4070 の12GBの倍 |
| NVIDIAドライバ | **591.86** | Isaac Sim 5.1 の Windows 要件 580.88 以上を満たす |
| RAM | **127.4 GB** | 要件32GBを大きく超える |
| OS | **Windows 11 Education** | Isaac Sim 5.1 対応 |
| C: | 41.3GB 空き / 930.4GB | **使わない** |
| **D:** | **553.8GB 空き** / 931.5GB | **★ここに全部入れる** |
| Python環境 | Miniconda（`C:\\Users\\WRS\\miniconda3`） | 既設 |
| ユーザー名 | `WRS` | ホームは `C:\\Users\\WRS` |

### ★ これは共有マシンである

conda 環境の一覧に **`jerry_isaaclab` / `matsuuchi_env` / `matsuuchi_env_backup` / `unitree_sim_env` / `pcnT` / `tf_1` / `wilor`** がある。**複数人が使っている。**

IsaacLab は**すでに2箇所に入っている**：

| 場所 | バージョン | 扱い |
|---|---|---|
| `C:\\Jerry\\IsaacLab` | 不明 | **Jerryさんの個人環境。絶対に触らない** |
| `D:\\IsaacLab` | **2.3.2**（main, `b4c3210247`） | **共有と思われる。読むだけ。書き込まない** |
| conda `env_isaaclab` | 中身未確認 | **他人のもの。使わない。この名前を再利用しない** |

> **★注意: Isaac Lab 公式ドキュメントの手順は conda 環境名に `env_isaaclab` を使う。この機体には同名の環境が既にある。そのまま打つと他人の環境を壊す。**
> **この指示書では `--prefix D:\\haruto\\envs\\isaac_env` を使って名前の衝突を避ける。**

---

## 1. 共有マシンの掟（毎回守る）

1. **書き込んでいいのは `D:\\haruto\\` の中だけ。**
2. **`C:\\Jerry\\`、`D:\\IsaacLab`、他人の conda 環境には一切書き込まない。** 読むのは可。
3. **C ドライブに大きいものを置かない。** 空きが 41GB しかない。**C が埋まると共有マシン全体が止まる。** conda 環境も `--prefix` で D: に作る。
4. **GPU を長時間占有する前に、持ち主に一言入れる。** 学習は数十分〜数時間 GPU を 100% 使う。
5. **他人のプロセスを kill しない。** タスクマネージャーで python が複数走っていても、自分が起動したもの以外は触らない。
6. **`.bak` は `.bak_<変更内容>` 形式。** 日付だけの名前は付けない（2026-09-08 に取り違え事故）。

---

## 2. TeamViewer で繋ぐ

### 繋ぎ方

手元のノートPCで TeamViewer を起動 → **「パートナーID」欄にデスクトップの9〜10桁のIDを入力** → 「接続」→ パスワードを入力。

### ★ 最初にやること: IDを控える

**「ご使用のID」は変わらない。** 今のうちにメモしておけば、デスクトップの画面が見えなくなっても繋げる。

**Alienware で詰んだ原因はこれをやっていなかったこと。** 同じ轍を踏まない。

### パスワードが「-」で出ないとき

ランダムパスワードが無効になっている。**持ち主に `claude/wrs_pc_host_instruction.md` の §2 をやってもらう**（固定の個人パスワードを設定するか、ランダムパスワードを有効に戻す）。**勝手に設定を変えない。**

---

## 3. Windows と Ubuntu の差分（読み替え表）

Alienware（Ubuntu）の手順書コマンドはそのままでは動かない。

| Ubuntu（Alienware） | Windows（この機体） |
|---|---|
| `source .../isaac_env/bin/activate` | `conda activate D:\\haruto\\envs\\isaac_env` |
| `./isaaclab.sh` | `isaaclab.bat` |
| `python -m pip`（**この原則は同じ**） | `python -m pip` |
| `ls -lt` | `Get-ChildItem \\| Sort-Object LastWriteTime -Descending` |
| `grep` | `Select-String` |
| `/` 区切り | `\\` 区切り |
| symlink（`ln -s`） | **ハードリンク（`mklink /H`）／ジャンクション（`mklink /J`）**（§7） |
| `~/projects/slope-climbing-robot` | `D:\\haruto\\slope-climbing-robot` |

**PowerShell を開く:** Windowsキー + X → 「ターミナル」または「Windows PowerShell」。

---

## 4. 構築の全体像

```
D:\\haruto\\
├── envs\\isaac_env\\              ← 自分専用の conda 環境（--prefix で D: に作る）
├── IsaacLab\\                    ← 自分専用に clone（他人のものを使わない）
└── slope-climbing-robot\\        ← GitHub から clone
    ├── my_robot_code\\           ←   自作5ファイル（clone で入る）
    ├── references\\
    │   └── BipedalRobotSim\\     ←   Skyentific 参考実装（別途 clone）
    └── onshape_export\\          ←   USD 置き場（★中身は別途入手。§8）
```

**進め方は「小さく通してから本番」**（手順書 A5）。各段階で確認コマンドをセットで打つ。

---

## 5. 段階1〜4: 環境を作る

### 段階1: フォルダを作る

```
New-Item -ItemType Directory -Force -Path D:\\haruto\\envs | Out-Null ; Get-ChildItem D:\\ | Select-Object Name
```

**確認: `haruto` が D: の直下に出ること。** 手順書 A4 の「mkdir したら必ず場所確認」と同じ理由（過去に置き場所を間違えた事故がある）。

### 段階2: conda 環境を D: に作る

**★`-n 名前` ではなく `--prefix` を使う。** `-n` だと C ドライブの `C:\\Users\\WRS\\miniconda3\\envs\\` に作られてしまう。

```
conda create --prefix D:\\haruto\\envs\\isaac_env python=3.11 -y
```

有効化（**以降のコマンドは全部この環境の中で打つ**）:

```
conda activate D:\\haruto\\envs\\isaac_env ; python --version ; python -m pip install --upgrade pip
```

**確認: `Python 3.11.x` が出て、プロンプトの先頭が `(D:\\haruto\\envs\\isaac_env)` になること。**

> **Alienware と同じ Python 3.11 系に揃えている。** バージョン不整合はこのプロジェクトで既に2回踏んでいる罠（手順書 B8）。

### 段階3: Isaac Sim 5.1 を入れる（20〜40分。回線次第）

```
python -m pip install \"isaacsim[all,extscache]==5.1.0\" --extra-index-url https://pypi.nvidia.com
```

続けて PyTorch（**Isaac Lab 公式が指定している版に合わせる**）:

```
python -m pip install -U torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128
```

**確認（GPUが見えているか）:**

```
python -c \"import torch; print('torch', torch.__version__, '| cuda', torch.cuda.is_available(), '|', torch.cuda.get_device_name(0))\"
```

**`cuda True` と `NVIDIA GeForce RTX 3090 Ti` が出れば合格。**

> **★`pip` 単体を使わない。必ず `python -m pip`**（手順書 A2 の落とし穴1）。Windows でも同じ理由で効く。
> **★途中で止まったように見えても待つ。** Isaac Sim は数十GBある。

### 段階4: Isaac Lab を自分用に clone して入れる

```
cd D:\\haruto ; git clone https://github.com/isaac-sim/IsaacLab.git --branch main ; cd D:\\haruto\\IsaacLab ; git log -1 --oneline
```

**★この機体で実績のある版に合わせる。** `D:\\IsaacLab` は **2.3.2 / `b4c3210247`** で動いている。同じ commit に揃えておくと、他人の環境との差でハマらない。

```
cd D:\\haruto\\IsaacLab ; git checkout b4c3210247 ; git log -1 --oneline ; Get-Content VERSION
```

**確認: `2.3.2` が出ること。**

インストール:

```
cd D:\\haruto\\IsaacLab ; .\\isaaclab.bat --install
```

**動作確認（公式の検証コマンド）:**

```
cd D:\\haruto\\IsaacLab ; .\\isaaclab.bat -p scripts\\tutorials\\00_sim\\create_empty.py
```

**★ここまでで「素の Isaac Lab が動く」が確定する。** 自分のコードを入れる前にこれを通しておくと、あとでエラーが出たとき「環境が悪いのか自分のコードが悪いのか」で悩まずに済む。

> **TeamViewer 経由では描画系が落ちる可能性がある**（手順書 A3。Alienware では `omni.kit.renderer.init` 付近で落ちた）。**落ちたら `--headless` を付けて再試行する。** 学習は元々 headless なので支障はない。

---

## 6. 段階5: 自分のコードを入れる

```
cd D:\\haruto ; git clone https://github.com/Tominaga-Haruto/wanpbl2026_slope_climing_robot.git slope-climbing-robot ; cd D:\\haruto\\slope-climbing-robot ; git branch -a ; Get-ChildItem my_robot_code | Select-Object Name
```

**確認: `my_robot_code` に5ファイル**（`rough_env_cfg.py` / `skyentific_poclegs.py` / `curriculums.py` / `rewards.py` / `rsl_rl_cfg.py`）**が入っていること。**

> **★ブランチに注意。** 手順書 B5 に「Ubuntu 側は `master`、Windows クローンは `main` という記録がある」という**未解決の食い違い**が残っている。`git branch -a` の出力を必ず見て、どのブランチに居るかを確定させてから進む。
> **`fix/falling-down-end-condition`（`aa9e806`）は「2週間前の歩けていた状態」。消さない。**

Skyentific 参考実装も clone する（`.gitignore` 除外なので本体には入っていない）:

```
cd D:\\haruto\\slope-climbing-robot ; New-Item -ItemType Directory -Force -Path references | Out-Null ; cd references ; git clone https://github.com/Skyentific/BipedalRobotSim.git ; Get-ChildItem
```

> **★URL は未確認。** clone が 404 で失敗したら、**Alienware 側の `references/BipedalRobotSim/.git/config` に書いてある実際の remote を見るのが正解**（Alienware 復旧後）。それまでは、この段階で止めて先に §8（USD）と並行して進める。

---

## 7. 段階6: Windows での symlink 問題（★Linux と違うところ）

Alienware では `my_robot_code/` の実体に **symlink** を張って、`references/BipedalRobotSim/skyentific_poclegs/...` から読ませていた（手順書 B5）。

**Windows で symlink を作るには管理者権限か開発者モードが要る。借り物のマシンでは頼みにくい。**

**代わりにハードリンクを使う。** 同じドライブ（D:）の中なら**管理者権限なしで作れて、symlink と同じく「実体は1つ」になる。** `my_robot_code/` を編集すれば学習に即反映される、という性質は変わらない。

- **ファイル → `mklink /H`（ハードリンク）**
- **フォルダ → `mklink /J`（ジャンクション）**

**`mklink` は PowerShell のコマンドではなく cmd の組み込みコマンド。** PowerShell から使うときは `cmd /c` を前に付ける。

> **★リンク先のパスは、Skyentific リポジトリの実際のフォルダ構成を見てから決める。** 手順書 B5 の記述だけで推測して作らない。clone 後に該当の5ファイルがどこにあるかを `Get-ChildItem -Recurse -Filter rough_env_cfg.py` で実測してから、実名を埋めたコマンドを組む。

**タスク登録の1行も必要**（手順書 B8）。自分用の clone なので遠慮なく入れてよい。

```
cd D:\\haruto\\IsaacLab ; Select-String -Path scripts\\reinforcement_learning\\rsl_rl\\train.py,scripts\\reinforcement_learning\\rsl_rl\\play.py -Pattern \"skyentific_poclegs\"
```

**何も出なければ未追加。** `train.py` と `play.py` の両方に `import skyentific_poclegs  # noqa: F401` を足す。**足す前に `.bak_taskimport` を取る。**

---

## 8. ★ 最大の未解決: USD が無い

**`my_robot_code/` の5ファイルは GitHub にあるが、ロボット本体（USD と STL）は入っていない。** `.gitignore` で `*.usd` / `*.stl` / `**/usd/` を除外しているため（手順書 B5）。

**学習を回すには USD が要る。** 入手経路は2つ。

| 経路 | 内容 | 判断 |
|---|---|---|
| **① Alienware から救出** | `onshape_export/myrobot_dummy/usd*` と `assets/merged/` を取り出す | Alienware が不安定で、起動しても数分〜十数分で落ちる。**当てにしにくい** |
| **★② Onshape から再エクスポートし直す** | 手順書 B3 の段階2〜5 を**この機体で**実行する | **Alienware に依存しない。数時間。こちらが本線** |

**②を選ぶ強い理由がある。** 手順書 B2 の通り、**現行の USD は木構造が壊れた版**（右脚4関節・左脚6関節）で、**どのみち再エクスポートが必要**だった。CAD 側は 2026-09-14 に修正済み（インスタンス先頭を胴体 `Part 1 <6>` に変更）。**救出しても捨てるものを救出することになる。**

**→ USD は「救出」ではなく「作り直し」が本筋。** 手順は `claude/urdf_reexport_instruction.md`。

### ②をこの機体でやるときの未確認事項

- **`onshape-to-robot` が Windows で動くか未確認。** まず `python -m pip install onshape-to-robot` してから `onshape-to-robot --version` が通るか見る。
- **Onshape API キーが要る。** Alienware の `onshape_export/.env` にあるが、**`.gitignore` 除外なので GitHub には無い。** Onshape の管理画面で**新しいキーを発行し直すのが早い**（`cad.onshape.com` 右上アイコン → My account → 左メニュー Developer → API keys）。**キーはチャットに貼らない。ターミナルか `.env` ファイルにだけ書く**（手順書 A1）。
- **再エクスポート前に、インスタンス一覧の先頭が `Part 1 <6>`（胴体）であることをブラウザで目視する**（手順書 B3 段階1）。

### チェックポイントについて

**`model_11998.pt`（2週間前の歩けていた方策）は Alienware の中にしかない。**

ただし **B2 の通り、木構造を直した機体では既存チェックポイントは全部無効になる。** 再エクスポートする以上、**学習はどのみちゼロからやり直し。** 救出の価値は「過去の比較対象」としてのみ残る。**優先度は下がった。**

---

## 9. 学習コマンド（Windows 版・1行）

> **★これらは USD が入って段階7まで通ってから使う。** それまでは実行できない。
> **★実行前に必ず `conda activate D:\\haruto\\envs\\isaac_env` してあること。** Alienware で「venv 未起動」が原因のエラーを2回踏んでいる（手順書 A2）。

**テスト起動（64env / 20iter）:**
```
conda activate D:\\haruto\\envs\\isaac_env ; cd D:\\haruto\\IsaacLab ; .\\isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 64 --max_iterations 20 --headless
```

**本番学習:**
```
conda activate D:\\haruto\\envs\\isaac_env ; cd D:\\haruto\\IsaacLab ; .\\isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 4096 --max_iterations 1500 --headless
```

**録画（遠隔から歩容を見る）:**
```
conda activate D:\\haruto\\envs\\isaac_env ; cd D:\\haruto\\IsaacLab ; .\\isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\play.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 50 --headless --video --video_length 400
```

**停止は Ctrl+C。途中で止めてもチェックポイントは残る。**

### ★ 3090 Ti での基準値は取り直す

手順書 A5 の実測基準値（**VRAM 5.4GB / 12GB、GPU 63℃、1.0〜1.2秒/iter**）は **RTX 4070 のもの**。3090 Ti は VRAM が倍で世代も違うので、**この機体で初回の本番学習を回したときの値を測り直して記録する。**

**`--max_iterations` の暴走に厳重注意**（手順書 A5）。**起動直後に iter 番号を目視**し、想定と違えば即 Ctrl+C。

---

## 10. 詰まったときの確認コマンド

| 症状 | 打つコマンド |
|---|---|
| どの conda 環境にいるか分からない | `conda info --envs ; python -c \"import sys; print(sys.executable)\"` |
| GPU が見えているか | `nvidia-smi ; python -c \"import torch; print(torch.cuda.is_available())\"` |
| D: の空きが心配 | `Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=3\" \\| Select-Object DeviceID,@{n='FreeGB';e={[math]::Round($_.FreeSpace/1GB,1)}}` |
| 誰かが GPU を使っていないか | `nvidia-smi` の下段のプロセス一覧を見る |
| Isaac Lab のバージョン | `Get-Content D:\\haruto\\IsaacLab\\VERSION ; git -C D:\\haruto\\IsaacLab log -1 --oneline` |

---

## 11. この機体で新しく分かったことは記録する

**手順書 A2 は Alienware 1台前提で書かれている。** この機体で確定した値（1iterの秒数、VRAM使用量、Windows特有の落とし穴）は、**手順書 A2・A5 を書き換えて反映する**（追記しない）。

**特に記録する価値があるもの:**

- `onshape-to-robot` が Windows で動いたかどうか
- ハードリンク方式が symlink と同等に機能したかどうか
- Skyentific リポジトリの実際の remote URL
- 3090 Ti での 4096env の実測値（秒/iter、VRAM、温度）
- TeamViewer 経由で描画系が落ちるか（Alienware と同じか）
