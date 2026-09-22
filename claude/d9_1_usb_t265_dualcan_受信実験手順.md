# D9-1: T265＋USB2CAN同時接続・両ch受信（送信ゼロ）

## 目的

T265を接続したまま、USB2CANのch=0とch=1を**毎回同時に受信できるか**を確認する。MIT、原点設定、位置・トルク指令、ONNX、コントローラーは使わない。

現在は、T265接続時の`gs_usb` resetがランダムに失敗する。成功時にもPython上のch=0/1の列挙は固定でなく、左右が入れ替わりうる。これは送信経路を固定chで持つ限り不合格である。関節IDは固定し、各プロセスで10軸を受信してIDごとの経路を確定する。

## 実装上の前提

- `d7_origin_console.py` はUSB2CANの各interfaceを開くときに、`gs_usb` backendがUSB resetを行うため、chごとのopen結果とscan結果をログへ残す。
- `d9_usb_inventory.py` はUSBデバイスを列挙するだけで、CAN start/reset/送信をしない。
- `robot_joint_map.py`は関節IDの唯一の正本であり、USB chを固定しない。D7は全IDが一意に受信できた場合だけ、そのプロセスに限るID→ch経路を確定する。経路確定前は原点・MIT・方策送信をしない。

## 中止条件

異音、振動、支持ずれ、ケーブル干渉、`err!=0`、または受信が欠けた場合は主電源をOFFにする。PC操作で復旧しようとしない。この実験でCAN送信はゼロである。

## 1. 通電前のUSB列挙

主電源はOFFのまま、T265とUSB2CANを接続する。T265はUSB2CANと別の物理USBポートへ直結し、同じハブ・延長器には接続しない。

ノートPCのPowerShellで実行する。

```powershell
cd C:\Users\harut\Connect2USB2CAN
.venv310\Scripts\python.exe d9_usb_inventory.py
```

判定:

- `gs_usb_devices` が2件、T265が1件表示されること。
- この段階ではCANをstart/resetしない。失敗しても主電源はONにしない。
- JSONの絶対パスを記録する。

## 2. 両chの受信だけを確認する

支持・電源遮断担当・ケーブル干渉なしを確認してから主電源をONにする。3秒間はPC操作をせず、異常があれば主電源をOFFにする。

同じPowerShellで実行する。

```powershell
py -3.13 d7_origin_console.py
```

表示後に、次だけを入力する。

```text
scan 3
q
```

`o`、`s`、MIT送信、方策送信は入力しない。終了後は主電源をOFFにする。

## 3. 判定

新しいプロセスで上の手順2を**2回**実施する。各回で以下を満たす場合だけ合格:

- 10軸すべてを受信し、D7が`OK: 登録済み10軸を受信し、このプロセスの送信経路を確定しました。`と表示すること。固定chと一致することは要件にしない。
- 10軸すべてで `err=0`、`age <= 0.3 s`。
- D7ログに `open OK ch=0`、`open OK ch=1`、各chの`scan`結果が残る。
- T265を接続したままで、初回・2回目とも条件を満たす。

初回だけ片ch、USB resetエラー、または再起動で結果が変わる場合は不合格。MIT送信へ進まない。

## 次チャットへ渡すもの

- `logs\d9_usb\inventory_*.json`
- 2回分の `logs\d7_origin\session_*.txt`
- 各`scan 3`の画面写真
- T265とUSB2CANをどの物理USBポート・ハブ・延長器へ接続したか

次チャットはこの結果を見て、USB経路変更、D7コンソールのopen方式変更、またはUSB2CAN backend変更を選ぶ。D9のMIT送信は判断対象外である。
