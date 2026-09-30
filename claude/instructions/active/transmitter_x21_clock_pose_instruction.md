# 送信器: X21/X22 系の方策を載せる準備（時計の観測 44 次元と、差し替えられる既定姿勢）

作成 2026-09-30 14:50。**送信器用の新しいチャットに「チャットに渡すもの」のブロックだけを貼る。** 学習（WRS 実験22）と並行。
終わったらこのファイルを `../inactive/` へ移す。

## チャットに渡すもの

```
# 依頼: 送信器に、X21/X22 系の方策（観測 44 次元＝H の 42 ＋ 歩行の時計）と、方策ごとの既定姿勢を載せる。モーターは動かさない

## 前提
- 新しいチャット。トークン節約のため、読むのは下に書いたファイルだけ。AGENTS.md の「開始手順」の4文書は読まなくてよい
  （このプロンプトに必要な事実は全部書いた）。ただし commit・push の決まり（git add は列挙、`.bak_YYYYMMDD_内容`、
  CSV・重み・ONNX・logs を add しない）は守る。
- **実機のモーターは一切動かさない。** CAN を送らない乾式（ONNX を回す dry-run・テスト）だけ。
- 既定の挙動は変えない。新しいオプションを付けたときだけ新しい動きになる（今の H のパッケージと起動行はそのまま動くこと）。
- 数値・符号は推測しない。下の値と、C:\Users\harut\wanpbl2026_slope_climing_robot\my_robot_code\stand_env_cfg.py
  （STAND_JOINT_POS、X20 節の gait_phase_obs・GAIT_PERIOD_S、X21 節の H_STAND_JOINT_POS）で確かめる。

## 対象
- リポジトリ C:\Users\harut\Connect2USB2CAN、ブランチ feat/mit-mode（main に push しない）。
- まず読む: policy_integration.py（DEFAULT_JOINT_POS・build_observation・HPolicy・target_from_action）、ver9_integration.py、
  ver9_d8_sender.py（ノートPC版の送信器。立ち姿勢の ramp・保持・中止・--relaxed-start など）、それぞれの test_*.py、
  パッケージの検証（dump_contract.py・verify_onnx.py。場所は探す）。Jetson 版（ver9_jetson_deploy.py）は今回触らない。
- 最新 build は D10_13M_RELAXEDSTART_20260930。新しい build 名は D10_14_GAITCLOCK_20260930。

## シム側の決まり（X21a・X21b と、その再開の X22a・X22b。学習中）
1. 観測は 44 次元 = H と同じ 42 次元（順番も同じ）の**最後に** [sin(φ), cos(φ)]。φ = 2π·t / 0.7、
   t = k × 0.02 s、k は**方策の段階に入ってからの tick 数**（最初の方策の tick が k = 0 → sin 0・cos 1）。
   シムではエピソードの開始（立った状態・速度 0）で k = 0 になり、指令が 0 でも時計は進み続ける。
   → 送信器では、立ち姿勢の ramp・保持・直立ゲートのあと、方策を回し始めた tick を k = 0 にする。
   `--command-delay-seconds`（指令 0 の待ち）の間も時計は進める。tick が遅れたときは実時間でなく tick 数で数える
   （シムは 1 tick = 0.02 s 固定）。
2. 関節の観測 joint_pos_rel = 関節角 − 既定姿勢、行動の目標 = 既定姿勢 + 0.5 × 行動、は H と同じ。**既定姿勢が方策で違う**:
   - X21a / X22a（まっすぐ寄り、本命）[deg]: LL_HFE −2.6、LL_KFE −4.3、LL_FFE +6.9、LR_HFE −6.4、LR_KFE +0.8、LR_FFE +5.6、
     HR・HAA は 0。（stand_env_cfg.py の STAND_JOINT_POS。rad にすると D(値)）
   - X21b / X22b（H の姿勢）: HFE −0.1745、KFE +0.3491、FFE −0.1745 rad（左右同じ）、HR・HAA 0。今の DEFAULT_JOINT_POS と同じはず（確かめる）。
   どちらもシムの関節角（送信器の `--zero-offset cad_fk` で読み替えたあとの角度）で書いた値。
3. 立ち姿勢の ramp・保持の目標は、方策の既定姿勢にする（今は H の姿勢に固定のはず）。
4. シムは 4番目（HAA）を −16°まで使う。実機は −8.5〜−11°で足が触れるので、`--safe-clamp`（4番目を −8°で止める）が
   新しい方策でも効くか確かめる。

## やること
1. 「方策の仕様」を1か所にまとめる（例: パッケージのメタ情報か、`--policy-spec h|x21a|x21b`）: 観測の次元（42/44）、
   時計の周期（なし/0.7 s）、既定姿勢。既定は h（今と同じ）。ONNX の入力次元とこの仕様が食い違ったら起動時に止める。
2. build_observation に時計を足す（44 のときだけ）。観測の CSV（`<CSV名>_obs.csv`）の列も 44 まで、時計の k と φ も記録。
3. 立ち姿勢の ramp・保持・中止の基準（「立ち姿勢から 45°」など）が、選んだ既定姿勢を使うようにする。
   `--relaxed-start`・`--origin-ref stand`・`--safe-clamp` との組み合わせで食い違いが無いか見る。
4. テスト（既存は全部通すこと）:
   - h のとき観測 42・値が今と完全に同じ（golden の再生が一致）。
   - x21a/x21b のとき観測 44、k = 0 で [0, 1]、k = 35（0.7 s）で [0, 1] に戻る、k = 17・18 の値、立ち姿勢の目標が既定姿勢。
   - 44 次元のダミー ONNX（無ければテスト内で作る。onnx が無ければ numpy のダミー方策）で乾式ループが回る。
5. dump_contract.py・verify_onnx.py が 44 次元の ONNX を受け付け、仕様と照合できるようにする。本物の ONNX はまだノートPCに無い
   （WRS の run フォルダ\exported\policy.onnx。play.py を1回走らせると書き出される）。届いたらすぐ照合できる手順を書く。
6. 報告（短く）: 冒頭3行（何を足したか・テスト本数・残り）、変えたファイルと .bak、新しいオプション、
   本物の ONNX が届いたときのコマンド（照合 → 乾式 dry-run → 吊りの手順の起動行の案。起動行は実行フォルダ付き・1行版）。
   吊りでの実機試験の手順書は作らない（本人の承認が要る。案を報告に書くだけ）。
7. commit・push（Connect2USB2CAN の feat/mit-mode）。git status --short と git diff --stat を見せてから、対象ファイルを列挙して add。
   シェルで push できないときは、実行フォルダ付きの完成形のコマンドを出す。
```
