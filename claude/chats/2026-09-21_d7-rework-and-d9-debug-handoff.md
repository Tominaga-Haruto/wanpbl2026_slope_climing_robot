# 2026-09-21 D7再実施とD9デバッグ引継ぎ

## やったこと

- T265とUSB2CAN V3.3を同時接続したD9-1で、T265・ch=0/ch=1・10軸の受信を確認した。一方で、`gs_usb`のreset/openが初回に失敗すること、および成功後でもPython上のch=0/ch=1列挙が左右で入れ替わることを実測した。
- `C:\Users\harut\Connect2USB2CAN\d7_origin_console.py`、`ver9_d8_sender.py`、`ver9_jetson_deploy.py`は、固定chではなく、そのプロセスで受信したモーターIDからID→送信chを確定する実装へ変更済み。open失敗時はCANを送らず1.5秒後に1回だけ再試行する。
- 既決の機械ゼロ姿勢でD7を行い、全10軸の直後が0°だった。その後電源断・物理移動・姿勢復帰後、AK80-9の`0x21=-168.2°`、`0x2B=-76.9°`、`0x2A=-80.3°`、`0x22=+81.6°`を確認した。AK10-9は数度のずれだった。
- CubeMars公式現行manualと製品仕様を再確認した。`kind=0`は電源断で消える一時原点、`kind=1`はデュアルエンコーダ機種だけの恒久ゼロである。AK80-9 V3.0はSingle、AK10-9 V3.0はDualである。

## 決めたこと・分かったこと

- 過去ログの`origin sent kind=1`は、コードが一時原点を誤送信したものではない。しかしAK80-9には公式仕様上の恒久原点を作れない。AK80が4台あるため、全身の電源断後原点を成立させることはできない。
- D9/D10の現実的な前提は、**電源ON → 機械ゼロ姿勢 → D7の`o`（kind=0）を全10軸 → `scan 3`で10/10・err=0・0°付近 → 主電源を切らず、姿勢・配線を変えずD9**である。D7後に電源を切ったら、次のD9前に最初からD7を行う。
- AK10の「数度ずれ」はDualであることと整合するが、全身の恒久原点の証拠にはしない。AK10だけの保持精度を確認したい場合は、別途1台を固定姿勢で電源断前後比較する。
- USB物理ch番号に左右の意味を与えない。関節IDと左右対応は固定、ID→chは各プロセスの受信結果で決める。

## D7をやり直す手順

1. 吊り/棒支持、非常停止担当、機械ゼロ姿勢を確認する。主電源ON後、10軸のフィードバックが来るまで送信しない。
2. `py -3.13 C:\Users\harut\Connect2USB2CAN\d7_origin_console.py` を実行し、`scan 3`。10 ID、`err=0`、新鮮なfeedbackを確認する。reset/open失敗時の1回再試行は送信なし。二つのchが左右と逆でも異常ではない。
3. `d7_棒支持_全関節原点設定_実験手順.md`の順に、全10軸へ`o 0x..`→確認文字列→`s 0x..`を行う。これは`kind=0`であり、軸を動かす指令ではない。
4. 最後に`scan 3`で10軸すべて0°付近・`err=0`を確認する。ここからD9終了まで主電源を切らない。

## D9の次の停止点

1. まず`d9_1_usb_t265_dualcan_受信実験手順.md`だけを実施する。T265同時接続で、送信なし・新規プロセス2回とも10/10軸が受信できるかを確認する。
2. 受信が不安定ならMITを送らない。ログと、各回のID→ch結果を保存する。
3. D9のMIT送信器は開始前に10軸の新鮮なfeedbackを要求し、原点から45°超の軸があれば送信を中止する。D7直後の同一通電だけで先へ進む。

## 公式根拠

- CubeMars, AK Series Module Driver Manual V1.0.17, §5.1.6: `0` = temporary origin (lost on power failure)、`1` = permanent zero point (**dual encoder models only**)。https://www.cubemars.com/images/file/20250522/1747899365958473.pdf
- CubeMars, AK80-9 V3.0 product specification: Number of encoder = 1、comparison table: AK80-9 V3.0 = Single / AK10-9 V3.0 = Dual。https://www.cubemars.com/product/ak80-9-v3-0-robotic-actuator.html

## 更新した場所

- `d7_棒支持_全関節原点設定_実験手順.md` — D7を起動中原点として明記し、公式根拠を追記。
- `d9_吊り10軸MIT実験手順.md` — D7直後の同一通電をD9の必須条件に設定済み。
- `motor_can_findings.md`、`deployment_roadmap.md`、`project_handbook.md`、`README.md` — AK80恒久原点不可、D7再実施、D9ブロック状態を反映。

## 次チャットへの開始文

「`chats/2026-09-21_d7-rework-and-d9-debug-handoff.md`と`d9_1_usb_t265_dualcan_受信実験手順.md`を読んで。D7は同一通電で再実施済み/これから実施する。MITはまだ送らず、T265同時接続でUSB2CANの送信なし10軸受信を2回判定したい。」
