# 2026-09-20 D5 延長経路のUSB設定失敗
README.mdは最低限見て。
## やったこと

- Jetson通常ターミナルで、Switch 2 Proを直結した場合のD5乾式確認を完了した。`045e:028e`、`/dev/input/by-id/usb-045e_XBOX_360_For_Windows_000000000001-event-joystick`、`event7`で、50 Hzの中立・前後左右・抜線・再接続をCAN等未接続で確認済み。
- 実運用に必要な変換ケーブル経由で同じ試験を試したところ、安定パスとゲームパッドの`/dev/input`が消えた。
- `lsusb`、`lsusb -t`、`lsmod`、`journalctl -k`で、変換ケーブル経由ではPro Controller `057e:2009`が列挙する一方、`usb 1-2.3: can't set config #1, error -32`と切断・再列挙を約5秒ごとに繰り返すことを確認した。

## 決めたこと・分かったこと

- USBデータは一部届いているが、失敗はHIDや`evdev`より前のUSB設定段階である。Bluetoothのペアリング／ドライバ調査を主経路にして解決しようとはしない。
- 実用上の第一候補は、直結時と同じ`045e:028e`として安定認識するUSBデータ対応の延長ケーブルまたは延長アダプタである。候補の判定は、Jetson通常ターミナルの`lsusb`で`045e:028e Microsoft Corp. Xbox360 Controller`が出ること。
- したがってD5は、直結でのソフト・乾式確認は済んだが、実運用の延長経路では未完了である。CAN、ONNX、T265、モーターへは接続していない。

## 手を動かした場所

- ノートPC側では `deployment_roadmap.md`、コントローラー指示書、現在地、README索引を実運用経路未完了へ訂正した。
- Jetson側での変更・コード編集・CAN送信・モーター操作はない。`~/.venvs/controller-d5`と既存の`/home/wan-pbl-2026/Downloads/pad_probe.py`は直結時試験のまま。

## 積み残し・次にやること

1. USBデータ対応の延長経路を用意し、Jetson通常ターミナルで`lsusb`を実行する。`045e:028e`が出なければD5試験に進まない。
2. `045e:028e`と`/dev/input/by-id/usb-045e_XBOX_360_For_Windows_000000000001-event-joystick`が安定して見えたら、既存の`pad_probe.py`で中立・前後左右・抜線・再接続の乾式試験を再実施する。
3. D5を実運用構成で完了するまで、ver9、CAN、ONNX、T265、モーターとコントローラー入力を統合しない。
