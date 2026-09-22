# D9-2: 1軸MITランプ実験手順

> 対象はD9-2の**1軸だけ**である。片脚・全身へは進まない。異音、接触、支持ずれ、エラー、または表示された安全中止では、PC操作より先に主電源をOFFにする。

> **2026-09-22更新（停止中）:** 0x1C（LL_HR）は方策ランプを再実行しても、初期−0.6°→初期方策目標−5.8°の402フレームで位置・速度0.000°、最大|電流|0.74 Aだった。方策/T265を除いた相対−2.5° static probeも、最大|電流|0.40 Aで位置・速度0.000°だった。CAN経路、MIT量子化、方策は共通原因から外れ、**現行の実効PDトルクが吊り姿勢の0x1C負荷を越えられていない**。同じ二つの送信、ゲイン増加、目標拡大をしない。次の作業は無通電の機構確認だけである。根拠は`reports/2026-09-22_d9-0x1c-stall-analysis.md`。

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

## 追従なし後の原因分離（無通電のみ）

static probe はすでに完了した。`logs\d9_static_probe_0x1c.csv` は、0x1Cを−0.6°から−3.1°へ（相対−2.5°）8秒間・401フレーム送信し、位置・速度が全401行で一定、最大|電流|=0.40 Aだった。この結果は「MITトルク応答がない」ではなく、方策/T265を除いても負荷に対し位置ループが静止していることを示す。

次に許可されるのは、**主電源OFF・MIT送信なし**の目視／手回し確認だけである。吊り支持を維持し、0x1C（LL_HR）からリンク、スペーサ、ケーブル、反対脚／支持具までを確認する。接触、締結異常、ケーブル張り、支持具への干渉、期待方向への手動可動域を写真・動画に残す。無通電でも異常な抵抗、引っ掛かり、干渉がある場合は機械を修正してからD7へ戻る。手動確認で異常がなくても、D9を再送信しない。0x1C個体の静止摩擦・実効Kpを治具または負荷を除いた条件で測る診断案を別途レビューしてからにする。

この段階で禁止するものは、`--arm`、`--static-probe`、Kp/Kd・目標角・トルク欄の増加、片脚／全身MIT送信である。電源を再投入しても、この手順だけのためにD7 `oa`を実行しない。
