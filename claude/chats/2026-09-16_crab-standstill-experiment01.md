# 2026-09-16 カニ歩き・立ち往生の対策案と実験01の設計

## やったこと
- README → handbook → handover → next_chat_briefing → wrs_training_strategy → robot_model_conventions → wrs_training_operator_instruction を読んだ。
- ユーザーの依頼: カニ歩き・立ち往生をやめさせる案を全部出す／「約6時間 GPU を使って全部入りを一から回し、ダメなら修正、良ければ1つずつ試して原因を切り分ける」案の評価／WRS側への指示書。
- 立ち止まりの給料を指令レンジ別・std 別に数値計算（Cowork 側の Python、dt と std は Isaac Lab 既定を仮定）。
- 対策案の全リスト `crab_standstill_countermeasures.md`、WRS側に貼る指示書 `wrs_experiment01_instruction.md`、ラン記録の雛形 `training_runs.md` を新設。

## 決めたこと・分かったこと
- **ユーザー案（全部入り → 切り分け）は妥当。ただし:** ①最小変更の A（08-21＋log std）を並走させる（base の修正だけで十分だったかは B を削っても分からない）②全部入りは「直す系」だけで「縛る系」（アクチュエータ実機化）は入れない ③B の変更を3系統に絞って leave-one-out、冗長なら A に足す実験で補う、seed 2本 ④評価プロトコルと判定基準を先に固定（平地・固定指令）。
- **立ち止まりの給料（満点比）: 08-21 既定 0.24 → 戦略文書 §4 の「x (−0.3,0.6)、y ±0.3」だと 0.55（2.3 倍）。** → 実験01では指令レンジを変えない。`wrs_training_strategy.md` §4 の指令案は立ち往生のリスクがある（戦略文書側は未修正。判定後に書き換える）。
- **track_lin_vel_xy_exp の std 0.5 だと横残差 0.2 m/s で報酬 15% 減にしかならない＝カニ歩きがほぼ罰されない。** std 0.35 で横流れの罰と立ち止まりの給料削減が同時に効く → B に採用。
- 実験01: A_base0821（log std のみ・rough）/ B_combined（＋平地＋dense 足上げ G1 値＋std 0.35）/ B_combined_s2（seed 2、資源次第）。変更は weight 0 の報酬項をコードに足し、差は起動行の Hydra 上書きだけにする。判定は iter 1600。
- 次の波の最有力: 左右対称性の拡張（rsl_rl symmetry）。写像の試験付きで入れる。

## 手を動かした場所
- 新規: `claude/crab_standstill_countermeasures.md`、`claude/wrs_experiment01_instruction.md`、`claude/training_runs.md`
- 更新: `claude/README.md`（現在の状況・指示書の表・索引）
- WRS機・コードには何もしていない。

## 積み残し・次にやること
- ユーザーが WRS機の Claude Code に `wrs_training_operator_instruction.md` → `wrs_experiment01_instruction.md` の順に貼る。停止点1の報告を読んで起動可否を判断。
- 停止点1で確認: dt/decimation（給料計算の前提）、root_lin_vel_b が COM か、G1 の足上げ報酬の値、Hydra の null 上書きが効くか。
- 停止点2（iter 1600）の判定で分岐（`crab_standstill_countermeasures.md` §3）。結果を `training_runs.md` に記入し、`wrs_training_strategy.md` §4 と handbook A0/A5 を書き換える。
