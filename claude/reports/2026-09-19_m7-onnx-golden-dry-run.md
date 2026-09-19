# M7 ONNX golden dry run

## 実装

- `C:\Users\harut\Connect2USB2CAN\policy_dry_run.py` を追加した。
- `SHA256SUMS.txt` の6必須ファイルを推論前に照合する。
- `golden.npz` の主要キー、shape、dtype、関節順、既定角、action scale、目標角の式を検査する。
- 実際のONNX入出力名・型・shapeを取得して、float32の42→10だけを許可する。
- 500件のactionと `default_joint_pos + 0.5 * action` の目標角を比較する。`--realtime` は20 ms予定表のCSVを出す。
- CAN、USB、T265、コントローラー、`mit_sim.py`、モーターコンソールはimport・接続しない。

## 実測結果

対象パッケージは `C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999`。

- SHA256: 6/6一致。
- action最大絶対誤差: `1.1920929e-06`（step 335）。
- 目標角最大絶対誤差: `5.96046448e-07`（step 113）。
- 判定閾値: `1e-4`。両方PASS。
- `--realtime` CSV: `C:\Users\harut\Connect2USB2CAN\logs\policy_dry_run_m7.csv`（500行）。周期平均20.026 ms、最小0.504 ms、最大40.687 ms、最大deadline遅れ22.104 ms、推論最大4.409 ms。

## 確認

`C:\Users\harut\Connect2USB2CAN\.venv310\Scripts\python.exe -m unittest -v test_policy_dry_run.py` は3件すべてPASS。

## 残件

この乾式検証はCANや実観測を使わない。実機接続には、M5原点表、T265途絶停止を含む乾式設計、10モーター周期確認、およびユーザーの明示が別途必要。
