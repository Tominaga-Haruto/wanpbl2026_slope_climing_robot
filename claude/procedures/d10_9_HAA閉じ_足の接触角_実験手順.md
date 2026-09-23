# D10-9: HAA を閉じて、足が当たる角度を測る（吊り・方策なし）

> 作成 2026-09-23。根拠は `../reports/2026-09-23_d10-8_result.md`。
> 送信器 build **`D10_9_HAASWEEP_20260923_1500`**（`.bak_20260923_haasweep` あり、テスト 138本 OK）。
> 異音・接触・支持ずれ・エラー・中止表示が出たら、PC を操作する前に**主電源を切る**。

## なぜやるか

- シムの方策は、両脚の HAA を −13.5〜−16.4°に保って歩きます。URDF ではこのとき足首どうしの間隔は約 18 cm で、シムでは足は当たりません（自己衝突あり）。
- D10-8 では、URDF 上の間隔が 24〜29 cm（HAA −4〜−9°）のところで、実機の足が当たりました。
- 床に下ろす前に、**実機の足が HAA 何度で当たるか**をログで決めます。方策は動かしません。

## 何が変わったか

1. **`--haa-close-deg D` を追加しました（`--stand-only` 専用）。** 流れは次のとおりです。
   - 初期姿勢へ ramp（`--ramp-seconds`）
   - 初期姿勢で保持（`--stand-seconds`）
   - **両脚の HAA だけを 2°/s で内側（負）へ −D°まで閉じる**
   - 最後に 2 s 保持
2. **当たったら自動で止めます。** 脚が目標より 4°以上遅れた状態が 10 tick（0.2 s）続いたら「止められた」とみなします。
   - そのとき `HAA CONTACT` を表示します。
   - 両 HAA の目標を、脚がいま居る角度に固定します。足を押し付け続けることはありません。
   - 自由な脚は自重で目標より内側に垂れるので（D10-8 で −1〜−5°）、「遅れ」は何かに止められたときにしか出ません。
3. **`--analyze` に `HAA SWEEP` の節を足しました。** 軸ごとに、止められた角度（`BLOCKED at feedback …`）か `NOT blocked` を出します。
4. 変えていないもの: 関節符号、中止値（`--gravity-limits` の表）、速度中止、stale、原点 45°、Kp/Kd。方策の run は D10-8 と同じ動きのままです。

## 見方の目安（URDF、初期姿勢で両脚の HAA だけを変えたとき）

| HAA（両脚） | 0° | −4° | −8° | −10° | −12° | −14° | −16° |
|---|---:|---:|---:|---:|---:|---:|---:|
| 足首の間隔 | 32.6 cm | 28.5 | 24.4 | 22.3 | 20.2 | 18.1 | 15.9 |

シムの歩行は 17.9〜18.9 cm（HAA −14〜−16°相当）です。

## 共通の事前条件（毎回）

D10-8 と同じです。

1. 機体を吊ります。電源を切る担当が主電源に手を置いておきます。
2. 電源は片脚に1台ずつつなぎ、GND を共通にします。電流制限のつまみは最大にします。**各 run で電源の電流表示の最大値を記録します。**
3. `scan 3` → 基準姿勢で脚を持ったまま `oa` → `scan 3` で全軸 `+0.0deg` を確認します。
   - **`oa` の直前、脚を基準姿勢で持った状態で、左右の足裏の内側どうしのいちばん近いところの隙間を定規で測ってください（cm）。** これが HAA 0°での実機の値です。
4. 最初の `RAMP progress: 0/10s` で手を離します。
5. 起動した直後の行を確認します。
   - `ver9_d8_sender build=D10_9_HAASWEEP_20260923_1500`
   - `JOINT SIGNS`（5軸が −1）
   - `HAA SWEEP planned: ... -16.0deg at 2deg/s (8.0s)`
6. **正面から動画を撮ります。** 足のあいだに定規かメジャーを置くと、あとで隙間が読めます。
7. CSV の名前は run ごとに変えます。電源を切ったら、手順3からやり直します。

実行フォルダはすべて `C:\Users\harut\Connect2USB2CAN` です。

## R0: 送信なし（承認は不要）

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --preflight --all-axes --stand-seconds 2 --stand-only --haa-close-deg 16 --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --csv logs\d10_9_r0_preflight_a.csv
```

見るもの:
- `HAA SWEEP planned`
- `ALL-AXES PRE-ARM GATE: ok`
- `PREFLIGHT complete: CAN transmit count is zero.`

## R1: 初期姿勢 → HAA を −16°まで閉じる（要承認・動画を撮る）

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --all-axes --gravity-limits --stand-seconds 2 --stand-only --haa-close-deg 16 --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --ramp-seconds 10 --csv logs\d10_9_r1_haa_sweep_a.csv
```

- 全体で約 22 s です（ramp 10 s、保持 2 s、閉じる 最大 8 s、最後の保持 2 s）。
- `HAA SWEEP progress: …` が1秒ごとに出ます。**足が触れた瞬間に声に出し、そのときの表示を覚えておいてください。**
- `HAA CONTACT` が出たら、脚はその場で止まります。**足どうしが押し合い続けていたら、主電源を切ってください。**
- 終わったら（`STAND ONLY: ... zero MIT`）、脚は力が抜けて垂れます。

## R2: R1 の繰り返し（要承認）

R1 で当たった場合だけ、同じコマンドを CSV 名だけ変えて実行します。角度が再現するかを見ます。

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --all-axes --gravity-limits --stand-seconds 2 --stand-only --haa-close-deg 16 --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --ramp-seconds 10 --csv logs\d10_9_r2_haa_sweep_b.csv
```

## 解析（run のたびに・承認は不要）

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --analyze logs\d10_9_r1_haa_sweep_a.csv
```

R2 は CSV 名を `d10_9_r2_haa_sweep_b.csv` に差し替えます。`HAA SWEEP (D10-9)` の節が出ます。

## 判定（run のあとで基準を変えない）

「当たった角度」は、`--analyze` の `BLOCKED at feedback` の値（両脚のうち浅い方）と、本人が「触れた」と言った時点の表示の、浅い方を使います。

| | 所見 | 意味 | 次 |
|---|---|---|---|
| **1** | −14°まで当たらない（`NOT blocked`、目視でも触れない） | 足の形・間隔はシムと合っている。D10-8 の接触は、吊りで出た HR の内向き（LR_HR −10°。シムの歩行は −1〜+4°）か振り回しによるもの | 床上の手順書を書く（slew の扱い、電流中止値を含む） |
| **2** | −10〜−14°で当たる | シムの歩行姿勢の端で当たる。床では時々ぶつかる | 当たった部位を写真で報告。WRS 機で足のメッシュどうしの距離を HAA ごとに計算し、差を探す |
| **3** | −10°より浅いところで当たる | この方策の歩き方は、この機体では足がぶつかる。モデルと実機の足・股の幅、または原点の取り方がずれている | 床に進まない。モデルの修正か、足の間隔を守る再学習を検討する |
| **4** | R1 と R2 で当たる角度が 3°以上ちがう | 原点（手で持った基準姿勢）が回ごとにずれている | 原点の支持治具（`../CONTEXT.md` の優先順位2）を先に作る |
| **5** | `current abort` | 中止した軸と電流を報告する | **上限を上げない** |
| **6** | 電源の表示が 1台 10 A に近づく、または電圧が落ちる | 電源が足りない | 電源構成を見直す |

## 許可／禁止

- **許可（承認は不要）:** R0、`scan`・`oa`・`--preflight`・`--analyze`。
- **要承認:** R1・R2。
- **禁止:**
  - run の途中で脚を触ること（足が押し合い続けたときは、触らずに主電源を切る）
  - `--haa-close-deg` を 16 より大きくすること（プログラムも拒否します）
  - Kp/Kd・トルク欄を上げること
  - 速度中止・stale・原点 45° を緩めること
  - `--gravity-limits` の表を引き上げること
  - 方策の run（この手順では方策は回さない）
  - 同じ名前の CSV に上書きすること
  - **床上で run すること**

## 次のチャットに貼るもの

- 各 run の画面ログ全文（`HOLD POSE RESULT` / `HAA SWEEP progress` / `HAA CONTACT` / `HAA SWEEP (D10-9)` / `AXIS SNAPSHOT` / 中止行）
- `--analyze` の出力
- CSV 名
- `oa` 直前に測った、足裏の内側どうしの隙間（cm）
- 触れたときの表示の角度（声に出したもの）、**どこが当たったか**（足裏の縁・つま先・かかと・すね・モーター）の写真
- 動画
- 電源2台それぞれの電流の最大値（D10-8 から未報告）
