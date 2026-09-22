# WRS CLI 用: 自動旋回・直接旋回の実装とコマンド作成（2026-09-21）

> WRS機の新しいCLIチャットへ、下のコードブロックをそのまま貼る。終点は実装・64 envテスト・前景実行用コマンドの返答であり、本番学習はCLIに開始させない。結果評価と文書更新はノートPC側の別チャットが行う。

```text
WRS機で、旋回方法の異なる2つの実験用方策を実装し、64 env / 20 iter のテストまで行ってください。本番学習、再生、評価、監視は開始しないでください。

テストが両方通ったら、最後に次だけを返して止まってください。
1. `READY`、変更ファイル、ハードリンク5組のSHA256一致・リンク数確認結果
2. 実験A / B の64 envテスト結果と、テストrunのparamsで確認した実効設定
3. 実験Aを前景で実行する完全なPowerShell一行
4. 実験Bを前景で実行する完全なPowerShell一行
5. 実験A / B の平地16 env・固定checkpoint用の完全なplay PowerShell一行

ユーザーが上のtrainコマンドを自分のPowerShellで実行する。本番学習をあなたが起動したり、Start-Process、バックグラウンド実行、逐次runner、監視、待機、ログ確認、評価をしてはいけない。結果確認とMarkdown更新はノートPC側の別チャットの担当である。

開始時に `nvidia-smi` と `git status --short` を各一度だけ確認する。他人の計算プロセスがGPUを使用中なら、何も起動せずPID・使用量だけ報告して止まる。他人のプロセスには触らない。git操作、install、削除、Isaac Lab本体の変更、実機/CAN/モーター/T265操作は禁止。`D:\\Tominaga\\` の外へ書かず、README、project_handbook、training_runs、chats、reportsなどのMarkdownは一切編集・作成しない。

編集前に対象自作ファイルの `.bak_20260921_autoturn_directturn` を作る。5組のハードリンクはin-place編集し、編集後にSHA256とリンク数2を確認する。Hの実run `2026-09-19_21-34-51_H_eff13p5_extend_20000` の `model_19998.pt`、params/env.yaml、params/agent.yaml、および実在するプリロード起動・playラッパーを読んでから作業する。起動方法を推測しない。

共通条件: H `model_19998.pt（これはあなたが最適な場所を選んで。こんなところから始めたら意味ない気もする。そのほかもこのプロンプト柔軟に変更してよい。）` からresume、各4096 env・追加3000 iter・checkpoint保存間隔200 iter。平地はsub_terrainsをflat=1.0・他0.0、terrain_levels=null。`agent.policy.noise_std_type=log`。実効weight 2.0の `feet_air_time` は `yaw_gate=true`。weight 0の `feet_air_time_biped` を有効化して代用しない。`track_ang_vel_z_exp` はweight=1.0、std=0.35。gain DR、トルク上限、観測次元、行動次元、その他の報酬はHと同一。

実験Aのrun名は `A_auto_heading_world_H20000`。`rough_env_cfg.py` に専用velocity command termを追加する。単に `rel_heading_envs` を増やしてはいけない。再サンプル時、世界座標の目標速度の大きさを0.25〜0.70 m/s、方向を現在yawから[-pi, pi]で均等に選ぶ。目標headingは同じ世界速度ベクトルの方向から作る。毎updateで目標世界速度を現在の胴体座標へ変換し、方策が受ける `(vx_body, vy_body)` とする。同じ目標headingとのyaw差から既存Isaac Labと整合する `wz` 指令を作る。角度差はwrapし、既存指令レンジでclipする。観測・行動の次元を変えない。

実験Bのrun名は `B_direct_wz_turn_H20000`。`(vx, vy, wz)` を直接操作する専用command termを追加する（既存TurnAwareVelocityCommandでこの内訳を正確に保証できるなら拡張してよい）。再サンプル時の割合を以下に固定する。
- 38%: `(0, 0, ±U(0.3, 1.0))`
- 30%: `(U(0.2, 0.7), 0, 0)`
- 30%: `(U(0.2, 0.6), 0, ±U(0.2, 0.6))`
- 2%: `(0, 0, 0)`
heading処理が直接指定したwzを再上書きしないようにする。64 envテストで、各カテゴリの指令が次updateで壊れないことを確認する。

両実験を64 env / 20 iterでテストする。テストrunのparams/env.yamlとagent.yamlから、平地上書き・terrain_levels=null・`feet_air_time.weight=2.0`かつ`yaw_gate=true`・Aの世界速度とheadingの対応・Bの38/30/30/2カテゴリとheading再上書き防止・`noise_std_type=log`を確認する。テストまたはハードリンク検証が失敗したら、train/playコマンドを作らず、原因とdiff要点だけを報告して止まる。
```
