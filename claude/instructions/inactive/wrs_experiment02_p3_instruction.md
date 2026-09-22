# 指示書 実験02 P3（改訂版）: 旋回・rough への移行・姿勢保持の診断（WRS機に貼る）

> 作成 2026-09-16 13:30。`instructions/inactive/wrs_experiment02_instruction.md` の P3 を**差し替える**。停止点1の報告（C_flatonly が 2400 で歩いた、rel_heading_envs の件、action 0 で前に倒れる）を受けて改訂。
> 根拠は `reference/crab_standstill_countermeasures.md` §5。

```
# 指示: 実験02 P3 改訂版（元の P3 は破棄。これに差し替える）

停止点1の報告を読んだ。C_flatonly の iter 2400 まで追ってくれたおかげで結論が変わった。以下で進めてほしい。
このメッセージを貼ったこと自体が、下の commit と P3 の起動の了承。

## 変更の理由（読むだけ）
- 立ち往生の分かれ目は地形（rough 2本は立ち往生、平地 2本は歩いた）。報酬・std の違いは「歩き出す時期」だけで、1000 か 2400 かは seed 1本では揺れと区別できない。だから D_noStd / D_noBiped（歩き出す時期の切り分け）はやめる。
- 目的は坂なので、次に知りたいのは「平地で歩ける方策を rough に移すと、レベル 0 から上がれるか」。
- 旋回は rel_heading_envs=1.0 のせいで、直接の旋回指令が一度も出ていなかった。E_yawcmd はそのまま回す。
- action 0 で倒れるのは、COM が支持多角形の中（前余裕 6.6 cm）にあるので、重心の位置より PD の剛性不足で関節が沈むせいの可能性が高い（stiffness 10〜15 で膝に数 N·m かかれば 0.2〜0.5 rad 沈む）。安い診断で確かめる。

## P2.5 commit（先にやる）
- コミット候補から tools\\runs\\TEST_A.ps1 と tools\\runs\\TEST_B.ps1 を外す（削除はしない。git の管理に入れないだけ）。残りの候補で commit する。
- commit 後に git log -1 --stat を報告に載せ、ユーザーが PowerShell で打つ push の1行（実行フォルダ付き）を表示して、学習の起動に進んでよい（push を待たない）。
- commit 後にハードリンク5組の Get-FileHash とリンク数を確認。

## P3a 姿勢保持の診断（学習の起動前に。GPU は短時間）
tools\\stance_check.py の action 0 の試験を、アクチュエータの stiffness だけ変えて3条件で回す（damping はそのまま）:
- 現状（hr 10 / haa 15 / kfe 15 / ffe 10）
- 2倍
- 4倍
それぞれ: 5 s 後の転倒率、倒れた向き、0.5 s 時点の各関節の「目標角との差」（左右平均、rad）、10 s 生存した env の pitch 平均。
Hydra の上書き（env.scene.robot.actuators.グループ名.stiffness=値）が効くかは params で確認。効かなければスクリプト内で cfg を書き換える。これは診断だけで、学習の cfg は変えない。

## P3b 本番（2本同時に起動、4096 env）
共通は B の起動行（平地は sub_terrains の proportion 方式、noise_std_type=log、feet_air_time_biped w0.25、feet_air_time w0、std 0.35）。

1. E_yawcmd（--run_name E_yawcmd、--seed 1、--max_iterations 2000）
   - B ＋ env.commands.base_velocity.rel_heading_envs=0.5
   - params\\env.yaml で heading_command=True と rel_heading_envs=0.5 を確認。
   - 評価: iter 1000 / 1600 / 1999 で measure_crab.py。

2. F_BtoRough（--run_name F_BtoRough、--seed 1）
   - B_combined の model_2999.pt から再開し、地形だけ 08-21 の rough に戻す（平地の proportion 上書きを外す。terrain_levels カリキュラムは有効のまま＝A と同じ地形設定）。報酬・std・biped は B のまま。
   - 再開は train.py の --resume --load_run 2026-09-16_05-15-41_B_combined --checkpoint model_2999.pt。追加で回す iter 数が 1500 になるよう --max_iterations を決める（rsl_rl の learn が「追加 iter 数」か「通算」かを grep で確かめてから。報告に書く）。
   - 起動直後に: 読み込んだチェックポイントのパス、iter 番号の始まり、Mean action noise std が B の最終（約 0.40）付近から始まることを確認。
   - 評価: 再開後 +500 / +1000 / +1500 で measure_crab.py（平地の評価プロトコルのまま＝平地の歩行を忘れていないか）。あわせて学習ログの Curriculum/terrain_levels、正規化 error_vel_xy、base_contact / time_out を 100 iter ごとに記録。
   - 途中の目安: +500 で terrain_levels が 0 のまま、かつ平地評価の S1 静止率が 50% を超えたら、止めずにそのまま報告だけ（判断はユーザー）。

## 【停止点2】E_yawcmd の 1999 と F_BtoRough の +1500 の評価が終わったら報告して止まる
- 冒頭: 2本の判定（カニ歩き・立ち往生・転倒）1行ずつ
- P3a の表（stiffness 3条件）
- E_yawcmd と B の比較: S6 yaw rate、S1〜S5、正規化 error_vel_yaw（500 / 1000 / 1600 / 1999）
- F_BtoRough: terrain_levels の推移、平地評価の S1 / S2 / S4 / S5 / S6（B@2999 と並べる）、終了理由の推移
- 所見3行以内、次の候補1〜2個

## やらないこと
- アクチュエータの学習 cfg（stiffness・effort・friction・グループ）は変えない（P3a は診断のみ）
- 指令レンジ（lin_vel_x / lin_vel_y / ang_vel_z）は変えない
- push はしない（ユーザーが行う）。何も削除しない
```
