# 指示書: Onshape 再エクスポートで機体を作り直す（WRS共用PC の Claude Code 向け）

> 作成 2026-09-15。旧版 `instructions/urdf_reexport_instruction.md`（Alienware / Ubuntu 前提）を **WRS機（Windows 11）用に作り直したもの。**
> **読み手の Claude Code はこれまでの経緯を知らない前提で書いてある。必要な情報はこの文書に全部入れた。**
> 事前に、クラウド側で GitHub の中身と onshape-to-robot 1.8.3 のソースを読んで確認した事実を反映してある（§0-3）。**ただし WRS機の実物で必ず再確認すること。**

---

## 0. あなたの状況

### 0-1. マシン

- **あなたが動いているのは WRS の共用 Windows 11 デスクトップ（RTX 3090 Ti）。Alienware（Ubuntu）ではない。** Alienware は 2026-09-13 から故障中。Ubuntu 前提の記憶や手順（`~/projects/...`、`source .../activate`、`./isaaclab.sh`）は**このマシンでは使わない。**
- 最初に確認: `powershell -Command \"hostname; (Get-CimInstance Win32_OperatingSystem).Caption; nvidia-smi --query-gpu=name --format=csv\"` → **`Windows 11` と `RTX 3090 Ti` が出なければ作業を始めず報告。**
- Bash ツールは Git Bash のことが多い。PowerShell 固有のものは `powershell -Command \"...\"``cmd /c \"...\"` で包む。

### 0-2. ★ 共用PCの掟（環境構築時と同じ。必ず守る）

1. **書き込むのは `D:\\Tominaga\\` の中だけ。** 他人の環境（`C:\\Jerry\\IsaacLab`、`D:\\IsaacLab`、他の conda 環境）は読むのみ。
2. **C: に大きいものを置かない**（空き約41GB）。conda 環境は `--prefix` で D: に作る。pip キャッシュは `PIP_CACHE_DIR=D:\\Tominaga\\cache\\pip`。
3. `git config --global`・`setx`・レジストリ・Windows の証明書ストアは触らない。環境変数は**その場限り**で設定する。
4. **他人のプロセスを止めない。** GPU を数分以上使う前はユーザーに一言確認。
5. **ファイルを書き換える前は `.bak_変更内容` でバックアップ。**
6. **ユーザーの指示があるまで commit / push しない。**

### 0-3. 構築済みの環境（`reference/wrs_pc_environment.md` より）

| 項目 | 値 |
|---|---|
| Isaac 用 conda 環境 | `D:\\Tominaga\\envs\\isaac_env`（Python 3.11.16 / Isaac Sim 5.1.0 / torch 2.7.0+cu128 / **tensordict 0.7.0 固定**） |
| Isaac Lab | `D:\\Tominaga\\IsaacLab`（2.3.2 / `b4c3210247`）。`train.py` / `play.py` に `import skyentific_poclegs` 追加済み |
| 自作リポジトリ | `D:\\Tominaga\\slope-climbing-robot`（ブランチ `main`、**中身は 2026-08-21 版**） |
| 参考実装 | `D:\\Tominaga\\slope-climbing-robot\\references\\BipedalRobotSim`（editable インストール済み） |
| 自作5ファイル | `my_robot_code\\` ↔ 参考実装側が**ハードリンク**（git 操作やエディタ保存で切れる。`Get-FileHash` で確認） |
| 証明書 | **Avast の HTTPS 検査で SSL 検証が落ちる。** `D:\\Tominaga\\cache\\certs\\combined-ca-bundle.pem` をセッション限りの環境変数で指定して回避 |

### 0-4. 事前にクラウド側で確認済みの事実（WRS機で再確認はする）

| 事実 | 意味 |
|---|---|
| GitHub に `onshape_export\\myrobot_dummy\\config.json` / `robot_sim.urdf`（08-21 版・旧木構造）/ `rename_links_dummy.py` / `set_limits_dummy.py` が**入っている** | config.json は作り直さなくてよい。`robot.urdf`・STL・USD・`.env` は無い |
| config.json の `url` = `https://cad.onshape.com/documents/d103e836077cf07efd7a6f0f/w/5f12ac3c351e45b12f00dce2/e/8f867c9398c906dbec790638`、`no_dynamics:false`、`merge_stls:\"all\"` | ワークスペース URL なので**最新状態（＝木構造修正後）**を取りに行く |
| **onshape-to-robot 1.8.3（PyPI 最新）の根の選び方:** `assembly.py` の `process_mates()` が最初に `make_body(rootAssembly.instances[0])` を呼び、以後 merge で**小さい body id を残す** → `build_trees()` が body id 順に根を選ぶ | **「インスタンス一覧の先頭 ＝ base」は 1.8.3 の実装どおり。** 実行ログにも `Found N root nodes:` と根の名前が出る |
| 1.8.3 の依存は `numpy / requests / commentjson / colorama / numpy-stl / transforms3d / python-dotenv` のみ（pybullet 等は extra） | Windows でもビルド不要で入るはず |
| 1.8.3 は `.env` を**カレントディレクトリから上へ**探す（`find_dotenv(usecwd=True)`）。変数は `ONSHAPE_API` / `ONSHAPE_ACCESS_KEY` / `ONSHAPE_SECRET_KEY` | `.env` は `onshape_export\\.env` に置けばよい（`.gitignore` の `**/.env` で除外済み） |
| 1.8.3 の config は `use_collisions_configuration` を読んでいない | 残っていても無害。削らない |
| **1.8.3 は mesh パスを `os.path.relpath` で作り `package://` を付ける** | **Windows では `package://assets\\merged\\part_1_visual.stl` のようにバックスラッシュになる可能性が高い。** Step 7 で `/` に直す |
| Onshape の Mate に limit が無い関節は `effort=\"10\" velocity=\"10\" lower=-π upper=π` で出る | Step 8 で扱う |
| `my_robot_code\\skyentific_poclegs.py`（08-21 版）の `usd_path` は既に `{ISAAC_ASSET_DIR}/robots/myrobot_dummy/robot.usd` | **このファイルは今回編集しない。** USD を置く場所だけ合わせる |
| `ISAAC_ASSET_DIR` = `references\\BipedalRobotSim\\skyentific_poclegs\\skyentific_poclegs\\assets` | USD の置き場所は `...\\assets\\robots\\myrobot_dummy\\`（`URDF+USD\\` 以下の同名フォルダではない） |
| `convert_urdf.py`（Isaac Lab `b4c3210247`）の引数に `--joint-stiffness` / `--joint-damping` / `--joint-target-type` / `--merge-joints` / `--fix-base` がある | Ubuntu 時と同じ引数で変換できる |

---

## 1. ゴールと停止点

**ゴール:** Onshape（004_sim ＝ダミー円柱版アセンブリ）から再エクスポートし、**左右対称な木構造・正しい質量の URDF → USD** を作り、`Velocity-Rough-Skyentific-Poclegs-v0` の 64 env / 20 iter テスト起動を通す。

**背景（一行）:** 以前の URDF は、onshape-to-robot が「インスタンス一覧の先頭」を根にする仕様のせいで、先頭だった右股ブラケット（0.065 kg）が base になり「右脚4関節・左脚6関節」に化けていた。2026-09-14 に Onshape で胴体 `Part 1 <6>` を先頭に並べ替えた（Mate は無変更）。**再エクスポートでそれが本当に直るかを検証するのが主目的。**

期待値（Onshape API で実測済み）:

| 項目 | 期待値 |
|---|---|
| 根リンク | 胴体（`Part 1 <6>` + `Part 1 <12>` + AK10-9 ×2）＝ **約 2.918 kg** |
| 木構造 | base から左右2本、それぞれ **HR → HAA → HFE → KFE → FFE の5関節** |
| link / joint | **11 / 10（revolute 10 / fixed 0）** |
| 総質量 | **10.1058 kg** |

**★停止点（ここでは必ず報告して、ユーザーの返事を待つ）:**
- **停止点A（Step 3 の後）:** 道具とキーの準備ができた時点
- **停止点B（Step 5 の後）:** 再エクスポート結果の検算
- **停止点C（Step 8）:** 関節 limit / effort / velocity の値決め
- **停止点D（Step 10 の前）:** GPU を使うテスト起動の前

---

## 2. 鉄則

- **推測で進めない。** この文書・0-4 の事実も、WRS機の実物（ファイル・`--help`・ソース）で確認してから動く。食い違ったら止めて報告。
- **複数行 Python をターミナルに直貼りしない。** `D:\\Tominaga\\slope-climbing-robot\\tools\\` に `.py` として書いてから実行する。
- **`D:\\Tominaga\\IsaacLab` 本体は触らない**（`train.py` / `play.py` の import 追加は済み）。
- **API キー・シークレットをチャットに出さない／表示しない／commit しない。** `.env` の中身を `cat` しない。
- **ユーザーはターミナルの長文が苦手。** 報告は要点を日本語で、次にやることは1〜2個に絞る。コマンドを見せるときは**実行フォルダを明示し、山括弧プレースホルダを使わず、実名入りの1行の完成形**で。

---

## Step 0 — 現状確認（読むだけ）

1. `git -C D:\\Tominaga\\slope-climbing-robot status --short` と `git -C D:\\Tominaga\\slope-climbing-robot log -1 --format=\"%h %ad %s\" --date=short`
2. `onshape_export\\myrobot_dummy\\` の中身一覧（`config.json` / `robot_sim.urdf` / `rename_links_dummy.py` / `set_limits_dummy.py` があるはず。`robot.urdf`・`assets\\`・`usd\\` は無いはず）
3. 自作5ファイルのハードリンクが生きているか（`my_robot_code\\` と参考実装側の `Get-FileHash` 比較。対応表は `reference/wrs_pc_environment.md` §1）
4. `...\\assets\\robots\\` の中身（`myrobot_dummy\\` はまだ無いはず）
5. C: / D: の空き容量
6. **証明書の環境変数:** 環境構築時にどの変数名で `combined-ca-bundle.pem` を指定したか（`SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` / `PIP_CERT` / `GIT_SSL_CAINFO` / `CONDA_SSL_VERIFY` など）。**記録が無く、ユーザーが知りたがっている。分かる範囲で報告に含める。**
   - **onshape-to-robot は `requests` を使うので `REQUESTS_CA_BUNDLE` が必須**（`requests` は `SSL_CERT_FILE` を見ない）。

## Step 1 — onshape-to-robot 専用の小さい conda 環境を作る

**`isaac_env` には入れない。** tensordict 固定・torchaudio 消失など壊れやすい前歴があり、numpy 等を触られるリスクを避ける。依存は軽いので別環境で数百MB。

```
cmd /c \"set PIP_CACHE_DIR=D:\\Tominaga\\cache\\pip&& set CONDA_PKGS_DIRS=D:\\Tominaga\\cache\\conda&& conda create --prefix D:\\Tominaga\\envs\\onshape_env python=3.11 -y\"
```

（証明書エラーが出たら、Step 0-6 で分かった変数を同じ `set` で足して再実行。）

```
cmd /c \"set PIP_CACHE_DIR=D:\\Tominaga\\cache\\pip&& set PIP_CERT=D:\\Tominaga\\cache\\certs\\combined-ca-bundle.pem&& D:\\Tominaga\\envs\\onshape_env\\python.exe -m pip install onshape-to-robot==1.8.3\"
```

**確認:**
- `D:\\Tominaga\\envs\\onshape_env\\Scripts\\onshape-to-robot.exe` が存在する
- `D:\\Tominaga\\envs\\onshape_env\\python.exe -m pip show onshape-to-robot` → Version 1.8.3
- **`D:\\Tominaga\\envs\\isaac_env\\python.exe -m pip show tensordict` が 0.7.0 のまま**（別環境なので変わらないはずだが念のため）

## Step 2 — ★ 根の選び方を実物で確認する

```
powershell -Command \"Select-String -Path D:\\Tominaga\\envs\\onshape_env\\Lib\\site-packages\\onshape_to_robot\\assembly.py -Pattern 'make_body\\(top_level_instances\\[0\\]','def build_trees','root_nodes.append','body1_id > body2_id' | Select-Object LineNumber,Line\"
```

**判定:**
- 4つとも見つかる → 0-4 の読み（**インスタンス一覧の先頭の剛体グループが根**）どおり。次へ
- 見つからない／別の書き方 → **止めて報告**（周辺を読んで、根をどう選んでいるかを要約する）

`onshape_export\\myrobot_dummy\\config.json` も表示し、0-4 の値（`url` / `no_dynamics:false` / `merge_stls:\"all\"` / `output_format:\"urdf\"`）と一致するか確認する。**書き換えない。**

## Step 3 — Onshape API キーを用意する（ユーザーの作業）

**キーはユーザー自身が発行し、ユーザー自身がファイルに書く。あなたはキーを見ない。**
Alienware の `.env` は持ち出せていないので新規発行が要る。

1. まず `.env` が git 除外されることを確認:
   `git -C D:\\Tominaga\\slope-climbing-robot check-ignore -v onshape_export/.env` → `.gitignore` の `**/.env` が表示されれば OK
2. ユーザーに次を案内する（**GUI は画面のどこを押すかまで分解**。ユーザーは Onshape 初心者）:
   - ブラウザで `https://cad.onshape.com` を開く → **右上の自分のアイコン** → **「My account」** → 左メニュー **「Developer」** → **「API keys」** → **「Create new API key」**（権限は読み取りでよい）→ Access key と Secret key が表示される（**Secret はこの画面でしか見られない**）
   - ※ `dev-portal.onshape.com` は OAuth 用なのでそこではない
   - WRS機でメモ帳を開き、次の3行を書いて **`D:\\Tominaga\\slope-climbing-robot\\onshape_export\\.env`** として保存（「ファイルの種類: すべてのファイル」にして `.env.txt` にならないように）:
     ```
     ONSHAPE_API=https://cad.onshape.com
     ONSHAPE_ACCESS_KEY=ここにAccess key
     ONSHAPE_SECRET_KEY=ここにSecret key
     ```
3. あなたは**存在と行数だけ**確認する（中身は表示しない）:
   `powershell -Command \"Test-Path D:\\Tominaga\\slope-climbing-robot\\onshape_export\\.env; (Get-Content D:\\Tominaga\\slope-climbing-robot\\onshape_export\\.env | Where-Object { $_ -match '^ONSHAPE_(API|ACCESS_KEY|SECRET_KEY)=' }).Count\"` → `True` と `3`
4. **ユーザーに、Onshape で config.json の URL を開いて、左のインスタンス一覧の一番上が `Part 1 <6>` になっているか目で見てもらう。** 先頭が違えば再エクスポートしても直らない。

### ★ 停止点A — ここまでを報告して待つ

報告: Step 0 の状態／onshape_env の作成結果／Step 2 の判定／config.json／`.env` の有無と行数／先頭インスタンスの目視結果／証明書の変数名。

## Step 4 — バックアップと再エクスポート

1. `onshape_export\\myrobot_dummy\\bak_prereexport_20260915\\` を作り、`robot_sim.urdf` と `config.json` をコピー（git に 08-21 版があるが、明示的に残す）。
2. 再エクスポート（**必ず `onshape_export` フォルダで実行**。ログは全文ファイルに残す）:

```
cmd /c \"cd /d D:\\Tominaga\\slope-climbing-robot\\onshape_export && set PYTHONUTF8=1&& set PYTHONIOENCODING=utf-8&& set REQUESTS_CA_BUNDLE=D:\\Tominaga\\cache\\certs\\combined-ca-bundle.pem&& D:\\Tominaga\\envs\\onshape_env\\Scripts\\onshape-to-robot.exe myrobot_dummy > myrobot_dummy\\export_log_20260915.txt 2>&1\"
```

- 242 部品のメッシュ取得で数分〜十数分。**完了まで無出力が正常。**
- `PYTHONUTF8` / `PYTHONIOENCODING` は、Windows のコンソール文字コード（cp932）で色付き出力や記号が落ちるのを防ぐため。
- 終わったらログの末尾40行と、**`Found ... root nodes:` の直後の行**を見る:
  `powershell -Command \"Select-String -Path D:\\Tominaga\\slope-climbing-robot\\onshape_export\\myrobot_dummy\\export_log_20260915.txt -Pattern 'root node' -Context 0,3\"`
  → **root node が1個で、名前が `Part 1 <6>` 系なら期待どおり。**

**止めて報告するケース:**
- `SSLError` / `CERTIFICATE_VERIFY_FAILED` → 証明書の指定。1回だけ変数を見直して再試行、ダメなら報告
- `401` / `403` / 認証エラー → キーの問題。ユーザーに `.env` を見直してもらう（あなたは中身を見ない）
- `KeyError: 'mass'` → 本物モーター版（外部参照）を見ている。URL が違う
- root node が2個以上、または先頭が `Part 1 <6>` でない

## Step 5 — ★★ 検算（今回の成果の検証）

`D:\\Tominaga\\slope-climbing-robot\\tools\\verify_export.py` を書き、`D:\\Tominaga\\envs\\onshape_env\\python.exe` で新しい `onshape_export\\myrobot_dummy\\robot.urdf` に対して実行する（numpy は onshape_env に入っている）。引数で URDF パスを受け取れるようにし、Step 6 以降も使い回す。

出すもの:
1. **木構造（`parent -> child (joint名)`）を base から深さ付きで** → **base から2本、それぞれ HR→HAA→HFE→KFE→FFE の5関節なら成功。** 4と6に分かれたら失敗
2. **base（根）の質量** → **約 2.918 kg。1 kg を切ったら根がずれている**
3. link 数 / joint 数 / type 内訳 → **11 / 10 / revolute 10 / fixed 0**
4. 全リンクの質量一覧と**合計** → **10.1058 kg と一致するか**（丸めで ±0.001 程度は可）
5. 慣性の非対角成分（`ixy` / `ixz` / `iyz`）が全リンクでゼロでないか → `no_dynamics:false` で実値が取れた証拠
6. **左右対（`LR_xx` の child と `LL_xx` の child）の質量を並べて比較** → HR/HAA/HFE/KFE/FFE すべてで一致するか
7. 全 joint の `axis` / `origin xyz rpy` / `limit`
8. mesh `filename` の書式（`package://` 付きか、区切りが `\\` か `/` か）と、**実ファイルの存在チェック（MISSING 件数）**
9. ゼロ姿勢の順運動学（全リンク原点のワールド座標）を `tools\\fk_new.txt` に保存し、**左右対のリンクの y 座標が符号反転・x/z がほぼ一致するか**を併記
   URDF の rpy は外因性 XYZ ＝ `R = Rz(yaw) @ Ry(pitch) @ Rx(roll)`

### ★ 停止点B — 結果を表で報告して待つ

特に: **5/5 になったか／根の質量／合計質量／非対角慣性／左右対の質量が一致したか／mesh パスの区切り文字。**

## Step 6 — link 名の改名（★最大の落とし穴）

- **`rename_links_dummy.py` のハードコード表は絶対に使わない。** 連番 `part_1_N` は再エクスポートで変わり、**古い表は黙って別のリンクに名前を付ける。エラーは出ない。**
- **旧 `robot_sim.urdf`（git 版）との照合も使わない。** 旧版は木の根がずれていて、リンク名と実体が対応していない（旧 `lr_hr` は実は胴体だった）。
- **木構造から機械的に割り当てる:**
  - 根 → `base`
  - 各 joint の child に、joint 名を小文字にした名前を付ける（`LR_HR` の child → `lr_hr`、`LL_FFE` の child → `ll_ffe`）
  - joint 名は Onshape の `dof_` Mate 名がそのまま入っているので信用できる。**joint 名は大文字のまま変えない**
- 手順:
  1. `robot.urdf` を `robot_sim.urdf` に**上書きコピー**（Step 4 でバックアップ済み）。`robot.urdf` は原本として触らない
  2. `tools\\rename_links_from_tree.py` を書く: `robot_sim.urdf` を XML として読み、上の規則で対応表を作って表示 → `<link name>` と joint の `<parent link>` / `<child link>` だけを書き換える。**mesh の `filename` は触らない**。文字列置換ではなく XML の属性で書き換える（`part_1` が `part_1_2` に誤マッチする事故を構造的に避ける）
  3. 実行後、`verify_export.py robot_sim.urdf` を再実行し、**link 名一覧・木構造・MISSING 件数**を確認
- 期待するリンク名: `base` / `lr_hr lr_haa lr_hfe lr_kfe lr_ffe` / `ll_hr ll_haa ll_hfe ll_kfe ll_ffe`

## Step 7 — mesh パスの整形

`robot_sim.urdf` の mesh `filename` について:
1. 先頭の `package://` を除去
2. **`\\` を `/` に統一**（Windows の `os.path.relpath` 由来）
3. 結果が `assets/merged/xxx.stl` の形になること

`tools\\` のスクリプトで XML 属性として書き換え（`.bak_meshpath` を取ってから）、`verify_export.py robot_sim.urdf` で **MISSING 0 件**を確認。

## Step 8 — ★ 関節 limit / effort / velocity（停止点C。値は決めない）

1. 再エクスポート直後の全 joint の `lower / upper / effort / velocity` を表で報告する（Mate に limit が無ければ ±π / 10 / 10 のはず）
2. **Isaac Lab 2.3.2 で URDF の effort / velocity が学習に効くのか**を実物で確認して報告する:
   - `my_robot_code\\skyentific_poclegs.py` の actuators は `DelayedPDActuatorCfg`（08-21 版: hr 24/23、haa 30/15、hfe+kfe 30/20、ffe 20/23 [N·m / rad/s]）
   - `D:\\Tominaga\\IsaacLab\\source` を grep して、明示（explicit）アクチュエータのとき `effort_limit` / `effort_limit_sim` / `velocity_limit_sim` と USD の joint drive の max force / max velocity がどう決まるか（URDF の値が上書きされるのか残るのか）を要約
   - **関節の可動範囲（lower / upper）は USD に入り、`dof_pos_limits` 報酬と物理に効く**はず。これも実装で確認
3. **やってはいけないこと:** 2026-09-06 の Skyentific 値の再適用（モーターが違う）／`set_limits_dummy.py` の無断実行／自分で値を決めること
4. 参考として併記: **HR・HAA・KFE = AK10-9（定格 18 / ピーク 53 N·m）、HFE・FFE = AK80-9（定格 9 / ピーク 22 N·m）。** 定格とピークのどちらを使うかは**未決（ユーザー判断）**。なお 08-21 版の actuators は HFE と KFE を同じグループにしていて、モーターの割り当てと合っていない（今回は直さず、報告に一言添える）

**報告して、ユーザーの指示を待つ。** 指示が「そのまま進めて」なら URDF の limit は再エクスポート値のまま Step 9 へ。

## Step 9 — USD 変換と配置

1. 変換（**isaac_env を有効化して、`D:\\Tominaga\\IsaacLab` で実行**）:

```
cmd /c \"conda activate D:\\Tominaga\\envs\\isaac_env && where python && cd /d D:\\Tominaga\\IsaacLab && isaaclab.bat -p scripts\\tools\\convert_urdf.py D:\\Tominaga\\slope-climbing-robot\\onshape_export\\myrobot_dummy\\robot_sim.urdf D:\\Tominaga\\slope-climbing-robot\\onshape_export\\myrobot_dummy\\usd\\robot.usd --joint-stiffness 0.0 --joint-damping 0.0 --joint-target-type none --headless\"
```

   - **`where python` の1行目が `D:\\Tominaga\\envs\\isaac_env\\python.exe` であること**（他人の環境で実行しない）
   - 実行前に `isaaclab.bat -p scripts\\tools\\convert_urdf.py --help` で引数名を確認
   - fixed joint 0 なので `--merge-joints` 不要。**`--fix-base` は付けない**（地面固定になる）
   - 終了しない場合（ログに保存完了が出たのに戻らない）は Ctrl+C でよい
2. `usd\\robot.usd`（数KB の入れ物）と `usd\\configuration\\`（`robot_base.usd` / `robot_physics.usd` 等）が**今日のタイムスタンプで**あることを確認
3. 見本アセットフォルダへ配置（**学習が読むのはこちら**。忘れると古い／無い USD で回る）:
   - 配置先: `D:\\Tominaga\\slope-climbing-robot\\references\\BipedalRobotSim\\skyentific_poclegs\\skyentific_poclegs\\assets\\robots\\myrobot_dummy\\`
   - 既にフォルダがあれば `myrobot_dummy.bak_20260915` にリネームしてから
   - `robot.usd` と `configuration\\` を**同じ位置関係で**コピー
   - `robot.usd` がメッシュを相対パスで参照していることを確認（Isaac Sim 経由のスクリプトで読むか、コピー先でロードできるかは Step 10 で分かる）
4. C: の Omniverse キャッシュ（`C:\\Users\\WRS\\AppData\\Local\\ov`）の増え方を一言報告

## Step 10 — テスト起動（★停止点D: 実行前にユーザーに確認）

GPU を数分使うので、**実行前にユーザーの了承を取る。**

```
cmd /c \"conda activate D:\\Tominaga\\envs\\isaac_env && where python && cd /d D:\\Tominaga\\IsaacLab && isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 64 --max_iterations 20 --headless\"
```

- 起動前に `D:\\Tominaga\\envs\\isaac_env\\python.exe -m pip show tensordict` が **0.7.0** であることを確認（違うと access violation で落ちる）
- **起動直後に iteration 番号が 0 から始まっているか目視**
- **20 iter 完走 = ロード・joint 10・観測・行動が通った。** 初期方策なので `Episode_Termination/base_contact` が高く episode が短いのは正常
- `ValueError: ... base: []` 等 → リンク名の不一致。env_cfg が要求する body 名を `my_robot_code\\rough_env_cfg.py` から grep して報告
- **注意:** 今回から `base` が本当に胴体になるので、`base_contact` 終了条件や `add_base_mass` イベントの効き方が以前と変わる。挙動が変わっても異常ではない
- 報告: 完走可否、秒/iter、VRAM、終了理由の内訳（最後の iter）

## Step 11 — 後片付けと報告

1. `git -C D:\\Tominaga\\slope-climbing-robot status --short` を表示。**`.env` / `*.stl` / `*.usd` / `*.part` / `assets\\merged` が出ていないこと。** 出ていたら止めて報告
2. commit 候補の一覧（`robot_sim.urdf`、`tools\\verify_export.py`、`tools\\rename_links_from_tree.py`、パス整形スクリプト、`export_log_20260915.txt` を含めるか）を提示するだけ。**commit / push はユーザーの指示を待つ**
3. ハードリンク5組の `Get-FileHash` をもう一度比較（今回 git 操作をしていなければ切れていないはず）
4. ユーザーに、**Onshape の API キーを使い終わったら Revoke するか `.env` を削除する**よう一言勧める（共用PCのため）

---

## 注意（全体）

- **既存チェックポイントは機体が変わるので全部無効。** 学習はやり直し。
- **2026-09-08 のトルク実測（HFE 43〜48 / KFE 60 N·m など）は壊れた URDF で取ったもの。** 取り直し対象。
- **WRS機のコードは 08-21 版。** 手順書に書かれた9月の報酬・リミット・`noise_std_type=\"log\"` などは入っていない。今回はそれを直さない（テスト起動が通ることの確認までが範囲）。
- Onshape で**インスタンスの並び順を動かさない／「固定（Fixed）」を使わない**（ユーザーにも伝える）。

## 報告してほしいこと（まとめ）

| いつ | 内容 |
|---|---|
| 停止点A | 現状（git・ハードリンク・空き容量）／onshape_env の作成結果／根の選び方の grep 結果／config.json／`.env` の有無と行数／先頭インスタンスの目視／**証明書の環境変数名** |
| 停止点B | **木構造 5/5 か／根の質量／合計質量／非対角慣性／左右対の質量一致／mesh パスの区切り** |
| Step 6–7 | リンク名の対応表（旧 part 名 → 新名）／MISSING 0 件 |
| 停止点C | 再エクスポート直後の limit / effort / velocity／URDF 値が学習に効くかの調査結果 |
| Step 9 | USD の生成・配置結果／C: キャッシュの増分 |
| Step 10 | テスト起動の可否・秒/iter・VRAM・終了理由 |
| Step 11 | git status／commit 候補／ハードリンク確認 |
