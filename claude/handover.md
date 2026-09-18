# 引き継ぎ書 — 坂登坂ロボット（2026-09-16 時点）
 
> **これは何:** このプロジェクトを引き継ぐ人、または久しぶりに戻ってきた本人が、
> 最初の15分で「今どこにいて、次に何をすればいいか」を掴むための文書。
> 手順の詳細は**手順書（`claude/project_handbook.md`）**、WRS機の環境は `wrs_pc_environment.md`、機体モデルの約束は `robot_model_conventions.md`、学習方針は `wrs_training_strategy.md`。
>
> **★ この文書の自動更新について（ユーザー承認済み・2026-09-04）**
> 重要な発見があったら、Claude はその場でこの文書を自分の判断で書き換えてよい。
> ルール: ①該当箇所を書き換える（末尾に追記しない） ②「確認済み」と「推測」を区別する
> ③誤りを訂正したら「旧記述は誤りだった」と一言残す ④更新したらユーザーに1〜2行で伝える
 
---
 
## 1. 60秒サマリ
 
**作っているもの:** 機械学習で坂を登る二足歩行ロボット。最終的に実機で坂を登らせる。
 
| | 柱A（シミュ） | 柱B（実機） |
|---|---|---|
| やること | Isaac Lab で坂を登れる方策を学習させる | CubeMars モーターを CAN で動かすコードを作る |
| 場所 | **WRS共用PC（Windows 11 / RTX 3090 Ti）**。作業は WRS機上の Claude Code、判断は Cowork のチャット | Windows ノートPC |
| 現在地 | **機体を作り直し、テスト起動が通った（2026-09-16）。学習はこれから** | **MIT（モード8）で疎通。トルク指令は通る。位置指令は未達** |
| 次の一歩 | **学習戦略を決めて学習を回す（新しいチャット）** | **`morg` で MIT の位置原点を出す** |
 
**合流点:** 学習ずみの方策ファイル1個（ONNX）を実機側のプログラムが読み込む。
 
### ★ 2026-09-16: 機体の作り直しで、過去の学習の前提が崩れた
 
WRS機で Onshape から再エクスポートした。木構造の修正（根＝胴体）は狙いどおりだったが、**途中で別の問題が2つ見つかった。**
 
1. **base の +X がロボットの横だった。** onshape-to-robot の base フレームは CAD のワールド軸そのままで、この機体では X＝左右。Isaac Lab は +X を前として速度指令を出す。**GitHub の 08-21 版 URDF も同じだった＝Alienware での過去の学習は「前進指令＝横に歩け」だった可能性が高い。カニ歩きの有力な説明。** → base を +90° 回転して修正。
2. **関節軸の符号が左右・脚の中で食い違っていた。** 同じ角度で左右が鏡写しに動かず、膝だけ軸が逆で、Skyentific の初期姿勢は 22 cm 非対称だった。→ 5関節の軸を反転。初期姿勢の HAA を 0、スポーン高さを 0.3758 m に。
**意味:** 9月に Alienware で重ねた報酬・指令の調整（前進限定、weight 上げなど）は、**横向きの機体に対する対症療法だった可能性がある。** しかもそれらは GitHub に push されておらず、WRS機のコードは 08-21 版（＋今回の機体修正）。**新しい機体でまず素直に学習し、カニ歩きが消えるかを確かめてから、戻す変更を選ぶ。**
 
---
 
## 2. すぐ動かしたいとき
 
### 柱A — WRS機（PowerShell）
 
**前提:** `conda activate D:\Tominaga\envs\isaac_env` の後 `where.exe python` が `D:\Tominaga\envs\isaac_env\python.exe`。`python -m pip show tensordict` が 0.7.0。
 
テスト起動（64 env / 20 iter）:
```
conda activate D:\Tominaga\envs\isaac_env ; cd D:\Tominaga\IsaacLab ; .\isaaclab.bat -p scripts\reinforcement_learning\rsl_rl\train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 64 --max_iterations 20 --headless env.commands.base_velocity.debug_vis=false
```
 
本番学習:
```
conda activate D:\Tominaga\envs\isaac_env ; cd D:\Tominaga\IsaacLab ; .\isaaclab.bat -p scripts\reinforcement_learning\rsl_rl\train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 4096 --max_iterations 1500 --headless env.commands.base_velocity.debug_vis=false
```
 
- **Ctrl+C で止められる。途中で止めてもチェックポイントは残る。起動直後に iter 番号を目視。**
- `debug_vis=false` が無いと、矢印アセットの取得タイムアウトで落ちる。
- **共用機なので、GPU を長く使う前に一言。**
- **2026-09-16 より前のチェックポイントは全部無効**（機体が変わった）。
### 柱B（実機）— Windows ノートPC
 
**通電前に必ず: 脚を外すか固定する／電源をすぐ切れる状態にする。**
```
cd C:\Users\harut\Connect2USB2CAN
python motor_console_ver6.py
```
- `s` で状態が1行出れば通信は生きている。`log on` でセッション記録。
- トルクのみ（`t` / `sweep` / `brk`）は原点が無くても使える。位置系は `morg` で原点を出すまでロック。
- `x` はソフト停止。本当の非常停止は電源を切ること。
- バスが落ちたら: 電源OFF → USB2CAN 抜き差し → 10秒 → 電源ON。
### CAD（Onshape）— ブラウザのみ
ログイン済みセッションから Assembly API を叩けば、木構造・質量・Mate を実測できる。
 
---
 
## 3. 直近で何が変わったか
 
### 2026-09-16: 再エクスポート完了・機体の座標と符号を修正（`chats/2026-09-15_wrs-reexport-instruction.md`）
 
- **Onshape → onshape-to-robot 1.8.3（WRS機）→ URDF 後処理 → USD → テスト起動（64 env / 20 iter 完走）→ commit / push（`6ede75b`）。**
- **確認済み:** 木構造 5/5、根＝胴体 2.918 kg、総質量 10.1058 kg、左右対の質量一致、USD でも関節・limit・質量一致。
- **発見と修正:** base の前後 90° ずれ、関節軸の符号の食い違い（上記1章）。**約束事は `robot_model_conventions.md`。**
- **後処理を `tools/postprocess_urdf.py` に1本化**（robot.urdf から再実行して robot_sim.urdf と差分0を確認）。
- **limit:** velocity は URDF の値が学習に効く（過去は 10 rad/s 上限だった）→ 15〜23 rad/s に。effort は URDF では効かない。lower/upper は ±π のまま（機構的可動域は宿題）。
- **WRS機の落とし穴が増えた:** URDF インポーター 2.4.31 を Kit キャッシュからコピー、`OMNI_KIT_ACCEPT_EULA=Y`、変換は失敗しても終了コード 0、`debug_vis=false`（`wrs_pc_environment.md` §3）。
- **08-21 版コードの棚卸し完了**（`wrs_training_strategy.md` §1）: `noise_std_type` 無し、`clip_actions` 無し、指令は Isaac Lab 既定（全方向・heading 全周）、`bad_orientation` 1.3 rad あり、`command_vel` は昇格のみ、HFE と KFE が同じアクチュエータグループ、ゲインのランダム化無し。
### 2026-09-15: WRS機に環境構築・GitHub の push 漏れ判明
 
- `D:\Tominaga\` に Isaac Sim 5.1 / Isaac Lab 2.3.2 を構築（`wrs_pc_environment.md`）。
- **GitHub の `main` は 08-21 で止まっていた。** Alienware の 9月の変更は未 push。**ブランチは `main`（`master` は存在しない）。**
- 学習方針 `wrs_training_strategy.md` を作成（Kp/Kd は速さのつまみではない、heading 固定はやめる提案）。
### 2026-09-14: MIT モード確定・木構造の真因・Alienware の故障切り分け
 
- **MIT = 送信モード8**、ペイロード順 Kp → Kd → 位置 → 速度 → トルク、enable 不要。実効 Kd = 指令 × 0.48。**位置指令は未達（原点がサーボと別物）。** 次は `morg`（`mit_implementation_briefing.md`）。
- **木構造の非対称の真因はインスタンス並び順**（先頭が base になる）。胴体を先頭にして解決。
- Alienware は間欠故障。「熱依存」は棄却。
### 2026-09-06〜08（Alienware、横向きの機体での結果として読む）
 
- **学習クラッシュの真因:** rsl_rl の std が生の実数パラメータ → `noise_std_type="log"` で根絶。**これは機体と無関係に有効。**
- **立ち往生:** 立ち止まりの給料が ≈5 → ≈59 に12倍化。**考え方は有効。**
- **`feet_air_time` はスケールが2桁小さい。** 考え方は有効。
- **カニ歩き「機体の非対称＋前進限定＋報酬の重み」:** **base の前後ずれが見つかったので再検証が必要。**
- **トルク要求（HFE 43〜48 / KFE 60 N·m）:** 壊れた機体で測ったもの。damping 項支配の疑い。**取り直す。**
---
 
## 4. 次の一歩（優先順）
 
### ① 学習戦略を決めて学習を回す（柱A・新しいチャット）
→ `next_chat_briefing.md`（Cowork 側の新チャットへの指示書）と `wrs_training_operator_instruction.md`（WRS機の Claude Code の新チャットへの指示書）。
 
**最初の問い:** base の前後を直した機体で、08-21 版に近い素直な設定でもカニ歩きは出るか。
 
### ② `morg` で MIT の位置原点を出す（柱B・今すぐできる）
```
cd C:\Users\harut\Connect2USB2CAN
python motor_console_ver6.py
```
→ `log on` → `s` → `morg` → `morg` → `hold 1 0.5 2` → `ramp 3 0.5`。
 
### ③ 関節名 ↔ モーターID ↔ 符号の対応表（柱B・橋）
機体モデルが確定したので作れる。`robot_model_conventions.md` の軸の約束を基準に。
 
### ④ Kt を分銅ありで測る（柱B）
 
### ⑤ Onshape API キーの Revoke、Alienware の費用ゼロの4手
 
---
 
## 5. 触ると壊れるもの・触ってはいけないもの
 
- **★WRS機は共用。`D:\Tominaga\` の外に書き込まない。システム設定（Avast 等）を勝手に変えない。`D:\Tominaga` をリネームしない。**
- **★WRS機のハードリンクは git 操作やエディタ保存で切れる。エラーは出ない。** `Get-FileHash` で確認。
- **★tensordict を 0.7.0 から上げない**（Windows で access violation）。
- **★URDF を作り直したら `postprocess_urdf.py` を通し、自己チェック（軸の向き）を必ず見る。** 座標と符号の誤りはエラーが出ない。
- **★Onshape のインスタンス一覧の先頭（胴体 `Part 1 <6>`）を動かさない。「固定（Fixed）」を使わない。**
- **`.env`・GitHub PAT・SSH秘密鍵は絶対にコミットしない・チャットに貼らない。** リポジトリは public。
- **Isaac Lab 本体は触らない。** 例外は `import skyentific_poclegs # noqa: F401` の1行。
- **編集は必ず `my_robot_code/` 側で。**
- **push したら GitHub 側の日付を確認する**（08-21 で止まっていた前例）。
- **Alienware の NVIDIA ドライバを上げない**（復旧した場合）。
- **実機: Kp が 0.06 未満だと量子化で 0。Kp>0 で Kd=0 にしない（発振 277 deg/s）。`morg` で原点を出す前に位置指令を打たない（16.5 A / 39.7 A）。`cubemars.f_mit` を直接呼ばない。電流指令 `c` を脚付きで使わない。**
---
 
## 6. 未決の判断
 
| # | 内容 | 影響 |
|---|---|---|
| 1 | **★学習戦略: 9月の変更のどれを戻すか、最初の実験を何にするか** | 新しいチャットで決める（`wrs_training_strategy.md`） |
| 2 | **アクチュエータの実機値（effort 定格/ピーク、friction、armature、グループ分け、DCMotor 化）** | sim2real と「速すぎる」の両方に効く |
| 3 | **Kt の物理値**（停止中 0.59 は循環の疑い／回転中 0.78） | friction・effort・`brk` の根拠 |
| 4 | **Kp のスケール**（Kd は 0.48 倍と判明） | シムの stiffness を実機に翻訳できない |
| 5 | **トルク要求は damping 支配か位置誤差支配か** | 歩容チューニングか機体設計か。新しい機体で測る |
| 6 | **機構的可動域（lower/upper）** | `dof_pos_limits` が実質死んでいる |
| 7 | **base 原点を胴体中心／IMU 位置へ移すか** | 観測の速度の意味、実機の IMU との対応 |
| 8 | **制御周期と実機 50 Hz の整合** | 方策側を合わせるか、実機を上げるか |
| 9 | 脚パーツの製作材料 | 慣性精密化の前提 |
| 10 | 電源系・実機構成の確定 | 調達リードタイム |
| 11 | Alienware の修理・データ救出 | 優先度は下がった |
 
> **決定済み:** 柱Aは WRS機／ブランチ `main`／モーター割り当て（HR・HAA・KFE=AK10-9、HFE・FFE=AK80-9）／制御モードは MIT（モード8）／**機体の座標は +X 前・+Y 左・+Z 上、関節の正の向きは `robot_model_conventions.md`**／**初期姿勢 HAA=0**／`noise_std_type="log"` はクラッシュの根本対策／木構造はインスタンス並び順で解決／IMU は RealSense T265／電源はテザー給電／非常停止＝電源を切る
 
---
 
## 7. ドキュメントの地図
 
**入口は `claude/README.md`。** 主なもの:
 
| 文書 | 何が書いてあるか |
|---|---|
| `project_handbook.md` | 前提・鉄則・現在地・環境・手順・報酬設計・トラブル表 |
| `next_chat_briefing.md` | **次の Cowork チャット（学習戦略と実行）への指示書** |
| `wrs_training_operator_instruction.md` | **WRS機の Claude Code の新チャットへの指示書** |
| `wrs_training_strategy.md` | 学習方針と 08-21 版コードの棚卸し |
| `robot_model_conventions.md` | 機体の座標・関節符号・初期姿勢・limit の正本 |
| `wrs_pc_environment.md` | WRS機の環境と落とし穴の正本 |
| `wrs_urdf_reexport_instruction.md` | 再エクスポート手順（WRS機） |
| `motor_can_findings.md` / `mit_implementation_briefing.md` | 実機 CAN の実測と MIT 実装 |
| `actuator_params.md` | モーター諸元・ベンチ実測・ゲイン対応 |
| `urdf_asymmetry_finding.md` | 木構造の非対称の調査記録と診断手順 |
| `alienware_repair_instruction.md` | Alienware 故障の切り分け |
| `chats/` | 各チャットの経緯 |
 
---
 
## 8. 詰まったときの入口
 
| 状況 | まず見るところ |
|---|---|
| WRS機でコマンドがエラー | `wrs_pc_environment.md` §3（証明書、conda、tensordict、ハードリンク、EULA、debug_vis） |
| **横に流れる（カニ歩き）** | **残差 `v_y − cmd_y` で測る。まず base の前後（手順書 B2）** |
| ロボットが歩かない／立ち止まる | 立ち止まりの給料を計算（手順書 B4） |
| 学習が `normal expects std >= 0.0` で落ちる | `noise_std_type="log"` が入っているか |
| URDF を作り直した | `postprocess_urdf.py` → `verify_export.py` → `verify_usd.py` → 配置（手順書 B3） |
| 設定が有効か分からない | 文書を信じず実ファイルを grep |
| 実機: 位置指令で過大電流 | `morg` で原点を出したか |
| 実機: バスが落ちて戻らない | 電源OFF → USB2CAN 抜き差し → 電源ON |
| 数値の根拠 | `actuator_params.md`（機体）／`motor_can_findings.md`（CAN） |
 
---
 
## 9. 進め方の原則（これだけは引き継いでほしい）
 
1. **推測で進めない。** 外した実績多数（「カニ歩きの主因は構造非対称」「非対称の原因は CAD の Mate」「MIT には ID 方式で入れない」「HR が 45° 回っている」…）。
2. **ツールの暗黙の前提を一次資料・ソースで確認する。** onshape-to-robot の根と base フレーム、Isaac Lab の +X＝前、MIT のペイロード順。
3. **数を数える検証は構造・座標・符号の誤りを検出できない。** 親子関係、軸の向き、FK、3面図を目で見る。
4. **「2つの出力が一致する」は「正しい」ではない。** 照合先は設計意図。
5. **指標の定義が設定によって意味を変える。** 生の `v_y`、`computed_torque`、指令トルク。
6. **エラーが出ないタイプの失敗を疑う。** 木構造、base の向き、軸の符号、Kp の量子化、ハードリンク切れ、終了コード 0 の変換失敗、push 漏れ。
7. **小さく回して通す → 本番。一度に1つだけ変える。**
8. **iter を増やしても設計問題は解けない。**
9. **ユーザーの設計知識と観察は強い証拠。** 前後・膝の向き・HAA=0 はユーザーの判断で決着した。
10. **`.bak`・Onshape のバージョン・Git のコミットは資産。push したら確認する。**
 