# D9-6: 支持を直して、0x1C と足首（0x2B）を記録つきで1回ずつ

> 作成 2026-09-22。根拠 `../reports/2026-09-22_d9-4_result.md`。対象は **0x1C（LL_HR）と 0x2B（LL_FFE）**。
> 異音・接触・支持ずれ・エラー・表示された中止のときは、PC操作より先に**主電源OFF**。

## 何が分かっていて、何が分かっていないか（1段落）

0x1C は D9-3（−6.5°）でも D9-5A（+6.5°）でも 0.86 A で動かなかった。**ただし D9-5A は複数回走らせており、「動いた」と見えたのは手で支えて角度を調整していた回で、CSVに残っている最後の回（足先を揃えた状態）は動いていない。** CSV名が固定だったので、動いた回のログは上書きされて残っていない。つまり **手で支えると動き、吊って足を閉じたままだと動かない、という可能性が生きている**。吊ると脚は内側へ閉じるので HR の軸が傾き、足どうしが横から押し合う。その状態では HR に荷重と摩擦がかかる。ここを潰すのがこの実験である。**支持を直し、走行中は機体に触れず、毎回別のCSV名で記録する。**

## 軸ごとの数字（変えない前提値）

| 軸 | 機種 | Kp [A/rad] | Kd | probe 最大角 | その角での到達電流 |
|---|---|---:|---:|---:|---:|
| 0x1C LL_HR | AK10-9 | 7.937 | 1.233 | 6.64° | 0.92 A |
| 0x2B LL_FFE | AK80-9 | 19.048 | 2.867 | **2.77°** | 0.92 A |
| 0x13 LR_HR | AK10-9 | 7.937 | 1.233 | 6.64° | 0.92 A |

FFE は Kp が HR の 2.4 倍なので、**2.77° で HR の 6.64° と同じ 0.92 A に届く**。角度が小さいのは手抜きではない。

---

## 段階1: 支持を直す（主電源OFF・承認不要）

**手では支えない。** 手の摩擦が測定に入り、脚が回ったのか手が動いたのか区別できない。次の3つを**治具・つっかい棒・紐・スペーサー**で作る。

1. **脚を立ち幅に開いたまま保持する。** ゼロ点は立たせた状態で取ってあるので、立ち幅に開くとゼロ姿勢に近くなる。足先は接触させない。
2. **機体本体が吊り紐ごと回らないように止める。** HR にトルクを入れると反作用で機体が回り、脚が回ったように見える。D9-5A の見間違いはこれが原因の可能性が高い。
3. **足は床に触れさせない。** 関節に荷重を乗せない。

写真を1枚撮る。「足の開き」「機体の回り止め」「足が浮いていること」が写っていればよい。

---

## 段階2: 通電して3回（**要ユーザー承認**）

### 共通の事前条件

1. **電源遮断担当が主電源に手を置く。**
2. 通電後、D7 コンソールで `scan 3`。全10 IDの受信と `err=0` を確認する。
   - **0x1C と 0x2B の現在角をメモする。**
   - **どれかの軸が原点から 45° を超えていると `origin/pre-arm pose abort` で止まる。** その場合だけ、同じ通電中に D7 の `oa` を行ってからやり直す。
3. 冒頭の `ver9_d8_sender build=D9_DIRSTALL_20260922_2300` を確認する。違うビルドなら実行しない。
4. `STALL GUARD:` と `PROBE DIRECTION:` の行が出ることを確認する。出ないビルドなら実行しない。
5. **走行中は機体に触れない。CSV名は毎回変える。** 同じ名前で走らせると前の記録が消える。

実行ディレクトリはすべて `C:\Users\harut\Connect2USB2CAN`。

### 実行1: 0x1C を正しい支持で +6.5°（本命）

支持だけを変えて、D9-5A と同じ向き・同じ角度をもう一度。**今度は手を触れず、ログを残す。** 送信器は正方向を拒否しない（編集不要）。

```powershell
cd C:\Users\harut\Connect2USB2CAN
.venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x1C --probe-target-deg 6.5 --ramp-seconds 8 --duration 2 --csv logs\d9_6a_hr_pos_supported_0x1c.csv
```

1行版:

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x1C --probe-target-deg 6.5 --ramp-seconds 8 --duration 2 --csv logs\d9_6a_hr_pos_supported_0x1c.csv
```

8秒で +6.5° まで直線に増やし、2秒保持（約 0.81°/s）。爪先が外へ開く向き。

### 実行2: 足首 0x2B を −2.7°（ゲインの陽性対照）

実行1 の結果によらず走らせる。吊れば足は無荷重で、機体の中でいちばん動きやすい軸である。

```powershell
cd C:\Users\harut\Connect2USB2CAN
.venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x2B --probe-target-deg -2.7 --ramp-seconds 4 --duration 2 --csv logs\d9_6b_ffe_neg_0x2b.csv
```

1行版:

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x2B --probe-target-deg -2.7 --ramp-seconds 4 --duration 2 --csv logs\d9_6b_ffe_neg_0x2b.csv
```

4秒で −2.7° まで、2秒保持（約 0.68°/s）。爪先が上がる向き。**動いたら足先が 2.7° ほどパタッと振れる。**

### 実行3: 足首 0x2B を +2.7°

実行2 が C（不動）だったときだけ走らせる。実行2 で動いたなら答えが出ているので走らせない。

```powershell
cd C:\Users\harut\Connect2USB2CAN
.venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x2B --probe-target-deg 2.7 --ramp-seconds 4 --duration 2 --csv logs\d9_6c_ffe_pos_0x2b.csv
```

1行版:

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x2B --probe-target-deg 2.7 --ramp-seconds 4 --duration 2 --csv logs\d9_6c_ffe_pos_0x2b.csv
```

### 任意: 同じ通電中に 0x13（LR_HR）も1回

当日の判断でよい。左右の鏡なので結果は同じ公算が高いが、**「0x1C 固有の故障か、HR グループのゲイン不足か」を切り分けられるのはこれだけ**である。停止記録が無いので拒否されない。編集も不要。

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --arm --static-probe --motor-id 0x13 --probe-target-deg -6.5 --ramp-seconds 8 --duration 2 --csv logs\d9_6d_lr_hr_neg_0x13.csv
```

---

## 中止

`motion/current abort`（電流 1.0 A／速度 100°/s）、`stale feedback`、`motor error`、`origin/pre-arm pose abort`、`repeat-probe abort`、異音、接触、支持ずれ ── いずれも**主電源OFF**。再試行しない。零MITは終了時に自動で送られる。

## 事前に決めた判定（走らせる前にここを読む。走らせた後に基準を変えない）

読む行: `PROBE DIRECTION:` / `STATIC PROBE:` / `TORQUE PATH:` / `BREAKAWAY:` か `DEADBAND:` / `VERDICT:`。
ブレークアウェイの線は「**目標へ向かう正味かつ持続した変位 0.5°（5目盛）以上**」。

| | 条件 | 意味 | 次 |
|---|---|---|---|
| **1** | 実行1 が **A か B** | **支持が原因で確定。0x1C は健全。** 吊って足を閉じた状態が HR を拘束していた | `BREAKAWAY:` の動き出し電流が本当の値。「不感帯 6.2°以上」を撤回し、この値で報告書と CONTEXT を書き換える。**吊り試験はこれ以降この支持で行う** |
| **2** | 実行1 が **C**、実行2（か3）が **A か B** | ゲインと MIT 経路は効く。**動かないのは HR だけ** | HR の Kp（デプロイ値 10）が HR の静止摩擦に対して低い、が本線。ゲインを勝手に上げず、`reference/actuator_params.md` と学習側の stiffness に戻して設計し直す。任意の 0x13 をやると確度が上がる |
| **3** | 実行1 も 実行2・3 も **C** | **デプロイ用ゲインでは、無荷重の足首すら静止から動かせない** | 主電源OFF。位置指令方式は打ち止め。Kp=0・トルク欄ランプ（最初の 0.1° で即停止）の設計を起こし、**別途レビュー**してから実行 |
| **4** | どれかが **D**（`TORQUE PATH: absent/anomalous`） | 前提（電流＝Kp×誤差）が崩れている | 主電源OFF。電気・通信側へ戻る。機構を触らない |
| **5** | （任意を実施して）0x13 が **A か B** で 0x1C が C | **0x1C だけが動かない** | 0x1C を機体から外して単体で手回し（**要ユーザー承認**） |

## 許可／禁止

- **許可（承認不要）:** 段階1すべて（無通電の目視・手回し・支持治具の製作・寸法測定）、`--analyze` での再判定、文書更新。
- **要ユーザー承認:** 段階2 の実行すべて。0x1C を機体から外すこと。
- **禁止:** Kp/Kd・トルク欄・電流中止（1.0 A）・`STATIC_PROBE_MAX_DEG` の増加。`repeat-probe abort` をゲインや目標角で回避すること。**走行中に手で機体を支えること。同じCSV名で上書きすること。** 片脚／全身MIT、床上デプロイ。

> **なぜ 0x1C の正方向がまだ拒否されないのか。** D9-5A は正方向で 0.86 A の停止を記録したが、**支持のしかたという機械的条件がこれから変わる**ので、`DEMONSTRATED_STALL_CURRENT_A` に正方向の記録は入れていない。これはガードの設計どおり（「機械的な負荷を変えるか、別途レビューした診断を走らせる」）の扱いである。**実行1 が支持を直したうえで C だったら、そのとき初めて `(0x1C, 1): 0.86` を記録する。**

## 実機なしの再判定

```powershell
cd C:\Users\harut\Connect2USB2CAN; .venv310\Scripts\python.exe ver9_d8_sender.py --analyze logs\d9_6a_hr_pos_supported_0x1c.csv
```

CANを開かない。保存済みCSVを同じ判定に掛け直すだけなので、何回やっても安全である。

## 終わったら渡すもの

1. CSV の絶対パス（全部。**上書きしていないこと**）と画面ログ全文
2. `scan 3` の 0x1C・0x2B 現在角（実行前）
3. 支持のしかたが分かる写真（足の開き・機体の回り止め・足が浮いていること）
4. 異音・温度・abort の有無
