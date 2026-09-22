# プロジェクト現在地

最終更新: 2026-09-22。これはClaude CodeとCodexが共有する短い現在地であり、実験の生ログそのものではない。

## 目的と共有方法

- 目的は坂走行ではなく、まず平地での安全な実機デプロイである。
- GitHub `main`が文書・ソースの共有正本。ノートPCの実行環境は`C:\Users\harut\Connect2USB2CAN`、WRS学習環境は`D:\Tominaga\slope-climbing-robot`である。
- CSV、重み、ONNX、USD/STL、鍵はGitに入れない。報告書に絶対パス・時刻・要約を残す。

## 現在の優先順位

1. **D9-3（0x1C の不感帯を越える1軸 static probe）をユーザー承認の上で1回だけ行う。** 片脚、全身MIT、床上デプロイは未許可。詳細は`handoffs/ACTIVE.md`。
2. **実機を動かさない作業は並行可能。** D7受信確認、CAN経路確認、D9 preflight、シミュレーション評価、コントローラー乾式統合はD9の追従不合格とは別に進められる。
3. **方策はH_eff13p5@2999が第一回実機候補。** B直接旋回方策は64 envでは有望だが、資格評価が未完了で候補へ昇格していない。根拠は`reports/2026-09-22_exp10-autoturn-directturn-assessment.md`。

## 実機の状態

- D7受信・ID→ch経路確定、D9 preflight、MITの1軸安全停止は実装済み。USBのPython ch番号は固定せず、毎プロセスで10軸受信から送信先を確定する。
- 0x1C（LL_HR、AK10-9）はD9方策ランプ4回とstatic probeで追従0°。**ただし原因はMIT経路ではなく試験の要求角である。** 保存済みCSVの回帰で `電流 = 8.2 A/rad × 位置誤差`（指令Kp 7.937、比1.03）＝MITトルク経路は正常。不感帯 = 動き出し電流 ÷ 指令Kp で 0x1C は 4.8°以上あり、要求角 4.52° / 2.5° では健全な軸でも動かない。根拠は`reports/2026-09-22_d9-0x1c-current-vs-error.md`。
- モーターの原点は電源断をまたぐと仮定しない。MITは機械ゼロ姿勢でD7を済ませた同一通電中だけ扱う。
- JetsonのコントローラーD5乾式確認は完了。CAN/T265/方策への実機統合は未完了。

## 正本への案内

| 項目 | 読むファイル |
|---|---|
| 今の実機作業 | `handoffs/ACTIVE.md` |
| D9停止の根拠 | `reports/2026-09-22_d9-0x1c-current-vs-error.md`（`..._d9-0x1c-stall-analysis.md` はその前段・一部訂正済み） |
| CAN、ID、MITゲイン、原点 | `motor_can_findings.md` |
| 関節対応と符号 | `reports/2026-09-20_d4-m5-joint-map-and-origin-procedure.md` |
| アクチュエータ諸元 | `actuator_params.md` |
| 方策の資格評価 | `reports/2026-09-22_exp10-autoturn-directturn-assessment.md` |

`README.md`、`project_handbook.md`、`next_chat_*`、`chats/`は削除しない。過去の根拠・詳細手順として残すが、現在地の入口は`PROJECT.md`、`CONTEXT.md`、`handoffs/ACTIVE.md`へ統一した。

## 学習側への持ち帰り（2026-09-22、実機不要）

実機の位置不感帯はデプロイゲインで 0x1C 4.8°以上。シムの `friction`（AK80-9 実測 0.22 N·m）が意味する 0.9〜1.3° の4倍以上あり、H_eff13p5 の頑健性スイープには friction を振った条件が無い。床上デプロイの前に、WRS機で **friction 3〜5倍のスイープ**を回して H_eff13p5@2999 の可否を見る。D9 の進捗と独立に着手できる。
