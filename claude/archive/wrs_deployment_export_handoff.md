# WRS側: Hのデプロイ成果物抽出 引き継ぎ（2026-09-19）

## 現状

- WRS側のcloneはGit同期を打ち切っており、ノートPC側にある `claude/deployment_01_h_export_instruction.md` を持たない。WRS側への指示で当該ファイルを読ませない。
- WRS側で確認済みのHの入力は、run `2026-09-17_00-08-51_H_eff13p5`、checkpoint `model_2999.pt`、`noise_std_type=log`、平地上書き一式、`tools/runs/_launch.ps1` と `_play.ps1` の存在である。
- 現時点の採用方策は H_eff13p5@2999。G_real_peak@2999は予備であり、今回の抽出対象ではない。P_gainDR_narrowの置換判定は未完了、P2/P3はrough地形で学習したため候補外、Lは旋回再現性・頑健性不足で候補外。

## WRSへ貼る自己完結プロンプト

```text
実機統合用に、既存のH方策の成果物を取り出す作業だけをしてください。学習、評価の新規実行、play、GPU長時間処理、Git操作、コード変更、依存関係変更、監視はしません。Git同期は打ち切り済みなので、fetch/pull/push/clone/reset/checkout/restore/stash/add/commitを行わず、未追跡ファイルも削除しません。

参照する文書パスは前提にしません。WRS側cloneに無い文書を探して停止しないでください。

採用方策は次に固定です。
- run: 2026-09-17_00-08-51_H_eff13p5
- checkpoint: model_2999.pt
- policy noise std type: log
- G_real_peak、P_gainDR_narrow、P2、P3、Lは今回対象外です。

最初に、次の実在パスだけを確認してください。
- D:\\Tominaga\\IsaacLab\\logs\\rsl_rl\\skyentific_poclegs_rough\\2026-09-17_00-08-51_H_eff13p5\\model_2999.pt
- 同runのparams\\env.yaml と params\\agent.yaml
- 同runのexported_2999 または exported にある policy.onnx
- 現在のcheckout内の tools\\dump_contract.py、tools\\dump_golden.py、tools\\verify_onnx.py

既存のpolicy.onnxがあれば再exportせず使ってください。無ければ、既存の _play.ps1 または既存のplay起動方法でHのpolicy.onnxだけを書き出してください。新規の学習・評価はしません。

既存のdump_contract.pyとdump_golden.pyがあれば、それらだけを使って観測契約とgolden datasetを作ってください。無ければ新規実装はせず、何が無いかを報告して停止してください。

次の出力フォルダを作り、ファイルを揃えてください。
D:\\Tominaga\\deploy_pkg\\20260919\\H_eff13p5_2999\\

- policy.onnx
- obs_contract.md
- golden.npz
- actuator_table.md（env.yamlから10関節のstiffness、damping、effortを読んだ表）
- SHA256SUMS.txt（上の出力ファイル全て）
- DEPLOY_README.md（run名、checkpoint名、Python実行パス、依存関係、ONNXが42入力・10出力である確認結果）

ONNXの42入力・10出力は既存のverify_onnx.py、onnxruntime、またはonnxのうち既に使えるものだけで確認してください。足りない依存関係を入れないでください。

失敗・不明点では推測して直さず停止し、実在確認できたパス、足りないファイル、エラー全文だけを短く報告してください。成功時は出力一覧、SHA256、42入力・10出力の確認結果だけを短く報告してください。
```

## Avast / Codexのネットワーク障害

### 確認済みの症状

- AvastのHTTPSスキャンを無効にしている間だけCodexがネットワーク接続できる。
- これはHTTPS検査（TLS復号）の経路が原因である強い切り分け結果だが、恒久的な無効化は安全性を下げる。

### 次の順番

1. HTTPSスキャンを有効に戻す。
2. AvastをRepairし、Windowsを再起動する。Repairは設定・証明書コンポーネントの不整合を直すための公式推奨手順である。
3. Codexを再試行する。失敗したら、HTTPSスキャンは有効のまま、Avast Web Guardの「hardware network acceleration」だけを無効にして再試行する。
4. それでも失敗した場合だけ、Codexが失敗時に接続しようとした公式OpenAI URLとエラー画面を採取し、Avastサポートへ送る。URL例外を作る場合も、確認済みの単一URLに限定する。広いドメイン・アプリ・フォルダ除外やHTTPSスキャンの恒久無効化はしない。

## 次の引き継ぎ先

1. WRSが上の成果物抽出を完了または停止理由を返す。
2. ノートPC側で成果物のSHA256を照合し、`obs_contract.md`のvelocity_commandsの順番・単位・範囲を確認する。
3. その後にのみ、D5相当のコントローラー速度指令対応を実装する。
