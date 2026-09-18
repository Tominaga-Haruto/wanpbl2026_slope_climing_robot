# 次チャットへの指示書（学習側 Cowork）── 2026-09-18 朝版（夜間の自走の後）
 
> 前チャット: `chats/2026-09-17_exp08-stop8b-review.md` → `chats/2026-09-18_overnight-and-controller.md`。恒久ルールは `project_handbook.md`、入口は `README.md`。
> **この文書だけで始められるように短くしてある。** 足りないときだけ個別資料を `project_search` で引く（全文 read は最小限に）。
> WRS機は Cowork から操作できない。WRS に貼る文はユーザーが貼る。WRS の報告と実測を正とする。
> 実機側（モーター・T265・制御ループ）は `next_chat_briefing_motor.md`、コントローラーは `controller_prep_briefing.md`。このチャットは学習側と「今日の仮デプロイに何を持っていくか」の判断を受け持つ。
 
## 0. 最初にやること
1. この文書を読む（README は索引の確認だけ）。
2. ユーザーに WRS の朝の報告を貼ってもらう: `D:\Tominaga\slope-climbing-robot\tools\logs\MORNING_0945.md` の冒頭3行・判定の表（無ければ `NIGHT_LOG_20260918.md` の末尾 30 行）。
   - 表示のコマンド（WRS機の PowerShell、どこで実行してもよい）: `Get-Content D:\Tominaga\slope-climbing-robot\tools\logs\MORNING_0945.md`
3. §2 の規則で今日の仮デプロイの方策を決め、ユーザーに伝える。再生コマンドは MORNING_0945.md に実名で入っている（Cowork で作り直さない）。
4. 09:45 の予約メッセージは前のチャット（`2026-09-18_overnight-and-controller` のチャット）に届く。こちらでは使わない。
## 1. 現在地（2026-09-18 01:10 時点。夜間の結果で上書きする）
- ゴール: まず平地で実機デプロイ（今日 09-18 に仮デプロイ＝吊った状態で方策をつなぐ想定）。坂は後回し。
- **まっすぐのデプロイ候補:** H_eff13p5@2999（第一）、G_real_peak@2999（予備）。
  - 弱点: damping ×2 で転倒（実機の Kd は機種別換算で ×1.0 に合わせられる見込み、09-17 夜に実機側で決着）、stiffness ×0.7 で S1 転倒 6.2%、base_lin_vel を 0 にすると転倒。
  - 速度観測（T265）が途切れたら直前値保持、0.2 s で停止動作。
- **その場旋回（S6 / S9: 前進 0 で ±0.5 rad/s）:**
  - 合格ライン（実験06）: |yaw| ≥ 0.25・符号一致・左右比 0.5〜2、|(vx, vy)| ≤ 0.10、転倒 ≤ 5%、左右とも足を上げる、既存基準を落とさない。
  - 採用規則（実験09 で事前に決定）: 同じ run で連続 300 iter 以上の合格（256 env・評価 seed 2 回とも）＋既存基準の退行なし＋H_eff13p5 に無い頑健性の不合格を出さない。
  - 実験08: 効いたのは track_ang_vel_z_exp の weight 1.0（std 0.35 だけでは不合格）。
  - 実験09 停止点9a（`REPORT_exp09_stop9a.md`、commit `6f70dfd`）: L_angstd_w1 の合格は 4000・4200 だけ（幅 200 iter）→ 規則上、旋回候補なし。S1 の関節トルク RMS は全関節定格以下（FFE 5.93 / 5.78）。H_eff13p5 に無い不合格が2件: stiffness ×0.7 で全シナリオ 12.5〜42.2% 転倒、速度観測の 0 埋め 0.2 s で 9.4%（H は 1.6%）。歩くと増える罰は 1 step 0.14〜0.17。
- **夜間の自走（`wrs_overnight_20260918_instruction.md`、WRS の新チャット Opus）:**
  - ①仮デプロイ用パッケージ `D:\Tominaga\deploy_pkg\20260918\`（H_eff13p5_2999 / G_real_peak_2999 / L_angstd_w1_4000 実験用、DEPLOY_README.md、`deploy_pkg_20260918.zip`）
  - ②1巡目3本: T1 N_w1_seed2、T2 N_w1p5（00:48 に iter 3049、02:30 ごろ終了見込み）、P1 P_gainDR_narrow（H_eff13p5@2999 ＋ stiffness ×0.85〜1.15・damping ×0.8〜1.25）
  - ③2巡目は事前の規則（旋回: (a) 合格範囲あり → ゲインのランダム化を足す O_turn_gainDR / (b) weight 1.5 の方が合格が多い → O_w2 / (c) それ以外 → その場旋回の指令 0.35 の O_turn35。まっすぐ: P1 合格 → P2_seed2 / 静止に落ちた → P2_stiffonly / それ以外 → 旋回に枠を回す）。07:00 以降は新規起動なし
  - ④許した手直し5種類（落ちたら1回だけ再開、VRAM 不足で env 半分、noise std 崩壊で止める、評価ハングで env 半分、他人のプロセスで新規起動をやめる）
  - ⑤09:30 に `REPORT_night_20260918.md`、09:45 に `MORNING_0945.md`（結論・表・普通に見る用と動画用の再生コマンド）
- 未 push のコミット: `664105a` 〜 `f7131f4`、`6f70dfd`、夜間の commit。push の手順は §3。
## 2. 朝に決めること（規則。結果を見てから変えない）
- **今日の仮デプロイの方策:**
  - 既定は H_eff13p5@2999。
  - P_gainDR_narrow@4498 が「既存基準に合格・c06（stiffness ×0.7）の転倒 ≤ 5%・H_eff13p5 に無い不合格なし」を満たし、deploy_pkg にパッケージ（golden npz・verify・SHA256）がそろっていれば、第一候補を P_gainDR_narrow に替えてよい。そのときも H_eff13p5 は予備として持っていく。
  - 旋回の方策は、採用規則を満たしても今日は「吊って見るだけ」。満たさなければ L_angstd_w1@4000 を実験用のまま。
- **確認すること:** deploy_pkg の zip があるか、DEPLOY_README.md の数値（観測 42 次元・行動 10 次元・scale 0.5・50 Hz・アクチュエータ表）が obs_contract と一致しているか、SHA256。夜間ログに異常や諦めた枠がないか。
- **ユーザーの再生の所感を聞く:** 普通に見る用・動画用で見た印象（歩き方、旋回、足の運び）。数値と食い違ったら記録する。
- 次の学習（今日の昼以降）の候補は、夜間の結果を見てから1〜2本に絞る。9b 相当でも旋回が安定しなければ、左右対称のデータ拡張、またはその場旋回の指令中だけ罰（歩くと増える 0.14〜0.17）を緩める案。
## 3. push の手順（ユーザーが WRS機の PowerShell で。WRS の Claude Code は push しない）
実行ディレクトリ: `D:\Tominaga\slope-climbing-robot`
```
cd D:\Tominaga\slope-climbing-robot
git status --short
git log --oneline origin/main..main
git diff --stat origin/main..main | Select-String -Pattern "\.pt|\.onnx|\.npz|\.usd|\.stl|\.env|\.bak"
git push origin main
git log -3 --format="%h %ad %s" --date=iso origin/main
```
1行版:
```
cd D:\Tominaga\slope-climbing-robot; git status --short; git log --oneline origin/main..main; git diff --stat origin/main..main | Select-String -Pattern "\.pt|\.onnx|\.npz|\.usd|\.stl|\.env|\.bak"; git push origin main; git log -3 --format="%h %ad %s" --date=iso origin/main
```
- 3行目で何か出たら push しない。PAT はチャットに貼らない。push 後に WRS でハードリンク5組の `Get-FileHash` を確認。
- 学習や評価が走っている間でも push は問題ないが、夜間の commit が終わってから（09:30 以降）の方が1回で済む。
## 4. デプロイは旋回と切り離して進められる
- 実機側の M1〜M9（`next_chat_briefing_motor.md`）は方策の旋回と独立。今日（09-18）は残りのモーターの配線予定。
- 旋回の方策も観測・行動の契約は H_eff13p5 と同じ（同じ env から resume）なので、制御ループ ver9 は共通。golden npz だけ差し替える。
- コントローラー（Switch 2 Pro）の準備は別チャット（`controller_prep_briefing.md`）。指令の範囲・並びは DEPLOY_README.md を正とする。
## 5. ユーザーとの対話・トークン節約の運用
- 返信の冒頭で「いま何が起きていて、次に何をするか」を短く。略号は初出で意味を添える。
- WRS に貼る文はコードブロック1つ。停止点を明示し「推測で直さず止まって報告」を入れる。
- **WRS の報告は、ユーザーに冒頭3行＋判定の表だけ貼ってもらう。** 詳細は WRS 側の報告書ファイルに残させ、必要な節だけ追加で貼ってもらう。
- ユーザーが「了承系はすべて了承」と言ったら、Cowork の推奨どおり進め、何を決めたかを返信に明記する。
- 大きい文書を丸ごと書き直さない。README の「現在の状況」は増やさず、この文書の §1 を上書きする。chats/ は追記。
- WRS のチャットは Opus で。Sonnet で進めていたことがあった（09-17）。
- 積み残しの文書整理（ユーザーの了承を得てから）: README を 5,000 字以内の索引にし、「現在の状況」の古い行を `wrs_training_history.md` へ移す。`training_runs.md` に停止点4・実験06〜09・夜間の結果を追記（停止点4 から止まっている）。
- 終わる前に `chats/YYYY-MM-DD_件名.md` を作り、README の索引に1行追加する。
 