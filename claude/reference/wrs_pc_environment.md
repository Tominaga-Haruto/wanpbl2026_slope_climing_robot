# WRS共用PC の Isaac Lab 環境（構築完了記録）

> 作成 2026-09-15。WRS機上の Claude Code が `instructions/wrs_pc_host_instruction.md` に沿って構築し、その完了報告をもとに書いた。
> **この機体で柱Aを進めるときの「今の正しい状態」。** 構築手順そのものは `instructions/wrs_pc_host_instruction.md`。
> 2026-09-15 夜: 再エクスポート作業（`instructions/wrs_urdf_reexport_instruction.md`）の停止点A の報告で、シェル構成と証明書の変数名が判明したので §3-1・§4 を更新。

---

## 1. 構成（確定値）

| 項目 | 値 |
|---|---|
| 機体 | WRS 共用 Windows 11 Education デスクトップ（ホスト名 `DESKTOP-MACG22A`、TA さんが主に使用）。TeamViewer 固定パスワードで接続 |
| GPU | RTX 3090 Ti 24.5GB |
| 作業フォルダ | **`D:\\Tominaga\\`**（これ以外に書き込まない） |
| conda 環境 | `D:\\Tominaga\\envs\\isaac_env`（Python **3.11.16**、約15.4GB） |
| conda 環境（CAD 書き出し用） | `D:\\Tominaga\\envs\\onshape_env`（Python 3.11.16 / **onshape-to-robot 1.8.3**）。isaac_env を汚さないため分離（2026-09-15） |
| Isaac Sim | **5.1.0**（pip 版、isaac_env 内） |
| Isaac Lab | `D:\\Tominaga\\IsaacLab`（**2.3.2 / `b4c3210247`**。共用の `D:\\IsaacLab` と同じ版） |
| torch | **2.7.0+cu128** / torchvision 0.22.0+cu128 / torchaudio 2.7.0+cu128 |
| tensordict | **0.7.0 に固定**（§3-3） |
| キャッシュ | `D:\\Tominaga\\cache\\`（pip / conda / 証明書） |
| 自作リポジトリ | `D:\\Tominaga\\slope-climbing-robot`（ブランチ **`main`**。**2026-09-16 に `6ede75b`（再エクスポート・軸修正・limit・初期姿勢）を push 済み。報酬などそれ以外は 08-21 版のまま**＝§1a） |
| 参考実装 | `D:\\Tominaga\\slope-climbing-robot\\references\\BipedalRobotSim`（`SkyentificGit/BipedalRobotSim`、commit `33aaad3`） |
| Onshape API キー | `D:\\Tominaga\\slope-climbing-robot\\onshape_export\\.env`（2026-09-15 新規発行。git 除外。**共用PCなので使い終わったら Revoke**） |
| LongPathsEnabled | 1（有効） |
| ディスク | C: 42.4GB → 41GB（構築直後） → 43.6GB（09-15 夜） / D: 534GB |

### 自作5ファイルのハードリンク（SHA256 一致確認済み。09-15 夜もリンク数2で健在）

| my_robot_code | 参考実装側（`skyentific_poclegs\\skyentific_poclegs\\` 以下） |
|---|---|
| `skyentific_poclegs.py` | `assets\\skyentific_poclegs.py` |
| `rough_env_cfg.py` | `tasks\\locomotion\\velocity\\config\\skyentific_poclegs\\rough_env_cfg.py` |
| `rsl_rl_cfg.py` | `tasks\\locomotion\\velocity\\config\\skyentific_poclegs\\agents\\rsl_rl_cfg.py` |
| `curriculums.py` | `tasks\\locomotion\\velocity\\mdp\\curriculums.py` |
| `rewards.py` | `tasks\\locomotion\\velocity\\mdp\\rewards.py` |

`train.py` / `play.py` に `import skyentific_poclegs  # noqa: F401` 追加済み。参考実装は `--no-deps` で editable インストール（`setup.py` の `torch==2.5.1` 固定を回避）。

### ★ `D:\\Tominaga` をリネームしない

**フォルダ名を変えると壊れる。** conda 環境（`python.exe` のパスや `Scripts\\*.exe` のランチャー）、editable インストール（参考実装のパス）、Isaac Lab のビルド済みパスが絶対パスを埋め込んでいる。**エラーの出方が分かりにくい壊れ方をする。**
2026-09-15 にユーザーから `D:\\pbl2026` へのリネーム案が出たが保留。**どうしても変えるなら「新しい名前で環境を作り直す」扱い**（conda 環境2つの再作成・参考実装の再インストール・ハードリンクの張り直し）。

---

## 1a. ★ GitHub の `main` は 2026-08-21 で止まっている（2026-09-15 判明）

WRS機で打った結果:

```
D:\\Tominaga\\slope-climbing-robot> git log -5 --format=\"%h %ad %s\" --date=short origin/main
b50a6ee 2026-08-21 Merge pull request #1 from Tominaga-Haruto/fix/falling-down-end-condition
aa9e806 2026-08-21 koronndarasyuuryousuruyounihanatta.kedo,korobunowoosoretearukanakunatta.
b029621 2026-08-21 Fix file name in README and update reference format #2
9565510 2026-08-21 Add initial README with parameter settings and references#1
4cc5f9d 2026-08-20 rewards.py と rsl_rl_cfg.py を symlink分離で追加
```

**結論: Alienware で 2026-08-21 以降に行った `my_robot_code/` の変更は GitHub に push されていなかった。** Alienware は故障中なので、それらは現状 Alienware の SSD の中にしか無い。

### 何を意味するか

- **WRS機の `my_robot_code/` 5ファイル（＝学習が読むファイル）は 08-21 の版。** `fix/falling-down-end-condition`（「転倒で終了するようになった版」＝手順書の「2週間前の歩けていた状態」）を main にマージした直後の状態に相当する。
- **手順書・handover に書かれている 08-21 以降の設定（例: 2026-09-06 の関節リミットの Skyentific 値反映、09-08 時点の報酬設定、`noise_std_type=\"log\"` の導入など）は、WRS機のコードには入っていない前提で扱う。** 文書とコードが食い違ったら、**コードは 08-21 版**と考えて grep で実物を確認する。
- 手順書 A6 に「Ubuntu 側は `master`」とあった。**GitHub に `master` が存在しないので、Alienware で `master` に commit していても push は一度も通っていなかった**と考えると整合する（推測。Alienware が起動したら `git log origin/master` / `git status` で確認）。

### まだ確認していないこと

- **他のブランチ（`kani_walk` / `original`）に 08-21 以降の commit があるか。** WRS機で `git -C D:\\Tominaga\\slope-climbing-robot log -3 --all --format=\"%h %ad %d %s\" --date=short` を打てば分かる。
- **失われた変更をどう扱うか。** 経路は「Alienware が起動したら SSD から `my_robot_code/` を救出して push」か「文書（手順書・handover・chats）の記述から WRS機で手で再現」。**再エクスポートで機体が変わるので、報酬まわりは再エクスポート後に改めて詰める余地もある。** 決めるのはユーザー。
- Alienware の救出優先度は「USD は作り直すので低い」としていたが、**`my_robot_code/` の未 push 分は作り直しが効かないので、救出対象に加える。** 容量は数十KBなので、起動できたら USB メモリか GitHub push で数秒で済む。

### 2026-09-16: push 再開

- `b50a6ee..6ede75b main -> main` で push 成功、`origin/main` の最新が `6ede75b` であることを確認。
- **WRS機の Claude Code の Bash からの `git fetch` は証明書未設定で失敗する**（push はユーザーが PowerShell で実行して成功）。git 用の変数（`GIT_SSL_CAINFO` のはず）は未検証。

### 再発防止

- **push したら、別マシン（または GitHub の画面）で `git log origin/ブランチ名` の日付を見て、本当に上がったか確認する。**
- ブランチは **`main`** に統一する。

---

## 2. 動作確認の結果

- 同梱タスク `Isaac-Velocity-Flat-Anymal-D-v0`（64 env / 5 iter）: 完走。約 0.9 秒/iter、VRAM 約 1.3GB
- **`Velocity-Rough-Skyentific-Poclegs-v0`（新 USD、64 env / 20 iter、`debug_vis=false`）: 完走（2026-09-16）。** 1.5〜2.3 秒/iter、VRAM 約 7.4GB。iter19 の終了理由 bad_orientation 99.5% / base_contact 1.2% / time_out 0%、episode 長 21.2 → 38.1 ステップ（初期方策なので想定内）
- **4096 env での基準値は未測定。** ロボットの USD ができて本番学習を回したときに取る

---

## 3. ★ この機体特有の落とし穴

1. **Avast の HTTPS 検査で SSL 検証が失敗する**（conda / pip / git / Python の requests すべて）。
   `D:\\Tominaga\\cache\\certs\\combined-ca-bundle.pem`（Avast のルート証明書を足した束）を作ってあり、**セッション限りの環境変数で指定して回避している**。Windows の証明書ストアもユーザー/システムの永続環境変数も変更していない（09-15 夜に Machine/User スコープに SSL 系変数が無いことを確認）。
   **道具ごとに変数が違う**（09-15 夜に判明・実証済みのもの）:

   | 道具 | 変数 | 状態 |
   |---|---|---|
   | conda | `CONDA_SSL_VERIFY` | 実証済み（`conda create` が通った） |
   | pip | `PIP_CERT` | 実証済み |
   | Python `requests`（onshape-to-robot） | `REQUESTS_CA_BUNDLE` | 09-15 の再エクスポートで使う予定。**`requests` は `SSL_CERT_FILE` を見ない** |
   | git | `GIT_SSL_CAINFO` のはず | 未確認（環境構築時に何を使ったかは記録なし） |

2. **`isaaclab.bat --install` が途中の git clone 失敗で黙って中断することがある**（証明書未設定で rl-games が落ち、rsl-rl-lib が入らなかった）。→ `isaaclab.bat --install rsl_rl` で個別に入れ直した。**インストール後は `python -m pip show rsl-rl-lib` で入っているか確認する。**
3. **tensordict の最新版（0.14.2）は Windows で access violation クラッシュする。** 0.7.0（rsl-rl-lib の最小要件）に下げて解消。**`isaaclab.bat --install` や pip の再実行で最新版に戻されうる。** 学習が理由不明のクラッシュをしたらまず `python -m pip show tensordict` を確認。
4. **torchaudio が isaacsim / torch の再インストールのたびに消える。** そのつど `torchaudio==2.7.0+cu128` を入れ直す。
5. **ハードリンクは git 操作で切れる。** `git pull` / `checkout` / 一部エディタの保存は、ファイルを作り直すのでリンクが外れ、**エラーは出ずに片方だけ古いまま学習が回る。** git 操作の後は5ファイルの `Get-FileHash` を比べる。
6. **`create_empty.py` は無限ループで自分では終わらない。** 起動ログを確認したら Ctrl+C（2026-09-15 に約2時間回り続けた）。
7. **Omniverse のキャッシュは C: に溜まる**（`C:\\Users\\WRS\\AppData\\Local\\ov`）。USD 変換や学習を重ねると増えるので、ときどき C: の空きを見る。
8. **conda は PowerShell からしか使えない**（`Invoke-Conda` エイリアス経由）。**cmd には conda が無い。** 指示書に `cmd /c \"conda activate ... && ...\"` と書いてあったら PowerShell に読み替える（09-15 夜に判明）。conda 不要なら `D:\\Tominaga\\envs\\...\\python.exe` や `Scripts\\*.exe` をフルパスで呼べば cmd でも動く。
9. **URDF→USD 変換（`convert_urdf.py`）は `isaacsim.asset.importer.urdf` **2.4.31** を要求する**（Isaac Lab `urdf_converter.py` が Isaac Sim 5.1 以上で pin。API も 2.4.30 と違い `set_merge_fixed_ignore_inertia` が無いと落ちる）。本来は Kit の拡張レジストリから自動取得されるが、**Avast のせいでレジストリに接続できない（Python 用の証明書変数は Kit には効かない）。**
   2026-09-15 の対処: 同じ Windows ユーザーの Kit キャッシュ `C:\\Users\\WRS\\AppData\\Local\\ov\\data\\exts\\v2\\` に既にあった `isaacsim.asset.importer.urdf-2.4.31+107.3.3.wx64.r.cp311` と依存の `omni.kit.pip_archive-5df61bf515266ea2` を、**isaac_env の isaacsim の extscache（2.4.30 が置いてある場所）へコピー**して解決。Isaac Lab のファイルは無変更。**isaacsim を入れ直すと消えるので、その時は同じコピーをやり直す。**
   変換時は `OMNI_KIT_ACCEPT_EULA=Y` も必要。**変換は失敗しても終了コード 0 を返す**ので、`usd\\robot.usd` の時刻で成否を判断する。
10. **学習起動で速度指令の矢印（`arrow_x.usd`、S3 から取得）が 300 秒タイムアウトして落ちる。** 学習には無関係な可視化なので、**起動コマンドに Hydra オーバーライド `env.commands.base_velocity.debug_vis=false` を付ける**（ファイル変更なし）。
11. **`.env` をメモ帳で作るときの事故**（09-15）: 「`.env` という名前のフォルダ」の中にファイルを作ってしまった／中身が `KEY=値` の3行形式になっていなかった。**確認は `Test-Path` と「`ONSHAPE_...=` で始まる行が3行あるか」の件数だけで行う（中身は表示しない）。**

### 任意（TA さんの許可が要る）

- Avast のスキャン除外に `C:\\Users\\WRS\\AppData\\Local\\ov` と `C:\\Users\\WRS\\AppData\\Local\\NVIDIA` を入れると起動が速くなる可能性がある。必須ではない。

---

## 4. 毎回の起動（PowerShell で）

- シェルは **PowerShell**（§3-8）
- 環境の有効化: `conda activate D:\\Tominaga\\envs\\isaac_env`（CAD 書き出しは `D:\\Tominaga\\envs\\onshape_env`）
- **有効化したら `where.exe python` の1行目が狙った環境か確認**（他人の環境で `isaaclab.bat` を実行しない）
- ネットに出る作業の前にセッション限りで設定:
  - `$env:PIP_CACHE_DIR=\"D:\\Tominaga\\cache\\pip\"`
  - `$env:CONDA_SSL_VERIFY=\"D:\\Tominaga\\cache\\certs\\combined-ca-bundle.pem\"`
  - `$env:PIP_CERT=\"D:\\Tominaga\\cache\\certs\\combined-ca-bundle.pem\"`
  - `$env:REQUESTS_CA_BUNDLE=\"D:\\Tominaga\\cache\\certs\\combined-ca-bundle.pem\"`
- onshape-to-robot を動かすときは文字化け対策に `$env:PYTHONUTF8=\"1\"`

---

## 5. 未解決・次にやること

1. **~~ブランチの確認~~ → 済（§1a）。main は 08-21 で止まっていた＝以降は未 push。** 残りは `kani_walk` / `original` の日付確認と、失われた変更を「Alienware から救出」か「文書から再現」かの判断
2. ~~証明書の環境変数名を記録する~~ → **conda / pip は済（§3-1）。** git は未確認
3. ~~USD の再エクスポート~~ → **完了（2026-09-16 未明）。** URDF 後処理（base +90°、軸反転、limit）→ USD → 配置 → 64 env / 20 iter 完走。機体の約束事は `reference/robot_model_conventions.md`。**commit / push 済み（`6ede75b`、2026-09-16）**
4. 4096 env の基準値（秒/iter、VRAM、温度）を測る
