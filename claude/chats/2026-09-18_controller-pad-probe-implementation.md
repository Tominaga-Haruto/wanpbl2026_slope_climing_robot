# 2026-09-18 controller pad probe 実装

## やったこと
- README.md、controller_next_chat_briefing.md、controller_prep_briefing.md、実機側の引き継ぎを読み、コントローラー単体の乾式部品を実装可能か整理した。
- C:\Users\harut\Connect2USB2CAN\controller\pad_probe.py を追加した。Switch 2 Pro の安定した evdev パスを50 Hzで読み、CSVと画面へ生値・正規化値・速度指令・状態を出す。
- CAN、モーター、ONNX、方策は import も送信もしていない。入力が200 ms来ないと timeout とゼロ指令を出す。

## 決めたこと・分かったこと
- 左右・前後の符号は、WRSからの obs_contract.md の velocity_commands 契約を確認するまで未確定である。したがって既定では速度指令をゼロにし、--confirm-base-mapping を明示したときだけ表示用の非ゼロ指令を作る。
- 初期上限は vx ±0.3 m/s、vy ±0.2 m/s、wz=0。方策・CANを接続する ver9 は、ONNX、golden npz、観測契約、アクチュエータ表、SHA256を受領してから着手する。

## 手を動かした場所
- C:\Users\harut\Connect2USB2CAN\controller\pad_probe.py
- C:\Users\harut\Connect2USB2CAN\controller\.gitignore
- py -3.13 controller\pad_probe.py --self-test と py -3.13 -m py_compile controller\pad_probe.py は合格。Jetson実機の evdev 読み取り・切断試験は未実施。

## 積み残し・次にやること
- Jetsonで使用するPython環境に evdev があるか確認し、未導入なら導入方針を決める。
- Jetsonで中立・最大値・50 Hz・USB切断を乾式試験する。
- WRSのデプロイパッケージを検品し、観測・関節順・ゲイン表を得てから ver9 を乾式実装する。
