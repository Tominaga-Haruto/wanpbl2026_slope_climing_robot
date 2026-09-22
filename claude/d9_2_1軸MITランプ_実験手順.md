# D9-2: 1軸MITランプ実験手順

> 対象はD9-2の**1軸だけ**である。片脚・全身へは進まない。異音、接触、支持ずれ、エラー、または表示された安全中止では、PC操作より先に主電源をOFFにする。

## 目的

原点から最初の方策目標へ一気に跳ばず、指定秒数で線形補間して1軸だけ送信できることを確認する。`0x1C`の直近preflight目標は`-1.6deg`であり、6秒ランプなら目標の傾きは約`-0.27deg/s`である。これは全身の安全性を示さない。

## 開始条件

- 機体は吊り支持済みで、電源遮断担当が主電源に手を置いている。
- D7の`oa`を同じ通電中に実行し、全10軸が`err=0`かつ`pos=+0.0deg`である。
- 直後の`--preflight`が10軸経路と初期目標を表示して終了している。
- 選択する1軸に機械的な干渉がない。

## 実行

1. 主電源をONにし、数秒はPC操作せず支持・配線・異音がないことを確認する。
2. 次の1行を実行する。`--motor-id 0x1C`以外のMITフレームは送らない。

```powershell
cd C:\Users\harut\Connect2USB2CAN
.venv310\Scripts\python.exe ver9_d8_sender.py --arm --motor-id 0x1C --ramp-seconds 6 --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --duration 2 --csv logs\d9_one_axis_0x1c.csv --vx 0 --vy 0 --wz 0
```

3. 次の表示を確認する。`desired`は方策が算出した値、`sent`は安全な傾きに制限して実際に送った値である。両者が違うことは異常ではない。

```text
ARM active: motor=0x1C; ramp=6s; then policy=2s
RAMP progress: 0/6s; ...
RAMP complete: CAN tx=...; entering policy hold.
POLICY complete: CAN tx=...; sending selected-axis zero MIT cleanup.
```

## 中止と判定

- `motion/current abort`、`stale feedback`、`motor error`、異音、接触、支持ずれなら主電源OFF。再試行しない。
- 完走しても片脚・全身へは進まない。
- 完走時はCSVの`stage`が`ramp`→`policy`、`sent_motor_id`が全行`0x1C`であることを確認する。`requested_target_rad`は制限後の要求値、`wire_target_rad`は量子化してMITフレームへ入れた位置、`feedback_position_rad`・`feedback_velocity_rad_s`・`feedback_current_a`が受信した実測値である。
- `desired_target_rad`が符号反転しても、`requested_target_rad`はランプ勾配を超えて跳ばないことを確認する。
- 方策ランプの`TRACKING`は、初期ランプ要求角の50%以上を追従しなければ`tracking abort`である。送信数の完走や0.1degだけの変化を成功扱いにしない。目標値・ゲインをその場で増やさず、CSVと動画を渡して次の1軸試験を決める。

## 次に渡すもの

- `logs\d9_one_axis_0x1c.csv`
- 画面ログと、支持・0x1C・周辺ケーブルが見える動画
- 実行中の異音・動き・温度・abort有無

## 追従なし後の小実験（0x1Cのみ）

直近の方策ランプは量子化後 -2.12deg、最大 |電流|=0.33A で位置0.00degだった。次は方策とT265を外し、同じD9ゲインで相対 -2.5deg だけを確認する。これはゲイン・トルクを増やす試験ではない。

開始条件は、吊り支持、遮断担当、D7 `scan 3`で全10 IDが新鮮・`err=0`、0x1C周辺に干渉がないことを全て満たすこと。完全吊り下げで他軸が原点から外れている場合、**static probe のためだけに `oa` を実行しない**。このコマンドは0x1Cだけへ現在位置からの相対指令を送り、他9軸にはMITフレームを送らない。条件のどれかが欠ければ実行しない。

```powershell
cd C:\Users\harut\Connect2USB2CAN
.venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x1C --probe-target-deg -2.5 --ramp-seconds 6 --duration 2 --csv logs\d9_static_probe_0x1c.csv
```

- 異音、接触、支持ずれ、`motion/current abort`、`stale feedback`、`motor error`なら、PC操作より先に主電源OFF。再試行・値の増加はしない。
- `position tracking observed`は、0.1degだけでなく要求した相対角の50%以上を追従した場合だけ表示される。CSVと動画を保存して終了する。片脚・全身には進まない。
- `position stalled before target`なら、0x1Cの静止摩擦または機構負荷で目標の途中に止まった状態である。値を上げず、CSVと動画を渡す。
- `no position response and no meaningful current`なら、MITトルク応答が未確認である。値を上げず、配線・モード・個体状態の診断へ戻る。
