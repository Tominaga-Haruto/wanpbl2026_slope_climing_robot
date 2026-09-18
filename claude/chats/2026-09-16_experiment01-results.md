# 2026-09-16 実験01の結果の読み取りと実験02の設計

## やったこと
- WRS側の `REPORT_exp01_final.md`（A・B 3000 iter、1000/1600/2400/2999 評価）と `REPORT_ablation.md`（C_noflat / C_flatonly の iter 1000）を読んだ。
- Isaac Lab v2.3.2 のソースを Cowork 側で sparse clone して、velocity_command.py の metrics、terrain_levels_vel、random_uniform_terrain、terrain_importer の max_init_terrain_level を確認。
- 学習ログの error_vel をエピソード長で正規化して再計算。
- `crab_standstill_countermeasures.md` に §4（結果・訂正）を追記、`training_runs.md` を記入、`wrs_experiment02_instruction.md` を新設、README 更新。

## 決めたこと・分かったこと
- A（08-21＋log std、rough）は全 iter で完全静止。B（平地＋biped 足上げ w0.25＋std 0.35）は 1600・2999 で全基準合格、2400 は yaw rate 0.105 で一度外れる。B は旋回しない（S6 +0.028）、滞空 0.07〜0.11 s。
- **error_vel_xy/yaw は「毎ステップ誤差 / 500 step」の積算＝エピソード長に比例。** 正規化値＝生値×500/episode 長。A は 500 iter 時点で正規化 0.61＝最初から歩いていない（WRS側の「500→1000 で局所解へ転落」は誤読）。B は 0.16〜0.17。error_vel_yaw の悪化も正規化で 0.26→0.38 と小さい。手順書 A5・operator 指示書 §6 の目安は要修正（未修正）。
- **max_init_terrain_level を上げると初期地形は難しくなる（None＝全レベル）。random_uniform は difficulty を無視＝レベル0でも凹凸そのまま。** WRS側の「rough のまま max_init を上げる」案は採らない。
- 切り分けの「平地と報酬/std の組み合わせが要る」は iter 1000・seed 1本だけ。B の seed 再現も無い。C は 3000 まで完走させて評価する。
- 旧 feet_air_time（threshold 0.2 s）は、この機体が出した滞空 0.07〜0.11 s では毎歩マイナス（A の報酬項は終始負）。
- 並走は速くならない（2本で合計 +17%）。実験の並行性のためだけに2本並走。
- 実験02: C 完走評価＋読むだけ調査（レベル0の地形、COM と足の支持範囲・action 0 で倒れる向き、yaw 系報酬関数）→ 停止点1 → 第1組 B_combined_s2 / D_noStd → 第2組 D_noBiped / E_yawcmd（rel_heading_envs 0.5）、各 2000 iter。

## 手を動かした場所
- 新規: `claude/wrs_experiment02_instruction.md`、この chats ファイル
- 更新: `claude/crab_standstill_countermeasures.md`（§4 追記）、`claude/training_runs.md`、`claude/README.md`
- WRS機・コードには何もしていない。

## 積み残し・次にやること
- ユーザーが WRS側に実験02の指示書を貼る。停止点1で commit / push（rough_env_cfg.py の weight 0 項と tools スクリプト）を判断。
- ユーザーが WRS機の本体ディスプレイで B の録画を見る（すり足か）。
- 手順書 A5・`wrs_training_operator_instruction.md` §6 の error_vel の目安を正規化値に書き換える。`wrs_training_strategy.md` §4 と handbook A0 に実験01の結論を反映する。
