# 2026-09-19 motor_console_ver8_2 二機同時試験

## やったこと

- `motor_console_ver8.py` を丸ごと土台にした `Connect2USB2CAN/motor_console_ver8_2.py` を作成した。ver8の全コマンドを保ち、二機用に `dualpreview` と `dual` を追加した。
- 対象は固定: ID34（上位機22番、AK80-9）とID18（上位機12番、AK10-9）。`dual` は各50 Hz周期内で `0x822`、`0x812` の順にMITフレームを送る。
- `dual` の終了・中止、`x`、`q`、Ctrl+C、コマンド例外では、両IDへ零MIT指令を3回送る。
- `--dry-run --pos22 0.2 --pos12 0 --seconds 2` のフレーム表示、`--sim` 内の `dualpreview 0.2 0`、構文検査を通した。実機の初回起動はUSB2CANが0台検出で、MITフレームを送る前に停止した。

## 実験手順（打つコマンドだけ）

### 0. USB2CANを認識させる

USB2CANを接続してから、次を起動する。

```powershell
cd C:\Users\harut\Connect2USB2CAN
py -3.13 motor_console_ver8_2.py
```

`CAN 接続に失敗: Cannot find device 1. Devices found: 0` なら、この時点で終了する。モーターには送っていない。USB2CANの接続・給電・ドライバーを直してから、同じ起動コマンドをやり直す。

### 1. 二軸の状態だけ確認する

コンソールの `>` に、順に入力する。

```text
log on
scan 3
id 34
model AK80-9
s
id 18
model AK10-9
s
```

次へ進む条件は、ID34とID18の両方が表示され、`err=0`、速度がほぼ0、異音なしであること。どちらか一方でも満たさなければ `q`。

### 2. 安全姿勢をこの試験のゼロにする

二軸が干渉しない安全姿勢にあることを目で確認してから、次を入力する。

```text
id 34
o 0
id 18
o 0
```

`o 0` はモーターを動かさず、今の姿勢をMIT位置0 radにする。この二機試験の間だけ、`dual` の目標角はこのゼロからの角度として扱う。

### 3. 送信せず二機フレームを確認する

```text
dualpreview 0 0
dualpreview 0.2 0
```

2行目は「ID34だけ+0.2 rad、ID18は0 rad」のフレームを表示するだけで、CANには送らない。表示が `ID=34 (0x22) AK80-9`、`ID=18 (0x12) AK10-9` の順であることを確認する。

### 4. 最初の実機試験: 二機ゼロ保持

```text
dual 0 0 2
```

成功なら `完了: ... 周期 / 最大送信skew ... / CSV: logs\\v7_YYYYMMDD\\dual_HHMMSS.csv` と表示される。二機ともゼロ姿勢を2秒保持する。

次のどれかでは自動中止して両方へ零MIT指令を送る: フィードバック0.3秒途絶、`err!=0`、電流1.0 A超、速度100 deg/s超、開始位置から15 deg超。異音・想定外の動き・急な発熱なら、表示を待たず電源OFF。

### 5. 小さい同時移動: 段階4が無中止のときだけ

正方向と干渉しない目標が分かっている場合だけ、操作者が確認した値を入れる。例は**構文例**であり、符号・値を推測して実行しない。

```text
dualpreview 目標22rad 目標12rad
dual 目標22rad 目標12rad 2
```

目標は各軸ともこの試験のゼロから±0.20 radまで、送信は最大3秒。Kp=1.0、Kd=0.5は固定である。

### 6. 終了

```text
x
q
```

どちらもID34とID18の両方へ零MIT指令を送る。非常停止は常に電源OFF。

## 決めたこと・分かったこと

- 二機同時試験は、一度だけの短いゲートとして行う。共有CAN・両IDの受信・停止処理・右脚の膝/足首の干渉を確認する。
- 二台の送信負荷だけでは、10台＋推論の50 Hz周期（D3）や全身電源負荷を評価できない。`dual 0 0 2` が無中止なら、細かい条件振りはせずver9の10台乾式・周期試験を優先する。
- 今回の `Devices found: 0` はUSB2CAN未検出であり、ID・CANチャンネル・MITフレームの不具合ではない。

## 手を動かした場所

- `C:\Users\harut\Connect2USB2CAN\motor_console_ver8_2.py`
- `claude/chats/2026-09-19_motor-console-ver8-2-dual-test.md`

## 積み残し・次にやること

- USB2CANをOSが認識する状態にして、手順4の `dual 0 0 2` を1回実行する。
- 結果のCSVと画面ログを確認し、実測結果だけを `motor_can_findings.md` に反映する。
