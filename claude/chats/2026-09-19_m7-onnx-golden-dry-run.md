# 2026-09-19 M7 ONNX golden乾式ループ

## やったこと

H_eff13p5@2999の読み取り専用デプロイパッケージを使い、`Connect2USB2CAN/policy_dry_run.py` と最小テストを追加した。SHA256検品、golden形式検査、実際のONNX 42→10検査、500 stepのaction／目標角比較、50 Hz予定表CSVを実装・実行した。

## 決めたこと・分かったこと

- 6必須ファイルのSHA256はすべて一致した。
- action最大絶対誤差は `1.1920929e-06`（step 335）、目標角は `5.96046448e-07`（step 113）で、双方が閾値 `1e-4` 以下だった。
- 50 Hz CSVは500行。周期平均20.026 ms、最大40.687 ms、最大deadline遅れ22.104 ms、推論最大4.409 ms。Windowsの乾式測定値であり、実機統合の周期合格とは扱わない。
- CAN、モーター、T265、コントローラー、USB機器には接続していない。M7完了はCAN統合の開始許可ではない。

## 手を動かした場所

- `C:\Users\harut\Connect2USB2CAN\policy_dry_run.py`
- `C:\Users\harut\Connect2USB2CAN\test_policy_dry_run.py`
- `C:\Users\harut\Connect2USB2CAN\logs\policy_dry_run_m7.csv`（Git非追加）
- `C:\Users\harut\wanpbl2026_slope_climing_robot\claude\reports\2026-09-19_m7-onnx-golden-dry-run.md`

`Connect2USB2CAN` は `e0a9448`、本体リポジトリの乾式報告は `11f56a7` としてpush済み。

## 積み残し・次にやること

次の統合タスクはこの引き継ぎでは指定しない。CANへ方策を接続するには、M5原点表、T265途絶停止を含む乾式設計、10モーター周期D3、およびユーザーの明示が別途必要。
