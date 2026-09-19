# D1: Hのデプロイ成果物を一度だけ取り出す

## 対応するロードマップ

- §1 作業3、完了物全件
- §4 完了条件1の入力

## 目的

採用済みの `H_eff13p5@2999` から実機統合に必要な成果物を作る。再学習、追加評価、候補比較はしない。

## 入力

- Hの実run名と `model_2999.pt` の実在パス
- Hの保存済み `params/env.yaml` と `params/agent.yaml`

## 実施内容

1. HのcheckpointからONNXを出力する。
2. `tools/dump_contract.py` を小規模環境で一度だけ実行して `obs_contract.md` を出力する。
3. `tools/dump_golden.py` をHのcheckpointに対して一度だけ実行してgolden npzを出力する。
4. Hの `env.yaml` から、関節グループ別 `stiffness`、`damping`、`effort` を抜き出す。
5. ONNXとgolden npzのSHA256、実行に必要なPython版・依存関係・Hのrun/checkpoint名を `DEPLOY_README.md` に記す。

## 出力・完了条件

同一フォルダに `policy.onnx`、`obs_contract.md`、`golden.npz`、アクチュエータ表、SHA256、`DEPLOY_README.md` が揃うこと。ここでGPU長時間学習を開始しない。

