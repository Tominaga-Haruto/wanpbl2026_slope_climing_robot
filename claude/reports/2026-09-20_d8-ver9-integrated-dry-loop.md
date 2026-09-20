# D8: ver9統合乾式ループ

2026-09-20。対象は `C:\Users\harut\Connect2USB2CAN`。実機CAN、モーター、T265、コントローラーを開かず、H_eff13p5@2999の読み取り専用デプロイ成果物だけを使ってPC上で確認した。

## 実装

- `ver9_integration.py`: D3 base観測、D4/D7のH順10関節フィードバック、固定速度指令、前周期actionから、契約通り42要素観測を作る。
- ONNXの10 actionからH順目標角を作り、D4/D7の全符号`+1`でCAN順 `0x13, 0x1C, 0x1B, 0x11, 0x2A, 0x21, 0x12, 0x1A, 0x22, 0x2B` の計画へ並べ替える。
- これは送信不能なD8 PC確認用の境界であり、CANをopen・送信しない。実機のCAN接続はD9だけで行う。
- `ver9_shell.py`: T265のbase原点補正を `v_b = R_CB^T v_c - w_b × R_OFFSET` で実装した。`--t265`では `--t265-r-offset X Y Z` を必須にし、未記録の取付値を推測して使えないようにした。

## 検証

`C:\Users\harut\Connect2USB2CAN` で `.venv310\Scripts\python.exe -m unittest test_policy_dry_run.py test_policy_integration.py test_ver9_shell.py test_ver9_integration.py` を実行し、14件すべて合格。

同じディレクトリで、次を実行した。

```powershell
.venv310\Scripts\python.exe ver9_integration.py --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --duration 5 --csv logs\ver9_d8_synthetic_check.csv
```

- golden 500件: action最大絶対誤差 `1.1920929e-06`（step 335）、H順目標角 `5.96046448e-07`（step 113）。ともに閾値`1e-4`以下。
- 合成入力の50 Hz乾式ループ: 251周期、平均`19.993 ms`、p95`20.828 ms`、最大`22.814 ms`、deadline超過8回。
- Windowsでは`monotonic()`が約15.6 ms刻みになるため、スケジューリングと周期評価には`perf_counter()`を使用し、実行中だけ1 msタイマー分解能を要求して終了時に戻す。

## D9への制約

CADに記録済みとされる実機の `R_OFFSET=[x,y,z] m` は、現在の文書に3軸の数値ベクトルとしては残っていない。D9のT265起動では、`--t265-r-offset X Y Z` へCADの実値を明示するまで実機観測を開始しない。ゼロや外形寸法からの推測は禁止する。
