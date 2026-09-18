# 2026-09-16 公式資料の再調査と motor_console_ver7 / ver8（MIT で位置指令が通った・原点手順が決まった）

## やったこと

1. README・`mit_implementation_briefing.md`・`motor_can_findings.md`・`motor_bench_checklist.md`・`next_chat_briefing.md`・09-14 のチャット記録を読み、ユーザーの「モーター制御の現状」とデプロイ最低限 9 項目を前提に据えた。
2. ノートPCの `Connect2USB2CAN` にアクセスし、`motor_console_ver6.py` 全体・`cubemars.py`・09-14 のセッション記録を読んだ。
3. **公式資料を探し直した**（v3.0.0 製品マニュアル、V1.0.15 ドライバマニュアル、公式FAQ、製品ページ、ダウンロードページ）。最新 V3.2.0 マニュアルと AK 3.0 用 Arduino デモは取得拒否 → ユーザーに DL 依頼（未着）。
4. ユーザー指示「実装を頼む、実験は自分がやる、ver7 以降を作って」→ **`motor_console_ver7.py` と練習用シム `mit_sim.py` を作成**、シムで隠し値を当てて検算。
5. **実機（夜・5個接続）:** バスに見えるのは ID18（0x12）と ID34（0x22）だけ。`sniff`・`ping`・`jog`・`limit` を追加。**12番＝ID18（真ん中）、22番＝ID34（先端）**を `jog 10` の目視で確定（上位機の番号は16進）。手で軸は回せない。**真ん中は危ないので今日は先端（ID34）だけ（ユーザー決定）。**
6. ID34（脚付き・limit 8）で ver7 の `isign`/`wdog`/`lat`/`morg`/`vscale` → CSV を読んで**電流の符号が信用できない**ことを発見 → **ver8** を作成・配置。
7. ver8 で `isign` → `morg`（成功）→ `kpscale` ×2 → `vscale`（静止）→ `hold 2 1 3` → `ramp` → `step 5 5 1 2` → `step 5 15 1 2`。
8. `ocheck` → `jog`+`morg fine`（Kp 0.24 段の R² が雑音で 0.76 → 合格ラインを 0.6 に、Kp 0.98 段は 0.8 のまま）→ 2か所で原点採用。
9. **電源再投入を3回**（途中2回はスクリプト再起動だけで電源を切っていなかった → ユーザー申告で判明し、やり直した）。
10. `motor_can_findings.md` と `motor_bench_checklist.md` を書き換えた。

## 決めたこと・分かったこと

- 公式資料の要点と仮説は **`motor_mit_official_notes.md`（新規）**。
- ver6 の隠れ誤差: 速度0欄の半LSB → Kd=1 で常に −0.016 N·m → dither で修正。
- **フィードバックの電流は大きさだけ正しく符号は信用できない**（t −0.20 → +0.35 A 等）。ver7 の morg / kpscale / vscale 静止は不成立だった。
- **A13: MIT 位置 = サーボ角**（4か所で offset −0.29〜+0.56 deg、左右検証 ±0.5 deg 以内、倍率のずれなし）。
- **A14: `o 0` で MIT 原点も同時に0（同じカウンタ）。** → 09-14 の 16.5A/39.7A は原点のずれでは説明できない（未確定）。
- **A3: 電源を入れ直すと絶対角は失われ、投入時の値は 80 deg の窓に折り返す**（86.1→86.1、96.1→16.1、6.1→86.1）。offset は電源を越えて有効。
- **デプロイの原点手順（結論）: 起動 → フィードバック待ち（投入直後の数秒は来ない）→ 決まった姿勢で `o 0`。** 姿勢が ±40 deg で分かれば 80 deg 単位で直せるが確認用。
- **E5b: 実効Kp/指令Kp = 0.538**（2回再現）。シム stiffness 15 → 指令 Kp ≈ 28。
- **c_d × r_v = 0.545〜0.564**（r_v 未分離）。09-14 の「実効Kd 0.48」は撤回候補。
- **A4: 指令を止めても最後のトルクを出し続ける。** **D2: 最小 8 / 中央値 10 ms。** **C6: MIT ではリミットサイクルなし。** **C7: step は 95 ms で停止、静止摩擦の不感帯で 2.6 deg 手前。**
- 送信周期が一度だけ最大 80.6 ms に揺れた（D1 要測定）。

## 手を動かした場所

- ノートPC `C:\\Users\\harut\\Connect2USB2CAN\\`: `motor_console_ver7.py`（+ `.bak_ping` `.bak_jog` `.bak_limit`）、**`motor_console_ver8.py`（現行、+ `.bak_vs` `.bak_r2`）**、`mit_sim.py`、`mit_calib.json`（ID34 の vscale_static を 0.564 に手で修正）、ログ `logs\\v7_20260916\\`。
- プロジェクト: `motor_mit_official_notes.md` 新規、`motor_can_findings.md`・`motor_bench_checklist.md` 書き換え、この記録、README 索引。

## 積み残し・次にやること

1. 先端関節（ID34）の「決まった姿勢」を決め、`o 0` → 方策の初期姿勢との対応（E2）。`jit`、ステップ数点。
2. 脚を外せる日: `vscale` 回転テスト（c_d と r_v）、Kt を分銅で。
3. バスに出ない3個の電源・配線、ID・機種・関節・符号の対応表。別個体で 80 deg の折り返しを確認。
4. `mit_implementation_briefing.md`（ver6 前提で古い）と `actuator_params.md` §0c（Kd 0.48 前提）を ver8 の数字で書き換え。手順書 A7、`next_chat_briefing.md` のデプロイ残作業表（C 実機モーター）も。
5. V3.2.0 マニュアル・Arduino デモ、上位機の設定読み（フィードバック周期、CAN 途絶時の設定）。
6. 制御ループの骨組み（50Hz、起動時フィードバック待ち → `o 0`、受信タイムアウトで零指令、電流は大きさだけ、Kp/Kd 換算）。
7. ver6〜8・ログ・mit_calib.json のコミット。
