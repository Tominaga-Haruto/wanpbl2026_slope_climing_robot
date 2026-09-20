# T265取付け（0b-2）: CAD位置と既存の座標確認の整理

日付: 2026-09-20

## 実施したこと

- `deployment_03_t265_mount_instruction.md`、`realsense_t265.md`、`deployment_roadmap.md` を、ユーザーが提示したOnshape CAD寸法に基づいて更新した。モーター通電・CAN送信・T265への接続はしていない。
- 正面をwaist前面の長方形開口が向く方向と定義した。T265はレンズ前向き・水平で固定する。
- IntelのT265データシートで、tracking centerが左右イメージャの中点、イメージャ間隔が64.00 ± 0.15 mm、tracking centerが背面から5.95 mmであることを確認した。
- CADの開口左端からレンズ中心までが13.000 / 77.000 mmで差が64.000 mmのため、tracking centerは開口左端から45.000 mmと確定した。

## CAD外形での位置

| 基準 | tracking center候補 |
|---|---:|
| waist右端から左向き | 234.000 mm |
| waist下辺から上向き（開口上下中央） | 67.750 mm |

この値はwaistの外形基準であり、base座標の`R_OFFSET`ではない。`R_OFFSET`には、base原点への変換と前後（奥行き）位置を固定後に測ってから入れる。

## 既存記録と次の物理作業

- `C:\Users\harut\Connect2USB2CAN\t265\logs\t265_20260917_213011.csv` ほかに、前向き・水平での静止・前進・左移動・前下げ・反時計回りの確認記録がある。
- 同じ向きで剛固定できた場合、今日の手順3〜5は再実施しない。向きが少しでも異なる、または固定後に動いた場合だけ、同じ5動作を再取得して`R_CB`を確認する。
- 取付け後に残すものは、正面・側面の写真、固定具の写真、base原点からtracking centerまでの3軸値、奥行きの実測値である。

## 参照

- Intel, *RealSense Tracking Camera T265 Datasheet*, §3.1 / §4.2 / §4.3.
- RealSense SDK, `doc/t265.md` のsensor origin and coordinate system。

## 引継ぎ書

- 実機取付け、`R_OFFSET`実測、取付け後のconfidence／途絶試験、ver9に渡すまでの残作業を `next_chat_t265_mount_handoff.md` に分離した。
- 既存の5動作CSVは取付け姿勢が同じ場合に再利用し、再取得は向きが異なる場合だけとした。モーター通電・CAN送信はこの引継ぎの範囲外である。
