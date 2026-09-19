# 次チャットへの指示書 — このノートPCの Isaac Lab debugging #11（2026-09-19）

## このチャットの役割

- ここは**ノートPC側の講評・判断チャット**である。WRS側には既に稼働中のCodexがあり、ユーザーが明示して「WRS側の新しいチャット」を求めない限り、新しいWRSチャットを作らない。
- 最初に `README.md`、`project_handbook.md`、`handover.md`、この文書の順で読む。恒久規約は `project_handbook.md` A1/A5 が正本で、この文書へ運用規約を足さない。
- WRS側Codexには、必要な作業を既存チャットへの追記として渡す。実行結果を受けて、このチャットで採点・次の判断を行う。

## 現在地

- **WRS成果物抽出（2026-09-19）:** WRS cloneにはノートPC側の `deployment_01_h_export_instruction.md` が無く、そのパスを読ませる指示は停止した。Hの実在runは `2026-09-17_00-08-51_H_eff13p5` / `model_2999.pt`。次は `wrs_deployment_export_handoff.md` の自己完結プロンプトで、Git操作なし・学習なしにHのONNX、観測契約、golden dataset、アクチュエータ表、SHA256、READMEを抽出する。Pの置換評価は未確定、P2/P3はrough地形で候補外、Lは候補外、Gは予備。Avast HTTPSスキャンでCodex接続が失敗するため、WRS側のGit同期は再開せず、Avast Repair→再起動→hardware network accelerationのみ無効化の順で切り分ける。
- 直進の第一候補は H_eff13p5@2999、予備は G_real_peak@2999。
- P2_gainDR_seed2 / P3_stiffonly は平地上書きを欠き、terrain level 4.714 / 5.075 のrough地形で学習した。平地候補・再開元に使わない。
- WRS側の既存cloneには多数の未追跡ファイルがあり、GitHub fetchはローカルCA不足によるSSL証明書エラーで失敗する（2026-09-19）。**WRS側のGit同期は打ち切り**。sslVerify=false・証明書設定変更・二重cloneはしない。WRSは現在の作業ツリーを実行専用として使い、GitHub側の文書更新はこのノートPCで行う。

## 最初にWRS側の既存Codexへ渡す指示

WRS側Codexへ次を送る。Git操作をさせず、実在する実行環境・run・起動スクリプトだけを確認させる。

```text
WRS側のGit同期は打ち切りです。git fetch/pull/push/clone/reset/checkout/restore/stash/add/commit、SSL設定変更、証明書回避を行わないでください。現在の作業ツリーを実行専用として扱い、未追跡物は削除しないでください。

1. `D:\Tominaga\IsaacLab`で、`tools\runs`、`_preload_h5py_and_run.py`、平地の既存評価・学習スクリプトを読み、h5py DLL衝突を回避する実在の起動方法を確定する。
2. H_eff13p5@2999、L_angstd_w1、J_turn_resumeの実run名・checkpoint・`params\env.yaml` / `agent.yaml`を確認する。
3. 平地用`sub_terrains`上書きの実際のHydra keyと値を、既存の平地run・評価スクリプトから確認する。推測で書かない。
4. 結果を踏まえ、下記F1/T1の64 env / 20 iterテスト用と、平地16 env再生用の完成コマンドを提示してから実行に進む。

学習を起動する前に、各runについて平地16 envの再生コマンドをユーザーへ先に提示してください。実在するプリロード起動方法・平地上書きから作り、学習中/終了後にそのrunの最新保存済みcheckpointを自動選択する完成コマンドにします。学習終了後は、採用した固定checkpoint名を埋めた再生コマンドも必ず提示してください。
```

## WRS実在確認後に行う学習案（まだWRSへ送らない）

平地用起動方法を既存スクリプト・paramsから確認できた後に限り、長時間GPU許可を使って次の2本を並列実行する。

1. F1: H_eff13p5@2999から、平地、seed 2、stiffness x0.85〜1.15・damping x0.8〜1.25だけを加えた直進gain DR。
2. T1: H_eff13p5@2999から、L_angstd_w1の実設定を基準に、平地、std=0.35、yaw報酬weight=1.0、yaw_gate、translate-only比率0.15を保ち、純旋回比率だけ0.20→0.35にする旋回学習。

両方とも64 env / 20 iterで、平地上書き・noise_std_type=log・再開元・意図した差分だけを`params\\env.yaml` / `agent.yaml`で確認してから4096 envへ進む。F1はc06転倒率≤5%かつ既存平地基準、T1は評価2回とも連続300 iterの旋回合格を満たした場合だけ候補にする。第三ランは勝手に始めない。

本番を起動したWRS側Codexは、iteration 30後に各runの実測秒/iter、残りiteration、予想終了時刻、そこからの残り時間を必ず報告する。並列時はrunごとに計算し、遅い方の終了時刻を全体の終了見込みとして併記する。

## このチャットの終了時

- WRS側のGit状態と実行結果を `training_runs.md` / 該当report / `chats/` に記録する。
- 次のチャットへの指示書を更新するのは、ユーザーがこのノートPC側で「次へ移る」と明示した時だけ。
