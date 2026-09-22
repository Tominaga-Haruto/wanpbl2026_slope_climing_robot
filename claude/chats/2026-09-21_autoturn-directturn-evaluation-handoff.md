# 自動旋回・直接旋回実験の評価引継ぎ

日付: 2026-09-21

## 現在地

WRS側CLIには、実験A/Bの実装、64 env / 20 iterテスト、および前景実行用train/playコマンドの作成だけを依頼する。本番学習はユーザーが前景PowerShellで実行し、結果評価と文書更新はノートPC側の後続チャットが行う。

既存の第一回デプロイ候補はH `model_19998.pt`（前進・緩い移動旋回用）のまま。A/Bは評価前の実験方策であり、候補を置き換えない。

## 実験A: `A_auto_heading_world_H20000`

- 再開元: H `model_19998.pt`。平地、4096 env、追加3000 iter、200 iterごとに保存。
- 世界座標の目標移動ベクトルと同じ方向をheading目標にし、毎stepで世界速度をbody速度指令へ変換する。
- 評価: heading誤差、向き直り時間、目標方向速度成分、横ずれ、転倒率。前進・小旋回・トルクもHと比較する。

## 実験B: `B_direct_wz_turn_H20000`

- 再開元: H `model_19998.pt`。平地、4096 env、追加3000 iter、200 iterごとに保存。
- 指令比: 純旋回38%、前進30%、歩行旋回30%、静止2%。純旋回は `(0, 0, ±U(0.3, 1.0))`。
- 報酬: `track_ang_vel_z_exp` weight 1.0 / std 0.35、有効な`feet_air_time`は`yaw_gate=true`。
- 評価: S6/S9を256 env・評価seed 2回で測る。両方向で符号一致、`|wz| >= 0.25 rad/s`、`|(vx,vy)| <= 0.10 m/s`、転倒率5%以下、左右とも歩行、S6/S9比0.5〜2を要求する。S1〜S8・トルクもHと比較する。

## 評価前に回収するもの

- CLIが返した実装クラス名、変更ファイル、64 envテスト結果、train/playの完成コマンド
- A/Bのrunフォルダ名、params/env.yaml、params/agent.yaml、各checkpoint
- 学習ログと保存点ごとの評価結果

評価後にだけ、`training_runs.md`、`project_handbook.md`、READMEの現在地を実測に基づき更新する。
