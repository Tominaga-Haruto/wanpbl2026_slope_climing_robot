# 2026-09-18 Jetson Switch 2 Pro コントローラー準備

## やったこと
- `README.md`、`controller_gpu_today_instruction.md`、`controller_prep_briefing.md` と `project_handbook.md` の実機安全規則を確認した。
- Jetson に有線接続した Switch 2 Pro について、モーター・CAN・方策へ接続しない乾式テストの順番をチェックリスト化した。

## 決めたこと・分かったこと
- 最初は Linux 上で USB 認識、入力デバイス、軸・ボタンの生値、50 Hz の更新周期、切断時の挙動を順に実測する。
- モーターは Kt 用の固定治具がそろうまで動かさず、CAN にも送らない。
- 速度指令はデッドマン・非常停止ラッチ・0.2 秒の入力途絶停止・変化率制限を実装してから、実機制御ループへ渡す。

## 手を動かした場所
- 読み取りのみ。既存の未整理変更には触れていない。

## 積み残し・次にやること
- Jetson 側の USB 認識結果と `/dev/input` の対応を取得する。
- 軸・ボタン番号を実測後、読み取り専用の `controller/pad_probe.py` を作る。
