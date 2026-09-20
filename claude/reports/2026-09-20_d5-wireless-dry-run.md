# 2026-09-20 D5 Bluetooth 無線乾式確認

## 結論

ユーザー判断により、D5 の実運用経路は Bluetooth 無線を第一候補とする。有線直結で確認済みのソフト・入力対応を再利用し、CAN、ONNX、T265、モーターを一切接続しない Jetson 単体の乾式試験で受け入れる。

有線延長経路の USB 設定失敗（`error -32`）は未解決のまま残す。Bluetooth を試すことは、その原因を HID や `evdev` の問題として扱うことを意味しない。

## 事前条件

- Switch 2 Pro と Jetson だけを使う。CAN、モーター電源、T265、ONNX 実行はすべて外す。
- Jetson 通常ターミナルを使う。Codex 側の実行環境には `/dev/input` が公開されない。
- 既存の `~/.venvs/controller-d5` と `/home/wan-pbl-2026/Downloads/pad_probe.py` を使う。パッケージの追加・更新はしない。
- H の指令契約は `(lin_vel_x, lin_vel_y, ang_vel_z)`、それぞれ ±1。今回の乾式確認では既定どおり左スティックだけを `(vx, vy, 0)` として表示する。

## 既知の無線機器

2026-09-20 の実測で、対象は次の Bluetooth HID と確定した。

- Name: `Pro Controller`
- MAC: `98:B6:E9:4A:87:92`（public）
- Bluetooth HID vendor/product: `057e:2009`
- 接続後の Linux 入力: `Name="Pro Controller"`、`js0` と動的な `eventN`

`/dev/input/by-id` には Bluetooth HID のリンクが作られなかった。したがって D5 の受入条件を有線と同じパス名にはしない。毎接続後、`Uniq=98:b6:e9:4a:87:92` で現在の `eventN` を再検出する。

## ゼロからの接続手順

Jetson 通常ターミナルで次を順に実行する。いずれかが失敗したら、インストールやドライバ変更をせず、その出力で止める。CAN、モーター電源、T265、ONNX は接続しない。

```bash
systemctl is-active bluetooth
bluetoothctl show
```

`active` と Bluetooth アダプタ情報が得られた場合だけ、次のとおり登録をいったん削除してから新規に接続する。`remove` の対象はこのコントローラーの登録だけである。

```bash
bluetoothctl
```

`bluetoothctl` の中で順に入力する。

```text
disconnect 98:B6:E9:4A:87:92
remove 98:B6:E9:4A:87:92
power on
agent on
default-agent
pairable on
scan on
```

Switch 2 Pro の SYNC ボタンを少なくとも1秒長押しし、`Device 98:B6:E9:4A:87:92 Pro Controller` が表示されたことを確認する。別の無名機器や周囲の機器には接続しない。次を順に入力する。

```text
pair 98:B6:E9:4A:87:92
trust 98:B6:E9:4A:87:92
connect 98:B6:E9:4A:87:92
info 98:B6:E9:4A:87:92
scan off
quit
```

`info` で `Paired: yes`、`Trusted: yes`、`Connected: yes`、`Icon: input-gaming`、Human Interface Device UUID を確認する。`ServicesResolved: yes` が接続時に表示されることも確認する。

## 現在の入力イベントの解決

Bluetooth を再接続するたびに、次を実行する。`eventN` の番号は固定しない。

```bash
grep -A 6 -B 2 'Uniq=98:b6:e9:4a:87:92' /proc/bus/input/devices
```

出力内の `Handlers=js0 eventN` の `eventN` を使う。`Pro Controller`、`Uniq=98:b6:e9:4a:87:92`、`eventN` が揃わなければ D5 不合格として止める。

## 50 Hz 乾式試験

上で確認した現在の `eventN` を `pad_probe.py` の `--device` に渡す。以下は実測時の `event7` の例であり、次回接続時に番号を再確認する。USB用の既定パスは使わない。

```bash
~/.venvs/controller-d5/bin/python /home/wan-pbl-2026/Downloads/pad_probe.py --device /dev/input/event7 --confirm-base-mapping --x-sign -1 --y-sign -1 --duration 60
```

確認する順序は、有線直結時と同じである。

1. 中立で約10秒、約20 ms周期で `(0, 0, 0)` が出続ける。
2. 左スティック前後左右で、前=`+vx`、後=`-vx`、右=`-vy`、左=`+vy`、`wz=0` が画面とCSVで一致する。
3. コントローラーの電源断またはBluetooth切断でプローブが入力切断として終了する。CAN送信は行わない。
4. 再接続後に上の `grep` で `eventN` を再検出してからプローブを新規起動し、最初はゼロ指令になる。

既存プローブは切断時に終了する設計である。入力途絶に対するゼロ指令継続と安全停止は D8/D9 の受け手側で実装・確認するものであり、このD5試験には含めない。

## D5 の合格と次の分岐

Bluetooth 接続、MACで照合した現在の入力イベント、上の4項目がすべて通れば、D5 は実運用経路で完了と記録する。D8 の入力境界へ接続する前にも、同じ Jetson・同じ無線経路で `eventN` を再確認する。

Bluetooth サービスが停止中、ペアリング不能、安定パスなし、入力途絶、または50 Hz試験のいずれかが不合格なら、D5 は未完了のままとする。無断のパッケージ導入・ドライバ変更・CAN/ONNX/T265/モーター統合には進まない。
