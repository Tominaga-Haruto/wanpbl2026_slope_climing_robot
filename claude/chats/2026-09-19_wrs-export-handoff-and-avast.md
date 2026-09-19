# 2026-09-19 WRS成果物抽出の引き継ぎとAvast HTTPS障害

## やったこと

- WRS側の2つの応答を確認した。WRS cloneにはノートPC側の `deployment_01_h_export_instruction.md` が無く、そのパスを読ませたことが停止理由だった。
- WRSが確認できたHの実在情報は、run `2026-09-17_00-08-51_H_eff13p5`、`model_2999.pt`、`noise_std_type=log`、平地上書き、`_launch.ps1` / `_play.ps1`である。
- Avast HTTPSスキャンを無効にするとCodexネットワーク障害が解消するという切り分け結果を受け、Avast公式の復旧順を確認した。
- WRS clone内の文書に依存しない、自己完結した成果物抽出プロンプトを `wrs_deployment_export_handoff.md` に作成した。

## 決めたこと・分かったこと

- 現在はH_eff13p5@2999を成果物化する。P_gainDR_narrowは置換条件の評価が未確定であり、P2/P3はrough地形学習、Lは旋回再現性・頑健性不足のため今回の候補にしない。G_real_peakは予備として保持する。
- WRSはGit同期を行わず、文書パスを前提にせず、既存runと既存ツールだけで成果物を抽出する。
- AvastのHTTPSスキャンを恒久的に無効化しない。HTTPSスキャン有効の状態でAvast Repairと再起動を行い、未解決ならhardware network accelerationだけを無効化して切り分ける。

## 手を動かした場所

- `wrs_deployment_export_handoff.md` を追加した。
- 実機、WRS、Avast、CAN、学習runには変更なし。

## 積み残し・次にやること

1. ユーザーが自己完結プロンプトをWRS側へ貼り、成果物または停止理由を取得する。
2. Avast Repair後、HTTPSスキャンを有効に戻した状態でCodex接続を確認する。
3. Hの成果物を受領後、SHA256と観測契約を照合してコントローラー対応へ進む。
