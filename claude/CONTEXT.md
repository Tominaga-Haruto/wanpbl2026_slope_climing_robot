# プロジェクト現在地

最終更新: 2026-09-23。これはClaude CodeとCodexが共有する短い現在地であり、実験の生ログそのものではない。

## 👉 いま有効な引き継ぎ書

**`handoffs/active/2026-09-23_d10-7_符号修正後の吊り立ち.md`**

**D10-6 完了: 実機→H 符号は LL_HAA・LR_HR・LR_HFE・LR_KFE・LL_FFE が −1（D4 の全軸 +1 は誤り）。D10-7 を実装した（build `D10_7_SIGNPOSE_20260923_1430`、テスト 129本 OK）。** 次は `procedures/d10_7_符号修正後_吊り立ちと方策_実験手順.md` の R1（`--sign-pose`、HR・HAA +8°）で、両脚が鏡像になるかを目で確かめる。符号は観測値では判定できない。その後、R2 で初期姿勢の保持電流と電源の電流を取り直し、R3・R4 で方策を回す。すべて要承認。**D10-3〜D10-5 の方策 run は符号が誤ったまま回していた。**
実験11（WRS friction スイープ、`instructions/active/wrs_experiment11_friction_instruction.md`）は実機と独立に並行で回す。

## 学習側の現在地（2026-09-23 夜）

- **今夜（約10時間）は実験12の2本を前景で回す。** 指示 `instructions/active/wrs_experiment12_friction_dr_overnight_instruction.md`。どちらも「親の設定そのまま＋関節 friction の DR を ×1.0〜4.0」だけを変える。
  - **X12a**: H_eff13p5@2999（第一回実機候補）から再開。実機の不感帯（シムの 1.7〜3.1 倍）に耐える版を作る。
  - **X12b**: L_angstd_w1@4000（`2026-09-17_21-18-22_L_angstd_w1`）から再開。その場旋回に合格した H 派生（S6 +0.268 / S9 −0.353 rad/s、転倒0、64 env）。旋回も持つデプロイ候補を作る。4498 で旋回が崩れた前例があるので 200 iter ごとに保存して点で選ぶ。
- **B 系（B_continue / B_lateral10 @40006）は延長しない。** 見た目は「旋回しようとして抵抗し、横歩きになる」、立往生あり。plane で延長すると坂の能力も落ちた。
- **坂は後回し。** 10°の坂で転倒せず登れたのは rough＋カリキュラムの4本だけで、最良は B_direct_wz_turn_H20000@25000（20 s で 6.7 m、転倒0、立往生6%）。後半ほど坂で横を向く。坂の段階に入るときはここを親の第一候補にする。根拠 `reports/2026-09-23_学習H以降の棚卸し.md`。
- **旋回の重み（track_ang_vel_z_exp）を上げても横歩きは直らない見込み。** 0.5→1.0→1.5 で改善したのは yaw 追従だけだった。旋回中の横ずれを抑えるのは並進追従の幅（std 0.5 が緩い）の方で、旋回への抵抗は `joint_deviation_hip` が HR（股のひねり）を罰していることと `feet_slide` が候補（推測・未検証）。
- WRS機の CLI には自己完結プロンプトを渡し、学習・評価はユーザーが前景で回す（`../AGENTS.md`「WRS機 CLI の運用」）。CLI 側の整理は `instructions/active/wrs_cli_refactor_instruction.md`。

## 目的と共有方法

- 目的は坂走行ではなく、まず平地での安全な実機デプロイである。
- GitHub `main`が文書・ソースの共有正本。ノートPCの実行環境は`C:\Users\harut\Connect2USB2CAN`、Git作業ツリーは`C:\Users\harut\wanpbl2026_slope_climing_robot`、WRS学習環境は`D:\Tominaga\slope-climbing-robot`である。
- CSV、重み、ONNX、USD/STL、鍵はGitに入れない。報告書に絶対パス・時刻・要約を残す。

## 現在の優先順位

1. **D10-7（`procedures/d10_7_符号修正後_吊り立ちと方策_実験手順.md`）: R1 で符号を目で確認 → R2 で保持電流と電源の電流 → R3・R4 で吊りの方策（要承認）。** 電源は2台を並列にせず、片脚に1台ずつつなぎ、GND を共通にする。
2. **立たせた基準姿勢で D7 の原点を取るための支持治具。床上デプロイの前提条件に格上げした。** D10-2 では前の run で垂れた姿勢のまま `oa` が打たれ、ゼロ姿勢が回ごとに 20〜30° 動いていた。方策の観測量はこの原点からの関節角なので、原点が動けば方策は毎回ちがうロボットを見ている。
3. **実験12（今夜の学習2本、上の節）と実験11: WRS機で friction スイープ（評価のみ・学習なし）。** 指示は `instructions/active/wrs_experiment11_friction_instruction.md`。時間が無ければ「最短ルート」節の3条件（F1.0 / F3.0 / F5.0）だけでよい。実機と並行。
4. **床上の電流中止値は D10-5 R1（初期姿勢の保持電流）と R2/R3・D10-4 の方策 run 実測（最大 LR_HFE 4.4 A、LL_HFE 3.15 A、HAA 1.8 A）から決める。** 推定で決めない。
5. **HR の可動域を URDF／シムへ入れる。** 実測 外90° / 内45°（配線長）。URDF は ±π のまま。
6. コントローラー乾式統合、方策Bの資格評価。
7. 床上デプロイは未許可のまま。

## 実機の状態

- D7受信・ID→ch経路確定、D9 preflight、MITの1軸安全停止は実装済み。USBのPython ch番号は固定せず、毎プロセスで10軸受信から送信先を確定する。
- **MIT の Kp 欄は「位置誤差1 radあたりの電流[A]」として効く**（実測、機種によらない）。**不感帯 = 動き出し電流 ÷ 指令Kp。**
- **電流中止 1.0 A は、脚を方策の初期姿勢へ動かすのに足りない（D10-3 R3 の ramp で LL_HAA 1.7〜2.0 A、LL_HFE 0.9〜1.2 A）。吊り静止の保持は ≤0.10 A（手の支えあり、D10-4 R1 で取り直す）。** 下表の「必要電流」は URDF からの推定で、ゼロ姿勢の HAA 1.70 A は吊り静止の実測と合っていない:

| 軸 | 機種 | ゼロ姿勢の必要電流 | 最悪姿勢の必要電流 | 指令Kp [A/rad] | 1.0 A に達する誤差 | D10-2 で中止したか |
|---|---|---:|---:|---:|---:|---|
| HR 0x1C/0x13 | AK10-9 | 0.03 A | 1.95 A | 7.95 | 7.21° | していない |
| **HAA 0x11/0x1B** | AK10-9 | **1.70 A** | 3.78 A | 11.92 | 4.81° | **R1（0x11）** |
| **HFE 0x21/0x2A** | AK80-9 | 0.02 A | **7.36 A** | 28.68 | **2.00°** | **4回** |
| KFE 0x1A/0x12 | AK10-9 | 0.11 A | 0.93 A | 11.92 | 4.81° | していない |
| **FFE 0x2B/0x22** | AK80-9 | 0.06 A | 0.20 A | 19.12 | **3.00°** | **ver2（0x22）** |

  方策が使ってよい量は AK10-9 42.1 A / AK80-9 25.8 A（effort 53.0 / 13.5 N·m ÷ c_p）。**1.0 A はその 2.4〜3.9% である。**
- **D9-6 実測（デプロイ用ゲイン、判定はすべて A）は有効のまま:** 0x1C LL_HR 0.90 A / 不感帯 6.50°、0x13 LR_HR 0.63 A / 4.55°、0x2B LL_FFE 0.72 A / 2.17°。**0x1C は故障していない。** 根拠 `reports/2026-09-22_d9-6_result.md`。
- **D9-3 / D9-5A の C は新ビルドでも C のまま。** あれは量子化ディザで、最後まで走り出していない。
- **送信器 build `D10_7_SIGNPOSE_20260923_1430`（`.bak_20260923_signpose`、テスト 129本 OK）: `--sign-pose`（`--stand-only` 専用。両脚とも HR・HAA +8°）、`JOINT SIGNS`・`LOOK CHECK` の表示。D7 の `scan` は全軸を実機・H 両方の座標でログに書く。** 以下は前 build から:
- **送信器 build `D10_6_JOINTSIGN_20260923_1340`（`.bak_20260923_jointsign`、テスト 123本 OK）: 関節符号（`robot_joint_map.JointBinding.sign`）を目標と観測の両方に適用。CSV 列 `wire_target_motor_rad`・`feedback_current_h_a`。** 以下は前 build から:
- **送信器 build `D10_5_STANDPOSE_20260923_1300`（`.bak_20260923_standpose`、テスト 89本 OK）: `--stand-seconds`（シム初期姿勢へ ramp→保持→方策）と `--stand-only` を追加。** 以下は前 build から:
- **送信器 build `D10_4_ALLSLEW_20260923_1200`（`.bak_20260923_allslew`、テスト 83本 OK）: `--policy-slew-dps`（全軸 slew、`--all-axes` の方策 run で必須）と全軸プレアーム・ゲート（|目標|>40° か |delta|>30° で送信前に拒否）、停止時の `POLICY STAGE` / `SLEW GAP` を追加。** 以下は前 build からそのまま:
- 送信器 build `D10_3_AXISLOG_20260923_1200`（`.bak_20260923_axislog`、テスト 73本 OK）。`--all-axes` は**全10軸をCSVに記録する**。停止時に `AXIS SNAPSHOT`（全10軸の pos/vel/cur/err/age）。`--analyze` は多軸CSVを読み、hold/policy段階が無いCSVに `INCOMPLETE` を出す。電流中止は軸ごとで、**既定は全軸 1.0 A のまま**。`--gravity-limits`（要承認・`--all-axes` 必須）で HR 3.0 / HAA 6.0 / HFE 11.0 / KFE 3.0 / FFE 2.0 A。`--hold-pose` は全軸をいま居る位置に保持するだけのモード（方策・T265・`--package` を使わない）。**速度中止 100°/s・stale feedback 0.3 s・原点 45°・Kp/Kd・トルク欄は据え置き。**
- `d7_origin_console.py` の `OPEN_ATTEMPTS` を 2→3（`.bak_20260923_openattempts`）。起動時の `USB open失敗 → 再試行 → 成功` は **libusb0 の device reset が1回目にほぼ必ず失敗する**ためで、CANは1フレームも出ていない。ただし2回しか試さない設計では予備がゼロだった。送信器 `DualBus.open` も同じく 3 回へ。
- **`friction 相当 [N·m] = 動き出し電流 [A] × c_p`**（c_p: AK10-9 1.258 / AK80-9 0.523）。実測 → HR 0.79〜1.13 N·m（シム 0.37 の 2.1〜3.1×）、FFE 0.38 N·m（シム 0.22 の 1.7×）。
- モーターの原点は電源断をまたぐと仮定しない。MITは機械ゼロ姿勢でD7を済ませた同一通電中だけ扱う。
- JetsonのコントローラーD5乾式確認は完了。CAN/T265/方策への実機統合は未完了。

## シムの数値の確認（2026-09-23、`my_robot_code/skyentific_poclegs.py` と `rough_env_cfg.py`）

- **初期姿勢:** HR 0、HAA 0、HFE −0.1745 rad（−10°）、KFE +0.3491 rad（+20°）、FFE −0.1745 rad（−10°）、胴体高さ 0.375776 m。リセット時に `reset_joints_by_scale` で関節角を ×0.5〜1.5 する（0 の HR・HAA は 0 のまま）。行動は「この姿勢＋0.5×行動」の目標角。WRS機の実体はハードリンクで同じファイルのはずだが、run ごとの実効値は各 run の `params/env.yaml` が正。
- **トルクのスケール:** ゲインは合わせてある。指令Kp = stiffness ÷ c_p、指令Kd = damping ÷ c_d（AK80-9 0.523 / AK10-9 1.258・1.216、実測）で、例えば HR は 7.95 A/rad × 1.258 = 10.0 N·m/rad ＝ シムの stiffness 10。**合っていないのは3つ:** ① 物理 N·m との絶対換算（Kt）が未測定、② 実機の摩擦がシムの 1.7〜3.1 倍（実験11・12）、③ 実機の電流中止 1.0 A がトルク上限として効いていて、シムの effort 上限（53 / 13.5 N·m）の数%しか出せない（D10-2 の失敗原因）。シムの `friction` が N·m として効いているかは実験12の P1 で確かめる。

## 学習側への持ち帰り（実機不要・最優先）

実機の位置不感帯はデプロイゲインで **HR 4.55〜6.50°、FFE 2.17°**。シムの `friction`（AK80-9実測 0.22 N·m）が意味する 0.9〜1.3° の **2〜5倍**である。H_eff13p5 の頑健性スイープに friction を振った条件が無いので、**WRS機で friction 3〜5倍のスイープ**を回して H_eff13p5@2999 の可否を見る。電流中止を直した後に、不感帯が歩容を壊すかが初めて実機で見られる。

## 正本への案内

| 項目 | 読むファイル |
|---|---|
| 次の作業（引き継ぎ書） | `handoffs/active/2026-09-23_d10-6_関節符号確認.md` |
| その実行手順 | `procedures/d10_6_関節符号_無通電確認手順.md` |
| **D10-5 の結果（初期姿勢の保持電流・左右で脚が前後に割れる・シムの軸の向き）** | `reports/2026-09-23_d10-5_result.md` |
| **D10-4 の結果（初の全身ループ完走・原点ずれ・吊り方策の破綻）** | `reports/2026-09-23_d10-4_result.md` |
| **D10-3 の結果（切替ステップ・保持電流）** | `reports/2026-09-23_d10-3_result.md` |
| **D10-2 の失敗分析・自重と中止値の数値** | `reports/2026-09-23_d10-2_result.md` |
| その実行手順（取り下げ済み） | `procedures/d10_2_吊り全身MITから床上_実験手順.md` |
| 今夜の学習（実験12） | `instructions/active/wrs_experiment12_friction_dr_overnight_instruction.md` |
| 学習H以降の棚卸し（坂評価・報酬の差分） | `reports/2026-09-23_学習H以降の棚卸し.md` |
| 並行（学習側・実機不要） | `instructions/active/wrs_experiment11_friction_instruction.md` と `handoffs/active/2026-09-23_exp11_friction_sweep.md` |
| D9-6 の結果・不感帯の実測 | `reports/2026-09-22_d9-6_result.md` |
| D9-4／D9-5A（接触仮説。D9-6 で取り下げ済み） | `reports/2026-09-22_d9-4_result.md` |
| D9-3 の結果と判定 | `reports/2026-09-22_d9-3_result.md` |
| 電流＝Kp×誤差 の根拠 | `reports/2026-09-22_d9-0x1c-current-vs-error.md` |
| CAN、ID、MITゲイン、原点 | `reference/motor_can_findings.md` |
| 関節対応と符号 | `reports/2026-09-20_d4-m5-joint-map-and-origin-procedure.md` |
| アクチュエータ諸元 | `reference/actuator_params.md` |
| 方策の資格評価 | `reports/2026-09-22_exp10-autoturn-directturn-assessment.md` |

読む順番と文書の更新ルールは `PROJECT.md`。`README.md`、`legacy/project_handbook.md`、`next_chat_*`、`chats/`は削除しないが、開始時には読まない。

## 未整理（2026-09-23 時点）

- `Connect2USB2CAN` の未追跡: `controller/command_*.py`（コントローラー乾式の途中）。`logs/`・`.venv310/`・`t265/`・旧 `motor_console_ver7/8.py` は意図的にGit外。
- `project_handbook.md` がリポジトリ直下で削除済みのまま未commit（2026-09-22 から）。
- このリポジトリの作業ツリーは 2026-09-22 に一度 CRLF→LF の差分が全ファイルに出ていた。中身の差分はゼロだったので`git checkout`で戻した。エディタの改行設定が原因なら再発する。
- **同じCSV名の上書きが2度起きている**（2026-09-22、2026-09-22夜の ver3）。手順書の禁止事項に入っているが守られていない。
