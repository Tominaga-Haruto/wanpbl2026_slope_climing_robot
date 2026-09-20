# 2026-09-20 D5 Jetson 乾式入力の引き継ぎ

## やったこと

- D5の対象文書、Hの `obs_contract.md`、D2・D4・M5の指示書を読み、D5の範囲とD1〜D10の依存関係を確認した。
- Hの速度指令は `(lin_vel_x, lin_vel_y, ang_vel_z)`、各範囲は `[-1, +1]`、機体baseは `+X=前`・`+Y=左`と確認した。
- Jetsonで有線Switch 2 Proを延長用変換器経由でなく直結すると、`/dev/input/by-id/usb-045e_XBOX_360_For_Windows_000000000001-event-joystick -> ../event7` が見えた。Python 3.8.10で、当初は `evdev` 未導入だった。
- Jetson側Codexの実行環境では `/dev/input` が見えなかったため、Jetson通常ターミナルで実測した。`python3-venv` を導入して `~/.venvs/controller-d5` に `evdev` を入れ、既存 `/home/wan-pbl-2026/Downloads/pad_probe.py` を使った（このファイルはGit管理外）。
- 中立約10秒では約20 ms周期で `(0, 0, 0)` を継続出力した。前後左右の操作は、前=`+vx`、後=`-vx`、右=`-vy`、左=`+vy`、`wz=0`で問題なく表示された。
- 抜線時は `input disconnected or unreadable: [Errno 19] No such device` を出して exit 3 で終了し、CSV末尾は`timeout`かつゼロ指令だった。再接続後は安定パスから起動でき、5秒間すべてゼロ指令だった。

## 決めたこと・分かったこと

- 左スティック前（`ABS_Y<0`）を `+vx`、右（`ABS_X>0`）を `-vy`、`wz=0`へ対応付ける。`pad_probe.py` の符号引数では `--x-sign -1 --y-sign -1` が必要。
- D5のソフト側の共通速度コマンド境界と、Jetson**直結時**の入力・50 Hz・方向・抜線・再接続の乾式確認は完了した。CAN、ONNX、T265、モーターへの接続はしていない。実運用の変換ケーブル経由は別問題として未解決であり、`chats/2026-09-20_d5-extension-path-handoff.md`へ引き継ぐ。
- 通常ターミナルでは`/dev/input/event7`へユーザーACLで読み取りアクセスできた。一方、Jetson側Codexの実行環境にはUSB／`/dev/input`が公開されないため、実機入力試験には使えない。
- `pad_probe.py`は抜線でexit 3となるため、統合時は受け手側が入力途絶を検出し、ゼロ指令と安全停止を継続する必要がある。これはD8/D9で実装・確認する。
- モーター主電源、CAN、ONNX、T265には一切触れていない。

## 手を動かした場所

- ノートPC側では文書更新のみ。Jetson側で`~/controller-d5-logs/`へ中立・方向・抜線・再接続のCSVを出力した（Gitへ追加しない）。
- Jetson側で実行した既存スクリプト: `/home/wan-pbl-2026/Downloads/pad_probe.py`（Git管理外）。

## 積み残し・次にやること

1. 実運用の延長経路で直結時と同じ`045e:028e`として安定認識できるようにしてから、同じ乾式試験を再実施する。
2. D5が実運用構成で完了するまで、ver9、CAN、ONNX、T265、モーターをこの入力試験と接続しない。
