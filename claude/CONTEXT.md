# プロジェクト現在地

最終更新: 2026-09-22。これはClaude CodeとCodexが共有する短い現在地であり、実験の生ログそのものではない。

## 👉 いま有効な引き継ぎ書

**`handoffs/2026-09-22_d9-3_ブレークアウェイ判定.md`**

次のチャットの最初の仕事は、ユーザーが実行した **D9-3（0x1C・要求角 −6.5°）の結果を、その引き継ぎ書の事前判定表で採点すること**である。

## 目的と共有方法

- 目的は坂走行ではなく、まず平地での安全な実機デプロイである。
- GitHub `main`が文書・ソースの共有正本。ノートPCの実行環境は`C:\Users\harut\Connect2USB2CAN`、Git作業ツリーは`C:\Users\harut\wanpbl2026_slope_climing_robot`、WRS学習環境は`D:\Tominaga\slope-climbing-robot`である。
- CSV、重み、ONNX、USD/STL、鍵はGitに入れない。報告書に絶対パス・時刻・要約を残す。

## 現在の優先順位

1. **D9-3 の結果判定。** 0x1C が普通のスティクションか機構の異常かを分ける。片脚、全身MIT、床上デプロイは未許可。
2. **実機を動かさない作業は並行可能。** WRSでの friction スイープ（下の「持ち帰り」）、コントローラー乾式統合、方策Bの資格評価、受信だけの診断。
3. **方策はH_eff13p5@2999が第一回実機候補。** B直接旋回方策は64 envでは有望だが資格評価が未完了。根拠は`reports/2026-09-22_exp10-autoturn-directturn-assessment.md`。

## 実機の状態

- D7受信・ID→ch経路確定、D9 preflight、MITの1軸安全停止は実装済み。USBのPython ch番号は固定せず、毎プロセスで10軸受信から送信先を確定する。
- **MIT の Kp 欄は「位置誤差1 radあたりの電流[A]」として効く**（実測、機種によらない）。物理トルクは`電流 × Kt`で、AK10-9 の Kt は未測定。よって判断は電流で行う。**不感帯 = 動き出し電流 ÷ 指令Kp。**
- 0x1C（LL_HR）は 0.66 A でも動かず、不感帯は 4.8°以上。D9-2 の要求角（4.52° / 2.5°）は裸のAK80-9（動き出し0.63 A）でも動かない条件だった。**MIT経路の異常ではない。** 根拠 `reports/2026-09-22_d9-0x1c-current-vs-error.md`。
- 送信器 build `D9_BREAKAWAY_20260922_2130`。静止が実証済みの電流以下しか掛けられない実行は `repeat-probe abort` で送信前に止まる。Kp 7.937 では 6.86° が電流中止(1.0 A)の限界。
- モーターの原点は電源断をまたぐと仮定しない。MITは機械ゼロ姿勢でD7を済ませた同一通電中だけ扱う。
- JetsonのコントローラーD5乾式確認は完了。CAN/T265/方策への実機統合は未完了。

## 学習側への持ち帰り（実機不要・未着手）

実機の位置不感帯はデプロイゲインで 0x1C 4.8°以上。シムの`friction`（AK80-9実測 0.22 N·m）が意味する 0.9〜1.3° の4倍以上あり、H_eff13p5 の頑健性スイープに friction を振った条件が無い。床上デプロイの前に、WRS機で **friction 3〜5倍のスイープ**を回して H_eff13p5@2999 の可否を見る。D9 の進捗と独立に着手できる。

## 正本への案内

| 項目 | 読むファイル |
|---|---|
| 次の作業 | `handoffs/2026-09-22_d9-3_ブレークアウェイ判定.md` |
| その実行手順 | `procedures/d9_3_1軸ブレークアウェイ_実験手順.md` |
| D9停止の根拠 | `reports/2026-09-22_d9-0x1c-current-vs-error.md` |
| CAN、ID、MITゲイン、原点 | `motor_can_findings.md` |
| 関節対応と符号 | `reports/2026-09-20_d4-m5-joint-map-and-origin-procedure.md` |
| アクチュエータ諸元 | `actuator_params.md` |
| 方策の資格評価 | `reports/2026-09-22_exp10-autoturn-directturn-assessment.md` |

読む順番と文書の更新ルールは `PROJECT.md`。`README.md`、`project_handbook.md`、`next_chat_*`、`chats/`は削除しないが、開始時には読まない。

## 未整理（2026-09-22 時点）

- `Connect2USB2CAN` の未追跡: `controller/command_*.py`（コントローラー乾式の途中）。`logs/`・`.venv310/`・`t265/`・旧 `motor_console_ver7/8.py` は意図的にGit外。
- このリポジトリの作業ツリーは 2026-09-22 に一度 CRLF→LF の差分が全ファイルに出ていた。中身の差分はゼロだったので`git checkout`で戻した。エディタの改行設定が原因なら再発する。
