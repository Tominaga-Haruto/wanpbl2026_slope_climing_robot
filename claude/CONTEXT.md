# プロジェクト現在地

最終更新: 2026-09-22。これはClaude CodeとCodexが共有する短い現在地であり、実験の生ログそのものではない。

## 目的と共有方法

- 目的は坂走行ではなく、まず平地での安全な実機デプロイである。
- GitHub `main`が文書・ソースの共有正本。ノートPCの実行環境は`C:\Users\harut\Connect2USB2CAN`、WRS学習環境は`D:\Tominaga\slope-climbing-robot`である。
- CSV、重み、ONNX、USD/STL、鍵はGitに入れない。報告書に絶対パス・時刻・要約を残す。

## 現在の優先順位

1. **D9 0x1C 1軸追従停止を安全に原因分離する。** 片脚、全身MIT、床上デプロイは未許可。詳細は`handoffs/ACTIVE.md`。
2. **実機を動かさない作業は並行可能。** D7受信確認、CAN経路確認、D9 preflight、シミュレーション評価、コントローラー乾式統合はD9の追従不合格とは別に進められる。
3. **方策はH_eff13p5@2999が第一回実機候補。** B直接旋回方策は64 envでは有望だが、資格評価が未完了で候補へ昇格していない。根拠は`reports/2026-09-22_exp10-autoturn-directturn-assessment.md`。

## 実機の状態

- D7受信・ID→ch経路確定、D9 preflight、MITの1軸安全停止は実装済み。USBのPython ch番号は固定せず、毎プロセスで10軸受信から送信先を確定する。
- 0x1C（LL_HR、AK10-9）はD9方策ランプ4回とstatic probeで追従0°。最新CSVは`C:\Users\harut\Connect2USB2CAN\logs\d9_one_axis_0x1c.csv`、2026-09-22 18:41:33更新、402行、wire target最小−5.128°、位置・速度不変、最大|電流|0.66 A。
- モーターの原点は電源断をまたぐと仮定しない。MITは機械ゼロ姿勢でD7を済ませた同一通電中だけ扱う。
- JetsonのコントローラーD5乾式確認は完了。CAN/T265/方策への実機統合は未完了。

## 正本への案内

| 項目 | 読むファイル |
|---|---|
| 今の実機作業 | `handoffs/ACTIVE.md` |
| D9停止の根拠 | `reports/2026-09-22_d9-0x1c-stall-analysis.md` |
| CAN、ID、MITゲイン、原点 | `motor_can_findings.md` |
| 関節対応と符号 | `reports/2026-09-20_d4-m5-joint-map-and-origin-procedure.md` |
| アクチュエータ諸元 | `actuator_params.md` |
| 方策の資格評価 | `reports/2026-09-22_exp10-autoturn-directturn-assessment.md` |

`README.md`、`project_handbook.md`、`next_chat_*`、`chats/`は削除しない。過去の根拠・詳細手順として残すが、現在地の入口は`PROJECT.md`、`CONTEXT.md`、`handoffs/ACTIVE.md`へ統一した。
