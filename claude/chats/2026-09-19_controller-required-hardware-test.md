# 2026-09-19 プロコン系の必須実機試験の切り分け

## 読んだもの

- `README.md`
- `project_handbook.md`
- `deployment_roadmap.md`
- `controller_prep_briefing.md`
- 既存の `chats/2026-09-18_controller-pad-probe-implementation.md`

## 結論

今日プロコン系で実機を使って必ず行うべきなのは、Jetson と有線 Switch 2 Pro だけをつないだ `pad_probe.py` の乾式試験である。CAN、モーター、ONNX、T265 はつながない。

確認対象は中立10秒、全4方向の生値と正規化値、50 Hz出力周期、USB抜線後200 ms以内の `timeout` とゼロ出力、再接続後に非ゼロ指令へ自動復帰しないこと。これは実装済み部品の未検証部分であり、実物入力がなければ確認できない。

`obs_contract.md` はリポジトリ内にまだ無く、学習パッケージから未受領だった。そのため今日はスティックの前後・左右を方策の base 座標の `vx` / `vy` へ確定できない。一方、上記の入力装置・切断挙動の試験は観測契約や学習の完了を待たずに行える。既定で非ゼロ表示を抑制する `pad_probe.py` のまま実行する。

## 次の判断

- 乾式試験が合格: 観測契約待ちの間に、ログからデッドゾーン候補と周期実測を確定する。
- 乾式試験が不合格: その原因（`evdev`、安定パス、切断例外、周期）だけを直して再試験する。
- `obs_contract.md` を受領後: base 座標の符号と速度範囲を照合し、`teleop.py` の実装・乾式試験へ進む。

## 追加の依存関係整理

H_eff13p5@2999 を採用済みと仮定するなら、新たな学習は不要である。学習側へ一度だけ依頼する成果物は、HのONNX、`obs_contract.md`、golden npz、Hの保存済み `params/env.yaml` からのアクチュエータ表、SHA256、短い `DEPLOY_README.md` である。`tools/dump_contract.py` と `tools/dump_golden.py` は既にあり、前者は2環境、後者はH checkpointを読むだけなので、長時間trainを再実行する作業ではない。

学習成果物なしで進められるのは、Jetson入力の乾式試験・`teleop.py` の状態機械とログ・T265の取付けと観測取得・CANフィードバックの収集・MIT送信の周期計測・ver9のプロセス境界とmit_simである。一方、42次元観測の組み立て、ONNXの推論照合、10行動を各関節目標角へ変換する本実装、スティックとbase座標の符号確定は、上の学習パッケージを待つ。

ユーザーの追加確認を受け、ロードマップ§2作業1（50 Hz・抜線）と§2作業3（デッドマン等）は、方策を動かすための技術的必須条件ではなく停止・安全のための条件として最短経路から外した。初回のH実行にはプロコン自体も不要で、ver9へ固定のvelocity commandを入れればよい。分割チャット用に `deployment_01_h_export_instruction.md` から `deployment_06_h_integration_instruction.md` を作成した。
