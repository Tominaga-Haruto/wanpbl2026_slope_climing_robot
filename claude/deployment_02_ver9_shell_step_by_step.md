# D2: ver9 方策非依存骨組み — 実装メモ

## 実装済みの範囲

`C:\Users\harut\Connect2USB2CAN\ver9_shell.py` に、方策非依存の受信専用50 Hzループを実装した。1周期ごとに次の時刻付きデータをCSVへ記録する。

- T265のbase座標の線速度・角速度・projected gravity
- 指定した10 CAN IDの最新の位置・速度フィードバック
- 固定の速度指令 `(vx, vy, wz)`
- 未確定の42要素ONNX入力プレースホルダ（全要素0）
- 10要素の `planned_target`（D2では常に0）
- tick時刻、実周期、overrun、各入力のage、欠損CAN ID

T265はバックグラウンドで受信し、50 Hzループをセンサ待ちで止めない。T265のD3取付け位置補正は未実装として `t265_offset_pending=1` を明記する。CAN IDは生のIDのままで、H順・原点・符号への変換は含めない。

## 明示的に含めないもの

- ONNX、42要素の観測構築、H順の関節変換、原点変換、ゲイン
- CANの位置・速度・トルク指令、MIT enable、原点設定、motor consoleの呼び出し
- コントローラー実デバイスの読み取り（固定速度指令だけを使う）

CAN受信には既存の `cubemars.MotorBus` を用いるが、終了時は `close(stop_motors=False)` に固定している。`ver9_shell.py` は `.send(`・`stop_all(` を持たず、送信経路はない。

## 実機なしの確認

追加した `test_ver9_shell.py` は、T265/CANの合成入力で以下を検証する。

- 50 HzスケジューラがCSVへ時刻付き行を生成する
- 42個の観測プレースホルダと10個の予定目標角がすべて0
- CAN送信数が0
- CAN ID数と固定コマンド範囲を拒否できる

実行結果（2026-09-20）: 2秒で101行、予定目標角の非ゼロ行0、CAN送信0。

## D2の確認コマンド

ノートPCのPowerShellで、次を実行する。これはUSB機器に接続しない合成入力だけの確認である。

```powershell
cd C:\Users\harut\Connect2USB2CAN
py -3.13 -m unittest test_ver9_shell.py
py -3.13 ver9_shell.py --synthetic --duration 2 --csv C:\Users\harut\Connect2USB2CAN\logs\ver9_shell_synthetic_check.csv
```

実機T265/CANへ接続するのはD3/D4/D7の確定値と、D8の統合範囲で行う。D2の完了に実機試験は含めない。
