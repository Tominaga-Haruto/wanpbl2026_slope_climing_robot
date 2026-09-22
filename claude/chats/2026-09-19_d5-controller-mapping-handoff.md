# 2026-09-19 D5 controller mapping handoff

## やったこと

- `next_chat_d5_controller_mapping.md` の範囲で、`Connect2USB2CAN/controller/` にCAN・モーター・ONNX・T265・実デバイス読取を含まない速度コマンド境界を追加した。
- `fixed` と `controller` を同一の `CommandRecord`（source、timestamp、正規化スティック、`(vx, vy, wz)`、state、`unit_unconfirmed`）で出力する。
- 画面／CSVの乾式確認とpure functionのユニットテストを行った。CSVはGit管理外の`$env:TEMP`に出した。

## 決めたこと・分かったこと

- Hのvelocity commandは`(lin_vel_x, lin_vel_y, ang_vel_z)`で、学習時範囲は各`[-1, +1]`。物理単位は未確定。
- D5では`wz=0`固定。固定値は範囲外をクリップせず拒否する。
- controller入力は正規化済みの`ABS_X`/`ABS_Y`を将来受ける境界だけを作った。base座標への対応・符号は未確定なので、`mapping_confirmed=False`では非ゼロ入力でも必ず`(0,0,0)`・`mapping_unconfirmed`となる。
- `fixed (0.25, -0.50, 0)`の画面とCSV一致、未確定controller入力`(0.8, -0.6)`のゼロ出力、範囲外`vx=1.01`の拒否を確認した。ユニットテスト5件はPASS。

## 手を動かした場所

- `C:\Users\harut\Connect2USB2CAN\controller\command_source.py`
- `C:\Users\harut\Connect2USB2CAN\controller\command_probe.py`
- `C:\Users\harut\Connect2USB2CAN\controller\test_command_source.py`
- `claude/README.md`：チャット記録はユーザーから「引き継ぐ」と言われたときだけ作成する運用へ更新。

## 次にやること

1. M7はD5の`fixed`経路を使い、CANなしでONNX golden乾式ループへ接続する。ただしD5自身はONNXをimportしない。
2. 左スティックを実際に読む段階では、既存`controller/pad_probe.py`でJetson上の入力・50 Hz・切断挙動を乾式確認する。D5の部品へ接続する前に、実行Pythonと`evdev`の有無を確認し、無断インストールをしない。
3. base座標の正本と照合し、ユーザー確認後にだけ`ABS_Y→vx`と`ABS_X→vy`の対応・符号を一度定義する。それまでは`--mapping-confirmed`を使わない。
4. その後の統合（デッドマン、途絶停止、変化率制限、ver9、CAN）は別段階であり、D5の変更範囲外。
