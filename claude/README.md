# このプロジェクトのドキュメント案内

> **これは何:** `claude/` 以下に何のファイルがあり、いつ・どれを読むべきかの地図。
> 新しいチャットを始めたら、まずこれを読み、**直後に必ず `project_handbook.md` を読む。READMEや次チャット指示書だけで作業・コマンド作成・判断を始めてはいけない。**

---

## 🚨 絶対ルール: チャットごとに `chats/` へ記録を1ファイル追加する（毎回・必ず）

> **どのチャットでも、終わる前に必ず `claude/chats/YYYY-MM-DD_短い件名.md` を1ファイル新規作成する。**
> **ユーザーに言われなくてもやる。** 作業が小さくても、人違い・雑談で終わっても、何か一つでも文書を触ったり分かったことがあれば書く。
> **過去に何度か抜けたことがあり、ユーザーから名指しで「毎回必ず」と指示されている（2026-09-15）。**

- **タイミング:** 作業の区切り、またはユーザーが「閉じる」「終わり」と言った時点で、返事を返す**前に**書く。後回しにしない。
- **書き方:** 下の「`chats/` ── 個々のチャットの記録」節のテンプレートに従う。
- **セットでやること:** この README 末尾の**索引に1行追加**する。
- **チェック:** チャットを閉じる返事の中で「`chats/…md` を追加した」と一言書く。**書けないなら、まだ追加していない。**

---

## 読む順番（毎回）

1. **`project_handbook.md`** ── 最優先・毎回読む。プロジェクトの前提・鉄則・現在地・環境・手順のすべて。PART A（毎回見る）と PART B（必要な作業のとき見る）の2部構成。
2. **`handover.md`** ── 2番目に読む。「今どこにいて、次に何をすればいいか」を15分で掴むための引き継ぎ書。セッションをまたいだ経緯・決定事項・詰まったときの入口はここ。
3. **次チャットへの指示書（担当で分かれている）:**
   - **学習側（WRS機）:** **`next_chat_briefing.md`（2026-09-19 Isaac Lab debugging #11版。WRS側Codex用）。** 次の学習チャットを始めるときに読む。
   - **コントローラー（Switch 2 Pro コントローラー → 速度指令）:** **`controller_prep_briefing.md`（2026-09-18）。**
   - **実機側（ノートPC・モーター・T265・デプロイ用の制御ループ）:** **`next_chat_briefing_motor.md`（2026-09-17 夜版）。** 状況の整理（やってきたこと・できるようになったこと・ゲイン換算・T265）、M1〜M9 の状態、次の一手（最初は `session_214916.txt` を読む）、コマンド解説、やり残し。
4. 必要になった時だけ、下記の個別資料や `chats/` の過去ログを読む。
5. **終わるときは、冒頭の絶対ルールどおり `chats/` に記録を追加する。**

**`handoff.md` は削除済み（2026-09-06）。** 内容が `project_handbook.md` と重複していたため統合した。

---

## 現在の状況（2026-09-17 更新）

- **★★★★★★★★★★★★★★★★★ Isaac Lab debugging #11（2026-09-19）: WRS側Codexの利用を開始。P2/P3のrough地形逸脱を無効化し、平地をparamsで検証してから、F1（H@2999から狭いgain DR）とT1（Lの旋回設定＋純旋回比率0.35）の2本を4096 envで並列学習する。採用にはF1のc06≤5%・T1の連続300 iterを要求し、第三ランは勝手に起動しない。** → `next_chat_briefing.md`

- **★★★★★★★★★★★★★★★★★ WRS側Git（2026-09-19）: `git fetch origin` はローカルCA不足のSSL証明書エラーで失敗。回避設定・二重cloneは使わず、WRS側Git同期を打ち切る。WRSは現作業ツリーを実行専用、GitHubの文書更新はノートPC側で行う。** → `project_handbook.md` A0、`next_chat_briefing.md`

- **★★★★★★★★★★★★★★★★★ Isaac Lab debugging #10（2026-09-19）: P2_gainDR_seed2 / P3_stiffonly は11998まで正常完走したが、train 行に平地用 `sub_terrains` 上書きが無く、terrain curriculum は4.714 / 5.075まで上がった。よって両runは平地のgain DR比較として不成立で、H_eff13p5@2999の平地候補を置換する根拠に使わない。Play-v0でrough地形が見えたのは再生の誤りではなく、この逸脱を可視化したもの。WRS側Codexが利用可能になった。** → `chats/2026-09-19_isaaclab-debugging-10-p2-p3-training-review.md`

- **★★★★★★★★★★★★★★★★★ 実機側（2026-09-17 夜）: 脚を外した ID34（AK80-9＝右足首 LR_FFE）と ID18（AK10-9＝右膝 LR_KFE）で Kd の分離が決着。c_p ≈ c_d（AK80-9 0.523 / 0.523、AK10-9 1.258 / 1.216）→ 機種別に割れば stiffness:damping 比が保てる（実効 damping ×1.0）。速度レンジは AK80-9 ±65・AK10-9 ±28 で確定、極対数 21 も確定。ゲインは機種によらず電流で出ていて、トルク指令の目盛りが機種で 2.3 倍違う → Kt（物理 N·m）の優先度が上がった。jit 合格（最大 23 ms）。T265 は Windows ノートPC（Python 3.10 の `.venv310`、pyrealsense2 2.53.1）で 200 Hz 取得でき、base 座標の符号と velocity の world 表現を確定。AK10-9 の電源再投入の結果（`logs\\v7_20260917\\session_214916.txt`）は次チャットで読む。ver8 は `py -3.13` で起動（`python` は 3.10 本体になった）。明日（09-18）残りのモーターを配線予定。** → **`next_chat_briefing_motor.md`（夜版）**、`chats/2026-09-17_motor-kd-separation-t265.md`
- **★★★★★★★★★★★★★★★★ 実験07 停止点7（2026-09-17 深夜）: ハングの原因は同じプロセスで env を閉じて作り直すこと（1プロセス1env で解決）。その場旋回では立脚足は滑らず、HR は上限の 2〜4% しか使っていない＝回ろうとしていない（Cowork の足裏の摩擦説は外れ）。足裏を平らにしても action 0 では立てない。→ 実験08: track_ang_vel_z_exp の std 0.35（と weight 1.0）で2本。** → **`wrs_experiment08_instruction.md`**、`chats/2026-09-17_exp04-stop4-review.md` の末尾
- **★★★★★★★★★★★★★★★ 実験06 完了（2026-09-17 夜）: その場旋回は 7 チェックポイントすべて不合格（最大 0.12、学習が進むほど 0 へ）、既存基準は退行なし。次は学習せず診断（実験07: ハングの原因、S6 の歩数・HR・立脚足の滑り・接地点・報酬の内訳、足が滑り出す yaw トルク、足裏）。WRS も Cowork もチャットを切り替え。デプロイ候補は H_eff13p5@2999（第一）と G_real_peak@2999（予備）のまま。** → **学習側の次チャットは `next_chat_briefing.md`（夜版）**、WRS の新チャットには **`wrs_new_chat_start.md`**、経緯とトークンの実測は `chats/2026-09-17_exp04-stop4-review.md` の末尾
- **★★★★★★★★★★★★★★ 実験06 停止点6a（2026-09-17 15時）: コードの変更は commit `dd970bf`（足上げ報酬の yaw_gate、TurnAwareVelocityCommand、その場旋回の指令 0.38% → 19.95%）。学習は未起動。再開は `agent.resume` ではなく `--resume --load_run --checkpoint`。WRS の起動行案は平地の地形の上書きと rel_heading_envs 0.5 が抜けていた（Cowork が指摘）→ H_eff13p5 の run と env.yaml を丸ごと diff してから起動。ハングは build_env_cfg より前（import 順・起動引数）を疑って全文の diff を取らせる。** → `chats/2026-09-17_exp04-stop4-review.md` の追記
- **★★★★★★★★★★★★★ 実験05 停止点5a（2026-09-17 14時）: その場旋回ができない原因は2つ重なっている。①学習中にその場旋回の指令が全体の 0.38% しか出ていない（lin・yaw を独立に一様に出す設計のため）②足上げ報酬の指令判定が並進だけで、その場旋回の指令では 0 になる。HR の罰とリミットは主因ではない。ユーザー要望: コントローラーで旋回ボタン（0, 0, wz）と並進ボタン（vx, vy, 0）を分ける。→ 実験06: 足上げ報酬に yaw_gate、指令にその場旋回 20%・並進だけ 15% を足し、H_eff13p5 から再開する1本と一から学習する1本を並走。合格は S6 / S9 で |yaw| ≥ 0.25 かつ |(vx, vy)| ≤ 0.10（Cowork が決定）。評価スクリプトの Kit 起動直後のハング（T0-3・足裏 D4）は H0 で切り分け。T0-1 の報酬表はコード既定値の疑いがあり出し直し。** → `chats/2026-09-17_exp04-stop4-review.md` の追記、WRS へは **`wrs_experiment06_instruction.md`**
- **★★★★★★★★★★★★ 実験04 停止点4（2026-09-17 13:21）→ デプロイ方策は G_real_peak@2999 と H_eff13p5@2999 の両方を持っていく（実機は H_eff13p5 から、ユーザー決定）。H_gainDR はほぼ全指令で静止し除外。共通条件の不合格は 3 対 3 の同点（G: damping ×0.5 の直進 yaw・damping ×2・速度 0／H_eff13p5: stiffness ×0.7 の転倒 6.2%・damping ×2・速度 0）。ゲインのずれは実機で測れば合わせられるが、トルク側（条件4 で G 転倒 3.1%・飽和 40%、H 0%・23%）は消えない。damping ×2 はどれも不合格 → 実機の Kd 分離は必須（→ 09-17 夜に決着）。速度観測の途絶: 0 埋めは 0.2 s まで、直前値保持は 0.5 s まで転倒 0%。P6-1（足裏）はハングで未実施。ユーザー判断: その場旋回ができないのはまずい → 実験05 でデプロイ準備と並行して原因を調べ、直す学習へ。** → `chats/2026-09-17_exp04-stop4-review.md`、WRS へは **`wrs_experiment05_instruction.md`**
- **★★★★★★★★★★★ 実機側のまとめ（2026-09-17 昼）: MIT で位置指令が通り（ID34）、原点手順（起動 → フィードバック待ち → 決まった姿勢で `o 0`）・指令途絶でトルクを出し続ける・電流は符号が信用できない、が確定。デプロイまでの実機側の最低限を M1〜M9 に整理（夜に M2・M3 済み、M6 は符号まで済み）。** → `next_chat_briefing_motor.md`、`chats/2026-09-17_motor-summary-handover.md`
- **★★★★★★★★★★ 実験04 停止点2（2026-09-17 朝）: H_nolinvel は不採用（S1 v_x 0.315、横移動で静止率 0.78、stiffness ×0.7 で転倒 100%）→ 速度観測は T265 から作る（途絶検出と停止が必須、取り付け位置補正も必要）。H_eff13p5 は G_real_peak と同等でトルクが低い。デプロイ候補は G_real_peak / H_eff13p5 / H_gainDR の3本から停止点4 で選ぶ。旋回（その場）はできないが後回し（ユーザー決定）、横移動と旋回はコントローラーの割り当てで分ける案。** → `chats/2026-09-17_exp04-stop1-review.md` の追記、WRS へは `wrs_experiment04_followup_instruction.md` 末尾の P6
- **★★★★★★★★★★ 実験04 停止点3（2026-09-17 朝）: 条件9（damping ×2）は数値不安定ではない（dt 半分でも転倒 98.4%）→ 実機の Kd 換算は必須の関門。G_real_peak は base_lin_vel を 0 にすると壊滅（バイアス・雑音・100 ms ホールドには頑健）→ H_nolinvel の価値が上がった。足裏平面は world で -30°、COM は支持範囲より前。H_gainDR（damping ×0.5〜2.0）を 07:55 起動。次は P6（足裏の出どころ、速度途絶の許容時間）と停止点4（`wrs_experiment04_followup_instruction.md` 末尾）。H_nolinvel の判定は停止点2 の中身待ち。** → `chats/2026-09-17_exp04-stop1-review.md` の追記
- **★★★★★★★ 実験04 停止点1（2026-09-17 00:09）: G_real_peak は effort 13.5 / 12（Kt 0.7 倍想定）・遅延 4 / 8 step・friction ×2・質量 +1 kg・地面摩擦 0.5・ノイズ・吊り下ろしで両 iter 合格。不合格は effort 9.0（2400）、stiffness ×0.7（2400）、damping ×0.5（両 iter、小旋回）、damping ×2.0（両 iter、2999 は転倒 100%）。ONNX は誤差 1.1e-5 で合格、正規化なし。保険の学習 H_nolinvel・H_eff13p5 を 00:08 起動。**
  **Cowork の推奨（ユーザー判断待ち）: デプロイ候補は G_real_peak（暫定 2999）。H_nolinvel が基準と頑健性で新しい不合格を出さなければ、T265 の速度を使わない方を第一候補。**
  **実機側の最優先は Kd の分離（c_d が 0.55 / 0.71 / 1.19 のどれかで実効 damping が ×1.0〜×2.2 に振れ、×2 は不合格帯）。Kt は優先度を下げる。**（→ 09-17 夜: Kd は決着、Kt は優先度が戻った） 条件9 はシムの数値不安定の疑いもある。
  **次は WRS に `wrs_experiment04_followup_instruction.md`（停止点2 は予定どおり ＋ P5: 表の欠け、dt 半分での条件9、速度への依存、golden npz とデプロイ用アクチュエータ表、H_gainDR、形状の出し直し）。** 左右 4 cm のずれは base 原点の横ずれ 2 cm で全部説明できるはず（WRS の「半分」は訂正）。 → `chats/2026-09-17_exp04-stop1-review.md`
- **★★★★★★★ 実験03 完了（2026-09-16 21:12）: 実機準拠アクチュエータの G_real_peak（AK10 53 / AK80 18）・G_real_rated（18 / 9）とも 3000 iter で歩く。全チェックポイントで転倒・立ち往生 0%、小旋回（S7/S8）合格。G_real_rated は足首 FFE が S1 で 20〜29% 飽和。Cowork はデプロイ候補を G_real_peak（2400 / 2999）と判断（ユーザー了承待ち）。** → `training_runs.md`、次の Cowork チャットは **`next_chat_briefing.md`（深夜版）**
  **次は実験04（`wrs_experiment04_instruction.md`）: 候補の頑健性スイープ（AK80 effort 13.5/12/9、ゲイン ×0.7/1.3、遅延、摩擦、吊り下ろし）、ONNX と torch の一致確認、足裏の傾き・左右 4 cm のずれ、保険の学習 H_nolinvel（観測から base_lin_vel を外す）＋1本。**
  h5py の DLL 競合は conda activate してから起動すれば出ない（起動スクリプトに組み込み済み）。未 push のコミット `664105a` `0a434a7` `5f3a487`（実験04 で `d4149ec` が追加）。
- 実験03 途中（2026-09-16 夜）: P1-1〜P1-3 完了（ONNX 入力 42・出力 10、50 Hz、観測に base_lin_vel あり）。B@2999 は S7/S8 で小旋回合格（その場旋回 S6 だけ不可）。
- **★★★★★ デプロイの合格基準が決まった（2026-09-16 夕、ユーザー決定）。** トルク: **S1 で RMS ≤ 定格（AK10 18 / AK80 9）、最大 ≤ ピーク（AK10 53 / AK80 18）**（シムでは最大は effort_limit で自動的に守られるので、飽和率と切る前トルクで見る）。旋回: **大旋回は不要、小旋回で可。ただし向き保持に使える小さな yaw 追従は必須**（S7/S8 = 前進 0.5 ＋ yaw ±0.3 で判定）。（「B / E は小旋回も満たしていない」は S6 だけを見た誤りで、B は S7/S8 で合格だった） → `next_chat_briefing.md` §1a
  **実験03 の指示書を停止点2の結果で改訂済み**（S7〜S9、computed torque・飽和率、左右対称性、旋回が出ない件の材料、並走の実測、占有見込み約5時間）。
  **並走は 4096 env × 2本（最大3本）。1024 env × 6 本は VRAM に入らず、GPU 計算も飽和済み**（`next_chat_briefing.md` §2a）。
- **実験02 停止点2（2026-09-16 16時）: E_yawcmd@1999 は旋回出ず（S6 +0.063）。F_BtoRough は terrain_levels 0.98 → 4.69、平地歩行保持、ただし S1 yaw rate +0.324 で円を描く。stiffness 4倍でも前に倒れる（沈み仮説は外れ）。** WRS機の `tools\\\\logs\\\\REPORT_exp02_stop2.md`
- **★★★★ ゴール変更: まず平地で実機デプロイ（坂は時間が余ったら。2026-09-16 15時、ユーザー決定）。実機は組み上がっている（ユーザー申告）。**
  **旧アクチュエータ設定（AK80-9 に effort 20〜30 N·m、HFE が AK10 と同グループ）で学習した方策は使わず、実機準拠で一から学習し直す → 実験03（`wrs_experiment03_instruction.md`、WRS の新チャット）:** 関節ごと5グループ、effort AK10 53 / AK80 18（G_real_peak）と定格 18 / 9（G_real_rated）を並走、friction・armature は実測/暫定値。同時に ONNX 書き出し・観測契約 `obs_contract.md`・B のトルク実態・立てない件の診断。
  デプロイ残作業の表は `next_chat_briefing.md` §3（実機側は `next_chat_briefing_motor.md` §2 が新しい）。
- **★★★ 立ち往生の分かれ目は地形だった（2026-09-16 13時、実験02 停止点1）。** 詳細 → `crab_standstill_countermeasures.md` §4〜§5、ラン表 → `training_runs.md`
  **rough の2本（A、C_noflat）は 3000 iter 立ち往生、平地の2本は歩く（B は iter 1000、08-21 報酬のままの C_flatonly も iter 2400 で歩き出す）。** 報酬/std の違いは歩き出す時期とカニ歩き基準の合否だけ（seed 1本）。実験01 時点の「組み合わせが要る」は撤回。
  **歩いている方策では横流れは小さい。旋回しない（rel_heading_envs=1.0 で旋回指令が出ていなかったという読みは、実験03 P1-5 で指令分布を実測して確かめる）。action 0 で前に倒れる（剛性不足の仮説は P3a で外れた）。**
  **訂正: `error_vel_xy`/`error_vel_yaw` はエピソード長に比例（正規化値＝生値×500/episode 長）。手順書 A5・operator 指示書 §6 の目安は未修正。`max_init_terrain_level` を上げると地形は難しくなる。**
  実験02 P3（`wrs_experiment02_p3_instruction.md`）は commit `6c80638` 済み・実行済み。
- **★ 柱Aの実行環境は WRS共用PC（RTX 3090 Ti / Windows 11）に移った。環境構築は 2026-09-15 に完了。**
  `D:\\\\Tominaga\\\\` に Isaac Sim 5.1 / Isaac Lab 2.3.2 / 自作コードを配置し、同梱タスクで学習が回ることを確認済み。→ `wrs_pc_environment.md`
  **`project_handbook.md` / `handover.md` / `next_chat_briefing.md` は 2026-09-16 に WRS機・新しい機体の前提へ書き換え済み。** `wrs_pc_operator_instruction.md` は古い（`D:\\\\haruto\\\\` 前提）。
- **★★ 再エクスポート完了（2026-09-16 未明、WRS機）。新 USD で 64 env / 20 iter のテスト起動が完走。** 木構造 5/5・根＝胴体 2.918 kg・総質量 10.1058 kg。
  **途中で URDF の座標と関節の符号の問題が2つ見つかり、後処理で直した → 約束事は `robot_model_conventions.md`（正本）:**
  ① base の +X が機体の横だった（**旧 URDF も同じ＝過去の学習は「前進指令＝横方向」だった可能性が高い。カニ歩きの有力な説明**）→ base を +90° 回転。
  ② 関節軸の向きが左右で揃っておらず、脚の中で膝だけ逆 → 5関節の軸を反転し「同じ角度＝左右鏡写し」に。初期姿勢の HAA を 0、スポーン高さ 0.3758 m に変更（`skyentific_poclegs.py`）。
  **commit / push 済み（`6ede75b`、GitHub 上で確認）。08-21 版コードの棚卸しも完了（`wrs_training_strategy.md` §1）。**
- **★ 再エクスポート後の学習方針を作成（2026-09-15）→ `wrs_training_strategy.md`。** Kp/Kd は速さのつまみではない／「速すぎる」は物理・指令・罰で抑える／heading 固定はやめる提案／08-21 版コードに9月の変更をどれだけ戻すかの仕分け
- **Git のブランチは `main`。** GitHub に `master` は存在しなかった（手順書の「正本は master」は古い）。
- **★ GitHub の `main` は 2026-08-21 で止まっていた＝Alienware での 08-21 以降の `my_robot_code/` の変更は push されていなかった（2026-09-15 判明）。**
  WRS機のコードは 08-21 版（`fix/falling-down-end-condition` をマージした直後）。**手順書・handover にある 09月の報酬・リミット等の変更は WRS機のコードに入っていない前提で扱う。** 未 push 分は Alienware の SSD にしか無い → `wrs_pc_environment.md` §1a
- **Alienware（Ubuntu機）は 2026-09-13 から故障中。** 起動しても数分〜十数分で電源が落ちる**間欠故障**。
  **「熱依存」という読みは 2026-09-14 に棄却された**（持続時間が休止時間と逆転）。→ `alienware_repair_instruction.md`
  **費用ゼロの手が4つ未実施**（保証確認・挿し直し4点・ホコリ除去・モニターのポート変更）
- **USD・STL・チェックポイントは Alienware の中にしかない。** ただし再エクスポートすればどれも作り直しになるので、**救出の優先度は下がった。** **ただし `my_robot_code/` の未 push 分は作り直せないので救出対象**
- **柱B（Windows ノートPC、`C:\\\\Users\\\\harut\\\\Connect2USB2CAN`）: 現行は `motor_console_ver8.py`（`py -3.13` で起動）。MIT（モード8）で位置指令が通る。**
  MIT 位置＝サーボ角、`o 0` で両方0、AK80-9 は電源再投入で角度が 80 deg の窓に折り返す（AK10-9 は確認中）、**Kp・Kd 換算は機種別（AK80-9 0.523 / AK10-9 1.258・1.216）**、指令途絶でトルクを出し続ける、電流は符号が信用できない、遅れ最小 8 ms、50 Hz の揺れ最大 23 ms。T265 は `.venv310\\Scripts\\python t265\\t265_check.py`。
  → 実測の正本 `motor_can_findings.md`、索引 `motor_bench_checklist.md`、T265 `realsense_t265.md`、公式資料 `motor_mit_official_notes.md`、**次の一手とコマンド解説 `next_chat_briefing_motor.md`**
- **実機が要らないデプロイ準備（制御ループ ver9 の乾式テスト）が溜まっている。** WRS から H_eff13p5 の ONNX・golden npz・obs_contract・アクチュエータ設定を受け取ってから。

---

## 個別資料（そのテーマを触るときだけ読む）

### 今アクティブな指示書

| ファイル | 内容 | いつ読む |
| deployment_roadmap.md | **平地デプロイまでの全体工程。学習パッケージ、コントローラー、実機設定、ver9乾式、段階的な実機試験の依存関係と完了条件** | 全体の残タスクを確認するとき |
| `deployment_01_h_export_instruction.md` 〜 `deployment_06_h_integration_instruction.md` | Hを採用済みとした最短統合の分割指示書。D1（成果物抽出）→D2（ver9骨組み）とD3（T265）・D4（関節対応）→D6（H統合）。D5はプロコンを使う場合だけ行う。 | 分割したデプロイ用チャットを始めるとき |
| `wrs_deployment_export_handoff.md` | **WRS cloneにD1文書が無い前提の自己完結した成果物抽出プロンプト、既知のH run、Avast HTTPS障害の復旧順、次の受け渡し** | WRSからHのデプロイ成果物を取り出すとき |
|---|---|---|
| `wrs_overnight_20260918_instruction.md` | WRS機 Claude Code に貼った夜間自走の指示。N_w1_seed2 / N_w1p5 と仮デプロイパッケージは完了したが、通知待機の失敗でP_gainDR_narrowと2巡目は未完了 | 経緯を確認するとき |
| **`controller_prep_briefing.md`** | **コントローラー準備チャットへの指示書（2026-09-18）。** 方策の指令の前提、Switch 2 Pro コントローラーの PC 対応（要実測）、認識確認 → pad_probe → 割り当て → teleop（デッドマン・非常停止・途絶・変化の制限）→ 乾式テスト → ver9 への渡し方 | **コントローラーのチャットの最初** |
| `wrs_experiment09_instruction.md` | WRS機に貼った実験09 の指示（2026-09-17 深夜、停止点8b 後。**N0-1・N0-2 完了、N0-3 途中で夜間の指示に引き継ぎ**）。 講評（効いたのは weight 1.0、@4000 の合格は左右が入れ替わる途中の1点）、事前の判定規則（連続 300 iter の合格範囲）、N0（密な評価 256 env × 2回・関節トルク RMS の実装・L_angstd_w1@4000 の頑健性スイープ・実験08 の記録）、N 本番2本（N_w1_seed2 / N_w1p5）、停止点9a・9b | 経緯を確認するとき |
| `wrs_experiment08_instruction.md` | WRS機に貼った実験08 の指示（2026-09-17 深夜）。停止点7 の講評、L0 報酬の全項と歩くと増える罰、track_ang_vel_z_exp の std 0.35 / weight 1.0 の2本、停止点8a・8b。**実行済み（L_angstd_w1@4000 だけ合格）** | 経緯を確認するとき |
| **`wrs_new_chat_start.md`** | **WRS機の Claude Code の新チャットに貼る文（2026-09-17 夜）。** リポジトリ側の README / handbook / exp06 の読み順、掟、トークン節約の作法、実験07（学習なし: ハングの原因、その場旋回の診断、足が滑り出す yaw トルク、足裏）、停止点7。**実行済み** | WRS の新チャットを始めるとき |
| **`wrs_experiment06_instruction.md`** | **WRS機に貼る実験06 の指示（2026-09-17 午後）。** 停止点5a の講評（報酬表の出し直し）、H0 評価のハングの切り分け、J0 足上げ報酬の yaw_gate と指令のその場旋回・並進だけモード、J 2本並走（J_turn_resume / J_turn_scratch）、その場旋回の合格ライン、停止点6a・6b・6c。**実行済み（失敗）** | 経緯を確認するとき |
| **`wrs_experiment05_instruction.md`** | **WRS機に貼る実験05 の指示（2026-09-17 午後）。** 停止点4 の講評とユーザー決定（G_real_peak と H_eff13p5 の両方を持っていく）、T0 その場旋回ができない原因の調査（報酬の実効値・足上げ報酬の指令判定・指令の組み合わせ・S6 の足と HR と報酬の内訳）、D デプロイ準備（1b93c48 の diff、H_gainDR の学習ログ、H_eff13p5 の golden npz と obs_contract、P6-2 の H_eff13p5 版、P6-1 のやり直し）、停止点5a・5b。**停止点5a まで受け取り済み** | 経緯を確認するとき |
| **`next_chat_briefing_motor.md`** | **実機側（モーター・T265・制御ループ）の次チャットへの指示書（2026-09-17 夜版）。** 最初のタスク（`session_214916.txt` を読む）、状況の整理（やってきたこと・できるようになったこと・機種別ゲイン換算・T265 の変換）、M1〜M9 の状態、次の一手、**ver8 と t265_check のコマンド解説**、ファイルの場所、やり残し、ユーザーとの対話の注意 | **実機側の新しいチャットの最初** |
| `wrs_experiment04_followup_instruction.md` | 実験04 の追加指示（2026-09-17 朝〜11 時）。停止点1 の講評と訂正、P5、停止点3、末尾に P6・停止点4 と H_gainDR の noise_std_type の回答。**停止点4 まで実行済み** | 経緯を確認するとき |
| `wrs_experiment04_instruction.md` | 実験04 の指示書（2026-09-16 深夜。停止点1 まで実行済み）。G_real_peak の頑健性スイープ、ONNX 検証、形状の診断、保険の学習 H_nolinvel ＋1本 | 評価条件の番号を確認するとき |
| `wrs_experiment03_instruction.md` | 実験03の指示書（**実行済み 2026-09-16**。実機準拠アクチュエータ、合格基準、S7〜S9、末尾に h5py の切り分け指示） | 経緯・評価条件を確認するとき |
| **`crab_standstill_countermeasures.md`** | **カニ歩き・立ち往生の対策案の全リスト（状態付き）、立ち止まりの給料の計算、実験01の設計・判定基準・判定後の分岐** | 実験の設計・結果を確認するとき |
| `wrs_experiment01_instruction.md` | WRS機に貼った実験01の指示書（**実行済み 2026-09-16**）。評価プロトコルと判定基準の原本 | 評価条件を確認するとき |
| `wrs_experiment02_p3_instruction.md` | 実験02 P3 改訂版（commit、stiffness 診断、E_yawcmd、F_BtoRough）。**実行済み** | 経緯を確認するとき |
| `wrs_experiment02_instruction.md` | 実験02の指示書（P0〜停止点1 は実行済み。**P3 は改訂版で差し替え**） | 経緯を確認するとき |
| **`training_runs.md`** | **学習ランの記録表（run フォルダ・変更・判定・基準値）。停止点4・実験06〜08 の結果は未記入** | **ランが増えるたび** |
| **`wrs_pc_environment.md`** | **WRS機に構築済みの環境の記録（正本）。** 版・パス・ハードリンク対応表・**GitHub が 08-21 で止まっている件（§1a）**・この機体特有の落とし穴（Avast 証明書、tensordict、ハードリンクが git で切れる） | **WRS機で柱Aを触るとき毎回** |
| **`next_chat_briefing.md`** | **学習側の次の Cowork チャットへの指示書（2026-09-18 朝版）。夜間の自走の中身、朝に決める規則（仮デプロイの方策）、§3 に push の手順** | **学習側の新しいチャットの最初** |
| **`wrs_training_history.md`** | **WRS機での学習の経緯を用語の説明つきで時系列にまとめた読み物（09-15〜09-17 昼）** | 途中から入るとき・用語を確認するとき |
| **`wrs_training_operator_instruction.md`** | **WRS機の Claude Code の新チャットに最初に貼る指示書。** 共用PCの掟・環境・学習コマンド・報告の書式・作法 | **WRS側で新しいチャットを始めるとき** |
| **`robot_model_conventions.md`** | **機体モデルの約束事（正本）。** base 座標（+X 前）、関節軸と正の角度の意味、ゼロ姿勢・初期姿勢・スポーン高さ、URDF limit が学習に効くか | **報酬・観測・実機の関節↔モーター対応を触るとき毎回** |
| `wrs_urdf_reexport_instruction.md` | 再エクスポートの手順書（WRS機・Windows 版）。**2026-09-16 実行済み。** 実際には後処理（base 回転・軸反転）が追加で必要だった → `robot_model_conventions.md` | URDF を作り直すとき |
| **`wrs_training_strategy.md`** | **再エクスポート後の学習方針。** ゲインの考え方・「速すぎる」対策の順番・heading 方針・9月変更の仕分け・坂への段取り。**§4 の指令を絞る案は立ち止まりの給料を上げる（`crab_standstill_countermeasures.md` §1）** | 段階1以降を決めるとき |
| `urdf_reexport_instruction.md` | 再エクスポート手順の**旧版（Alienware / Ubuntu 前提）**。検算項目の考え方は同じ | 読まなくてよい |
| `wrs_pc_host_instruction.md` | **WRS機の Claude Code に渡した環境構築の指示書**（2026-09-15 実行済み） | 環境を作り直すとき |
| `wrs_pc_operator_instruction.md` | **旧版（2026-09-14）。** `D:\\\\haruto\\\\` 前提で古い | 読まなくてよい |
| `alienware_repair_instruction.md` | **Alienware 故障の切り分け手順**（間欠故障。費用ゼロの手が4つ未実施） | 本体の前に行けるとき |
| `mit_implementation_briefing.md` | **古い（ver6 時点）。** 「位置指令未達・実効Kd 0.48」の前提。**`next_chat_briefing_motor.md` §4 と `motor_can_findings.md` が後継** | 読まなくてよい |
| **`motor_mit_official_notes.md`** | **公式資料（v3.0.0 / V1.0.15 / FAQ / 製品ページ）の要点、仮説 H1〜H6 と検証コマンドの対応、ver6 の隠れ誤差（速度0欄の半LSB）、シム検算** | 実機のMITを触るとき |

### 調査記録・リファレンス

| ファイル | 内容 | いつ読む |
|---|---|---|
| `motor_can_findings.md` | **実機CANの実測結果（正本、2026-09-17 夜更新）。** 機種別の r_v・c_d・c_p・原点・jit、モード8・ペイロード順・レンジ（AK80 ±65 / AK10 ±28 確定）・量子化・電源再投入・指令途絶・電流の符号 | 実機の通信仕様や数値を確認するとき |
| `motor_bench_checklist.md` | 実機の未確認項目の索引と次にやる順（2026-09-17 夜更新） | 次に何を実測するか決めるとき |
| `actuator_params.md` | **モーター諸元と Isaac Lab 設定値の根拠。** トルク実測（§3b）、シムのゲイン↔実機の対応（§0c、**Kd 0.48・Kp 0.538 は古い → 機種別換算は `motor_can_findings.md`**）、**Kt の未決（§2b）** | 機体のアクチュエータ定義を触るとき |
| `urdf_asymmetry_finding.md` | 木構造の非対称の真因調査（2026-09-14 決着）と、再利用できる診断手順 | CAD/URDF を触るとき |
| `onshape_cad_fix_instruction.md` | CAD 修正の**完了記録**。今後 Onshape を触るときの注意もここ | Onshape を触るとき |
| `realsense_t265.md` | **T265 の環境（Windows・Python 3.10）、確認スクリプト、確定した座標変換と符号（2026-09-17）、起動の癖、残作業** | 実機構成・観測・制御ループを触るとき |
| `project_structure_map.md` | ディレクトリ構成の詳細図 | 迷子になったとき |
| `rough_env_cfg_walkthrough.md` | `rough_env_cfg.py` の解説 | env_cfg の中身を読み解くとき |
| `isaaclab_edit_guide.md` | Isaac Lab 側の編集ガイド | Isaac Lab 本体に手を入れる前 |
| `template_code_reference.md` | 見本コード（Skyentific PocLegs）のリファレンス | 見本の実装を確認するとき |

### 廃止

| ファイル | 状態 |
|---|---|
| `urdf_tree_fix_instruction.md` | **廃止（2026-09-14）。** URDF の親付け替えパッチは不要になった。FK 検証などの技術メモとしてのみ残している |

**注意1:** `isaaclab_edit_guide.md` と `rough_env_cfg_walkthrough.md` には、
**`bad_orientation` の実装状況と報酬 weight について古い誤記が残っている可能性がある。**
さらに **`bad_orientation` の limit_angle が文書間で食い違っている**（手順書 1.3 rad / 旧 handover 0.8 rad）。
**WRS機で実物を読めるようになったので、grep して統一すること。** **ただし WRS機のコードは 08-21 版なので、grep 結果は「08-21 時点の値」であり、Alienware 上の最終値とは限らない。**

**注意2（2026-09-14 に発見、2026-09-17 夜更新）:** **`project_handbook.md` の A7 は「実機で動いているのはサーボモード。MIT は実装済みだが未検証」のまま古い。`actuator_params.md` §0c も「Kd 0.48」のまま古い。** 実測の正本は `motor_can_findings.md`（MIT で位置指令まで通った、機種別の Kp・Kd 換算）。**手順書 A7 と §0c を書き換えること。**

---

## `chats/` ── 個々のチャットの記録

> 🚨 **毎チャット必ず1ファイル追加（冒頭の絶対ルール）。省略・後回し禁止。**

`project_handbook.md` と `handover.md` は「今の正しい状態」だけを書く**体系的な記録**。それとは別に、
**「あのときのチャットで何をどう決めたか」という個々の記録**を `chats/` 以下に残していく。

### 目的
- 手順書・引き継ぎ書は書き換え式なので、**過去の試行錯誤や当時のやり取りは消えていく。**
- 「あの時なぜこの数値にしたんだっけ」を後から追えるように、チャット単位の記録を積み上げる。

### ファイルの置き方
- パス: `claude/chats/YYYY-MM-DD_短い件名.md`
- **1チャット＝最低1ファイル。例外なし。** 1チャットで複数トピックを扱ったら分けてよい。長く続く作業は日付を分けてよい。
- **これは追記式でよい。** 書き換え原則はここには適用しない。古いチャットのファイルは基本触らない。
- **作ったら下の索引に1行追加する。**

### 各ファイルに書くこと（テンプレート）
```markdown
# YYYY-MM-DD 件名

## やったこと
（このチャットで何を進めたか、時系列で）

## 決めたこと・分かったこと
（結論・数値・判断の根拠）

## 手を動かした場所
（触ったファイル・実行したコマンドの要約。フルログは不要、要点だけ）

## 積み残し・次にやること
（このチャットの続きとして誰かがやるべきこと）
```

### 体系的記録との使い分け
- **`project_handbook.md` / `handover.md` に書く:** 今後ずっと有効な事実・手順・現在地。
- **`chats/` に書く:** その結論に至った経緯・具体的なやり取り・当時の判断理由。
- **体系的記録を更新しただけでは不十分。** 更新したチャットでも、`chats/` への記録は別途必ず作る。

### 索引（新しい順）
- chats/2026-09-19_h-deployment-package-received.md ── H_eff13p5@2999のデプロイ成果物をノートPCでSHA256照合し、全6必須ファイルの一致とONNX 42入力・10出力／Torch照合PASSを確認。次はCANなしのM4ゲイン表とM7乾式実装。
- chats/2026-09-19_wrs-export-handoff-and-avast.md ── WRS cloneにD1文書が無いことを確認し、H成果物の自己完結抽出プロンプトを引き継ぎ書に作成。Codex接続を阻害するAvast HTTPSスキャンはRepair→再起動→hardware network accelerationの順で復旧する方針。
- chats/2026-09-19_deployment-05-priority-review.md ── D5の着手条件を確認。速度指令の符号・範囲はD1の`obs_contract.md`なしに推測できないため、既存Hのデプロイ成果物エクスポートを先行する。実機・CAN・コントローラーの状態変更はなし。
- chats/2026-09-19_motor-console-ver8-2-dual-test.md ── ID0x22（AK80-9）とID0x12（AK10-9）の二機同時MIT試験用に、ver8派生の `motor_console_ver8_2.py` を追加。二機ゼロ保持100周期、同時実動、個別の電流・速度・移動量中止と両軸零MIT指令を実機で確認。10台＋推論のD3は未。
- chats/2026-09-19_controller-required-hardware-test.md ── プロコン系で今日必須の実機試験を、Jetson＋有線Switch 2 Proだけの50 Hz乾式入力・切断試験に限定した。`obs_contract.md` 未受領は base 座標へのvx/vy符号確定だけを阻害し、入力試験自体は妨げないと整理した。
- chats/2026-09-19_isaaclab-debugging-10-close-next11.md ── Isaac Lab debugging #10を閉じ、WRS側Codexの利用開始、P2/P3のrough地形逸脱、既存cloneの同期方針、平地F1/T1並列学習を#11の指示書に確定した。
- chats/2026-09-19_isaaclab-debugging-10-p2-p3-training-review.md ── Isaac Lab debugging #10。P2（狭い stiffness+damping DR、seed 2）とP3（stiffness-only、seed 1）はともに11998まで正常完走。P3の最終報酬・episode長は高いが、カリキュラムとseedが異なるため学習ログだけでは優劣・頑健性を判定しない。通常再生後、既定の平地・頑健性評価でH_eff13p5@2999と比較する。
- chats/2026-09-18_p1-4498-next-run-decision.md ── P_gainDR_narrow@4498 の正常な学習統計を確認。3時間枠は評価を先行し、その結果で P2_seed2 / P2_stiffonly / 学習停止を固定規則により選ぶ。
- chats/2026-09-18_deployment-roadmap-and-fixture-status.md ── 学習から平地デプロイまでの依存関係を deployment_roadmap.md に集約し、Kt測定用の固定治具が無いことを実機文書へ反映。
- chats/2026-09-18_controller-pad-probe-implementation.md ── Connect2USB2CAN/controller/pad_probe.py を追加。Switch 2 Pro を50 Hzで乾式読取し、CSV・タイムアウト零指令を実装。CAN/ONNX/モーターには未接続。
- `controller_next_chat_briefing.md` ── **Jetson上のSwitch 2 Proの次チャット用。実測済みの入力対応、左スティックだけの50 Hz乾式 `pad_probe.py`、切断テスト、禁止事項をまとめた。**
- `chats/2026-09-18_jetson-switch2-controller-checklist.md` ── **Jetson に有線接続した Switch 2 Pro の乾式テスト手順。認識・生値・50 Hz・切断・非常停止を、モーター/CAN/方策へ接続せずに確認する。**
- `controller_gpu_today_instruction.md` ── **2026-09-18 の実行順をまとめた指示書。Switch 2 Pro の有線認識・乾式入力確認、WRS GPU の夜間結果判定、deploy package の検品とノートPCへの受け渡し。モーターは動かさない。**
- `chats/2026-09-18_motor-debugging-6.md` ── **motor debugging #6。ID18（AK10-9）の `session_214916.txt` を判定: 動かした後の電源再投入で座標変化はあるが、操作時刻と物理角がログになく、原点窓の幅・再現則は未判定。全10台のID・機種・関節・正方向はユーザー設定済みのためM1の再実験は省略。Ktは治具待ちで、コントローラーとGPU成果物へ切り替え。Connect2USB2CAN は独立リポジトリとして維持。**
- `chats/2026-09-18_p1-foreground-handoff.md` ── **実験09朝の確定結果、P_gainDR_narrow再開、今後はバックグラウンド学習を禁止してフォアグラウンド専用ランチャーへ切り替えた記録。**
- `chats/2026-09-18_overnight-and-controller.md` ── **実験09 の中間（合格は L_angstd_w1 の 4000・4200 だけで幅 200 iter、@4000 は stiffness ×0.7 で全シナリオ転倒＝旋回は候補にならず）を受けて、WRS の新チャット（Opus）に夜間の自走の指示: 仮デプロイ用パッケージ（H_eff13p5@2999 第一・G_real_peak@2999 予備・L_angstd_w1@4000 実験用）、学習3本（N_w1_seed2 / N_w1p5 / まっすぐの改良 P_gainDR_narrow）、事前の判断規則の2巡目、許した手直し5種類、09:45 に再生コマンド。コントローラー（Switch 2 Pro）準備チャットの指示書 `controller_prep_briefing.md`**
- `chats/2026-09-17_exp08-stop8b-review.md` ── **実験08 停止点8b の講評。L_angstd（std 0.35・weight 0.5）は全不合格、L_angstd_w1（weight 1.0）は @4000 だけ合格（S6 +0.268 / S9 −0.353）で @3600・@4498 は左右の釣り合いが崩れて不合格 → 効いたのは weight 1.0、1点の合格ではデプロイ候補にしない。直進の候補は H_eff13p5@2999 のまま。実験09 の指示書（密な評価 256 env × 2回、関節トルク RMS の実装、@4000 の頑健性スイープ、N_w1_seed2 / N_w1p5、事前の判定規則「連続 300 iter の合格範囲」）。push コマンドを提示。`next_chat_briefing.md` を深夜版に**
- `chats/2026-09-17_motor-kd-separation-t265.md` ── **実機側（夜）。脚を外した ID34（AK80-9＝LR_FFE 右足首）・ID18（AK10-9＝LR_KFE 右膝）で `vscale`・`morg`・`kpscale` → Kd 分離が決着（c_p ≈ c_d: 0.523/0.523、1.258/1.216、機種別に割れば比が保てる）、速度レンジ AK80 ±65・AK10 ±28 と極対数 21 を確定、ゲインは機種によらず電流で出ていてトルク指令の目盛りが 2.3 倍違う → Kt の優先度が上がった。jit 合格（最大 23 ms）。T265 を Windows で動かす（Python 3.10 `.venv310`・pyrealsense2 2.53.1、起動の再試行と子プロセス再起動。Cowork の変更で一度悪化）、base 座標の符号と velocity の world 表現を確定。AK10-9 は動かさない電源再投入で角度不変、動かしてからの入れ直し（`session_214916.txt`）は次チャットで読む。`python` が 3.10 を指すようになり ver8 は `py -3.13`。「引き継ぐと言ったら即引き継ぎ書と文書更新」を絶対ルール2 に。`next_chat_briefing_motor.md`（夜版、コマンド解説つき）・`motor_can_findings.md`・`motor_bench_checklist.md`・`realsense_t265.md` を書き換え**
