# 指示書 実験02: 切り分けの仕上げ・seed 再現・旋回（WRS機の Claude Code に貼る）

> 作成 2026-09-16 昼。実験01（`instructions/inactive/wrs_experiment01_instruction.md`）と同じ WRS側チャットに続けて貼る。
> 根拠は `reference/crab_standstill_countermeasures.md` §4（実験01の結果と訂正）、記録は `reference/training_runs.md`。

```
# 指示: 実験02 切り分けの仕上げ・seed 再現・旋回

実験01の最終報告と切り分け報告を読んだ。よくやってくれた。掟・作法・評価プロトコルはこれまでと同じ。
まず報告の解釈を3点訂正する（次の作業の前提になる）。

## 訂正（読むだけ。P1-3 で実物を grep して確かめること）
1. error_vel_xy / error_vel_yaw はエピソード長に比例して大きくなる。Isaac Lab 2.3.2 の velocity_command.py では毎ステップ誤差 / (resampling_time_range[1] / step_dt) を足し込み、エピソード終了時に記録する。20 s 完走なら「平均誤差の2倍」になる。
   → 比べるときは 正規化値 = 生値 × 500 / Train/mean_episode_length を使う。A の iter 500 の 0.26 は正規化すると 0.61 で、A は最初から歩いていない（「500→1000 で局所解に落ちた」は誤読）。B 2999 は 0.174。error_vel_yaw の「0.33→0.70 と悪化」も正規化すると 0.26→0.38 で、悪化はしているが幅は小さい。
2. max_init_terrain_level を上げると初期地形は難しくなる（None＝全レベルからランダム）。レベル 0 が一番易しい。さらに random_uniform_terrain は difficulty を無視するので、rough の 20 % のタイルはレベル 0 でも noise_range の凹凸がそのまま出る。「上げる」案は立ち往生を増やす方向なので採らない。
3. 切り分けの結論「平地と報酬/std の組み合わせが要る」は iter 1000・seed 1本だけの話。B 自身も iter 1000 では学習ログ上まだ歩き始めたばかりで、C_flatonly は後退をもう獲得している。「1000 で出ない」は「出ない」ではない。

## P0 走っている C_noflat / C_flatonly はそのまま 3000 まで完走させる
- iter 1600 / 2400 / 2999 のチェックポイントで measure_crab.py を実行（A・B と同じプロトコル）。

## P1 待ち時間にやること（読むだけ・学習コードは変えない）
1. 自作 ROUGH_TERRAINS_CFG の全 sub_terrain のパラメータ（proportion、noise_range、amplitude_range、step_height_range、slope_range など）と num_rows / num_cols / size。レベル 0 でそれぞれ何 cm の凹凸・段差・傾斜になるかを表にする。
2. 前進と後退の非対象の手がかり（新規スクリプト tools\\stance_check.py、64 env、平地、評価と同じ中立設定）:
   - 初期姿勢での全身 COM の base 座標 (x, y, z)
   - 左右の足（lr_ffe / ll_ffe）の衝突形状の、base 座標での x の最小・最大（＝支持多角形の前後）
   - action を 0 のまま 5 s 置いたとき: 転倒率、前に倒れたか後ろに倒れたか（base の pitch の符号と COM の x 変位）、10 s 生存した env の pitch 平均
3. Isaac Lab 2.3.2 で確認: velocity_command.py の metrics の式（訂正1）、UniformVelocityCommandCfg の rel_heading_envs の意味、mdp に track_lin_vel_xy_yaw_frame_exp と track_ang_vel_z_world_exp があるか（引数も）。
4. measure_crab.py に参考指標を2つ足す（判定には使わない。評価スクリプトの変更なので可）: 遊脚中の足の最大高さの平均 [cm]（lr_ffe / ll_ffe、接地面からの body 原点の高さでよい。求め方を報告に書く）、1 秒あたりの着地回数。B_combined の 2999 で一度走らせて値を出す。

## P2 git の準備（commit / push はまだしない）
- git status --short と、コミット候補（my_robot_code\\rough_env_cfg.py、tools\\measure_crab.py、tools\\tb_extract.py、tools\\stance_check.py、tools\\runs\\*.ps1）の git diff --stat。.bak・ログ・動画・run フォルダが混ぶまらないことを確認。
- コミットメッセージ案と、ユーザーが PowerShell で打つ push の1行を用意する。

## 【停止点1】C の評価（1600 / 2400 / 2999）と P1・P2 がそろったら報告して止まる
報告:
- C_noflat / C_flatonly の判定（実験01と同じ基準）と、A・B と並べた S1 / S2 / S4 / S6 の表（iter 1000 / 1600 / 2400 / 2999）
- 学習ログの正規化 error_vel_xy / error_vel_yaw（4本 × 500 / 1000 / 1600 / 2999）
- P1-1 のレベル 0 の表、P1-2 の結果、P1-3 の grep 結果、P1-4 の B の値
- P2 の確認結果
ユーザーの了承を待つ。

## P3 本番（了承後）。2本ずつ並走、4096 env、--max_iterations 2000
共通は実験01の B の起動行と同じ（平地は sub_terrains の proportion を flat=1.0 にする方式、noise_std_type=log）。
第1組（同時に起動）:
- B_combined_s2: B と完全に同じで --seed 2（B が seed の当たりだっただけか）
- D_noStd: B から std だけ戻す（track_lin_vel_xy_exp の std 上書きを外す＝0.5）。--seed 1
第2組（第1組が終わったら同時に起動）:
- D_noBiped: B から dense 足上げだけ戻す（feet_air_time_biped の weight 0、feet_air_time の weight 2.0 のまま＝上書きを外す。std 0.35 と平地は残す）。--seed 1
- E_yawcmd: B ＋ env.commands.base_velocity.rel_heading_envs=0.5（半分の env は旋回速度を直接指令）。--seed 1
- それぞれ iter 1000 / 1600 / 2000 で measure_crab.py。起動直後の iter 確認、params\\env.yaml で上書きの反映確認はこれまでどおり。
- 1本目の iter 30 で秒/iter を記録。第2組は第1組の iter 2000 の評価が終わってから起動してよい（ユーザーの再確認は不要）。

## 【停止点2】第2組の 2000 の評価が終わったら報告して止まる
- 冒頭: 各ランの「カニ歩き・立ち往生・転倒」判定を1行ずつ
- B / B_combined_s2 / D_noStd / D_noBiped / C_noflat / C_flatonly の比較表（iter 1000 / 1600 / 2000、S1 / S2 / S4 / S5 / S6、静止率、転倒率、足の最大高さ、着地回数）
- E_yawcmd と B の S6（yaw rate）と正規化 error_vel_yaw の比較
- 所見3行以内、次の候補1〜2個

## やらないこと
- アクチュエータ・指令レンジ（lin_vel_x / lin_vel_y）・地形カリキュラムの設定は変えない
- 走っているランの cfg を変えない
- commit / push はしない（P2 は準備だけ）
- 何も削除しない
```
