# D8: ver9統合乾式ループ

2026-09-21更新。対象は `C:\Users\harut\Connect2USB2CAN`。D8の実機送信プログラムまで実装したが、実機CAN、モーター、T265はまだ起動していない。

## 実装

- `ver9_integration.py`: D3 base観測、D4/D7のH順10関節フィードバック、固定速度指令、前周期actionから、契約通り42要素観測を作る。
- ONNXの10 actionからH順目標角を作り、D4/D7の全符号`+1`でCAN順 `0x13, 0x1C, 0x1B, 0x11, 0x2A, 0x21, 0x12, 0x1A, 0x22, 0x2B` の計画へ並べ替える。
- これは送信不能なD8 PC確認用の境界であり、CANをopen・送信しない。実機のCAN接続はD9だけで行う。
- `ver9_shell.py`: T265のbase原点補正を `v_b = R_CB^T v_c - w_b × R_OFFSET` で実装した。CAD確定値 `R_OFFSET=(+0.06345,+0.08900,+0.04275) m` を `T265_R_OFFSET_M` と `--t265-r-offset` の既定値にし、実機T265でも自動適用する。
- `ver9_integration.py --live-dry`: T265とch=0/1のCANフィードバックを受信して、42要素→ONNX→D4/D7の10軸CAN計画を50 HzでCSVへ記録する。T265の最初のposeを最大5秒待つ。MIT送信APIを持たず、送信数が0以外なら失敗する。実機では未起動である。
- `ver9_d8_sender.py`: D8の送信器。両CANへ10軸のmode 8 MITフレームを50 Hzで送信し、AK10/AK80の実測 c_p/c_d でKp/Kdを換算する。`--arm`なしでは送信しない。例外・終了時は全10軸へ零MITフレームを3回送る。

## 検証

`C:\Users\harut\Connect2USB2CAN` で `.venv310\Scripts\python.exe -m unittest test_policy_dry_run.py test_policy_integration.py test_ver9_shell.py test_ver9_integration.py` を実行し、15件すべて合格。D3確定値を使い、base z軸まわりの角速度に対する補正速度 `(-0.08900,+0.06345,0) m/s` も回帰試験に固定した。

同じディレクトリで、次を実行した。

```powershell
.venv310\Scripts\python.exe ver9_integration.py --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --duration 5 --csv logs\ver9_d8_synthetic_check.csv
```

- golden 500件: action最大絶対誤差 `1.1920929e-06`（step 335）、H順目標角 `5.96046448e-07`（step 113）。ともに閾値`1e-4`以下。
- 合成入力の50 Hz乾式ループ（最新5秒再実行）: 250周期、平均`20.000 ms`、p95`20.710 ms`、最大`22.397 ms`、deadline超過4回。
- Windowsでは`monotonic()`が約15.6 ms刻みになるため、スケジューリングと周期評価には`perf_counter()`を使用し、実行中だけ1 msタイマー分解能を要求して終了時に戻す。

## D9への境界

`R_OFFSET=(+0.06345,+0.08900,+0.04275) m` はCAD値としてver9へ固定済みである。D8は送信器実装まで完了した。D9は [`d9_吊り10軸MIT実験手順.md`](../d9_吊り10軸MIT実験手順.md) に従って実機で実行・判定するだけであり、D9中にプログラムを新規作成しない。
