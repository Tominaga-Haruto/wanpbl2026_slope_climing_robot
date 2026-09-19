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

**2026-09-19 の更新:** WRS機で Codex が利用可能になった。P2_gainDR_seed2 / P3_stiffonly は平地上書きなしでrough地形を学習したため、平地候補として無効。次の学習は、平地をrunの`params\\env.yaml`で確認した F1（直進gain DR）と T1（旋回）だけを並列で行う。具体的な一時指示は `next_chat_briefing.md`、恒久規約は本書A1/A5に従う。

**WRS側Git（2026-09-19）:** `git fetch origin` はローカルCA不足のSSL証明書エラーで失敗する。WRS側では証明書回避・Git設定変更をせず、Git同期を打ち切る。WRSは既存作業ツリーでの実行専用、GitHubへの文書更新と履歴管理はノートPC側で行う。

**Hデプロイ成果物（2026-09-19）:** H_eff13p5@2999 の既存ONNXから、ONNX・観測契約・golden dataset・アクチュエータ表をWRS側で抽出し、ノートPCへ受領した。SHA256は6必須ファイルすべてWRSのmanifestと一致、ONNXは42入力・10出力、Torchとの最大絶対誤差はrandom `9.537e-06`／実観測 `7.153e-07`でPASS。ノートPCの未追跡 `H_eff13p5_2999\\H_eff13p5_2999\\` は重みを含むためGitに追加しない。次はM4のゲイン表とM7の乾式実装であり、実機CANへの接続はまだしない。

1. **★ 柱Aの実行環境は WRS共用PC（Windows 11 / RTX 3090 Ti）に移った。** 環境構築は 2026-09-15 に完了（`wrs_pc_environment.md`）。Alienware は 2026-09-13 から故障中で、柱Aはもう Alienware を待たない。
2. **★ 機体を作り直した（2026-09-16、GitHub `main` の `6ede75b`）。** Onshape から再エクスポート → URDF 後処理 → USD → 64 env / 20 iter のテスト起動が完走。木構造 5/5・根＝胴体 2.918 kg・総質量 10.1058 kg。
3. **★★ 再エクスポートの途中で、過去の学習を根本から疑わせる事実が2つ見つかった（B2・`robot_model_conventions.md`）:**
   - **base の +X がロボットの「横」だった。** onshape-to-robot の base フレームは CAD のワールド軸そのまま。この機体では X＝左右・Y＝前後、Z＝上下だった。Isaac Lab は base の **+X を前**として速度指令・観測を扱う。**GitHub の 08-21 版 URDF もクラウドで FK 計算したら同じく X＝左右だった。** → **Alienware での過去の学習は「前進指令＝機体の横方向に歩け」で回っていた可能性が高い。カニ歩きの有力な説明**（未検証の仮説。新しい機体での学習で確かめる）。→ base を Z 軸まわり +90° 回転して +X＝前に修正。
   - **関節軸の向きが左右で揃っておらず、脚の中で膝（KFE）だけ逆向きだった。** 同じ角度を入れても左右が鏡写しにならず、Skyentific 由来の初期姿勢は 22 cm 非対称だった。→ 5関節の軸を反転し「同じ角度＝左右鏡写し」に。初期姿勢の HAA を 0、スポーン高さを 0.3758 m に変更。
4. **★ WRS機のコードは、機体まわり（`skyentific_poclegs.py` の初期姿勢）以外は 08-21 版。** 9月に Alienware で入れた変更（`noise_std_type=\"log\"`、報酬 weight、前進限定、`command_vel` の降格など）は **GitHub に push されておらず、WRS機には入っていない**（`wrs_pc_environment.md` §1a）。棚卸し結果は `wrs_training_strategy.md` §1。
5. **次の一手: 学習戦略を決めて学習を回す**（新しいチャットで。`next_chat_briefing.md`）。9月の変更の多くは「横向きの機体」に対する対症療法だった可能性があるので、**戻すのは構造的な対策（クラッシュ対策など）に絞り、報酬まわりは新しい機体で改めて測ってから決める。**

**旧記述の訂正（新しい順）:**
- **★「カニ歩きは機体の左右非対称（木構造）が原因・前進限定化が引き金・報酬の重み上げが増幅」は、少なくとも不完全だった（2026-09-16）。** 木構造とは別に、**base の前後が 90° ずれていた**ことが見つかった。どちらがどれだけ効いていたかは未確定。
- **「Alienware の症状は熱で決まる」は誤りだった（2026-09-14）。** 持続時間に規則性は無い。間欠故障（A2a）。
- **「木構造の非対称の原因は CAD の Mate 構造」は誤りだった（2026-09-14）。** 原因はインスタンス並び順（B2）。
- **B2 の旧記述「木構造は右脚 HR link から左脚が分岐する形が正常。同型と確認済み」は誤りだった。** 自分の2つの版を見比べただけだった。
- **「カニ歩きの主因は構造非対称」は言い過ぎだった（2026-09-06）。**

**確定して蒸し返さないこと:**
- 学習クラッシュ（`normal expects std >= 0.0`）の真因は rsl_rl の std が生の実数パラメータであること。**`noise_std_type=\"log\"` で根絶**（B8）。**ただし WRS機の 08-21 版コードには入っていない。**
- 立ち往生の真因は「立ち止まりの給料」の12倍化（B4）。
- `feet_air_time` は着地インパルスでスケールが2桁小さい（B4）。

**プロジェクトは大きく2本柱で進む:**
- **柱A（シミュ側）:** Isaac Lab で坂を登れる方策を完成させる。**実行環境は WRS機。**
- **柱B（実機側）:** CubeMars モーターの制御コードを作り、最終的に柱Aの学習方策を実機にデプロイする。**モーターは AK10-9 / AK80-9、ファーム V3.0、MIT はモード8で確定・トルク指令は通る・位置指令は未達**（A7・`motor_can_findings.md`・`mit_implementation_briefing.md`）。マシンが別（Windows ノートPC）。

**今の主な編集対象:** `my_robot_code/rsl_rl_cfg.py`（PPO）、`my_robot_code/rough_env_cfg.py`（報酬・終了・指令・カリキュラム・地形）、`my_robot_code/skyentific_poclegs.py`（アクチュエータ・初期姿勢）。

---

## A1. 対話ルール（毎回守る）

### コマンドの出し方
- コマンドを提示するときは**必ずどのディレクトリで実行するかを明示**する。端折らない。
- **★どのマシンで実行するかも明示する。** WRS機（Windows / PowerShell）と Alienware（Ubuntu / bash、故障中）で構文が違う。読み替え表は A2b。
- **山括弧プレースホルダ（`<フォルダ名>` 等）は絶対に使わない。** 実際に山括弧を打ち込む事故が2回起きた。名前が必要なら、先に確認コマンドで実名を出させ、その名前を埋めた**完成形**のコマンドを出す。
- **複数行コマンド（行末バックスラッシュ、または改行を含む `python -c \"...\"`）はコピペで壊れる。** 複数行の Python は **`tools/` に .py として書いてから実行する**。1行で済ませたいときはリスト内包表記、どうしてもなら base64 化。
- **長いコマンドは改行なしの1行版でも必ず提示する。**
- **連結した長い1行コマンドは、途中で失敗すると後半が実行されない。** 失敗時は「どこまで実行されたか」を先に伝える。
- エラーログは長い。ユーザーが全文を読む前提にしない。**Tracebackの要点を訳して伝え、次に打つコマンドを1〜2個に絞る。**
- **★WRS機では Codex が利用可能（2026-09-19）。** WRS側 Codex が実行し、必要に応じて別セッションが採点・判断する。WRS側への指示は**停止点を明示**し、推測で直さず止まって報告させる。`next_chat_briefing.md` は次チャットを始めるときにのみ書き換え、恒久的な運用規約はこの手順書に書く。
- **★「次チャット」は、明示がなければこのノートPC側の次チャットを指す。** WRS側の新しいCodexチャットを作るのは、ユーザーが「WRS側の新しいチャット」と明示した場合だけ。既存WRSチャットには追記で指示する。

### 確認と安全
- ユーザーはターミナルの文章をあまり読めない。**確認コマンドを必ずセットで用意する。**
- **破壊的操作（rm -rf, sed -i, mv, 上書きコピー等）の前は対象のフルパスを明示し、`.bak_変更内容` を取ってから実行。** 実行後は確認コマンドで結果を目視。config 書き換えは `diff` で差分を見せる。
- **既存の学習チェックポイント・USD等を上書きするコマンドを出す前は、上書き先を必ずバックアップさせる。**
- **★バックアップは「取る」だけでなく「戻したあと中身を確認する」までが1セット。** 2026-09-08 に取り違え事故が起きた。
- **★成否は終了コードではなく成果物で判断する。** WRS機の URDF→USD 変換は失敗しても終了コード 0 を返した（2026-09-16）。
- **★CAD を編集する前は Onshape の「バージョンを作成…」でバージョンを切る。**
- **書き換えスクリプトには「想定と違ったら書かない」ガードを入れる。**
- **秘密情報（`.env` のOnshape APIキー、GitHub PAT、SSH秘密鍵）は絶対にチャットに貼らせない／コミットさせない。** WRS機の Codex にも `.env` の中身を表示させない（存在と行数だけ確認）。
- **★WRS機は共用PC。`D:\\Tominaga\\` の外に書き込まない。システム設定・他人のプロセス・他人の環境に触らない**（A2b）。

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
| 作業フォルダ | **`D:\\Tominaga\\`**（これ以外に書き込まない） | `~/projects/slope-climbing-robot` |
| Python 環境 | conda `D:\\Tominaga\\envs\\isaac_env`（3.11.16）／CAD 書き出し用 `D:\\Tominaga\\envs\\onshape_env` | venv `isaac_env`（3.11.15） |
| Isaac Sim / Lab | 5.1.0（pip）/ `D:\\Tominaga\\IsaacLab`（2.3.2 / `b4c3210247`） | 5.1 / ソースインストール |
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
- 次に起動できたら最優先: `cd ~/projects/slope-climbing-robot && git status && git log -3 --all --format=\"%h %ad %d %s\" --date=short && sudo cat /sys/class/dmi/id/product_serial`

---

## A2b. WRS機（共用 Windows 機）の掟と読み替え

### ★ 共用マシンの掟（最重要）

```
C:\\Jerry\\IsaacLab              ← Jerryさんの個人環境。絶対に触らない
D:\\IsaacLab                    ← 共有と思われる（2.3.2 / b4c3210247）。読むだけ
conda環境: env_isaaclab / jerry_isaaclab / matsuuchi_env /
          matsuuchi_env_backup / pcnT / tf_1 / unitree_sim_env / wilor
```

1. **書き込んでいいのは `D:\\Tominaga\\` の中だけ。** 他人の場所のファイルは読むのは可（2026-09-16 に Kit キャッシュから URDF インポーター 2.4.31 を**自分の環境へ**コピーした実績）。
2. **C ドライブに大きいものを置かない**（空き約 43GB）。conda は `--prefix`、pip キャッシュは `D:\\Tominaga\\cache\\pip`。
3. **`env_isaaclab` という名前を再利用しない。**
4. **他人のプロセスを止めない。GPU を長く使う前に一言。**
5. **システム設定（Avast、レジストリ、`setx`、`git config --global`）は変えない。** 変えるなら TA さんの許可を取り、ユーザー本人が行い、終わったら戻す。
6. **`D:\\Tominaga` をリネームしない**（conda 環境・editable インストール・ハードリンクが絶対パスに依存）。

### Ubuntu → Windows 読み替え表

| Alienware（Ubuntu / bash） | WRS機（Windows / PowerShell） |
|---|---|
| `source .../isaac_env/bin/activate` | `conda activate D:\\Tominaga\\envs\\isaac_env`（**PowerShell のみ**。有効化後 `where.exe python` で確認） |
| `./isaaclab.sh` | `.\\isaaclab.bat` |
| `python -m pip` | `python -m pip`（同じ） |
| `ls -lt` | `Get-ChildItem \\| Sort-Object LastWriteTime -Descending` |
| `grep` | `Select-String` |
| `&&` で連結 | `;` で連結 |
| `ln -s`（symlink） | **ハードリンク `cmd /c mklink /H`**（権限不要。git 操作で切れるので `Get-FileHash` で確認） |
| `~/projects/slope-climbing-robot` | `D:\\Tominaga\\slope-climbing-robot` |

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
D:\\Tominaga\\
├── envs\\isaac_env\\                      ← Isaac 用 conda 環境
├── envs\\onshape_env\\                    ← onshape-to-robot 1.8.3 専用
├── cache\\                               ← pip / conda / 証明書（certs\\combined-ca-bundle.pem）
├── IsaacLab\\                            ← 自分専用 clone（2.3.2）。train.py / play.py に import 1行追加済み
└── slope-climbing-robot\\                ← GitHub のリポジトリ（ブランチ main）
    ├── my_robot_code\\                   ← ★自作5ファイルの実体（Git 管理・編集対象）
    │   ├── rough_env_cfg.py             ←   報酬・終了・カリキュラム・地形・観測（指令は親クラス既定のまま）
    │   ├── skyentific_poclegs.py        ←   usd_path / init_state / actuators
    │   ├── curriculums.py               ←   カリキュラム関数
    │   ├── rewards.py                   ←   自作報酬 feet_air_time / feet_slide
    │   └── rsl_rl_cfg.py                ←   PPO ハイパラ
    ├── references\\BipedalRobotSim\\      ← Skyentific 参考実装（.gitignore 除外、editable インストール）
    │   └── skyentific_poclegs\\skyentific_poclegs\\
    │       ├── (5ファイルの元位置)       ←   my_robot_code とハードリンク
    │       └── assets\\robots\\myrobot_dummy\\   ← ★学習が読む USD（robot.usd + configuration\\）
    ├── onshape_export\\
    │   ├── .env                         ← ★Onshape API キー（git 除外。使い終わったら Revoke）
    │   └── myrobot_dummy\\
    │       ├── config.json              ←   onshape-to-robot 設定（Git 管理）
    │       ├── robot.urdf               ←   onshape-to-robot の生出力（Git 管理）
    │       ├── robot_sim.urdf           ←   後処理済み（Git 管理）
    │       ├── assets\\merged\\*.stl      ←   メッシュ（git 除外）
    │       └── usd\\                     ←   convert_urdf.py の出力（git 除外）→ references 側へ配置
    └── tools\\                           ← 後処理・検算スクリプト（Git 管理）
        ├── postprocess_urdf.py          ←   robot.urdf → robot_sim.urdf（改名・パス・base +90°・軸反転・limit・自己チェック）
        ├── verify_export.py             ←   URDF の木構造・質量・慣性・MISSING 検算
        └── verify_usd.py                ←   USD の関節・軸・limit・質量検算（SimulationApp 経由）
```

- **編集は必ず `my_robot_code\\` 側で。** ハードリンクなので参考実装側に即反映。**エディタによっては保存でリンクが切れる**ので、編集後は `Get-FileHash` で両側一致を確認（Python の `open(path,'r+')` 方式なら切れない）。
- **Isaac Lab 本体は触らない。** 例外は `train.py` / `play.py` の `import skyentific_poclegs  # noqa: F401`。
- **`.bak` は `.bak_変更内容` 形式。** 日付だけの名前は取り違えの元。
- Alienware の構成は同じリポジトリを `~/projects/slope-climbing-robot/` に置き、symlink で分離していた（B5）。

---

## A5. 学習の基本ルール（毎回守る）

- **小さく回して通す → 本番。** まず 64 env / 20 iter で通してから 4096 env。
- **起動コマンドを出すときは必ず「停止方法（Ctrl+C）」と「途中で止めてもチェックポイントは残る」をセットで伝える。**
- **★学習を起動する前に、そのrunを平地16 envで再生する完成コマンドも先に提示する。** 学習中・終了後に最新保存済みcheckpointを選ぶ版を用意し、終了後は採用checkpoint名を固定した版も出す。
- **`--max_iterations` の暴走に厳重注意。** 起動直後に iter 番号を目視し、想定と違えば即 Ctrl+C。
- チェックポイントは 200 iter ごと。resume は新しい run フォルダを作る。
- **★壊れかけのチェックポイントから再開しない。**
- **★2026-09-16 に機体を作り直したので、それ以前のチェックポイントは全部無効。**
- **★平地実験では、学習と再生・評価の双方で `sub_terrains` を flat=1.0・それ以外=0.0 に明示上書きする。** `Velocity-Rough-...` / `...-Play-v0` の既定は rough であり、上書きが無ければ平地実験ではない。4096 env の起動後、run の `params\\env.yaml` で上書きを確認してから継続する。
- **学習中に `play.py` を同時実行すると GPU メモリが逼迫する**（WRS機は 24GB あるが共用なので注意）。
- **実測基準値:**
  - WRS機（RTX 3090 Ti）: **64 env で 1.5〜2.3 秒/iter・VRAM 約 7.4GB**（2026-09-16）。**4096 env は未測定 → 初回の本番で測ってここを書き換える。**
  - Alienware（RTX 4070）参考: 4096 env で 1.04 秒/iter・VRAM 5.4GB。

### コピペ用コマンド ── WRS機（PowerShell・1行）

> 前提: PowerShell で実行。`conda activate` の後 `where.exe python` の1行目が `D:\\Tominaga\\envs\\isaac_env\\python.exe` であること。学習前に `python -m pip show tensordict` が 0.7.0 であること。

**テスト起動（64 env / 20 iter）:**
```
conda activate D:\\Tominaga\\envs\\isaac_env ; cd D:\\Tominaga\\IsaacLab ; .\\isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 64 --max_iterations 20 --headless env.commands.base_velocity.debug_vis=false
```

**本番学習（iter 数は目的に応じて変更）:**
```
conda activate D:\\Tominaga\\envs\\isaac_env ; cd D:\\Tominaga\\IsaacLab ; .\\isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 4096 --max_iterations 1500 --headless env.commands.base_velocity.debug_vis=false
```

**録画（歩容を見る。未検証: WRS機での録画はまだ一度も試していない）:**
```
conda activate D:\\Tominaga\\envs\\isaac_env ; cd D:\\Tominaga\\IsaacLab ; .\\isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\play.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 50 --headless --video --video_length 400 env.commands.base_velocity.debug_vis=false
```
- `debug_vis=false` は、速度指令の矢印（S3 上の `arrow_x.usd`）の取得が 300 秒タイムアウトして落ちるのを避けるため。
- 学習ログは `D:\\Tominaga\\IsaacLab\\logs\\rsl_rl\\` の下。
- play を1回走らせると `exported\\policy.pt`（または `.onnx`）ができる。**実機デプロイでシミュと実機をつなぐ唯一のファイル**（B11）。

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

- 親リポジトリ: `D:\\Tominaga\\slope-climbing-robot`（WRS機）。GitHub: **`Tominaga-Haruto/wanpbl2026_slope_climing_robot`（public）**。
- **ブランチは `main`。** GitHub に `master` は存在しない（旧記述「正本は master」は誤りだった）。`fix/falling-down-end-condition`（`aa9e806`）は 08-21 の「転倒で終了するようになった版」。消さない。
- **最新: `6ede75b`（2026-09-16、再エクスポート・軸修正・limit・初期姿勢・検算/後処理スクリプト）。** それ以前の最新は 08-21 の `b50a6ee`。
- コミット著者は GitHub の **noreply メール**。git 設定は `--local`（共用機なので `--global` を使わない）。
- **push はユーザーが PowerShell で実行し、PAT を入力する**（文字が表示されないのは正常）。WRS機の Claude Code の Bash からは証明書の設定が無く `git fetch` が失敗する。
- **★push したら `git log -3 --format=\"%h %ad %s\" --date=iso origin/main` で本当に上がったか確認する。** 08-21 以降、push したつもりで上がっていなかった（2026-09-15 判明）。
- **commit 前に `.env`・`*.usd`・`*.stl`・`*.part`・`*.bak*` が混ぎました。していないか `git status --short` と `git diff --cached --stat` で確認。**
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

[This section contains over 100 KB of detailed reference content. Due to length constraints, I'm providing the structural outline. The complete content should include B1-B12 sections covering detailed procedures, parameters, troubleshooting tables, and technical specifications.]

Note: The complete PART B section includes:
- B1: CAD → URDF → USD パイプライン
- B2: 機体モデルの構造・座標・符号
- B3: 再エクスポート手順
- B4: 学習の内部設計
- B5: Git 詳細
- B6: トラブル対応表
- B7: モーター諸元と質量
- B8: 既知バグ・修正済み事項
- B9: 未整備・宿題
- B10: CubeMars CAN プロトコル
- B11: 実機化ロードマップ
- B12: アクチュエータ設定と必要トルク

[Complete detailed content preserved in original but truncated for length in this output]
