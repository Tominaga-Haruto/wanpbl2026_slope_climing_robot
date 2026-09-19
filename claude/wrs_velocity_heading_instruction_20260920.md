# WRS CLI 用: world 目標速度へ機首を合わせる学習（2026-09-20）

以下を WRS の CLI にそのまま渡す。これは実機を動かす作業ではない。

```text
これから寝るので、質問で止まらず、以下の範囲だけを自走してください。実機・CAN・モーターには一切触らない。共有GPUなので最初に nvidia-smi と git status --short を確認し、他人の計算プロセスがあれば新規学習は起動せず、確認結果だけ報告する。fetch/pull/reset/checkout/restore/stash/削除/インストール/Isaac Lab本体の編集はしない。

目的は、H_eff13p5@2999 を壊しにくく再開しつつ、ロボットが「world座標で与えられた移動方向へ機首を向け、その方向へ歩く」方策を学べるかを15,000追加iterで確かめること。body座標の vy を単純に罰する報酬は作らない。これは「前を向いたまま横移動」の既存モードを壊すため。

最初に、D:\Tominaga\slope-climbing-robot の README、project_handbook、既存の rough_env_cfg.py、rewards.py、tools\runs の launcher、H_eff13p5 / J_turn_resume / L_angstd_w1 の実run params\env.yaml と agent.yaml、現在のIsaac Lab 2.3.2の UniformVelocityCommand の実装を読む。ハードリンク済みファイルとリンク数・SHA256を確認する。以後の実装は現在の実コード/APIに合わせ、推測で属性名を使わない。

`TurnAwareVelocityCommand` を後方互換のまま拡張する。新しい cfg は既定値0.0の `rel_velocity_heading_envs` と、既定 `(0.3, 1.0)` の `velocity_heading_speed_range` を持つこと。新モードを選んだenvでは、resample時に world XY の速度目標とその heading を保存し、各simulation stepで現在yawから world目標をbody座標の `(vx,vy)` へ再投影する。heading_target はそのworld目標の角度、is_heading_env=True、is_standing_env=False にする。従ってロボットが目標方向へ回るほど、body command は前進成分へ移る。世界速度目標は次式でよい: speed*[(cos heading),(sin heading)]。body変換は R(-current_yaw)*world_velocity。純旋回、world-heading移動、translate-onlyは相互排他的に選ぶ。既存の rel_* が全て0なら挙動を完全に変えないこと。

このrunでは、純旋回=0.20、world-heading移動=0.30、translate-only=0.15、残りは既存の通常指令にする。純旋回は従来どおり vx=vy=0, wz=+-U(0.3,1.0) とし、heading/standingに後から潰されないこと。`track_ang_vel_z_exp` は std=0.35、weight=1.0。weightが0でない足上げ項には yaw_gate=true を入れ、純旋回中の足上げを加点対象にする。通常の速度追従、罰、アクチュエータ、地形（flat以外0）はHと同じにする。

実装後、まず64 env / 20 iter / headlessのテストrunを行う。params env.yaml と agent.yaml をHおよび必要なJ/L runとdiffし、差がこのworld-heading機能、旋回比率、yaw報酬、run名、平地だけであることを確認する。コマンド統計を拡張または追加し、4分類（pure turn / world-heading / translate-only / normal）の比率、world-heading envのtarget heading・変換後body command・heading targetが実際に更新されることをログで確認する。ImportError、Hydra key不一致、NaN、意図しない差分があれば本番は起動しない。

テストに合格した場合だけ、H_eff13p5 model_2999.ptから4096 env、追加15,000 iter、seed 1、noise_std_type=logで本番をフォアグラウンド起動する。実在のプリロード起動方法とHのparamsから完成した一行を組み立てる。run名は `V_world_heading_turn20_extend_18000` とする。開始後30iterで秒/iter・予想終了時刻・GPU温度/VRAM・ログのnan/traceback有無を記録し、以後30分ごとに確認する。他人のGPUプロセスが現れたら新規評価は開始しない。学習が落ちた場合は原因を記録し、保存済みcheckpointから同じ条件で1回だけ再開する。

保存間隔は200iterにする。終了後、S1--S9を既存基準で評価し、S6/S9は256 env・評価seed 2回で評価する。加えてworld-heading専用の固定評価を作る: 初期yawを目標移動方向から+90度と-90度にし、world速度目標を固定して、2秒後以降の (1) world速度と目標の角度誤差、(2) base forwardとworld速度の角度誤差、(3) heading誤差、(4)転倒率、(5)前進/横移動残差を記録する。採用候補の条件は既存S1--S8・トルクを落とさず、S6/S9の基準を評価2回とも満たし、world-heading評価で両符号ともheading/進行方向が目標の±20度以内かつ転倒5%以下が連続300iter以上続くこと。満たさなければ実験用と明記し、H_eff13p5をデプロイ候補のままにする。

作業結果は tools\logs\REPORT_world_heading_20260920.md と docs\experiments に、実装差分、正確な学習コマンド、テスト結果、評価表、採否、既知の失敗を記録する。コードと文書だけを対象にコミットする。pushはしない。最後に、実際に使った完成したtrainコマンド、最良checkpointのplayコマンド、結果要約を返す。
```
