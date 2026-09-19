# WRS CLI 用: 旋回学習コマンドの確認だけ（2026-09-20）

以下を WRS の CLI に貼る。CLI にコード変更・テスト・学習・待機・監視をさせない。

```text
調査だけを短く行い、ファイルを編集せず、コマンドを実行せず、学習も評価も監視も開始しないでください。実機/CAN/モーター、Git操作、インストール、削除、Isaac Lab本体変更は対象外です。

読む対象は必要最小限に限定します: H_eff13p5 の実runの params\env.yaml / agent.yaml、平地の既存train/playコマンド、tools\runs\_preload_h5py_and_run.py、現在使われている rough_env_cfg.py の TurnAwareVelocityCommand と rewards の該当箇所だけです。

目的は、H_eff13p5@model_2999.ptから追加15000 iter、平地、4096 envで、既存実装だけを使う旋回実験の完成コマンドを確定することです。world座標の速度方向へ自動で機首を向ける新機能はコード追加が必要なので、今回は提案も実装もしないでください。

既存の実装に存在すると確認できた場合だけ、次を上書き候補にしてください: rel_heading_envs=0.5、rel_standing_envs=0.02、rel_turn_in_place_envs=0.35、rel_translate_only_envs=0.15、track_ang_vel_z_exp の std=0.35 / weight=1.0、weightが非0の feet_air_time 項の yaw_gate=true、全sub_terrainsでflat=1かつ他=0、terrain_levels=null、noise_std_type=log。run名は `T_turn35_w1_extend_18000`。

返答は次の3行だけにしてください。説明、ログ、表、計画、監視提案は不要です。
1. `CHECK: PASS` または `CHECK: BLOCKED - <不足している実在情報だけ>`
2. `TRAIN: <PowerShell一行>`（PASS時のみ。フォアグラウンドで動く実在のプリロード起動方法を使う）
3. `PLAY: <PowerShell一行>`（PASS時のみ。平地16 env、model_2999.ptを再生する完成コマンド）
```
