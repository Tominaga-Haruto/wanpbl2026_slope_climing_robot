# D10-4: 手を離した吊り保持の取り直しと、全軸 slew つきの吊り方策 run

> 作成 2026-09-23。根拠 `../reports/2026-09-23_d10-3_result.md`。
> 送信器 build **`D10_4_ALLSLEW_20260923_1200`**（`.bak_20260923_allslew` あり、テスト 83本 OK）。
> 異音・接触・支持ずれ・エラー・表示された中止は、PC操作より先に**主電源OFF**。

## 何が変わったか（先に読む）

D10-3 の R3・R4 は ramp を完走したのに、方策に切り替えた 1〜2 tick 目で落ちた。方策段階で slew が掛かっていたのが 0x1C だけで、**残り9軸が 20 ms で最大 45° 跳んだ**からである。今回の送信器は次のとおり。

- `--policy-slew-dps D`: 方策段階の**全10軸**の目標変化を D °/s に制限する。`--all-axes` の方策 run では**付けないと拒否される**。
- **プレアーム・ゲート**: 初期方策目標が |target| > 40° または |delta| > 30° の軸があれば、MIT を送る前に拒否する。preflight に `ALL-AXES PRE-ARM GATE: ok` か `would REFUSE` が出る。
- 停止時に `POLICY STAGE: N tick(s)` と `SLEW GAP` の表が出る。

**slew を掛けた run は歩容の再現ではない。** 方策が 1 tick で 8° 動かしたくても 20〜30 °/s（1 tick 0.4〜0.6°）しか送らない。今回見るのは「全身の方策ループが中止なしで 3 秒回るか」と「そのとき各軸がどれだけ電流を使うか」である。

## 共通の事前条件（毎回）

1. 機体は**床から完全に離して吊る**。**電源遮断担当が主電源に手を置く。**
2. **run 中は脚に触らない（今回いちばん大事）。** D10-3 は全 run で脚を手で支えていたので、測った電流が手の分だけ小さい可能性がある。脚が閉じたり交差したりしても、それが測りたいものである。危ないと思ったら手ではなく**主電源OFF**。
3. 通電後、D7 コンソールで `scan 3`。10/10 受信・全 `err=0`・`age <= 0.3 s`。
4. **`oa` の前に脚を手で「まっすぐ下」に整え、`oa` の直後に手を離す。** 全軸 `+0.0deg` を確認。手を離して 5 秒待ち、脚が勝手に動いたかを見て記録する（動いても直さない）。
5. 冒頭の `ver9_d8_sender build=D10_4_ALLSLEW_20260923_1200` を確認。違えば実行しない。
6. **CSV名は毎回変える。** やり直すときは末尾の `_a` を `_b`、`_c` に変える。
7. D7／送信器の `USB open failed; retrying ...` → 成功は正常。2回続けて失敗したら止める。

実行フォルダはすべて `C:\Users\harut\Connect2USB2CAN`。

---

## R0: 送信なしの確認（承認不要）

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --preflight --all-axes --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --csv logs\d10_4_r0_preflight_a.csv --vx 0 --vy 0 --wz 0
```

見るもの: `PREFLIGHT complete: CAN transmit count is zero.`、**`ALL-AXES PRE-ARM GATE: ok`**、`AXIS SNAPSHOT` の全軸 `pos` が ±5° 以内。`would REFUSE` なら手順4からやり直す（脚を整えて `oa`）。

## R1: 手を離して既定 1.0 A で保持（承認不要）

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --all-axes --hold-pose --duration 3 --csv logs\d10_4_r1_hold_handsoff_a.csv
```

D10-3 R1 と同じコマンドで、**違いは手を離していることだけ。** `HOLD POSE RESULT` の表を丸ごと残す。

## R1b: 手を離して重力対応中止で保持（R1 が current abort のときだけ・要承認）

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --all-axes --hold-pose --gravity-limits --duration 3 --csv logs\d10_4_r1b_hold_handsoff_gravity_a.csv
```

## R2: 吊り・全軸 slew 20 °/s・ゼロ速度指令（要承認）

R1（または R1b）が完走したときだけ。**R0 の直後の preflight でゲートが ok であること。**

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --all-axes --gravity-limits --policy-slew-dps 20 --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --ramp-seconds 15 --duration 3 --csv logs\d10_4_r2_hang_zero_slew20_a.csv --vx 0 --vy 0 --wz 0
```

見るもの: `POLICY SLEW: every axis limited to 20.0deg/s`、完走なら `POLICY complete`、最後の **`POLICY STAGE: N tick(s)`**（3 秒完走なら約 150）、**`SLEW GAP`**、`PER-AXIS RESULT`、`AXIS SNAPSHOT`。

## R3: 吊り・全軸 slew 30 °/s・前進 0.2 m/s（要承認）

R2 が完走したときだけ。**まだ床に下ろさない。**

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --all-axes --gravity-limits --policy-slew-dps 30 --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999 --ramp-seconds 15 --duration 3 --csv logs\d10_4_r3_hang_vx02_slew30_a.csv --vx 0.2 --vy 0 --wz 0
```

見るもの: R2 と同じ表と、**脚が左右交互に振れるか**（動画必須）。

## 解析（送信なし・いつでも）

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --analyze logs\d10_4_r2_hang_zero_slew20_a.csv
```

---

## 事前に決めた判定（走らせた後に基準を変えない）

| | 所見 | 意味 | 次 |
|---|---|---|---|
| **1** | R1 が 3 秒完走・全軸 headroom 正 | 手を離しても吊り静止は 1.0 A 以内。D10-3 R1 の結論が確定 | R2 へ（要承認） |
| **2** | R1 が `current abort` | 手が自重を持っていた。静止でも 1.0 A を超える軸がある | R1b へ（要承認）。R1b の表を中止値の根拠にする |
| **3** | R1b も `current abort` | 見積りより重い／引っ掛かり | 主電源OFF。**値を上げない。** 報告 |
| **4** | R2 完走（`POLICY STAGE` 約 150 tick） | 全身の方策ループが中止なしで回った | R3 へ（要承認） |
| **5** | R2 が ramp 中に `current abort` | 初期姿勢へ動かすだけで上限を超える軸がある | 止まった軸と ramp 中の電流を報告。**上限は上げない**（ramp を延ばすか、初期目標を見直す） |
| **6** | R2 が方策段階で `current abort` | slew 20 °/s でもどこかの軸が追いつけない | `SLEW GAP` の表と中止行を報告。**slew は上げない** |
| **7** | R2 が `speed abort` | 目標は遅いのに脚が速く動いた＝振動・跳ね | 主電源OFF。Kd／不感帯を疑う。報告 |
| **8** | ゲートが `would REFUSE` で止まる | 初期目標が遠すぎる（原点ずれか方策の外挿） | 脚を整えて `oa` からやり直す。2回続けば報告 |
| **9** | R3 で左右交互に振れる | slew つきでも歩容の形が出る | 床上は**別手順を書いてから**。中止値は R1/R1b と R2/R3 の実測電流から決める |
| **10** | R3 で片側だけ／震える／交互にならない | 吊りの観測（接地なし）か slew のせい | 床へ下ろさない。`SLEW GAP` を持って報告 |

## 許可／禁止

- **許可（承認不要）:** R0・R1。`scan`・`oa`・`--preflight`・`--analyze`。
- **要ユーザー承認:** R1b・R2・R3。
- **禁止:** run 中に脚を手で支えること。Kp/Kd・トルク欄の増加。速度中止 100 °/s・stale・原点 45° の緩和。`--gravity-limits` の表をさらに上げること。`--policy-slew-dps` を 30 より上げること（この手順書の中では）。`--vx` 0.2 超。`--duration` 5 秒超。同じ CSV 名での上書き。**床上の run。**

## 終わったら次のチャットに貼るもの

1. 各 run の**画面ログ全文**（`PRE-ARM GATE` / `HOLD POSE RESULT` / `POLICY STAGE` / `SLEW GAP` / `PER-AXIS RESULT` / `AXIS SNAPSHOT` / 中止行）
2. CSV 名（CSV 自体はエージェントが `logs\` から読む）
3. 手を離したあと脚が勝手に動いたか（手順4）
4. R3 の動画、または見た目の所見（所見は所見として扱い、判定は CSV で行う）
