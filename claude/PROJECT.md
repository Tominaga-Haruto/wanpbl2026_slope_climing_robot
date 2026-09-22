# プロジェクト基本情報

## 目的

Isaac Labで学習した二足ロボットを、まず平地で安全に実機デプロイする。坂走行、旋回方策の昇格、長時間堅牢化はその後の段階である。

## システムの全体像

`Isaac Lab / RSL-RL`で方策を学習し、ONNXパッケージとして実機へ渡す。ノートPC側の制御ループはT265、コントローラー、CANフィードバック、方策出力を結び、CubeMars AKシリーズ10軸へMIT位置指令を送る。

## 実行環境と正本

| 場所 | 役割 | 取り扱い |
|---|---|---|
| GitHub `main` | ソース・手順・報告書の共有正本 | 作業単位でcommit/push |
| `C:\Users\harut\wanpbl2026_slope_climing_robot` | ノートPCのGit作業ツリー | 文書とソースを更新 |
| `C:\Users\harut\Connect2USB2CAN` | CAN、T265、実機送信器 | CSV・実行物はGitに入れない |
| `D:\Tominaga\slope-climbing-robot` | WRS学習・評価環境 | Git同期は止め、実行専用として扱う |

重み、ONNX、CSV、生ログ、USD/STL、鍵はGit管理外である。再現に必要な絶対パス、更新時刻、SHAや集計値だけを報告書へ記録する。

## 文書構造

- `CONTEXT.md`: 時々刻々の現在地・優先順位・ブロック。
- `handoffs/`: 次の担当へ渡す短い作業指示。`ACTIVE.md`だけが開始点。
- `domains/`: ハードウェア、方策、コントローラー、デプロイの詳細資料への入口。
- `procedures/`: 実機・評価の実行手順への入口。
- `reports/`: 実測・調査・判断の根拠。
- `legacy/`: 旧来の入口文書の扱い。元ファイルは保全し、開始点にはしない。
