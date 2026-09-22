# D9-5: 0x1C の「塞がっている向き」を確定し、自由な向きで動き出し電流を測る

> 作成 2026-09-22。根拠 `../reports/2026-09-22_d9-4_result.md`。対象は **0x1C（LL_HR）1軸だけ**。
> 前提の変更: D9-3 の判定 C は「0x1C の摩擦が大きい」ではなく「**負方向に 0.2° しか動く余地がなかった**」可能性が高い。左右の足先が触れているためである。
> 異音・接触・支持ずれ・エラー・表示された中止は、PC操作より先に**主電源OFF**。

## この実験の狙い（1段落）

HR は鉛直軸まわりのひねりで、足は前後に長い。軸まわりに回すと爪先と踵は逆向きに動くので、**足先どうしの接触は片側の向きしか塞がない**。D9-3 は負方向（爪先内向き）しか押していない。そこで、まず無通電で**どちらの向きが塞がっているか**を手で確定し、次に**自由なほうの向き**へ同じ probe を1回だけ掛けて、0x1C の本当の動き出し電流を測る。ゲイン・トルク欄・電流中止（1.0 A）・最大角（6.64°）は一切変えない。

---

## 段階0: 無通電（主電源OFF・吊り支持のまま）。承認不要

**0-1 いまの姿勢で 0x1C を手で両方向に回す。**

左足の爪先を手で持ち、水平にひねる。**「内向き（爪先が右足へ寄る）」と「外向き（爪先が外へ開く）」を別々に**確かめ、次を記録する。

| | 内向き（＝負・D9-3 が押した向き） | 外向き（＝正） |
|---|---|---|
| どこまで動くか（目分量で何度か） | | |
| 止まり方（**コツンと硬い**／じわっと重い／減速機なりの一様な重さ） | | |
| 止まった瞬間に**足先どうしが当たっているか**（目で見る） | | |

**「硬く止まって、そのとき足が当たっている」が片方だけで出れば、原因は確定である。**

**0-2 同じことを 0x13（LR_HR、右脚）で行う。** 鏡なので、塞がる向きは逆になるはずである。左右で「自由なほう」の手応えが同じなら、0x1C のモーター・減速機は無罪。

**0-3 足を離してもう一度 0x1C を回す。**

**関節は手で動かさない。吊り方だけ変える。** いちばん簡単なのは、**片脚の吊り点を 30〜50 mm 持ち上げて、左右の足の高さをずらす**こと。これで横方向には当たらなくなる。左右に広げる吊り方でもよい。
この状態で 0-1 をやり直し、**さっき硬く止まった向きが自由になるか**を見る。自由になれば確定。

> 注意: 関節を手で回すと D7 の原点がずれる。段階1の probe は相対指令なので原点合わせのやり直しは不要だが、**どれかの軸が原点から 45° を超えてずれると `origin/pre-arm pose abort` で止まる。** その場合だけ、同じ通電中に D7 の `oa` を行ってからやり直す。

**0-4 ゼロ姿勢での足先距離を測る。** 左右の足先の最短距離を mm で測り、写真を撮る。CAD の同じ姿勢での値と比べる（CAD 側は実機に触れずに出せる）。これは §「積み残し」用で、段階1の前提ではない。

### 段階0 の判定

| | 所見 | 結論 | 次 |
|---|---|---|---|
| **α** | 内向きで硬く止まり足が当たる／外向きは自由 | D9-3 の停止は足どうしの突き当たりで確定 | **段階1-A**（正 +6.5° の probe）へ |
| **β** | 外向きで硬く止まり足が当たる／内向きは自由 | 接触はあるが D9-3 の停止は説明できない | 段階1 に進まず報告。0x1C は別の原因なので設計をやり直す |
| **γ** | 足を離しても両方向とも硬い／引っ掛かる | 接触は無関係。減速機・軸受け側 | 段階1 に進まない。D9-4 判定表の B（0x1C を機体から外して単体で手回し）へ。**取り外しは要ユーザー承認** |
| **δ** | 足を離すと両方向とも 0x13 と同じ手応えで自由 | 機構は健全。接触だけが原因 | **段階1-B**（足を離したまま −6.5° の再現）へ。α と両方やるのが望ましい |

---

## 段階1: 通電して probe。**実行前にユーザー承認を取る**

共通の事前条件:

1. 機体は吊り支持済み。**電源遮断担当が主電源に手を置く。**
2. 通電後、D7 コンソールで `scan 3`。全10 IDの受信と `err=0` を確認する。
3. 冒頭の `ver9_d8_sender build=D9_DIRSTALL_20260922_2300` を確認する。違うビルドなら実行しない。
4. `STALL GUARD:` と `PROBE DIRECTION:` の行が出ることを確認する。出ないビルドなら実行しない。

### 段階1-A: 自由な向き（正 +6.5°）を1回。足は触れたままでよい

**これが本命である。** 編集は何も要らない。新ビルドは向きで記録を引くので、正方向は `repeat-probe abort` にならない。

実行ディレクトリ `C:\Users\harut\Connect2USB2CAN`。

```powershell
cd C:\Users\harut\Connect2USB2CAN
.venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x1C --probe-target-deg 6.5 --ramp-seconds 8 --duration 2 --csv logs\d9_5a_free_dir_0x1c.csv
```

1行版:

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x1C --probe-target-deg 6.5 --ramp-seconds 8 --duration 2 --csv logs\d9_5a_free_dir_0x1c.csv
```

- 8秒で +6.5° まで直線に増やし、2秒保持（約 0.81°/s）。到達できる最大電流は 0.90 A で、D9-3 と同じである。
- 足は**離れる**向きへ動く。動き出したら手を止めない。支持と主電源から目を離さない。

### 段階1-B: 足を離して、D9-3 と同じ −6.5° を1回

**段階0-3 で足を離した状態を作ってから行う。** この1回だけ、`DEMONSTRATED_STALL_CURRENT_A` の負方向の記録を外す。機構が変わったので、その記録はもう当てはまらないからである。

`ver9_d8_sender.py` の該当行（1行だけ）:

```python
DEMONSTRATED_STALL_CURRENT_A = {(0x1C, -1): 0.86}
```

を、こう書き換える:

```python
# 2026-09-22 D9-5: 足の接触を外したので、接触ありで取った 0.86 A の記録は
# もうこの機構に当てはまらない。reports/2026-09-22_d9-4_result.md を参照。
DEMONSTRATED_STALL_CURRENT_A = {}
```

書き換える前に `.bak` を取り、書き換えたら diff とテストを見せる:

```powershell
cd C:\Users\harut\Connect2USB2CAN; Copy-Item ver9_d8_sender.py ver9_d8_sender.py.bak_20260922_d95
cd C:\Users\harut\Connect2USB2CAN; git diff -- ver9_d8_sender.py
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe -m pytest test_ver9_d8_sender.py -q
```

> テストは `DEMONSTRATED_STALL_CURRENT_A` に `(0x1C, -1)` があることを見ているので、ここで落ちる。**落ちたテストを直すのは、段階1-B をやると決めた後**である。値を消すより先にテストを消さない。

実行:

```powershell
cd C:\Users\harut\Connect2USB2CAN
.venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x1C --probe-target-deg -6.5 --ramp-seconds 8 --duration 2 --csv logs\d9_5b_gap_neg_0x1c.csv
```

1行版:

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x1C --probe-target-deg -6.5 --ramp-seconds 8 --duration 2 --csv logs\d9_5b_gap_neg_0x1c.csv
```

---

## 中止

`motion/current abort`（電流 1.0 A／速度 100°/s）、`stale feedback`、`motor error`、`origin/pre-arm pose abort`、`repeat-probe abort`、異音、接触、支持ずれ ── いずれも**主電源OFF**。再試行しない。終了時は零MITが自動で送られる。

## 事前に決めた判定（走らせる前にここを読む。走らせた後に基準を変えない）

読む行: `PROBE DIRECTION:` / `STATIC PROBE:` / `TORQUE PATH:` / `BREAKAWAY:` か `DEADBAND:` / `VERDICT:`。
ブレークアウェイの線は D9-3 の改訂どおり「**目標へ向かう正味かつ持続した変位 0.5°（5目盛）以上**」。

| | 条件 | 意味 | 次 |
|---|---|---|---|
| **1** | 1-A が **A か B**（動いた） | **0x1C は健全。D9-3 の停止は足どうしの突き当たりだった。** 不感帯 6.2° は誤り | `BREAKAWAY:` 行の動き出し電流が本当の値。これを報告書と CONTEXT に書き、学習側の「不感帯5倍」の持ち帰りを差し替える。**次は接触そのものを直す**（ゼロ姿勢の見直し）。片脚へはそれから |
| **2** | 1-A が **C**（正方向でも 0.90 A で動かない） | 接触では説明できない。両方向とも塞がっている | 主電源OFF。ゲインを上げない。段階0-3（足を離す）をやってから 1-B。それでも C なら 0x1C を外して単体で手回し（要承認） |
| **3** | 1-B が **A か B** | 足を離したら動いた＝**接触が原因で確定** | 1 と同じ。加えて「ゼロ姿勢で足が接触している」を機構課題として立てる |
| **4** | 1-B が **C** | 足を離しても 0.90 A で動かない | 主電源OFF。位置指令方式は本当に打ち止め。Kp=0・トルク欄ランプ（最初の 0.1° で即停止）の設計を起こし、**別途レビュー**してから実行 |
| **5** | どちらかが **D**（`TORQUE PATH: absent/anomalous`） | 前提（電流＝Kp×誤差）が崩れている | 主電源OFF。電気・通信側へ戻る。機構を触らない |

## 許可／禁止

- **許可（承認不要）:** 段階0すべて（無通電の目視・手回し・吊り方の変更・寸法測定）、`--analyze` での再判定、文書更新、CAD 側の足先距離の算出、学習側の friction スイープ、コントローラー乾式。
- **要ユーザー承認:** 段階1 の実行すべて。`DEMONSTRATED_STALL_CURRENT_A` の書き換え。0x1C を機体から外すこと。
- **禁止:** Kp/Kd・トルク欄・電流中止（1.0 A）・`STATIC_PROBE_MAX_DEG` の増加。`repeat-probe abort` をゲインや目標角で回避すること。段階0 を飛ばして段階1 をやること。片脚／全身MIT、床上デプロイ。

## 実機なしの再判定

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --analyze logs\d9_5a_free_dir_0x1c.csv
```

CANを開かない。保存済みCSVを同じ判定に掛け直すだけなので、何回やっても安全である。

## 終わったら渡すもの

1. 段階0 の表（内向き／外向き × 0x1C／0x13、足を離す前後）と写真・動画
2. CSV の絶対パスと画面ログ全文（`PROBE DIRECTION` / `STALL GUARD` / `STATIC PROBE` / `TORQUE PATH` / `BREAKAWAY` か `DEADBAND` / `VERDICT`）
3. ゼロ姿勢での左右足先距離（実測 mm）
4. 異音・温度・abort の有無
