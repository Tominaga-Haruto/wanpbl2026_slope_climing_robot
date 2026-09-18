# 坂登坂ロボット プロジェクト 運用ルール & 手順書
 
> この文書は2部構成。
> **PART A（毎回見る）**= 会話のたびに必ず目を通す前提・鉄則・現在地。
> **PART B（必要なとき見る）**= 特定の作業に入るときだけ開くリファレンス。
>
> 更新方針: 情報が古くなったら「追記」ではなく該当箇所を**書き換える**。末尾に追記を積まない。
>
> **文書の地図は `claude/README.md` を見る。** どの文書をいつ読むか、個々のチャットの記録（`claude/chats/`）の置き場所もそこにまとまっている。
>
> **★ 正本の分担（2026-09-16）:** WRS機の環境の細部は `wrs_pc_environment.md`、機体モデルの座標・関節符号・初期姿勢は `robot_model_conventions.md`、学習の方針は `wrs_training_strategy.md` が正本。**この手順書と食い違ったらそちらを優先し、この手順書を直す。**
>
> **★ この文書の自動更新について（ユーザー承認済み・2026-09-04）**
> **重要な事実が判明したら、Claude は都度この手順書を自分の判断で更新してよい。** 毎回ユーザーに許可を取る必要はない。更新の対象になるのは:
> - 手順書の記述が**実物と食い違っていた**と判明したとき（最優先。誤った記述を放置すると数時間の手戻りになる）
> - 新しい確定値・実測値が出たとき（モーター諸元、質量、パラメータの効き方など）
> - 新しい落とし穴・エラーとその対処が判明したとき
> - 現在地（A0）が進んだとき
>
> 更新するときのルール:
> 1. **該当箇所を書き換える。** 末尾に追記しない。日付付きの但し書きを積み重ねない。
> 2. **「確認済み」と「未確認・推測」を必ず区別して書く。** 実測した値には根拠（どのコマンドで確認したか）を添える。
> 3. **誤りを訂正したときは、A0 か該当節に「旧記述は誤りだった」と一言残す。** 同じ誤りに再び引っかからないため。
> 4. 更新したらユーザーに一言伝える（何をどう直したか1〜2行で）。
> 5. **経緯や当時のやり取りの詳細まで残したいときは、この文書ではなく `claude/chats/YYYY-MM-DD_件名.md` に書く。** この文書は「今の正しい状態」だけを持つ。
 
---
---
 
# PART A ── 毎回見る部分
 
## A0. プロジェクトの目的と現在地
 
**最終目標: 自作の二足歩行ロボットが坂を安定して登れること（最終的に実機で）。**
 
**現在地（2026-09-16 時点）:**
 
1. **★ 柱Aの実行環境は WRS共用PC（Windows 11 / RTX 3090 Ti）に移った。** 環境構築は 2026-09-15 に完了（`wrs_pc_environment.md`）。Alienware は 2026-09-13 から故障中で、柱Aはもう Alienware を待たない。
2. **★ 機体を作り直した（2026-09-16、GitHub `main` の `6ede75b`）。** Onshape から再エクスポート → URDF 後処理 → USD → 64 env / 20 iter のテスト起動が完走。木構造 5/5・根＝胴体 2.918 kg・総質量 10.1058 kg。
3. **★★ 再エクスポートの途中で、過去の学習を根本から疑わせる事実が2つ見つかった（B2・`robot_model_conventions.md`）:**
   - **base の +X がロボットの「横」だった。** onshape-to-robot の base フレームは CAD のワールド軸そのままで、この機体では X＝左右・Y＝前後。**GitHub の 08-21 版 URDF も同じだった＝Alienware での過去の学習は「前進指令＝機体の横方向に歩け」で回っていた可能性が高い。カニ歩きの有力な説明**（未検証の仮説。新しい機体での学習で確かめる）。→ base を Z 軸まわり +90° 回転して +X＝前に修正。
   - **関節軸の向きが左右で揃っておらず、脚の中で膝（KFE）だけ逆向きだった。** 同じ角度を入れても左右が鏡写しにならず、Skyentific 由来の初期姿勢は 22 cm 非対称だった。→ 5関節の軸を反転し「同じ角度＝左右鏡写し」に。初期姿勢の HAA を 0、スポーン高さを 0.3758 m に変更。
4. **★ WRS機のコードは、機体まわり（`skyentific_poclegs.py` の初期姿勢）以外は 08-21 版。** 9月に Alienware で入れた変更（`noise_std_type="log"`、報酬 weight、前進限定、`command_vel` の降格など）は **GitHub に push されておらず、WRS機には入っていない**（`wrs_pc_environment.md` §1a）。棚卸し結果は `wrs_training_strategy.md` §1。
5. **次の一手: 学習戦略を決めて学習を回す**（新しいチャットで。`next_chat_briefing.md`）。9月の変更の多くは「横向きの機体」に対する対症療法だった可能性があるので、**戻すのは構造的な対策（クラッシュ対策など）に絞り、報酬まわりは新しい機体で改めて測ってから決める。**
**旧記述の訂正（新しい順）:**
- **★「カニ歩きは機体の左右非対称（木構造）が原因・前進限定化が引き金・報酬の重み上げが増幅」は、少なくとも不完全だった（2026-09-16）。** 木構造とは別に、**base の前後が 90° ずれていた**ことが見つかった。どちらがどれだけ効いていたかは未確定。
- **「Alienware の症状は熱で決まる」は誤りだった（2026-09-14）。** 持続時間に規則性は無い。間欠故障（A2a）。
- **「木構造の非対称の原因は CAD の Mate 構造」は誤りだった（2026-09-14）。** 原因はインスタンス並び順（B2）。
- **B2 の旧記述「木構造は右脚 HR link から左脚が分岐する形が正常。同型と確認済み」は誤りだった。** 自分の2つの版を見比べただけだった。
- **「カニ歩きの主因は構造非対称」は言い過ぎだった（2026-09-06）。**
**確定して蒸し返さないこと:**
- 学習クラッシュ（`normal expects std >= 0.0`）の真因は rsl_rl の std が生の実数パラメータであること。**`noise_std_type="log"` で根絶**（B8）。**ただし WRS機の 08-21 版コードには入っていない。**
- 立ち往生の真因は「立ち止まりの給料」の12倍化（B4）。
- `feet_air_time` は着地インパルスでスケールが2桁小さい（B4）。
**プロジェクトは大きく2本柱で進む:**
- **柱A（シミュ側）:** Isaac Lab で坂を登れる方策を完成させる。**実行環境は WRS機。**
- **柱B（実機側）:** CubeMars モーターの制御コードを作り、最終的に柱Aの学習方策を実機にデプロイする。**モーターは AK10-9 / AK80-9、ファーム V3.0、MIT はモード8で確定・トルク指令は通る・位置指令は未達**（A7・`motor_can_findings.md`・`mit_implementation_briefing.md`）。マシンが別（Windows ノートPC）。
**今の主な編集対象:** `my_robot_code/rsl_rl_cfg.py`（PPO）、`my_robot_code/rough_env_cfg.py`（報酬・終了・指令・カリキュラム・地形）、`my_robot_code/skyentific_poclegs.py`（アクチュエータ・初期姿勢）。
 
---
 
## A1. 対話の鉄則（毎回守る）
 
### コマンドの出し方
- コマンドを提示するときは**必ずどのディレクトリで実行するかを明示**する。端折らない。
- **★どのマシンで実行するかも明示する。** WRS機（Windows / PowerShell）と Alienware（Ubuntu / bash、故障中）で構文が違う。読み替え表は A2b。
- **山括弧プレースホルダ（`<フォルダ名>` 等）は絶対に使わない。** 実際に山括弧を打ち込む事故が2回起きた。名前が必要なら、先に確認コマンドで実名を出させ、その名前を埋めた**完成形**のコマンドを出す。
- **複数行コマンド（行末バックスラッシュ、または改行を含む `python -c "..."`）はコピペで壊れる。** 複数行の Python は **`tools/` に .py として書いてから実行する**。1行で済ませたいときはリスト内包表記、どうしてもなら base64 化。
- **長いコマンドは改行なしの1行版でも必ず提示する。**
- **連結した長い1行コマンドは、途中で失敗すると後半が実行されない。** 失敗時は「どこまで実行されたか」を先に伝える。
- エラーログは長い。ユーザーが全文を読む前提にしない。**Tracebackの要点を訳して伝え、次に打つコマンドを1〜2個に絞る。**
- **★WRS機では作業の実行を WRS機上の Claude Code に任せることが多い。** Cowork 側のチャットは「WRS側に貼る文」を用意し、報告を受けて判断する分担。WRS側への指示は**停止点を明示**し、推測で直さず止まって報告させる。
### 確認と安全
- ユーザーはターミナルの文章をあまり読めない。**確認コマンドを必ずセットで用意する。**
- **破壊的操作（rm -rf, sed -i, mv, 上書きコピー等）の前は対象のフルパスを明示し、`.bak_変更内容` を取ってから実行。** 実行後は確認コマンドで結果を目視。config 書き換えは `diff` で差分を見せる。
- **既存の学習チェックポイント・USD等を上書きするコマンドを出す前は、上書き先を必ずバックアップさせる。**
- **★バックアップは「取る」だけでなく「戻したあと中身を確認する」までが1セット。** 2026-09-08 に取り違え事故が起きた。
- **★成否は終了コードではなく成果物で判断する。** WRS機の URDF→USD 変換は失敗しても終了コード 0 を返した（2026-09-16）。
- **★CAD を編集する前は Onshape の「バージョンを作成…」でバージョンを切る。**
- **書き換えスクリプトには「想定と違ったら書かない」ガードを入れる。**
- **秘密情報（`.env` のOnshape APIキー、GitHub PAT、SSH秘密鍵）は絶対にチャットに貼らせない／コミットさせない。** WRS機の Claude Code にも `.env` の中身を表示させない（存在と行数だけ確認）。
- **★WRS機は共用PC。`D:\Tominaga\` の外に書き込まない。システム設定・他人のプロセス・他人の環境に触らない**（A2b）。
### 実機を扱うときの安全（柱Bで毎回）
- **実機モーターは物理的に動く。** 指令コードを実行する前は「そのコマンドで何が起きるか」を先に説明してから実行させる。
- 初回テストは**必ず脚を吊る／固定する／トルクを絞る**。非常停止（電源を切る）を手元に用意してから通電する。
- **1モーター → 脚1本 → 全身**の順で立ち上げる。
- **★関節の正の向きは `robot_model_conventions.md` の約束に合わせる。** モーターの正方向とは一致するとは限らないので、関節↔モーター対応表に符号の列を持つ。
### GUI操作の案内（ユーザーはOnshape/GitHub初心者）
- 「Part Studioを開いて全選択」のような一段抽象度の高い指示は通じない。**「画面のどこにある何をクリックするか」まで分解**して書く。
- 詰まったら**スクリーンショットを1枚もらって現状確認**してから次を指示する。
- **物理作業（ケースを開ける等）も同じ粒度に分解する。**
- **★Onshape はブラウザから API で直接読める**（ログイン済みセッション）。
- **★機体の形や姿勢の判断は、数値だけでなく3面図の PNG を出させてユーザーの目で確認する。** 2026-09-16 に「前はどっちか」「膝の向き」「HAA は開かないのが理想」をユーザーの目視と設計知識で決着させた。**数値診断は測り方を間違えることがある**（足首原点で足首の回転を測っていた等）。
### 説明の仕方（確認済みの好み）
- **例え話は最小限。** 概念を1つ掴ませる補助にとどめる。
- 好みの説明フォーマット: **概要を先に1段落 → 各項目を淡々と**。
- 冗長な確認ステップや既出事実の繰り返しは嫌う。前に進める。冗長な褒めも不要。
- **数字で語れるところは数字で語る。**
- **ユーザーは実験設計がうまい。** 交絡・スケール・統計的有意性の指摘は歓迎される。訂正はストレートに伝えてよい。
- **★ユーザーは自分の観察・設計知識に基づいて反論・判断してくる。その判断はたいてい正しい。** 反論が来たら守りに入らず、データを並べ直す。
- **★状況説明を忘れない。** ユーザーは WRS側の長い報告を読み切れないことがある。返信の冒頭で「いま何が起きていて、次に何をするか」を短く説明してから、貼る文を出す（2026-09-15 にユーザーから明示的に依頼）。
### 提案の姿勢
- 明らかな最適解が他にあれば**その提案も出す**（回避策と根本解決を区別して両方伝え、選ばせる）。
- ログや数値が「その方向では改善しない」と示すなら**正直に伝えて代替案を出す**。
- **自分の過去の結論が新しいデータで覆ったら、はっきり訂正する。** 実績: 「カニ歩きの主因は構造非対称」「非対称の原因は CAD の Mate」「Alienware の症状は熱依存」「HR が 45° 回っている（2026-09-16、実際は軸の符号の問題）」はいずれも外していた。
- 確認を飛ばすと数時間の手戻りになるリスクがあるなら正直に助言する。**ただし最終判断はユーザーに委ねる。**
### 推測で進めない（ルールの中核）
- バージョン不整合や実装とドキュメントの食い違いは、**憶測で直さず、まず本体側の実装を grep で確認**してから対処する。Isaac Lab は内部APIがバージョンで変わる。
- **★この手順書自身の記述も疑う。** 手順書は現実の写しであって現実そのものではない。
- **★「2つの出力が一致する」は「正しい」ではない。** 照合先は設計意図であって、自分の別の出力ではない。
- **★集計値（数を数える検証）は構造の誤りを検出できない。** 親子関係をダンプして目で見る。
- **★座標系と符号も同じ。** リンク数・質量・木構造が全部正しくても、**base の前後が 90° ずれていた／軸の符号が左右で食い違っていた**（2026-09-16）。**URDF を作ったら「+X が前か」「同じ角度で左右が鏡写しに動くか」を FK と絵で必ず確かめる**（B3 段階3）。
- **★ツールの「暗黙の前提」を必ず一次資料で確認する。** onshape-to-robot は「インスタンス一覧の先頭＝base」「base フレーム＝CAD のワールド軸」。Isaac Lab は「base の +X＝前、+Z＝上」。
- **★ソースを読める道具はソースを読む。** 2026-09-15 に onshape-to-robot 1.8.3 と Isaac Lab `urdf_converter.py` をソースで確認し、Windows のパス区切り問題や URDF インポーターの版固定を先回りできた。
- **★指標の定義が設定によって意味を変えることに注意。** 生の `v_y` は横指令が出ている設定では crab を測れない（残差 `v_y − cmd_y`）。`computed_torque` は「PD が要求した値」。
- 見本コードが要求する名前（body名の正規表現など）も思い込みで合わせず、**env_cfg を grep して実物を確認**してから合わせる。
- **数値の根拠が複数取れるときは、独立な経路で裏を取ってから信じる。**
- **実機CANも同じ。** まず生ログで実測してから確定する。
---
 
## A2. 環境 ── WRS機が柱Aの本線
 
| | **WRS機**（本線・共用） | **Alienware Aurora R16**（故障中） |
|---|---|---|
| 立場 | **柱Aの実行環境**（2026-09-15〜） | 2026-09-13 から故障。**柱Aは待たない** |
| OS | **Windows 11 Education**（`DESKTOP-MACG22A`） | Ubuntu 22.04.5 LTS |
| GPU | **RTX 3090 Ti 24.5GB** / ドライバ 591.86 | RTX 4070 12GB / 580.173.02（hold 済み） |
| RAM | 127.4 GB | 未記録 |
| 作業フォルダ | **`D:\Tominaga\`**（これ以外に書き込まない） | `~/projects/slope-climbing-robot` |
| Python 環境 | conda `D:\Tominaga\envs\isaac_env`（3.11.16）／CAD 書き出し用 `D:\Tominaga\envs\onshape_env` | venv `isaac_env`（3.11.15） |
| Isaac Sim / Lab | 5.1.0（pip）/ `D:\Tominaga\IsaacLab`（2.3.2 / `b4c3210247`） | 5.1 / ソースインストール |
| 遠隔 | TeamViewer（固定パスワード） | TeamViewer のみ |
 
- **WRS機の詳細（版・ハードリンク・落とし穴 11 件）は `wrs_pc_environment.md` が正本。** 特に: Avast の HTTPS 検査で証明書エラー（道具ごとに `CONDA_SSL_VERIFY` / `PIP_CERT` / `REQUESTS_CA_BUNDLE`）、tensordict 0.7.0 固定、ハードリンクは git 操作で切れる、conda は PowerShell からのみ、学習起動に `env.commands.base_velocity.debug_vis=false` が必要、URDF インポーター 2.4.31 は extscache にコピー済み。
- **長時間ジョブ中は本体をスリープ／電源オフしない。GPU を長く使う前に一言確認（共用機）。**
---
 
## A2a. Alienware の故障（2026-09-13〜・未解決・柱Aは待たない）
 
**症状: 電源は入る。モニターに「信号なし」。数分〜十数分で電源が落ちる。規則性の無い間欠故障。**
詳細な事実・切り分け手順は `claude/alienware_repair_instruction.md`。
 
- 電源ボタンLEDはケース照明と同期＝**Dell の診断エラーコードは出ていない**。TeamViewer で一度つながった＝Ubuntu は起動していた。
- 「熱で決まる」は棄却（2日休止で3分、15分休止で十数分）。
- **費用ゼロの手が4つ未実施:** 保証確認（サービスタグ）／挿し直し4点（GPU補助電源・GPU・メモリ・24ピン/CPU 8ピン）／ホコリ除去／モニターのポート変更。
- **救出価値のあるデータ:** `my_robot_code/` の 08-21 以降の未 push 分（数十KB）。ただし **base の前後が 90° ずれた機体での調整だった可能性が高い**ので、価値は「過去に何を試したかの記録」に下がった。USD・STL・チェックポイントは作り直し済み／無効。
- **修理に出す前に SSD を抜くか吸い出す。**
- 次に起動できたら最優先: `cd ~/projects/slope-climbing-robot && git status && git log -3 --all --format="%h %ad %d %s" --date=short && sudo cat /sys/class/dmi/id/product_serial`
---
 
## A2b. WRS機（共用 Windows 機）の掟と読み替え
 
### ★ 共用マシンの掟（最重要）
 
```
C:\Jerry\IsaacLab              ← Jerryさんの個人環境。絶対に触らない
D:\IsaacLab                    ← 共有と思われる（2.3.2 / b4c3210247）。読むだけ
conda環境: env_isaaclab / jerry_isaaclab / matsuuchi_env /
          matsuuchi_env_backup / pcnT / tf_1 / unitree_sim_env / wilor
```
 
1. **書き込んでいいのは `D:\Tominaga\` の中だけ。** 他人の場所のファイルは読むのは可（2026-09-16 に Kit キャッシュから URDF インポーター 2.4.31 を**自分の環境へ**コピーした実績）。
2. **C ドライブに大きいものを置かない**（空き約 43GB）。conda は `--prefix`、pip キャッシュは `D:\Tominaga\cache\pip`。
3. **`env_isaaclab` という名前を再利用しない。**
4. **他人のプロセスを止めない。GPU を長く使う前に一言。**
5. **システム設定（Avast、レジストリ、`setx`、`git config --global`）は変えない。** 変えるなら TA さんの許可を取り、ユーザー本人が行い、終わったら戻す。
6. **`D:\Tominaga` をリネームしない**（conda 環境・editable インストール・ハードリンクが絶対パスに依存）。
### Ubuntu → Windows 読み替え表
 
| Alienware（Ubuntu / bash） | WRS機（Windows / PowerShell） |
|---|---|
| `source .../isaac_env/bin/activate` | `conda activate D:\Tominaga\envs\isaac_env`（**PowerShell のみ**。有効化後 `where.exe python` で確認） |
| `./isaaclab.sh` | `.\isaaclab.bat` |
| `python -m pip` | `python -m pip`（同じ） |
| `ls -lt` | `Get-ChildItem \| Sort-Object LastWriteTime -Descending` |
| `grep` | `Select-String` |
| `&&` で連結 | `;` で連結 |
| `ln -s`（symlink） | **ハードリンク `cmd /c mklink /H`**（権限不要。git 操作で切れるので `Get-FileHash` で確認） |
| `~/projects/slope-climbing-robot` | `D:\Tominaga\slope-climbing-robot` |
 
---
 
## A3. GPU ドライバと遠隔アクセスの制約
 
TeamViewer 遠隔では **GPUの描画（Vulkan/OpenGL）が落ちることがある**。GPUコンピュートは動く。**学習・USD変換・録画（`--headless --video`）は headless で。** WRS機でも GUI は使わない。
 
### Alienware の GPU ドライバは 580 系で固定（復旧した場合）
- Isaac Sim 5.1 は Linux ではドライバ 580 系でのみ正常に動く。595 系は非対応（RTX 4070 名指し）。24 パッケージを `apt-mark hold` 済み。**上げない。**
- **hold はカーネルには効かない。** カーネル更新で nvidia モジュールが揃わなくなる経路が「映らない」の原因である可能性が 20〜30% 残る（未検証）。
- 595 を入れると **play だけ SIGSEGV（139）、学習は通る**という壊れ方をする。
- `Driver/library version mismatch` は再起動が第一候補。原因調査は `/var/log/apt/history.log` から。
- **WRS機の 591.86 は Windows 要件（580.88 以上）を満たすので別問題。**
### 遠隔アクセスの運用ルール
- 新しいマシンでは最初に **TeamViewer の ID をメモし、無人アクセス用パスワードを設定**する。Linux 機なら `openssh-server` も入れる。Alienware は TeamViewer だけで詰んだ。
---
 
## A4. ディレクトリ構成（WRS機・本線）
 
```
D:\Tominaga\
├── envs\isaac_env\                      ← Isaac 用 conda 環境
├── envs\onshape_env\                    ← onshape-to-robot 1.8.3 専用
├── cache\                               ← pip / conda / 証明書（certs\combined-ca-bundle.pem）
├── IsaacLab\                            ← 自分専用 clone（2.3.2）。train.py / play.py に import 1行追加済み
└── slope-climbing-robot\                ← GitHub のリポジトリ（ブランチ main）
    ├── my_robot_code\                   ← ★自作5ファイルの実体（Git 管理・編集対象）
    │   ├── rough_env_cfg.py             ←   報酬・終了・カリキュラム・地形・観測（指令は親クラス既定のまま）
    │   ├── skyentific_poclegs.py        ←   usd_path / init_state / actuators
    │   ├── curriculums.py               ←   カリキュラム関数
    │   ├── rewards.py                   ←   自作報酬 feet_air_time / feet_slide
    │   └── rsl_rl_cfg.py                ←   PPO ハイパラ
    ├── references\BipedalRobotSim\      ← Skyentific 参考実装（.gitignore 除外、editable インストール）
    │   └── skyentific_poclegs\skyentific_poclegs\
    │       ├── (5ファイルの元位置)       ←   my_robot_code とハードリンク
    │       └── assets\robots\myrobot_dummy\   ← ★学習が読む USD（robot.usd + configuration\）
    ├── onshape_export\
    │   ├── .env                         ← ★Onshape API キー（git 除外。使い終わったら Revoke）
    │   └── myrobot_dummy\
    │       ├── config.json              ←   onshape-to-robot 設定（Git 管理）
    │       ├── robot.urdf               ←   onshape-to-robot の生出力（Git 管理）
    │       ├── robot_sim.urdf           ←   後処理済み（Git 管理）
    │       ├── assets\merged\*.stl      ←   メッシュ（git 除外）
    │       └── usd\                     ←   convert_urdf.py の出力（git 除外）→ references 側へ配置
    └── tools\                           ← 後処理・検算スクリプト（Git 管理）
        ├── postprocess_urdf.py          ←   robot.urdf → robot_sim.urdf（改名・パス・base +90°・軸反転・limit・自己チェック）
        ├── verify_export.py             ←   URDF の木構造・質量・慣性・MISSING 検算
        └── verify_usd.py                ←   USD の関節・軸・limit・質量検算（SimulationApp 経由）
```
 
- **編集は必ず `my_robot_code\` 側で。** ハードリンクなので参考実装側に即反映。**エディタによっては保存でリンクが切れる**ので、編集後は `Get-FileHash` で両側一致を確認（Python の `open(path,'r+')` 方式なら切れない）。
- **Isaac Lab 本体は触らない。** 例外は `train.py` / `play.py` の `import skyentific_poclegs  # noqa: F401`。
- **`.bak` は `.bak_変更内容` 形式。** 日付だけの名前は取り違えの元。
- Alienware の構成は同じリポジトリを `~/projects/slope-climbing-robot/` に置き、symlink で分離していた（B5）。
---
 
## A5. 学習の基本ルール（毎回守る）
 
- **小さく回して通す → 本番。** まず 64 env / 20 iter で通してから 4096 env。
- **起動コマンドを出すときは必ず「停止方法（Ctrl+C）」と「途中で止めてもチェックポイントは残る」をセットで伝える。**
- **`--max_iterations` の暴走に厳重注意。** 起動直後に iter 番号を目視し、想定と違えば即 Ctrl+C。
- チェックポイントは 200 iter ごと。resume は新しい run フォルダを作る。
- **★壊れかけのチェックポイントから再開しない。**
- **★2026-09-16 に機体を作り直したので、それ以前のチェックポイントは全部無効。**
- **学習中に `play.py` を同時実行すると GPU メモリが逼迫する**（WRS機は 24GB あるが共用なので注意）。
- **実測基準値:**
  - WRS機（RTX 3090 Ti）: **64 env で 1.5〜2.3 秒/iter・VRAM 約 7.4GB**（2026-09-16）。**4096 env は未測定 → 初回の本番で測ってここを書き換える。**
  - Alienware（RTX 4070）参考: 4096 env で 1.04 秒/iter・VRAM 5.4GB。
### コピペ用コマンド ── WRS機（PowerShell・1行）
 
> 前提: PowerShell で実行。`conda activate` の後 `where.exe python` の1行目が `D:\Tominaga\envs\isaac_env\python.exe` であること。学習前に `python -m pip show tensordict` が 0.7.0 であること。
 
**テスト起動（64 env / 20 iter）:**
```
conda activate D:\Tominaga\envs\isaac_env ; cd D:\Tominaga\IsaacLab ; .\isaaclab.bat -p scripts\reinforcement_learning\rsl_rl\train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 64 --max_iterations 20 --headless env.commands.base_velocity.debug_vis=false
```
 
**本番学習（iter 数は目的に応じて変更）:**
```
conda activate D:\Tominaga\envs\isaac_env ; cd D:\Tominaga\IsaacLab ; .\isaaclab.bat -p scripts\reinforcement_learning\rsl_rl\train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 4096 --max_iterations 1500 --headless env.commands.base_velocity.debug_vis=false
```
 
**録画（歩容を見る。未検証: WRS機での録画はまだ一度も試していない）:**
```
conda activate D:\Tominaga\envs\isaac_env ; cd D:\Tominaga\IsaacLab ; .\isaaclab.bat -p scripts\reinforcement_learning\rsl_rl\play.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 50 --headless --video --video_length 400 env.commands.base_velocity.debug_vis=false
```
- `debug_vis=false` は、速度指令の矢印（S3 上の `arrow_x.usd`）の取得が 300 秒タイムアウトして落ちるのを避けるため。
- 学習ログは `D:\Tominaga\IsaacLab\logs\rsl_rl\` の下。
- play を1回走らせると `exported\policy.pt`（または `.onnx`）ができる。**実機デプロイでシミュと実機をつなぐ唯一のファイル**（B11）。
### ログの読み方（毎回これで判断する）
 
**Mean reward や episode 長だけ見ると必ず誤る**（棒立ちでも両方良くなる）。
 
| 指標 | 歩けている | 棒立ち局所解 |
|---|---|---|
| `Metrics/base_velocity/error_vel_xy` | 0.3 以下 | 0.7 以上 |
| `Curriculum/terrain_levels` | 0 より上に動く | 0 に張り付く |
| `Episode_Reward/feet_air_time` | プラス | マイナス |
 
- **★カニ歩きは残差 `v_y − cmd_y`（胴体座標）で測る。** 新しい機体で「横向き学習」が解消したかを判定する主指標。
- **立ち止まりの理論値を先に計算しておく**（B4）。
- `Mean action noise std` が 0.1 を切って下がり続けるのは探索が枯れているサイン（`noise_std_type` が scalar ならクラッシュが近い）。
- **2026-09-16 のテスト起動（iter 19）の終了理由は bad_orientation 99.5% / base_contact 1.2%。** base が本当に胴体になったので、以前（base_contact 優勢）と傾向が違っても異常ではない。
---
 
## A6. Git 運用（毎回の作業サイクル）
 
- 親リポジトリ: `D:\Tominaga\slope-climbing-robot`（WRS機）。GitHub: **`Tominaga-Haruto/wanpbl2026_slope_climing_robot`（public）**。
- **ブランチは `main`。** GitHub に `master` は存在しない（旧記述「正本は master」は誤りだった）。`fix/falling-down-end-condition`（`aa9e806`）は 08-21 の「転倒で終了するようになった版」。消さない。
- **最新: `6ede75b`（2026-09-16、再エクスポート・軸修正・limit・初期姿勢・検算/後処理スクリプト）。** それ以前の最新は 08-21 の `b50a6ee`。
- コミット著者は GitHub の **noreply メール**。git 設定は `--local`（共用機なので `--global` を使わない）。
- **push はユーザーが PowerShell で実行し、PAT を入力する**（文字が表示されないのは正常）。WRS機の Claude Code の Bash からは証明書の設定が無く `git fetch` が失敗する。
- **★push したら `git log -3 --format="%h %ad %s" --date=iso origin/main` で本当に上がったか確認する。** 08-21 以降、push したつもりで上がっていなかった（2026-09-15 判明）。
- **commit 前に `.env`・`*.usd`・`*.stl`・`*.part`・`*.bak*` が混ざっていないか `git status --short` と `git diff --cached --stat` で確認。**
- **git 操作（pull / checkout）の後はハードリンク5組の `Get-FileHash` を比べる。**
- **成果が出た時点（歩けた、クラッシュが止まった）で必ず commit / push。**
---
 
## A7. 実機モーターの前提（柱B着手時に毎回効く要点）
 
### モーター配置（2026-09-04 ユーザー確認済み）
 
片脚5個×2＝計10個。腰側→足先の順で:
 
| 順 | 関節 | 意味 | モーター | 定格 / ピーク |
|---|---|---|---|---|
| 1 | HR | 股回転 | **AK10-9** | 18 / 53 N·m |
| 2 | HAA | 股横開き | **AK10-9** | 18 / 53 N·m |
| 3 | HFE | 股前後 | **AK80-9** | 9 / 22 N·m |
| 4 | KFE | 膝 | **AK10-9** | 18 / 53 N·m |
| 5 | FFE | 足首 | **AK80-9** | 9 / 22 N·m |
 
- **★WRS機の `skyentific_poclegs.py`（08-21 版）は HFE を KFE と同じアクチュエータグループにしていて、モーター割り当てと合っていない。** 学習戦略で直す。
- 2026-09-08 のトルク要求実測（HFE 43〜48 / KFE 60 / FFE 41 N·m）は**壊れた URDF・横向きの機体で取ったもの。取り直す**（B12）。
### 制御モード（実測の正本は `motor_can_findings.md`）
 
- **ファーム V3.0。MIT は送信モード8 で確定**（`(8 << 8) | ID` の拡張29bit、ペイロード順 Kp → Kd → 位置 → 速度 → トルク、enable 不要、応答はサーボ形式 50Hz 定期）。
- **トルク指令は実機で通る。位置指令はまだ一度も成功していない**（MIT の位置原点がサーボと別物）。次の一手は `morg`（`mit_implementation_briefing.md`）。
- **実効 Kd = 指令 Kd × 0.48（天井 2.4）。Kp のスケールは未測定。Kp 1LSB = 0.1221（0.06 未満は 0 に潰れる）。**
- **旧記述「実機で動いているのはサーボモード。MIT は未検証」は古かった**（2026-09-14 に MIT を実測で確定）。
- **関節の正の向き・ゼロ姿勢は `robot_model_conventions.md` に合わせる。** 実機の原点合わせも「ゼロ姿勢＝脚まっすぐ下・爪先前」を 0 とする前提で考える。
---
---
 
# PART B ── 必要なとき見る部分
 
## B1. CAD → URDF → USD → タスク登録 → 学習 パイプライン全体像（2026-09-16 版）
 
```
Onshape (CAD, 004_sim ダミー円柱版)
   │ ← onshape-to-robot 1.8.3（WRS機の onshape_env）で書き出し
   │   ・dof_ Mate だけが joint になる
   │   ・★インスタンス一覧の先頭が base link になる（先頭＝胴体 Part 1 <6>）
   │   ・★base フレームは CAD のワールド軸そのまま（この機体では X＝左右）
   ▼
robot.urdf（生出力・Git 管理）
   │ ← tools\postprocess_urdf.py
   │   リンク改名 → mesh パス（package:// 除去・\→/） → base を Z 軸 +90° → 5関節の軸反転 → limit → 自己チェック
   ▼
robot_sim.urdf（Git 管理）
   │ ← tools\verify_export.py（木構造・質量・慣性・MISSING）＋ FK と3面図で「+X が前」「同じ角度で鏡写し」を確認
   │ ← IsaacLab\scripts\tools\convert_urdf.py（URDF インポーター 2.4.31 が必要）
   ▼
usd\robot.usd + configuration\   ← tools\verify_usd.py で検算
   │ ← ★references\...\assets\robots\myrobot_dummy\ へ配置（忘れると古いUSDで学習が回る。エラーは出ない）
   ▼
Isaac Lab で学習（skyentific_poclegs.py の usd_path / init_state / actuators）
```
 
- **質量・慣性は CAD の材質から一括で入る**（`no_dynamics:false`）。2026-09-06 に Onshape 側の材質を正したので、密度逆算スクリプトは不要になった。**STEP / STL は質量を運ばない。**
- 実行手順の詳細（Windows）は `wrs_urdf_reexport_instruction.md`。**ただしこの指示書は後処理（base 回転・軸反転）が必要と分かる前に書いたもの**なので、後処理は `postprocess_urdf.py` を使う。
---
 
## B2. ★ 機体モデルの構造・座標・符号（2026-09-16 に全部解決）
 
### 目標構成と命名（達成済み）
 
- **link 11 / 可動 joint 10 / fixed 0。** base から左右それぞれに HR→HAA→HFE→KFE→FFE が独立に生える。
- **joint 名（大文字）:** `LL_HR / LL_HAA / LL_HFE / LL_KFE / LL_FFE`（左）、`LR_*`（右）。Onshape の `dof_` Mate 名そのもの。
- **link 名（小文字）:** `base` ＋ `lr_hr / lr_haa / lr_hfe / lr_kfe / lr_ffe`、`ll_*`。env_cfg の正規表現（`.*ffe` など）に合わせるため。
- 意味: HR=股回転、HAA=股横開き、HFE=股前後、KFE=膝、FFE=足首。
### 問題1: 木構造の非対称（2026-09-14 に CAD 側で解決）
 
- onshape-to-robot は**アセンブリのインスタンス一覧の先頭を base link にする**（公式仕様。1.8.3 のソースでも確認: `process_mates()` が `instances[0]` を最初に body 化）。
- 修正前の先頭は右股ブラケット `Part 1 <3>`（0.065 kg）で、URDF は「右脚4関節・左脚6関節」に化けていた。`base` が 0.24 kg、`lr_hr` が実は胴体だった。
- **Onshape の一覧で胴体 `Part 1 <6>` を先頭にドラッグして解決。Mate は無変更。** バージョン `before_tree_fix_20260914` / `after_tree_fix_20260914`。
- 経緯と診断手順（Onshape API で Mate を読み、URDF を無向グラフで突き合わせる）は `urdf_asymmetry_finding.md`。
### 問題2: base の前後が 90° ずれていた（2026-09-16 発見・後処理で解決）
 
- **onshape-to-robot の base フレームは CAD のワールド軸そのまま。** この機体では **X＝左右、Y＝前後、Z＝上下**だった。Isaac Lab は base の **+X を前**として速度指令・観測を扱う。
- **GitHub の 08-21 版 URDF もクラウドで FK 計算したら同じく X＝左右だった。** → **Alienware での過去の学習は「前進指令＝横方向」で回っていた可能性が高い。カニ歩きの有力な説明**（未検証）。
- 爪先の向き（ユーザー確認: 爪先は回転後の +X）から、**base を Z 軸まわり +90° 回転**（base の inertial / visual / collision の origin と、LR_HR / LL_HR の origin に回転を掛ける）。FK で全リンク位置が回転と一致（誤差 0）。
- **Isaac Lab の `init_state.rot` では直らない。** base 座標の意味そのものが変わらないため。
### 問題3: 関節軸の符号が左右・脚内で食い違っていた（2026-09-16 発見・後処理で解決）
 
- 出力直後: LR = HR +Z / HAA −X / HFE +Y / **KFE −Y** / FFE +Y、LL = HR +Z / HAA −X / HFE −Y / **KFE +Y** / FFE −Y。
  - 左右: ピッチ軸が左右で逆、HAA/HR が左右で同じ → **同じ角度で鏡写しにならない**。
  - 脚内: **KFE だけ HFE・FFE と逆**。Skyentific の初期値（HFE −10° / KFE +20° / FFE −10°）が「膝曲げ・足裏水平」にならず、全部同じ向きに足されて脚を振り上げた姿勢になっていた。
- **LR_HR / LL_HAA / LL_HFE / LR_KFE / LL_FFE の axis 符号を反転**して、「HFE/KFE/FFE は両脚 +Y、HR と HAA は左右逆向き（正＝外向き）」に統一。
- **最終的な約束（正本は `robot_model_conventions.md`）:** HR 正＝爪先外向き、HAA 正＝足が外へ、HFE 負＝脚が前、KFE 正＝膝を曲げる（人間型）、FFE 負＝爪先が上。
- **初期姿勢: HAA を −0.1745 → 0.0**（足裏が平らなので開くと縁で立つ。ユーザー判断）、**スポーン高さ 0.449 → 0.375776 m**。確認値: 鏡映ズレ 10.9 mm、膝は HFE-FFE 線より 35〜42 mm 前、足裏 roll/pitch ≈ 0°。
### ★ この教訓（再エクスポートのたびに効く）
 
- **リンク数・関節数・質量・木構造が全部正しくても、座標系と符号が壊れていることがある。エラーは一切出ない。**
- **URDF を作ったら必ず:** ①base 座標で「左右の股が並ぶ方向＝Y」「爪先＝+X」「上＝+Z」を確認 ②初期姿勢と各関節 +0.2〜0.3 rad で FK し、**足の重心や足メッシュ中心（関節原点ではなく）**で左右が鏡写しか確認 ③3面図の PNG をユーザーが目で見る。
- **関節原点で関節自身の回転を測っても動かない**（足首の原点は足首の軸上）。数値診断の測り方を疑う。
### この CAD を今後触るときの注意
 
- **インスタンス一覧の先頭は胴体 `Part 1 <6>`。動かさない。** 再エクスポートの前に毎回確認する。
- **Onshape の「固定（Fixed）」は使わない。** 地面に固定されたロボットとして出力される。
- **config.json に根や base フレームを指定するオプションは無い。** 後処理で直す。
---
 
## B3. 再エクスポートの段階別手順（WRS機・要点）
 
> 詳細な指示書: `wrs_urdf_reexport_instruction.md`（WRS機の Claude Code に渡す形式）。以下は要点と、そこから変わった点。
 
### 段階1: Onshape 側
- 可動関節の Mate だけ `dof_` 始まり。Fastened には付けない。**Onshape 公式の URDF エクスポートは使わない**（link 1299 の異常出力になる）。
- **先頭インスタンスが胴体 `Part 1 <6>` か目視。** 編集する前は「バージョンを作成…」。
### 段階2: onshape-to-robot で書き出し（WRS機）
- 環境: `D:\Tominaga\envs\onshape_env`（isaac_env とは分離）。
- **API キー:** `cad.onshape.com` 右上アイコン → My account → 左メニュー Developer → API keys（dev-portal は OAuth 専用）。ユーザーが発行し、**`D:\Tominaga\slope-climbing-robot\onshape_export\.env`** に `ONSHAPE_API` / `ONSHAPE_ACCESS_KEY` / `ONSHAPE_SECRET_KEY` の3行で保存（メモ帳で `.env.txt` やフォルダにしない）。**使い終わったら Revoke。**
- 実行は `onshape_export` フォルダで。証明書: `REQUESTS_CA_BUNDLE`、文字化け対策: `PYTHONUTF8=1`。ログをファイルに残し、**`Found 1 root nodes: - Part 1 <6>` を確認**。
- config.json（Git 管理）: `url`（004_sim の Assembly、ワークスペース URL）/ `output_format: urdf` / `merge_stls: "all"` / `simplify_stls: false` / `no_dynamics: false`（`use_collisions_configuration` は 1.8.3 では読まれていないが無害）。
- **Windows では mesh パスが `package://assets\merged\...` とバックスラッシュで出る**（1.8.3 が `os.path.relpath` を使うため）。
### 段階3: 後処理と検証
- **`tools\postprocess_urdf.py`** で robot.urdf → robot_sim.urdf。**リンク改名は旧 `rename_links_dummy.py` の表を使わない**（連番が変わると黙って別のリンクに名前を付ける）。木構造から機械的に、XML 属性で書き換える。
- **`tools\verify_export.py`:** 木構造 5/5、根の質量 約 2.918 kg、合計 10.1058 kg、非対角慣性あり、左右対の質量一致、MISSING 0。
- **座標と符号の確認（B2 の教訓）:** 軸の表、HR/HAA +0.2 rad で外向き、初期姿勢の鏡映・膝・足裏、3面図。
- **CAD 形状を変えた場合、後処理の軸反転の組（固定リスト）が合わなくなる可能性がある。** `postprocess_urdf.py` の自己チェック（最終的な軸の向きの検証）が FAIL したら止めて調べる。
### 段階4: USD 変換（WRS機）
- `isaaclab.bat -p scripts\tools\convert_urdf.py (robot_sim.urdf) (usd\robot.usd) --joint-stiffness 0.0 --joint-damping 0.0 --joint-target-type none --headless`。**`--fix-base` は付けない。** fixed joint 0 なので `--merge-joints` 不要。
- **URDF インポーター 2.4.31 が必要**（Isaac Lab `urdf_converter.py` が Isaac Sim 5.1 以上で pin。2.4.30 には `set_merge_fixed_ignore_inertia` が無い）。Avast でレジストリに繋がらないので、Kit キャッシュからコピー済み（`wrs_pc_environment.md` §3-9）。`OMNI_KIT_ACCEPT_EULA=Y` も必要。
- **終了コード 0 でも失敗していることがある。** `usd\robot.usd` の時刻で判断。`tools\verify_usd.py` で関節・軸・limit・質量を検算。
- USD は分割構造: `robot.usd`（数KB）＋ `configuration\` に実体。
### 段階5: 配置とテスト起動
- `references\BipedalRobotSim\skyentific_poclegs\skyentific_poclegs\assets\robots\myrobot_dummy\` に `robot.usd` と `configuration\` を同じ位置関係で。**既存は `.bak_内容` にリネームしてから。**
- `usd_path` は `{ISAAC_ASSET_DIR}/robots/myrobot_dummy/robot.usd`（変更不要）。
- A5 のテスト起動（64 env / 20 iter、`debug_vis=false`）。`ValueError: ... base: []` はリンク名の不一致。
---
 
## B4. 学習の内部設計メモ（報酬・終了・カリキュラム調整時に見る）
 
> **★この節の数値の多くは 2026-09-08 時点の Alienware の設定で、しかも base の前後がずれた機体でのもの。WRS機のコードは 08-21 版で値が違う。現状値は `wrs_training_strategy.md` §1 の棚卸し（2026-09-16）を正とする。** 考え方（立ち止まりの給料、スケールの見方）はそのまま有効。
 
対象: `my_robot_code/rough_env_cfg.py`。報酬の式は `rewards.py`、PPOハイパラは `rsl_rl_cfg.py`、アクチュエータは `skyentific_poclegs.py`（B12）。
 
### ★ 最重要: 「立ち止まりの給料」を先に計算する
 
報酬は毎ステップ `関数の値 × weight × dt` で加算される（dt は制御周期。**WRS機のコードの `sim.dt × decimation` を grep で確認してから計算する**。Isaac Lab 親クラスの既定は 0.005 × 4 = 0.02）。1エピソード = 20秒。
 
**`exp(-誤差²/std²)` 型のタスク報酬は、誤差0で 1.0 を返す。** 指令が小さく `heading` が固定されていると、静止していることがほぼ満点になる。
 
| | `track_lin` | `track_ang` | 合計 |
|---|---|---|---|
| 8月の設定（weight 1.0 / 0.5、指令レンジ広い） | ≈1.8 | ≈3 | **≈5** |
| 9月の設定（weight 2.5 / 2.0、前進限定・heading固定） | ≈22 | ≈37 | **≈59** |
 
**12倍。** 立ち往生率は 3% → 16% に増えた。**→ 報酬を変えたら、まず立ち止まりの理論値を計算しておく。**
 
### ★ `feet_air_time` はスケールが2桁小さい
 
`rewards.py` の `feet_air_time` は**着地の瞬間だけ発火するインパルス**。着地1回あたり ≈ 0.3 × weight × dt。20秒で合計 0.5 程度で、`track_*` に対して 1〜2%。
- `rewards.py` に未使用の dense 版 `feet_air_time_positive_biped` がある（毎ステップ発火）。
- Alienware では `stance_timeout` を追加していた（**WRS機の 08-21 版には無い**）。
### 終了条件（Terminations）
 
**WRS機（08-21 版）の現状:** `time_out` / `base_contact`（body=`base`, threshold=1.0）/ **`bad_orientation`（limit_angle=1.3 rad）**。
> Alienware の 9月版は `bad_orientation` 0.8 rad と `joint_vel_out_of_manual_limit` 60 rad/s を持っていた（未 push で消失）。**「08-21 版に `bad_orientation` は無かった」という旧記述は、WRS機の実物では誤り（1.3 rad で存在）。** 文書間の 0.8 / 1.3 の食い違いは「9月版 / 08-21 版」の違いだった。
 
- **★2026-09-16 から `base` が本当に胴体になった。** 以前の `base_contact` は小さなブラケットの接地を見ていた。`add_base_mass` も 0.24 kg のリンクに ±1 kg を与えていた。**効き方が変わる。**
- `bad_orientation` の limit_angle は坂特化で前傾を誤判定しないか見直す。
- **終了ペナルティを足すのは逆効果**（立ち止まりの給料がプラスなので生存価値をさらに上げる）。
- 新しい termination 関数を足すときは Isaac Lab 本体を grep して存在確認。
### 指令レンジ（Commands）
 
- **WRS機（08-21 版）の `rough_env_cfg.py` は指令に触れていない＝Isaac Lab 親クラスの既定値**（2.3.2 のソースで確認）: `lin_vel_x=(-1,1)` / `lin_vel_y=(-1,1)` / `ang_vel_z=(-1,1)` / `heading=(-π,π)` / `heading_command=True` / `rel_standing_envs=0.02` / `resampling_time_range=(10,10)`。
- 9月に Alienware で入れた前進限定（`lin_vel_y=0`, `heading=0`, `lin_vel_x=(0,1)`）は、**横向きの機体で横に流れるのを抑える対症療法だった可能性がある。** `wrs_training_strategy.md` §4 は「入れない」方針。
- 前進限定化の副作用（記録）: 立ち止まりの給料の激増、`lin_vel_x` 下限 0 で「静止」指令が混ざる。
### 報酬（Rewards）
 
- **現状値は `wrs_training_strategy.md` §1。** 08-21 版の実効値: track_lin 1.0 / track_ang 0.5 / lin_vel_z −2.0 / ang_vel_xy −0.05 / joint_torques −1e-5 / action_rate −0.01 / feet_air_time 2.0（0.2〜0.5 s、`.*ffe`）/ feet_slide −0.25 / undesired_contacts −1.0 / joint_deviation_hip −0.1 / joint_deviation_knee −0.01 / flat_orientation −0.5（`__post_init__`）/ dof_pos_limits −1.0（`__post_init__`）。
- **重要: 報酬の実効値はクラス定義でなく `__post_init__` で上書きされる。**
- **`dof_pos_limits` は URDF の lower/upper に対して効く。** 現在 ±π なので実質死んでいる（機構的可動域は未入力）。
- **`joint_deviation_hip` は初期姿勢からのズレの罰。** 初期姿勢が歪んでいると歪みを強化する（2026-09-16 に初期姿勢を左右対称・HAA 0 に修正済み）。
- **★因果実験（2026-09-08、横向きの機体）:** 2週間前の健全チェックポイントを 9月の報酬設定で学習継続したら `error_vel_yaw` が 0.148 → 0.39〜0.50 に悪化した。
### カリキュラム（Curriculum）
 
- `terrain_levels`（歩いた距離で昇降格）。**0 に張り付いていたら「歩けていない」の決定的証拠。**
- `push_force_levels`（昇降格あり）。**棒立ちでも上がる。歩行の指標にならない。**
- `command_vel`（08-21 版は**昇格のみの一方通行**。Alienware で降格ロジックを追加したが未 push で消失）。
### PPO ハイパラ（`rsl_rl_cfg.py`）
 
- **08-21 版（WRS機）: `noise_std_type` 無し（＝scalar）、`clip_actions` 無し、`init_noise_std` 1.0、`entropy_coef` 0.005、`learning_rate` 1e-3、`num_steps_per_env` 24、`max_iterations` 30000。**
- **★`noise_std_type="log"` は学習クラッシュの根本対策（B8）。** 入れ直す方針（`wrs_training_strategy.md` §1）。
- Alienware の 9月版（参考）: `noise_std_type="log"` / `clip_actions` 6.0 / `init_noise_std` 1.5 / `entropy_coef` 0.002。
### 地形（Terrain）
 
- 08-21 版: flat 0.3 / hf_pyramid_slope 0.1 / _inv 0.1（slope_range 0〜0.4）/ stairs 0.05 / stairs_inv 0.05 / wave 0.2 / random_rough 0.2。8 m × 8 m、10 行 × 20 列。
- **診断目的では平地オンリーにする価値が高い**（`wrs_training_strategy.md` §2）。
- 坂特化は flat ＋ pyramid_slope / _inv の2本立てにして slope_range を terrain_levels で伸ばす（同 §5）。
### 坂登坂の優先順位
 
0. ~~再エクスポートで機体を正す~~ **完了（2026-09-16）**
1. **新しい機体で「横向き学習」が解消したかを確認する**（`v_y − cmd_y` の残差）。**9月の対症療法を戻す前に。**
2. 学習の土台（クラッシュ対策・アクチュエータの現実化・グループ分け）
3. 報酬・指令（立ち止まりの給料・dense な足上げ）
4. トルク要求の内訳の分離（B12）
5. 坂: 地形の坂比率・slope_range↑ → `flat_orientation_l2` を緩める → `bad_orientation` を坂に合わせる
6. 仕上げ: トルク-速度 droop、height_scan、base 原点の位置
- **iter を増やすだけでは改善しない**（実績3件）。
- **一度に1つだけ変える。**
---
 
## B5. Git / GitHub 詳細
 
### 自作5ファイルの分離
- 自作改変は元々 Skyentific リポジトリ（references 配下）の中に埋まっていた。実体を `my_robot_code/` へ移し、元位置からリンクを張る。
- **Alienware: 絶対パス symlink。WRS機: ハードリンク**（Windows の symlink は管理者権限か開発者モードが要るため）。対応表は `wrs_pc_environment.md` §1。
- 対象5ファイル: `curriculums.py` / `skyentific_poclegs.py` / `rough_env_cfg.py` / `rewards.py` / `rsl_rl_cfg.py`。
- タスク登録用 `config/…/skyentific_poclegs/__init__.py` は未分離（参考実装の実体のまま）。
### .gitignore で除外しているもの
`.env`、`IsaacLab/`、`logs/`、`**/usd/`・`*.usd`、`*.stl`・`assets/merged/`、`*.part`、`__pycache__`、`isaac_env/`、`references/`。
- **この除外のせいで、別マシンに移っても USD・STL・チェックポイントは付いてこない。** `robot.urdf` / `robot_sim.urdf` / `config.json` / `tools/*.py` は Git 管理なので、Onshape から再エクスポートすれば同じ機体を再現できる。
### 認証・remote・ブランチ
- PAT（HTTPS）。Username=`Tominaga-Haruto`。
- origin: `https://github.com/Tominaga-Haruto/wanpbl2026_slope_climing_robot.git`
- ブランチ: **`main`（正本）** / `original` / `fix/falling-down-end-condition`（08-21 の転倒終了版。消さない）/ `kani_walk`。**`master` は存在しない。**
- `kani_walk` / `original` に 08-21 以降の commit があるかは未確認。
---
 
## B6. トラブル対応早見表
 
| 症状 | 原因 | 対処 |
|---|---|---|
| **WRS機: pip / conda / git / onshape-to-robot で SSL 証明書エラー** | Avast の HTTPS 検査 | 道具ごとに `PIP_CERT` / `CONDA_SSL_VERIFY` / `REQUESTS_CA_BUNDLE` を `D:\Tominaga\cache\certs\combined-ca-bundle.pem` にセッション限りで設定 |
| **WRS機: cmd で `conda` が無い** | conda は PowerShell からのみ | PowerShell で実行。conda 不要なら exe をフルパスで |
| **WRS機: convert_urdf で `Can't find extension ... urdf 2.4.31`** | Kit の拡張レジストリに Avast で繋がらない | Kit キャッシュの 2.4.31 と `omni.kit.pip_archive` を isaac_env の extscache へコピー（`wrs_pc_environment.md` §3-9）。pin を 2.4.30 に変えても API 差で落ちる |
| **WRS機: convert_urdf が終了コード 0 なのに USD が無い** | エラーでも 0 を返す | `usd\robot.usd` の時刻で判断 |
| **WRS機: 学習起動で `arrow_x.usd` 取得が 300 s タイムアウト** | 速度指令の矢印の可視化アセット | `env.commands.base_velocity.debug_vis=false` |
| **WRS機: 学習が理由不明の access violation で落ちる** | tensordict が最新版に戻された | `python -m pip show tensordict` → 0.7.0 に戻す |
| **WRS機: my_robot_code を直したのに学習が変わらない** | ハードリンクが切れた（git 操作・エディタ保存） | `Get-FileHash` で両側比較。張り直す |
| **WRS機: URDF インポートで EULA エラー** | Isaac Sim の EULA 未承認 | `OMNI_KIT_ACCEPT_EULA=Y` |
| **WRS機: `.env` が読まれない** | `.env` フォルダの中にファイル／`.env.txt`／3行形式でない | `Test-Path` と `ONSHAPE_...=` 行数で確認（中身は表示しない） |
| `Command 'python' not found` / `Unable to find any Python executable` | 環境の有効化忘れ | venv / conda を有効化 |
| `ModuleNotFoundError: No module named 'pxr'` | SimulationApp 無しで import | 本体ソースを grep するか SimulationApp 経由で |
| `ValueError: … base: []`（学習起動時） | body名が見本regexに不一致 | リンク名を確認（B3 段階3） |
| **木構造が左右非対称になる** | インスタンス一覧の先頭が胴体でない | Onshape で胴体を先頭に（B2） |
| **`base` の質量が 1 kg 未満** | 同上 | 胴体なら 2.918 kg |
| **★前進指令で横に歩く／初期姿勢が左右非対称** | **base の +X が横／関節軸の符号の食い違い** | **B2 問題2・3。FK と3面図で確認。`postprocess_urdf.py` の自己チェック** |
| **Windows で mesh が MISSING** | mesh パスがバックスラッシュ | `\` → `/`、`package://` 除去 |
| ロボットが地面に固定されて動かない | Onshape の「固定」／`--fix-base` | 固定を外す |
| **`RuntimeError: normal expects all elements of std >= 0.0`** | rsl_rl の std が生の実数パラメータで負に落ちた | **`noise_std_type="log"`**（B8） |
| **ロボットが立ったまま歩かない** | 立ち止まりの給料／トルク不足／friction 不感帯 | 立ち止まりの理論値を計算（B4） |
| **横に流れる（カニ歩き）** | **まず base の前後（B2 問題2）**。その後に指令・報酬 | **残差 `v_y − cmd_y` で測る** |
| `Episode_Termination/` に期待した項目が無い | その終了条件が登録されていない | 実ファイルを grep |
| **数は合っているのに挙動がおかしい** | 集計値は構造・座標・符号の誤りを検出できない | 親子関係・軸の向き・FK を目で見る |
| URDFを直したのに学習の挙動が変わらない | USD 再変換＋配置を忘れた | B3 段階4→5 をセットで |
| 復元したのに設定が変わっていない | バックアップの取り違え | 復元したら grep で中身を確認 |
| 学習 iter が想定超過 | `--max_iterations` の指定ミス | 起動直後に iter を目視 |
| 学習中に play が落ちる | GPU メモリ逼迫 | 学習を止めるか env を絞る |
| **push したのに GitHub が古い** | push が通っていなかった | `git log origin/main` の日付で確認（A6） |
| Alienware: `Driver/library version mismatch` | ドライバのユーザー空間だけ更新 | 再起動 |
| Alienware: play だけ SIGSEGV（139） | ドライバが 580 系でない | `nvidia-smi` |
| Alienware: 映らず数分〜十数分で落ちる | 2026-09-13 からの間欠故障 | A2a |
| モーターに指令を送っても返信が来ない | CAN 設定不一致 | `motor_can_findings.md` |
 
---
 
## B7. モーター諸元・質量・CAD 注意
 
> **★ベンチ実測値・トルク実測の正本は `claude/actuator_params.md`。** この節は概要のみ。
 
### モーター諸元（CubeMars 公式値）
 
| 項目 | AK10-9 V3.0 KV60 | AK80-9 V3.0 KV100 |
|---|---|---|
| 質量 | 0.94〜0.96 kg | 0.485〜0.49 kg |
| 減速比 | 9:1 | 9:1 |
| **定格トルク** | **18 N·m** | **9 N·m** |
| **ピークトルク** | **53 N·m** | **22 N·m** |
| 無負荷回転数（出力軸） | 320 rpm = 33.5 rad/s | 570 rpm = 59.7 rad/s |
| トルク定数 Kt | 0.16 N·m/A（**未決。実機の Kt は分銅で測るまで確定しない**） | 0.095 N·m/A |
| ロータ慣性 | 1.002e-4 kg·m² | 1.1183e-4 kg·m²（×81 で 9.06e-3、**実測 9.77e-3**） |
| 外形 | Ø98 × 61.7 mm | Ø98 × 38.5 mm |
 
- **ベンチ実測（AK80-9）:** 動摩擦 **0.22 N·m** / 出力軸慣性 **9.77e-3 kg·m²**。旧 0.54 は静止摩擦だった。**AK10-9 は未実測**（friction 暫定 0.37）。
- 実機 MIT での静止摩擦 0.30〜0.32 N·m（`motor_can_findings.md`）。
### 質量（2026-09-16、新 URDF・USD で確認）
 
- **総質量 10.105775 kg**（Onshape API 実測 10.1058 kg と一致）。**根＝胴体 `base` 2.91813 kg。** 左右対の質量一致。慣性テンソルは非対角成分込みの CAD 実値。
- 旧 URDF 総質量 14.633 kg は CAD の材質がでたらめだった（2026-09-04 発覚、09-06 に Onshape 側を修正）。
- **旧 URDF の質量表（`base` 0.2406 / `lr_hr` 2.1692 …）は根がずれていたので無意味。** 削除した。
- 脚パーツの製作材料（アルミ / 樹脂）は未決。CAD の材質は仮。
### 関節 limit（2026-09-16、URDF）
 
| | HR | HAA | HFE | KFE | FFE |
|---|---|---|---|---|---|
| velocity [rad/s] | 23 | 15 | 20 | 20 | 23 |
| effort [N·m] | 24 | 30 | 30 | 30 | 20 |
| lower / upper | ±π | ±π | ±π | ±π | ±π |
 
- **effort は学習に効かない**（explicit actuator で `effort_limit_sim` 未指定なので実トルク上限は actuator cfg の `effort_limit`。Isaac Lab 2.3.2 の `actuator_base.py` で確認）。**旧記述「URDF の effort と actuator の effort_limit のどちらが効くか未確認」は解決。**
- **velocity は効く**（`velocity_limit_sim` 未指定で USD の値にフォールバック）。onshape-to-robot の既定は 10 rad/s で、**旧 URDF での過去の学習も 10 rad/s 上限だった。** 今回 actuator cfg の値に揃えたので上限が 1.5〜2.3 倍に上がった。
- **lower/upper は効く**（USD の可動域・`dof_pos_limits` 報酬）。**機構的可動域はまだ入れていない（宿題）。** 2026-09-06 に入れた Skyentific の USD 実測値（HR ±45° / HAA ±40° / HFE ±90° / KFE ±135° / FFE ±90°）は、**旧機体のゼロ点・符号に対するもの**で、新しい約束（`robot_model_conventions.md`）ではそのまま使えない。
- 値は 08-21 版 actuator cfg に合わせた暫定。**定格かピークかは actuator cfg 側の見直しで決める。**
### Onshape の注意
 
- **インスタンス一覧の先頭が base link になる。先頭は胴体 `Part 1 <6>`。動かさない。**
- **「固定（Fixed）」は使わない。**
- **編集前に「バージョンを作成…」。**
- **ブラウザのログイン済みセッションから Assembly API を叩けば構造を実測できる。**
- モーターは外部参照のサブアセンブリで材質を付けられない → ダミー版 004_sim は円柱に置き換えたもの。
- 脚パーツは Part Studio 内で材質を割り当てる（Assembly では不可）。
- **Onshape 標準 Export ダイアログの設定は onshape-to-robot とは無関係**（API を直接叩くため）。
### ゼロ点（2026-09-16 に意味が確定）
 
- **後処理後の URDF のゼロ姿勢＝脚がほぼまっすぐ下、爪先 +X、足裏ほぼ水平**（3面図で確認）。
- 学習方策が返す関節角は「`init_state.joint_pos` 基準の相対角」。**実機の原点（SET_ORIGIN / MIT の原点）はこのゼロ姿勢に合わせる前提で考える**（B11 段階2・3）。
---
 
## B8. 既知バグ・修正済み事項
 
### ★ rsl_rl の構造的欠陥（2026-09-07 に特定）
 
- **症状:** `RuntimeError: normal expects all elements of std >= 0.0`。学習後半で繰り返し発生。
- **真因:** 行動分布の std が**生の実数パラメータ**で、大きな勾配ステップ一発で 0 未満に落ちる。後半ほど std が小さいので落ちやすい。
- **対処:** `rsl_rl_cfg.py` で **`noise_std_type="log"`**。Alienware では以降ゼロ再発。
- **★WRS機の 08-21 版には入っていない。** 長い学習の前に入れ直す（`wrs_training_strategy.md` §1）。
- 外した仮説: `push_force` 上限／`joint_vel_out_of_manual_limit`／`clip_actions`（どれも再発）。発散直前に `action_rate_l2` が6〜10倍に跳ねる。
### 修正済み（WRS機のコードに入っているもの）
- `curriculums.py`: 旧API `_term_dones["…"]` → `get_term("…")`
- `train.py` / `play.py`: `import skyentific_poclegs  # noqa: F401`
- **機体モデル（2026-09-16、`6ede75b`）:** 根＝胴体、base +90°、5関節の軸反転、limit、初期姿勢 HAA=0・スポーン高さ 0.3758 m
### Alienware で直したが WRS機に入っていないもの（未 push で消失）
- `modify_command_velocity` の降格ロジック（2026-09-07）
- `feet_air_time` の `stance_timeout`（2026-09-07。初回実装で `threshold_max` を誤流用するバグを作ったので専用パラメータにした）
- `noise_std_type="log"` / `clip_actions` / 報酬 weight 変更 / 前進限定 / `bad_orientation` 0.8 rad / `joint_vel_out_of_manual_limit`
- **戻すかどうかは `wrs_training_strategy.md` §1 で仕分け。**
### 修正済みの CAD 側
- 2026-09-14: インスタンス並び順の先頭を胴体 `Part 1 <6>`（Mate 無変更）。
### 修正済みドキュメント誤記
- **「カニ歩きは機体の左右非対称が原因」は不完全だった**（2026-09-16。base の前後ずれが見つかった）
- **「GitHub の正本は master」は誤り**（2026-09-15。`main` しか無い）
- **「08-21 版に `bad_orientation` は無い」は誤り**（2026-09-16。WRS機の実物は 1.3 rad で存在。0.8 rad は Alienware 9月版）
- 「木構造は同型と確認済み」「非対称の原因は CAD の Mate」「Alienware の症状は熱依存」「ドライバ説は完全に排除」も誤り／言い過ぎだった
- `claude/handoff.md` は重複だったので 2026-09-06 に削除
### 過去に解決した環境トラブル
- Alienware: Slack(deb版) の syslog 肥大化でディスク満杯 / pip 消失（`python -m ensurepip --upgrade`）/ 595 ドライバ事故
- 参考実装 `setup.py` の `torch==2.5.1` pin → `--no-deps` で editable インストール（WRS機も同じ）
- WRS機の環境トラブル（Avast、tensordict、URDF インポーター等）は `wrs_pc_environment.md` §3
---
 
## B9. 未整備・宿題
 
### 【最優先】柱A: 新しい機体で学習を再開する（新しいチャットで）
 
1. **学習戦略を決める**（`wrs_training_strategy.md`、`next_chat_briefing.md`）。棚卸し済み（§1）。
2. **最初に確かめること: base の前後修正でカニ歩きが消えるか。** 残差 `v_y − cmd_y`、`error_vel_xy`、`terrain_levels`、録画。
3. **学習の土台:** `noise_std_type="log"`、アクチュエータのグループ分け（HFE を AK80-9 側へ）、effort / armature / friction の実機寄せ。
4. **4096 env の基準値を測る**（秒/iter、VRAM、温度）→ A5 を書き換える。
5. **制御周期（`sim.dt × decimation`）が実機の 50 Hz と合っているか確認。**
6. **WRS機での録画（`play.py --headless --video`）が動くか確認。** `exported\policy` が出るか。
### 柱A: その後
 
7. **トルク要求の内訳を分離する**（B12）。`stiffness × 位置誤差` と `damping × 関節速度` を別々に。
8. **トルク-速度 droop**（`DCMotorCfg` は存在を確認済み）。
9. **報酬の再設計**（立ち止まりの給料、dense な足上げ）。
10. **機構的可動域を URDF の lower/upper に入れる**（新しい符号の約束で測り直す）。
11. **base 原点の位置**（胴体中心でなく脚より約 9 cm 前）。観測の速度はこの点で測られる。胴体中心か IMU 位置へ移すか検討。
12. **地形を坂特化に。**
13. **run フォルダ対応表**（フォルダ名・iter・変更内容・評価）を残す。
14. **`isaaclab_edit_guide.md` / `rough_env_cfg_walkthrough.md` の古い記述の訂正。**
### 柱B：モーター制御（WRS機・Alienware に依存しない）
 
15. **`morg` で MIT の位置原点を出す**（`mit_implementation_briefing.md`）。
16. **Kt を分銅＋アームで測る**（3回とも分銅なしで無効）。
17. **AK10-9 の `fric` / `coast` ベンチ実測。**
18. 安全機構（非常停止・enable/disable・受信タイムアウト）。
19. **関節名 ↔ モーターID ↔ 符号の対応表**（`robot_model_conventions.md` の軸の約束を基準に。**再エクスポートで joint 順が確定したので作れる**）。
20. 定周期制御ループ（50 Hz）、サイン波で試歩行。
21. 保持時のリミットサイクル（90度で 0.4〜1.0 A を約5Hz で往復）。
### 橋：学習方策の実機デプロイ
 
22. 方策エクスポート確認（`play.py` で `exported/policy.onnx`）。
23. **観測ベクトルの契約を書き出す**（B11 段階2。新しい joint 順と符号で）。
24. 制御ループに方策を統合 → 1モーター→脚1本→全身。
### 共通・環境・その他
 
25. **Onshape API キーを Revoke**（2026-09-16 の作業後。次回は発行し直す）。
26. **Alienware:** 費用ゼロの4手（A2a）。救出価値は下がった（A2a）。
27. WRS機の git 用証明書変数の確認（`GIT_SSL_CAINFO`）。
28. `kani_walk` / `original` ブランチの中身の確認。
29. タスク登録用 `__init__.py` の分離（残1件）。
30. `.bak` の整理（WRS機の `onshape_export\myrobot_dummy\` に多数、`robot_sim_IN/OUT.urdf`）。
31. （ハード）電源系（12S 級、テザー給電）、実機構成（Jetson / T265 / USB2CAN）、脚パーツの材料。
---
 
## B10. CubeMars CAN プロトコル
 
> **★実測で確定した内容は `claude/motor_can_findings.md` が正本。MIT の実装指示は `claude/mit_implementation_briefing.md`。** この節は索引だけ。
 
- **制御モード（MIT / サーボ）とフィードバック方式（定期 / クエリ応答）は別の次元。** V3.0 では独立に選べる。
- **サーボ:** 拡張29bit、CAN ID = `(モード << 8) | ID`。0=Duty / 1=Current / 2=CurrentBrake / 3=Velocity / 4=Position / 5=SetOrigin / 6=Position-Speed。
- **MIT = モード8**（`(8 << 8) | ID`）。**ペイロード順は Kp → Kd → 位置 → 速度 → トルク**（classic MIT の位置先頭とは違う）。enable 不要。応答はサーボ形式 `0x29xx` の 50Hz 定期。
- **2026-09-07 に classic MIT 並びで送ってバスが落ちたのは、ペイロード順の誤りで Kp=250 と読まれ 48.7 A 流れたため。** 旧ルール「ext は使うな」は無効。
- **実機での主な数値:** レンジ（AK80-9 位置 ±12.56 rad / 速度 ±65 / トルク ±18、AK10-9 速度 ±28 / トルク ±54、Kp 0〜500 / Kd 0〜5）、実効 Kd = 指令 × 0.48、Kp の量子化 1LSB = 0.1221。
- **位置指令はまだ成功していない**（MIT の原点がサーボの原点と別物。Kp=2 で 16.5 A、Kd=0 保持で 277 deg/s の暴走）。
- 参考リポジトリ: `neurobionics/TMotorCANControl` / `wangykev/v3-v2_terminal_control` / `OpenFieldAutomation-OFA/cubemars_hardware` / `leggedrobotics/cubemars-ak-c-drivers`（**`cubemars.f_mit` 系のペイロード順は実機と違うので直接使わない**）。
---
 
## B11. 実機化ロードマップ
 
> Isaac Lab と実機をつなぐのは**学習ずみ方策ファイル1個**だけ。方策は「状態(obs)を入れると各関節の目標角(action)が出る関数」。
> **★2026-09-16 に機体モデル（木構造・座標・符号）が確定したので、段階2の対応表を作れるようになった。**
 
### 段階1: 方策を持ち出せる形にする
`model_*.pt` → ONNX。`play.py` 実行で `exported/policy.onnx` が出るか確認する。実機（Jetson）では onnxruntime だけで動く。
 
### 段階2: 観測ベクトルの契約を正確に写す（実機化の山場）
正解表は `rough_env_cfg.py` の policy 観測。08-21 版の連結順（height_scan は `__post_init__` で無効）:
```
base_lin_vel(3) → base_ang_vel(3) → projected_gravity(3) → velocity_commands(3)
→ hip_pos(.*HR) → kfe_pos(.*HAA,.*HFE,.*KFE) → ffe_pos(.*FFE)
→ joint_vel(全関節) → actions(前回)
```
- **base 座標は +X 前・+Y 左・+Z 上**（`robot_model_conventions.md`）。**IMU の取り付け向きをこれに合わせて変換する。** base 原点は胴体中心ではない。
- **`projected_gravity` は IMU から計算。**
- **関節角は `joint_pos_rel`＝初期姿勢からの相対角。** 実機でも「学習時 `init_state.joint_pos` を引いた値」を渡す。
- **関節順は Isaac Lab 内部順（USD ツリー順）でモーターID順とは限らない。** 学習ログか play でジョイント名の並びを出して対応表を作る。**符号の列も持つ。**
- **制御周期（`sim.dt × decimation`）と実機の 50 Hz を合わせる。**
### 段階3: アクションをモーター指令に変換
- `JointPositionActionCfg`（Isaac Lab 既定は scale 0.5、`use_default_offset=True`。**08-21 版での値は grep で確認**）→ 目標角 = 既定姿勢 + scale × action。
- **位置モード（動作確認向き）／MITモード（本命）。** シム側が飽和していると Kp/Kd の対応は成立しない（B12）。
### 段階4: 制御ループ（50Hz）
```
① CAN で現在角を読む → ② IMU と合わせて obs を組む → ③ policy(obs) → action
→ ④ CAN 指令に変換 → ⑤ 10モーターへ送信 → ①へ
```
 
### 段階5: 安全に立ち上げる順序
1モーターで生ログ確認 → 1モーターで位置指令の追従 → 脚1本を空中で → 全モーター → 方策を dt ループで。
**初回はトルク上限を絞る／脚を吊る／即停止できるように。**
 
---
 
## B12. アクチュエータ設定と必要トルク（歩かないとき・実機諸元を入れるとき見る）
 
対象: `my_robot_code/skyentific_poclegs.py`。**アクチュエータは実機の機種ごとにグループ分けする。**
**★数値の正本は `claude/actuator_params.md`。** この節は考え方と診断手順。
 
> **★この節の実測値（2026-09-08）はすべて「木構造が壊れ、base の前後が 90° ずれた機体」で測ったもの。取り直す。** 考え方はそのまま有効。
 
### WRS機（08-21 版）の現状
 
| グループ | joint_names_expr | effort_limit | velocity_limit | stiffness | damping | armature | friction | delay |
|---|---|---|---|---|---|---|---|---|
| hr | `.*HR` | 24 | 23 | 10 | 1.5 | 6.9e-5×81 | 0.02 | 0〜4 |
| haa | `.*HAA` | 30 | 15 | 15 | 1.5 | 9.4e-5×81 | 0.02 | 0〜4 |
| kfe | **`.*HFE`, `.*KFE`** | 30 | 20 | 15 | 1.5 | 1.5e-4×81 | 0.02 | 0〜4 |
| ffe | `.*FFE` | 20 | 23 | 10 | 1.5 | 6.9e-5×81 | 0.02 | 0〜4 |
 
- **HFE（AK80-9）が KFE（AK10-9）と同じグループ。** 実機と合っていない。
- **effort 20〜30 N·m は AK80-9 の定格 9 / ピーク 22 を超えている。** friction 0.02 は実測（0.22〜0.37）の 1/10。armature も Skyentific の値。
- Isaac Lab に `DCMotorCfg`（トルク-速度 droop）と `mdp.randomize_actuator_gains` があることを確認済み（未使用）。
### 各パラメータの意味
 
| パラメータ | 意味 | 効き方 |
|---|---|---|
| `effort_limit` | 出せるトルクの上限 [N·m] | **ハード飽和。関節速度に依らずフラット（DelayedPD の問題点）** |
| `velocity_limit` | 速度上限 | explicit actuator では `velocity_limit_sim` が未指定だと USD（URDF）の値が物理側に効く（B7） |
| `armature` | 関節から見た反射慣性 | ロータ慣性 × 減速比²。coast 実測があればそちら |
| `friction` | **関節摩擦トルク [N·m]** | **Isaac Sim 5.0 以降は「トルク」** |
| `stiffness` | 位置ゲイン Kp | 実機 MIT の Kp に対応（Kp のスケールは未測定） |
| `damping` | 速度ゲイン Kd | 実機 MIT の Kd に対応（実効 = 指令 × 0.48、天井 2.4）。**粘性摩擦とは別物** |
 
### ★ `computed_torque` の正しい読み方
 
```
computed_torque = stiffness × 位置誤差 + damping × 関節速度
```
- **`computed_torque` は PD が「出したい」値、`applied_torque` は上限で切った後の値。物理的に必要なトルクではない。**
- 2026-09-08 の実測（HFE 43〜48 / KFE 60 N·m）は **damping 項が支配**していた疑い（25 rad/s × 1.5 = 37.5 N·m）。**「モーターが小さい」ではなく「脚の振りが速すぎる」可能性。**
- **分離の方法（未実施）:** `stiffness × 位置誤差` と `damping × 関節速度` を別々に記録し、関節速度の分布も出す。関節速度が常時 20 rad/s 超 → 歩容側で対策。位置誤差項が支配 → 本当のトルク不足。
### ★ Kp/Kd は「速さのつまみ」ではない（`wrs_training_strategy.md` §0）
- ゲインは目標角への追従の仕方を決める。脚を速く振りたいのは方策。**速さは報酬・指令・アクチュエータの物理で抑える。**
- damping を上げるほど要求トルクが増えて飽和が悪化する。**Kp/Kd は実機で再現できる現実的な値に決めてほぼ固定＋ランダム化。**
### ★ モデルの穴: トルク-速度特性（droop）
- `DelayedPDActuatorCfg` の `effort_limit` は速度に依らずフラット。実機 BLDC は速度が上がると出せるトルクが落ちる。**`DCMotorCfg`（`saturation_effort` + `velocity_limit`）で表現できる**（AK10-9 無負荷 33.5 rad/s、AK80-9 59.7 rad/s）。
### ★ 飽和したまま歩くことの含意
- 2026-09-08 の effort カリキュラム（30 → 9）は歩けたが、18 N·m で p95 が上限に張り付いた＝恒常的に飽和。
- **PD が線形域で動かない → stiffness/damping が意味を持たない → MIT の Kp/Kd 対応の前提が崩れる。** 坂はさらにトルクを要求する。
- **「シムで歩けた」は「実機で動く」を意味しない。**
### friction の不感帯
```
動き始めるのに必要な角度誤差 = friction ÷ stiffness
```
friction 0.22、stiffness 10〜15 で 0.9〜1.3 度。**実機 MIT でも Kp 20〜60 が普通なので、stiffness を上げる方が sim-to-real 的には正しい。**
 
### 必要トルクの静的見積もり（参考）
```
必要トルク [N·m] = 総質量 [kg] × 9.81 × 足接地点から股軸までの水平距離 [m]
```
10.1 kg で水平距離 0.10 / 0.15 / 0.20 m → 9.9 / 14.9 / 19.8 N·m。**動的歩行では2〜3倍。定格は連続、ピークは短時間。`effort_limit` は定格基準が本筋。**
 
### 歩かないときの診断手順
1. 立ち止まりの理論値を計算する（B4）
2. 3指標で確定（A5）。`error_vel_xy` 高＋`terrain_levels` 0 張り付き＝棒立ち
3. `Episode_Reward/` の内訳を並べる
4. **横に流れるなら `v_y − cmd_y` の残差。まず base の前後（B2）を疑う**
5. effort を段階的に下げて限界を測る（歩ける方策からの fine-tune なら通る。全グループ同時に検証する）
 