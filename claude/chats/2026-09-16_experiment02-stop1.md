# 2026-09-16 実験02 停止点1の読み取りと P3 の差し替え

## やったこと
- WRS側の停止点1の報告（チャットに貼られた要約。`REPORT_exp02_stop1.md` / `stance_check.md` / `P1_terrain_level0.md` / `P1_grep_results.md` は WRS機にある）を読んだ。
- P3 を差し替える指示書 `wrs_experiment02_p3_instruction.md` を作成。`crab_standstill_countermeasures.md` §5、`training_runs.md`、README を更新。

## 決めたこと・分かったこと
- C_flatonly（08-21 報酬＋平地）が iter 2400 で歩き出した（S1 0.492、S2 0.921、静止 0%・転倒 0%）。C_noflat（rough＋biped＋std）は 2999 でも立ち往生。**立ち往生の分かれ目は地形。** 報酬/std は歩き出す時期（1000 対 2400）とカニ歩き基準の合否（C_flatonly は S1 進行方向角 −14.3°）の差だけで、seed 1本。
- 旋回: rel_heading_envs=1.0 で全 env が heading 追従、サンプルした ang_vel_z は上書き＝直接の旋回指令が出ていなかった（WRS側 grep）。
- action 0 で前に倒れる。COM は支持多角形の中（前余裕 6.6 cm）なので、剛性不足（stiffness 10〜15）で関節が沈むのが原因という読みを提示。stiffness 1×/2×/4× の診断を依頼。
- D_noStd / D_noBiped / B_combined_s2 は中止（歩き出す時期の比較は seed 1本では揺れと区別できない）。代わりに E_yawcmd（旋回指令）と F_BtoRough（B@2999 から rough へ再開、坂への道）。
- commit は TEST_A/B.ps1（EULA 変数なしの失敗版）を除外して実施。push はユーザー。

## 手を動かした場所
- 新規: `claude/wrs_experiment02_p3_instruction.md`、この chats ファイル
- 更新: `claude/crab_standstill_countermeasures.md`（§5）、`claude/training_runs.md`、`claude/README.md`

## 積み残し・次にやること
- ユーザーが WRS側に P3 改訂版を貼る → commit 後に push（PowerShell）。
- 停止点2で E_yawcmd と F_BtoRough を判定。
- 録画（すり足か）は未確認。手順書 A5・operator 指示書 §6 の error_vel の目安、handbook A0 と `wrs_training_strategy.md` §4 に実験01/02の結論を反映する作業が残っている。
