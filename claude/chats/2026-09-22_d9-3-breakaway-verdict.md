# 2026-09-22 D9-3: 0.200° をどう読むかと、静止を例外にしていた実装の修正

> 正本はリポジトリ `wanpbl2026_slope_climing_robot/claude/chats/2026-09-22_d9-3-breakaway-verdict.md`。

## やったこと

- ユーザーが実行した D9-3（0x1C・要求角 −6.5°）の画面ログと `logs\d9_3_breakaway_0x1c.csv`（501行）を、実機に触らずに読んだ。CAN送信は0。
- 原因を特定し、`ver9_d8_sender.py` を修正（build `D9_VERDICT_20260922_2015`）。単体テスト 44本、リポジトリ全体 71本 OK。
- 報告書 `reports/2026-09-22_d9-3_result.md` を新設、`CONTEXT.md`・`procedures/d9_3_...md`（末尾追記）を更新、引き継ぎ書 `handoffs/2026-09-22_d9-4_無通電機構確認.md` を新設。

## 分かったこと

- **判定は C（不動）。** 0x1C は保持 0.86 A でもブレークアウェイしない。**不感帯 6.2°以上。** MITトルク経路は正常（7.96 A/rad、指令Kp比 1.00）。
- **画面ログの「0.200° 動いた」は回転ではない。** 位置は −0.4 / −0.5 / −0.6 の3値（量子化 0.1°）しかとらず、t=2.6〜2.8 s に往復、t=5.05 s 以降は静止。弾性たわみとバックラッシュの取り切り。
- **事前判定表の B の下限 0.1° は量子化1目盛そのもので、最初から判定不能だった。** ブレークアウェイの定義を「正味かつ持続した変位 0.5°（5目盛）以上」に改め、判定は B → C になった。走らせた後の基準変更であることと、変更先がより慎重な側であることを報告書に明記した。
- **実装の誤りが4つ。** (1) 動かないことを `RuntimeError: static probe abort` にしていた（D9-2 の4回の再試行の原因）。(2) 最大振れ幅で判定していた。(3) 不感帯の下限をノイズのピーク 0.93 A から出していた（正しくは保持 0.86 A → 6.21°）。(4) `PROBE_CURRENT_HEADROOM = 0.95` は指令 0.95 A で、ノイズ +0.08 A が電流中止 1.0 A を誤って踏む。

## 手を動かした場所

- `Connect2USB2CAN/ver9_d8_sender.py`（`.bak_20260922_verdict` あり）: `ProbeResult` / `probe_result` / `held_rows` / `median` / `sustained_current_a` / `breakaway_current_a` / `report_probe` / `report_deadband` / `d9_3_letter` / `D9_3_NEXT_STEP` / `D9_3_EXIT_CODE`。`static_probe_summary` は撤去。`max_probe_angle_deg` は電流ノイズ 0.08 A ぶんを引く（Kp 7.937 で 6.64°）。`DEMONSTRATED_STALL_CURRENT_A[0x1C]` は 0.66 → 0.86。`stall_guard` を `main()` でも先に呼び、**電源を入れる前に**再実行を拒否する。
- **ゲイン・目標角・トルク欄・電流中止は一切上げていない。** 変更はすべて判定を厳しくする方向。
- 実機への送信は0。CANバスを開いていない。ブランチ `feat/mit-mode`（push はユーザー側）。

## 積み残し・次にやること

1. **D9-4: 主電源OFFでの 0x1C 機構確認**（承認不要）。0x13 との手回し比較が一番効く。
2. 機構で見つからなければ、Kp=0・トルク欄ランプの設計を起こして**別途レビュー**。
3. WRS機で friction 3〜5倍のスイープ。実機の不感帯はシムの 5倍以上で、前回見積り（4倍）より悪い。
4. Connect2USB2CAN のローカル `main` は origin/main より1つ遅れ。`feat/mit-mode` は origin/main を含み32先行しており、早送りで合流できる。
