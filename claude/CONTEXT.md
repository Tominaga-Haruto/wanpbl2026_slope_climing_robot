# プロジェクト現在地

最終更新: 2026-09-23。これはClaude CodeとCodexが共有する短い現在地であり、実験の生ログそのものではない。

## 👉 いま有効な引き継ぎ書

**`handoffs/2026-09-23_d10-3_吊り保持測定.md`**

**D10-2 は失敗。全5本が ramp 中に `motion/current abort` で落ちた。原因は方策でも軸の故障でもなく、電流中止 1.0 A がこの機体の自重より小さいこと。** 根拠 `reports/2026-09-23_d10-2_result.md`。次は方策を回さず、**吊りのまま「その場保持」で軸ごとの必要電流を実測する**（`procedures/d10_3_吊り保持測定_実験手順.md`）。次のチャットの最初の仕事は R0・R1 の結果を切り分けること。
実験11（WRS friction スイープ、`instructions/wrs_experiment11_friction_instruction.md`）は実機と独立に並行で回す。

## 目的と共有方法

- 目的は坂走行ではなく、まず平地での安全な実機デプロイである。
- GitHub `main`が文書・ソースの共有正本。ノートPCの実行環境は`C:\Users\harut\Connect2USB2CAN`、Git作業ツリーは`C:\Users\harut\wanpbl2026_slope_climing_robot`、WRS学習環境は`D:\Tominaga\slope-climbing-robot`である。
- CSV、重み、ONNX、USD/STL、鍵はGitに入れない。報告書に絶対パス・時刻・要約を残す。

## 現在の優先順位

1. **D10-3 R0・R1（吊り・`--hold-pose`・既定中止 1.0 A のまま・承認不要）。** 手順 `procedures/d10_3_吊り保持測定_実験手順.md`。R1 は**落ちるのが正解**で、それが「1.0 A が原因」を所見から測定に変える。**R2（`--gravity-limits`）・R3・R4 は要ユーザー承認。**
2. **立たせた基準姿勢で D7 の原点を取るための支持治具。床上デプロイの前提条件に格上げした。** D10-2 では前の run で垂れた姿勢のまま `oa` が打たれ、ゼロ姿勢が回ごとに 20〜30° 動いていた。方策の観測量はこの原点からの関節角なので、原点が動けば方策は毎回ちがうロボットを見ている。
3. **実験11: WRS機で friction スイープ（評価のみ・学習なし）。** 指示は `instructions/wrs_experiment11_friction_instruction.md`。時間が無ければ「最短ルート」節の3条件（F1.0 / F3.0 / F5.0）だけでよい。実機と並行。
4. **床上の電流中止値は D10-3 R2 の実測表から決める。** 推定で決めない。D10-2 の失敗はそこである。
5. **HR の可動域を URDF／シムへ入れる。** 実測 外90° / 内45°（配線長）。URDF は ±π のまま。
6. コントローラー乾式統合、方策Bの資格評価。
7. 床上デプロイは未許可のまま。

## 実機の状態

- D7受信・ID→ch経路確定、D9 preflight、MITの1軸安全停止は実装済み。USBのPython ch番号は固定せず、毎プロセスで10軸受信から送信先を確定する。
- **MIT の Kp 欄は「位置誤差1 radあたりの電流[A]」として効く**（実測、機種によらない）。**不感帯 = 動き出し電流 ÷ 指令Kp。**
- **電流中止 1.0 A はこの機体の自重より小さい。全身 run には使えない。** URDF から出した各軸の静的必要電流と、1.0 A に達する追従誤差:

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
- 送信器 build **`D10_3_AXISLOG_20260923_1200`**（`.bak_20260923_axislog`、テスト 73本 OK）。`--all-axes` は**全10軸をCSVに記録する**。停止時に `AXIS SNAPSHOT`（全10軸の pos/vel/cur/err/age）。`--analyze` は多軸CSVを読み、hold/policy段階が無いCSVに `INCOMPLETE` を出す。電流中止は軸ごとで、**既定は全軸 1.0 A のまま**。`--gravity-limits`（要承認・`--all-axes` 必須）で HR 3.0 / HAA 6.0 / HFE 11.0 / KFE 3.0 / FFE 2.0 A。`--hold-pose` は全軸をいま居る位置に保持するだけのモード（方策・T265・`--package` を使わない）。**速度中止 100°/s・stale feedback 0.3 s・原点 45°・Kp/Kd・トルク欄は据え置き。**
- `d7_origin_console.py` の `OPEN_ATTEMPTS` を 2→3（`.bak_20260923_openattempts`）。起動時の `USB open失敗 → 再試行 → 成功` は **libusb0 の device reset が1回目にほぼ必ず失敗する**ためで、CANは1フレームも出ていない。ただし2回しか試さない設計では予備がゼロだった。送信器 `DualBus.open` も同じく 3 回へ。
- **`friction 相当 [N·m] = 動き出し電流 [A] × c_p`**（c_p: AK10-9 1.258 / AK80-9 0.523）。実測 → HR 0.79〜1.13 N·m（シム 0.37 の 2.1〜3.1×）、FFE 0.38 N·m（シム 0.22 の 1.7×）。
- モーターの原点は電源断をまたぐと仮定しない。MITは機械ゼロ姿勢でD7を済ませた同一通電中だけ扱う。
- JetsonのコントローラーD5乾式確認は完了。CAN/T265/方策への実機統合は未完了。

## 学習側への持ち帰り（実機不要・最優先）

実機の位置不感帯はデプロイゲインで **HR 4.55〜6.50°、FFE 2.17°**。シムの `friction`（AK80-9実測 0.22 N·m）が意味する 0.9〜1.3° の **2〜5倍**である。H_eff13p5 の頑健性スイープに friction を振った条件が無いので、**WRS機で friction 3〜5倍のスイープ**を回して H_eff13p5@2999 の可否を見る。電流中止を直した後に、不感帯が歩容を壊すかが初めて実機で見られる。

## 正本への案内

| 項目 | 読むファイル |
|---|---|
| 次の作業（引き継ぎ書） | `handoffs/2026-09-23_d10-3_吊り保持測定.md` |
| その実行手順 | `procedures/d10_3_吊り保持測定_実験手順.md` |
| **D10-2 の失敗分析・自重と中止値の数値** | `reports/2026-09-23_d10-2_result.md` |
| その実行手順（取り下げ済み） | `procedures/d10_2_吊り全身MITから床上_実験手順.md` |
| 並行（学習側・実機不要） | `instructions/wrs_experiment11_friction_instruction.md` と `handoffs/2026-09-23_exp11_friction_sweep.md` |
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
