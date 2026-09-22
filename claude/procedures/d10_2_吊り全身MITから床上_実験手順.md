# D10-2: 吊り全身MIT → 床上まで、1通電で一気に行く

> 作成 2026-09-22。根拠 `../reports/2026-09-22_d9-6_result.md`。**片脚MITは飛ばす**（ユーザー判断・時間制約）。
> 送信器 build **`D10_ALLAXES_20260923_0100`**。`--all-axes` を追加した（`.bak_20260922_allaxes` あり、テスト 58本 OK）。
> 異音・接触・支持ずれ・エラー・表示された中止は、PC操作より先に**主電源OFF**。

## 何をどこまで飛ばしたか（先に読む）

D9-6 で 0x1C・0x13・0x2B の3軸が判定 A（動く）。MITトルク経路も3本とも verified。**残り7軸を1軸ずつ測る工程と、片脚MITの工程を飛ばす。** 代わりに次で守る:

- **吊ったまま、ゼロ速度指令から始める。** R1 が通るまで床に下ろさない。
- **ramp 15 秒**で現在角から方策の初期目標へ入る。ステップ入力にしない。
- **duration は 2〜3 秒。** 長く回さない。
- **電流中止 1.0 A・速度中止 100°/s・stale feedback・原点45°の中止は全部生きていて、全10軸を見ている。** ゲインもトルク欄もこれらも上げない。
- **主電源に手を置く担当を必ず置く。** 中止は PC ではなく主電源。

飛ばしたぶんのリスク: **未測定の7軸のうちどれかが 0x1C 並みに重い**可能性がある。その場合 R1 で「その軸だけ目標に届かない」形で出る。R1 の判定表で拾う。

---

## 共通の事前条件（毎回）

1. 機体は**床から完全に離して吊る**（R3 以降を除く）。**電源遮断担当が主電源に手を置く。**
2. 通電後、D7 コンソールで `scan 3`。**10/10 受信・全 `err=0`・`age <= 0.3 s`** を確認する。
   - **0x2A（LR_HFE）を特に見る。** 2026-09-21 に `stale feedback 0x2A` で止まった実績がある。
   - どれかが原点から 45° を超えていると `origin/pre-arm pose abort` で止まる。その場合だけ同じ通電中に D7 の `oa` をやり直す。
3. 冒頭の `ver9_d8_sender build=D10_ALLAXES_20260923_0100` を確認する。違えば実行しない。
4. `ALL AXES: driving all 10 registered axes` の行が出ることを確認する。出なければ実行しない。
5. **CSV名は毎回変える。**

実行ディレクトリはすべて `C:\Users\harut\Connect2USB2CAN`。
方策パッケージは `C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999`。

---

## R0: 送信なしの確認（30秒）

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --preflight --all-axes --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --csv logs\d10_2_r0_preflight.csv --vx 0 --vy 0 --wz 0
```

`Initial policy targets (no MIT sent yet):` の10行を見る。**どれかの `delta` が ±30° を超えていたら実行しない**（原点がずれている）。`PREFLIGHT complete: CAN transmit count is zero.` で終わること。

---

## R1: 吊り・全10軸・ゼロ速度指令・2秒（本命。ここが通らなければ先へ行かない）

```powershell
cd C:\Users\harut\Connect2USB2CAN
.venv310\Scripts\python.exe ver9_d8_sender.py --arm --all-axes --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --ramp-seconds 15 --duration 2 --csv logs\d10_2_r1_hang_zero.csv --vx 0 --vy 0 --wz 0
```

1行版:

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --all-axes --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --ramp-seconds 15 --duration 2 --csv logs\d10_2_r1_hang_zero.csv --vx 0 --vy 0 --wz 0
```

15秒かけて方策の初期目標（既定角）まで入り、2秒だけ方策を回す。**ゼロ速度指令は「方策への速度要求がゼロ」であって「MIT目標がゼロ」ではない。脚は既定角へ動く。** 動画を撮る。

---

## R2: 吊り・全10軸・前進 0.2 m/s・3秒

R1 が合格したときだけ。**まだ床に下ろさない。** 空中で脚が歩く動きをするのを見る。

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --all-axes --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --ramp-seconds 15 --duration 3 --csv logs\d10_2_r2_hang_vx02.csv --vx 0.2 --vy 0 --wz 0
```

見るところ: 左右の脚が**交互に**振れるか。片脚だけ動かない軸が無いか。異音・引っ掛かりが無いか。

---

## R3: 床上・ゼロ速度指令・2秒（**別途ユーザー承認**）

R1・R2 が合格し、**ユーザーがログと動画を確認してから**。吊り紐は外さず、**荷重が抜ける程度にたるませて残す**（倒れ止め）。周囲 1 m を空ける。

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --all-axes --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --ramp-seconds 15 --duration 2 --csv logs\d10_2_r3_floor_zero.csv --vx 0 --vy 0 --wz 0
```

**足が接地しているので、ramp 中に機体が持ち上がる／崩れる。** ramp の 15 秒は目を離さない。

## R4: 床上・前進 0.2 m/s・3秒（**別途ユーザー承認**）

R3 が合格したときだけ。

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --all-axes --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --ramp-seconds 15 --duration 3 --csv logs\d10_2_r4_floor_vx02.csv --vx 0.2 --vy 0 --wz 0
```

---

## 中止

`motion/current abort`（1.0 A）、`speed abort`（100°/s）、`stale feedback`、`motor error`、`origin/pre-arm pose abort`、`repeat-probe abort`、異音、接触、支持ずれ、転倒の気配 ── いずれも**主電源OFF**。再試行しない。終了時は零MITが自動で送られるが、**電源遮断の代わりにはならない。**

## 事前に決めた判定（走らせる前にここを読む。走らせた後に基準を変えない）

`--analyze` は1軸用なので、R1〜R4 は **CSV と画面ログと動画**で読む。CSV は先頭軸（0x13）の行だけを持つ点に注意。

| | 所見 | 意味 | 次 |
|---|---|---|---|
| **1** | R1 が例外なく完了。10軸に意図しない大きな動きが無い。既定角付近で落ち着く | 全身MITが通った | **R2 へ。同じ通電中でよい** |
| **2** | R1 で `stale feedback 0x2A`（または他ID） | 受信が落ちている。方策以前の問題 | 主電源OFF。`procedures/d9_受信確認_実行シート.md` の送信なし確認へ戻る。USB/T265 の同時接続を疑う |
| **3** | R1 で `current abort` / `speed abort` | どれかの軸が想定外に負荷を受けている | 主電源OFF。**ゲインも中止値も上げない。** 画面ログの中止行にあるIDを1軸 probe に戻す |
| **4** | R1 は通るが、**特定の軸だけ目標に届かない** | 未測定7軸のどれかが 0x1C 並みに重い | その軸を1軸 probe（`--motor-id 0x**  --probe-target-deg`、最大角は軸ごと）で測る。床へ下ろさない |
| **5** | R2 で左右が交互に振れる | 歩容が出ている | ユーザー確認のうえ **R3（要承認）** |
| **6** | R2 で片側しか動かない／震える | 不感帯が歩容を壊している | 床へ下ろさない。実験11（friction スイープ）の結果と突き合わせる |
| **7** | R3 で崩れる・立てない | 静止姿勢を保持できない | 主電源OFF。R4 へ行かない。立位保持は不感帯かゲインの問題なので、実験11 の P3（stiffness 見直し）をユーザー判断に上げる |
| **8** | R4 で歩く | **床上デプロイ成功** | 動画とCSVを残す。距離・時間・指令を報告書へ |

## 許可／禁止

- **許可（承認不要）:** R0・R1・R2（吊り）。`scan`・`--preflight`・`--analyze`・文書更新。
- **要ユーザー承認:** **R3・R4（床上）。** 未測定7軸の1軸 probe。
- **禁止:** Kp/Kd・トルク欄・電流中止（1.0 A）・速度中止（100°/s）・`STATIC_PROBE_MAX_DEG` の増加。`--duration` を 5 秒超にすること。走行中に手で機体を支えること。同じCSV名で上書きすること。R1 を飛ばして R3 へ行くこと。

## 終わったら渡すもの

1. 各 CSV の絶対パス（上書きしていないこと）と画面ログ全文（`ALL AXES` / `Initial policy targets` / 中止行）
2. 動画（R1・R2 は必須。R3・R4 も）
3. `scan 3` の10軸の角度・温度・err（実行前）
4. 止まった場合は、止まった行そのものと、そのときの見た目
