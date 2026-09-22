# 2026-09-22 D9 0x1C：電流‑誤差の回帰による原因確定と試験設計の修正

## やったこと

- Claudeの週間制限中にCodexで進んだ分を引き継ぎ、`handoffs/ACTIVE.md`（D9 0x1C 追従停止）から入った。
- 追加の実機送信をせず、保存済みCSV2本（`d9_one_axis_0x1c.csv` 402行、`d9_static_probe_0x1c.csv` 401行）で、**電流を位置誤差で回帰**した。
- `ver9_d8_sender.py` に判定と門を追加（build `D9_DIAG_20260922_1930`）。単体テストを9本足して31本 OK。
- 報告書 `reports/2026-09-22_d9-0x1c-current-vs-error.md` を新設、`d9_2_1軸MITランプ_実験手順.md` を書き換え、`handoffs/ACTIVE.md`・`CONTEXT.md`・`motor_can_findings.md` を更新、前の報告書に訂正の見出しを付けた。

## 決めたこと・分かったこと

- **MITトルク経路は正常。** `|I| = 8.20 / 8.31 A/rad × 位置誤差`、指令 Kp 7.937 に対し比 1.03 / 1.05、切片 0.02 A 未満、飽和なし。経路断・モード違い・量子化の失敗ならこの直線は出ない。
- **MIT の Kp 欄は「1 rad あたりの電流[A]」**（機種によらない）。物理トルクは `電流 × Kt` で、AK10-9 の Kt は未測定。だから **不感帯 = 動き出し電流 ÷ Kp_cmd** という Kt 不要の形で扱う。
- **動かなかった原因は試験の設計。** 0x1C の不感帯は 4.8°以上なのに、要求角は方策ランプ 4.52°（合格線 2.26°）、static probe 2.5°（同 1.25°）だった。合格するには動き出し電流が 0.31 A / 0.17 A 未満である必要があり、**脚も付いていない裸の AK80-9（0.63 A）でも満たせない条件**だった。0x1C 固有の異常を示す数値は今のところ無い。
- 電流中止 1.0 A のため、位置指令で探れるのは **要求角 7.2° まで**。それ以上は中止に当たるだけで情報が増えない。
- 前の報告書（`..._stall-analysis.md`）の「負荷に負けた」は向きは正しいが、最大電流しか見ておらず、不感帯を計算しておらず、比較対象（裸の AK80-9 の 0.63 A）が手元にあったのに使っていなかった。
- **学習側への含意:** 実機の不感帯はシムの `friction` 0.22 N·m が意味する 0.9〜1.3° の4倍以上。H_eff13p5 の頑健性スイープに friction を振った条件が無い。床上デプロイの前に WRS機で friction 3〜5倍のスイープを回す（実機不要、D9と独立）。

## 手を動かした場所

- `Connect2USB2CAN/ver9_d8_sender.py`（`.bak_20260922_diag` を取ってから）: `torque_path_summary` / `report_torque_path` / `deadband_lower_bound_rad` / `probe_ceiling_current_a` / `stall_guard` / `--analyze`。**ゲイン・目標角・トルク欄は一切変えていない。**
- `stall_guard` は、**すでに静止が実証された電流以下しか掛けられない実行を、MITフレームを1つも出さずに中止する**（`repeat-probe abort`）。同じ試験の5回目が物理的に打てなくなる。
- `Connect2USB2CAN/test_ver9_d8_sender.py`: `TorquePathTests` / `StallGuardTests` を追加（31 tests OK）。
- `claude/reports/2026-09-22_d9-0x1c-current-vs-error.md`（新規）、`claude/d9_2_1軸MITランプ_実験手順.md`（書き換え、`.bak_20260922` あり）、`claude/handoffs/ACTIVE.md`、`claude/CONTEXT.md`、`claude/motor_can_findings.md`、`claude/reports/2026-09-22_d9-0x1c-stall-analysis.md`（訂正見出し）。
- 実機への送信は0。CANバスを開いていない。

## 積み残し・次にやること

1. **無通電の機構確認**（主電源OFF・手回し・干渉/ケーブル/支持具）。承認不要。
2. **D9-3（要ユーザー承認）**: `STATIC_PROBE_MAX_DEG` を 2.5 → 7.0 にして、要求角 6.5°（最大 0.90 A）の static probe を1回。0.66 A の 1.4 倍で、裸の AK80-9 の動き出しも上回る。動けば普通のスティクション、動かなければ機構の異常に確定する。**承認が出てからコードを1行変える。**
3. D9-3 でも動かなければ、トルク欄ランプ（Kp=0、最初の 0.1° で即停止）で動き出しトルクを直接測る設計を別途レビューする。
4. WRS機で friction 3〜5倍の頑健性スイープ（H_eff13p5@2999）。
5. `Connect2USB2CAN` と本リポジトリには、他PC由来の未コミット変更（`docs/` の改行コード差分、`my_robot_code/`、`robot_joint_map.py` など）が残っている。**今回のコミットには含めていない。** どちらの版を残すか決めること。

---

## 追記（同日・後半）D9-3 の実装と、文書構造のリファクタリング

### やったこと

- ユーザーが push 済み。**D9-3 を承認**。ユーザーが実験を実行し、結果は次のチャットに貼る。
- **D9-3 を実装。** `STATIC_PROBE_MAX_DEG` を 2.5 → 7.0 にしたうえで、**probe角の上限を機種ごとに電流中止から導く** `max_probe_angle_deg()` を追加した（`電流 = Kp × 誤差` なので、角度＝掛けられる電流）。0x1C（Kp 7.937）は 6.86°まで、AK80-9 の硬い軸は 2°未満。Kp・Kd・トルク欄・電流中止 1.0 A は変えていない。テスト34本 OK。build `D9_BREAKAWAY_20260922_2130`。
- 手順書 `procedures/d9_3_1軸ブレークアウェイ_実験手順.md` を新設（事前の判定表つき）。D9-2 は冒頭に「置き換え済み」を明記して経緯として残した。
- 引き継ぎ書を `handoffs/2026-09-22_d9-3_ブレークアウェイ判定.md` として作成。**`ACTIVE.md` は廃止**（中身の分からない固定名をやめ、日付＋内容の名前にした。有効な1本は `CONTEXT.md` の冒頭が名指しする）。
- **未コミットの判断:** このリポジトリの78ファイルの差分は `git diff --ignore-cr-at-eol` が空＝**中身ゼロのCRLF→LF churn**だったので `git checkout` で戻した。`Connect2USB2CAN` の4ファイルは中身のある完成した作業（joint map から USB ch を外し、経路は受信から確定する設計に合わせたもの）で、全9テストファイル58本が通ったので**そのままコミット**した。
- `.gitignore` に `H_eff13p5_2999/`、`**/deploy_pkg*/`、`claude/.codex-build/` を追加。

### 文書構造のリファクタリング（ユーザー許可のもと）

**問題:** 「最初に読め」と言う入口が3つあり、互いに違うものを指していた。

| 入口 | 指していた先 | 大きさ |
|---|---|---|
| claude.ai プロジェクト指示欄（編集不可） | `claude/README.md` | **52 KB** |
| リポジトリ直下 `README.md` | `project_handbook.md` | 40 KB |
| `AGENTS.md` | PROJECT → CONTEXT → ACTIVE | 約10 KB（これが正しい） |

**直したこと:**

- `claude/README.md` を **52 KB → 1.6 KB の道しるべ**に置換（本体は `legacy/README_index_legacy.md` に保全）。これでプロジェクト指示欄に従って読んでも、正しい4つへ着地する。
- ルート `README.md` の「まず project_handbook を読め」を、AGENTS → PROJECT → CONTEXT → 名指しの引き継ぎ書に変更。
- `PROJECT.md` に「読む順番（この4つだけ、約1万字）」と「必要になった時だけ引く表」と「文書の更新ルール」を追加。
- **更新ルールに「全文の打ち直しが高くつくときは末尾に日付つきで追記してよい」を明記**（冒頭に「最新は末尾の追記」と1行書く）。`reports/` と `chats/` は追記のみ。
- 索引ファイル（README の巨大な chats 索引）の運用を廃止。ファイル名と `git log` を索引にする。

**残した判断:** `domains/` → 正本 の2段構えは良いのでそのまま。`legacy/` は開始時に読まない置き場として機能している。

### 積み残し

1. **ユーザーが D9-3 を実行 → 次のチャットで結果を判定**（事前判定表は引き継ぎ書に記載済み）。
2. WRS機で friction 3〜5倍の頑健性スイープ。
3. `Connect2USB2CAN` の `controller/command_*.py`（未追跡・作業途中）の扱いを決める。
4. CRLF churn が再発するなら、エディタの改行設定か `.gitattributes` を検討する。
