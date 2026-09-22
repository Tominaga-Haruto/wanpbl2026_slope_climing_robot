# Active handoff — D9-3 0x1C 不感帯を越える1軸診断（要承認）

更新日: 2026-09-22

## Claude Code / Codex への最初の依頼

「`reports/2026-09-22_d9-0x1c-current-vs-error.md` を読んで、D9-3（要求角 6.5° の static probe 1回）の承認待ちの状態を確認してください。ユーザーが明示的に承認するまで実機送信はしません。承認前にできるのは、無通電の機構確認の整理、学習側の friction スイープの用意、実機を動かさない作業だけです。」

## 目的と完了条件

0x1C（LL_HR、AK10-9）が「普通のスティクションで止まっている」のか「機構が異常で固まっている」のかを1回の通電試験で分ける。完了は、D9-3 の実行結果（CSV・画面ログ・動画）と判定、または承認が下りないまま無通電の機構確認だけを終えた状態である。

## 確認済みの事実（2026-09-22 に更新）

- **MITトルク経路は正常と確定した。** 保存済み2本のCSVで `|I| = 8.20 / 8.31 A/rad × 位置誤差`、指令 Kp 7.937 に対し比 1.03 / 1.05、切片 0.02 A 未満。**MIT の Kp 欄は「1 rad あたりの電流[A]」として効く**（機種によらない）。根拠 `reports/2026-09-22_d9-0x1c-current-vs-error.md`。
- **動かなかった理由は試験の設計。** 不感帯 = 動き出し電流 ÷ 指令Kp。0x1C は 0.66 A で動かないので不感帯は 4.8°以上。D9-2 の要求角は 4.52°（合格線 2.26°）、static probe は 2.5°（同 1.25°）で、**裸の AK80-9（動き出し 0.63 A、`actuator_params.md` §0）でも満たせない条件**だった。0x1C 固有の異常を示す数値は今のところ無い。
- 電流中止 1.0 A のため、位置指令で探れる動き出し電流は 1.0 A まで＝**要求角 7.2° が上限**。それ以上は中止に当たるだけ。
- `ver9_d8_sender.py` build `D9_DIAG_20260922_1930`: `TORQUE PATH` / `DEADBAND` 判定、送信前の `stall_guard`（静止実証済みの電流以下しか掛けられない実行を、MITフレームを出さずに中止）、実機なしの `--analyze <csv>`。ゲイン・目標角・トルク欄は変えていない。単体テスト31本 OK。
- D7受信・ID→ch経路確定、D9 preflight、零MIT停止は実装済み。USBのPython ch番号は毎プロセス確定。

## 最初に読むもの

1. `../CONTEXT.md`
2. `../reports/2026-09-22_d9-0x1c-current-vs-error.md`
3. `../d9_2_1軸MITランプ_実験手順.md` の「次の1軸診断（D9-3、要承認）」
4. `../motor_can_findings.md`（MIT・原点・機種別係数）
5. 必要な範囲だけ `C:\Users\harut\Connect2USB2CAN\ver9_d8_sender.py` と最新CSV

## 許可／禁止

- **許可（承認不要）:** 無通電・主電源OFFでの目視と手回し確認、`--analyze` によるCSV再判定、学習側の friction スイープ、コントローラー乾式、文書更新。
- **要ユーザー承認:** D9-3（`STATIC_PROBE_MAX_DEG` を 2.5 → 7.0 に変え、要求角 6.5° の static probe を1回）。承認は「吊り支持・電源遮断担当・同一通電中のD7 `oa`・preflight 済み」を確認した上で受ける。
- **禁止:** D9-2 と同じ試験の再実行、Kp/Kd・トルク欄の増加、承認のない要求角の変更、片脚／全身MIT、床上デプロイ。`repeat-probe abort` をゲインや目標を上げて回避すること。

## 実行環境と記録

- 実機: `C:\Users\harut\Connect2USB2CAN`（`.venv310\Scripts\python.exe`）。学習: WRS機 `D:\Tominaga\slope-climbing-robot`。
- CSV・生ログ・モデル・鍵はGitに入れない。要約と絶対パスを `../reports/` へ残す。
- 作業後は `ACTIVE.md` と `../CONTEXT.md` を更新し、触ったファイルだけを commit / push する。
