# 2026-09-16 ゴールを平地に変更し、実機準拠アクチュエータで一から学習する指示書を作成

## やったこと
- ユーザーから、別チャット（`chats/2026-09-16_deploy-readiness-and-goal-design.md`）で整理したデプロイまでの現状と、WRS側の途中経過（14:53）を受け取った。
- `actuator_params.md` を読み、実機値（effort・armature・friction・MIT レンジ）を確認。
- WRS機の新チャット向けに `wrs_experiment03_instruction.md`、次の Cowork チャット向けに `next_chat_briefing.md`（夕版に全面書き換え）を作成。`training_runs.md`、README を更新。

## 決めたこと・分かったこと
- **ゴール変更（ユーザー決定）: 平地で実機デプロイを先に。坂は時間が余ったら。** 実機は組み上がっている（ユーザー申告）。
- **ユーザー判断: AK80-9 の実機トルクを超えた設定で学習した方策は意味がないので、一から学習し直す。** Cowork 側も同意。旧設定は HFE / FFE（AK80-9、定格 9・ピーク 22・MIT トルク上限 18）に 20〜30 N·m を許し、HFE を AK10-9 と同じグループにしていた。
- 実験03: 関節ごと5グループ。effort は G_real_peak（AK10 53 / AK80 18）と G_real_rated（18 / 9）を並走し、実機で連続運転できるか（RMS ≤ 定格）をトルク表で判断する。armature 8.116e-3（AK10、計算値）/ 9.77e-3（AK80、実測）、friction 0.37（AK10、暫定外挿）/ 0.22（AK80、実測。Kt 依存の疑いあり）。stiffness・damping・delay・報酬・指令・地形は B と同じ＋rel_heading_envs 0.5。DelayedPD のまま（droop より遅延を優先。関節速度 p95 は無負荷速度より十分小さい見込みで、トルク表で確認）。
- 同時にデプロイ準備: play.py で ONNX、観測・行動の契約 `obs_contract.md`、B のトルクが実機値をどれだけ超えていたか、立てない件の診断（関節をほぼ固定しても倒れるか、足の衝突形状）。
- WRS途中経過: P3a で stiffness 4倍でも前に倒れる＝Cowork 側の「剛性不足で沈む」読みは外れ。F_BtoRough は terrain_levels 4.24、平地の歩行も保持。E_yawcmd は iter 1000 で旋回まだ。

## 手を動かした場所
- 新規: `claude/wrs_experiment03_instruction.md`、この chats ファイル
- 更新: `claude/next_chat_briefing.md`（全面書き換え）、`claude/training_runs.md`、`claude/README.md`

## 積み残し・次にやること
- ユーザーが前の WRS チャットの停止点2を受け取ってから、WRS を新チャットにして operator 指示書 → 実験03 の順に貼る。
- 次の Cowork チャットで実験03の報告を判定。デプロイの合格基準（RMS ≤ 定格など）と旋回の要否をユーザーと決める。
- 柱B の `morg`（MIT 位置原点）と `ramp`（Kp スケール）は学習と並行してノートPCで進められる。
- handbook / handover / operator 指示書の古い記述の修正（next_chat_briefing §4）。
