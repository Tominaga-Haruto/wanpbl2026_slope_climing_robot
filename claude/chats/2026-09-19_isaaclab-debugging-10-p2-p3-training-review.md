# 2026-09-19 Isaac Lab debugging #10 — P2/P3 学習ログの判定

## やったこと

- `README.md` と `next_chat_briefing.md` を確認し、H_eff13p5@2999 から再開した P2/P3 の最終学習統計を比較した。
- P2 は stiffness x0.85〜1.15・damping x0.8〜1.25 の gain DR（seed 2）、P3 は同 stiffness DR・damping x1.0固定（seed 1）で、どちらも iteration 11998/11999 まで完走した。

## 決めたこと・分かったこと

- どちらも NaN・発散のない正常完走である。
- P3 は mean reward 6.94、episode length 628.74 で P2（5.39、558.50）を上回る。しかし比較時点のカリキュラムが異なる（P3: terrain 5.075 / push 2.8 / command 1.0、P2: 4.714 / 0.0 / 1.5）うえ、seed も異なる。最終ログだけで P3 の方策が優れる、または damping DR が悪いとは結論できない。
- P2 は damping DR 下で学習を維持できたことを示す。一方、候補の採否は再生の見た目や学習報酬ではなく、既定の平地 S1〜S11 と c01/c03/c04/c06/c07/c08/c09/c10/c16、および速度観測途絶の評価表で H_eff13p5@2999 と比較して決める。
- WRS機には `tools\\runs\\_play.ps1` が無い。通常の再生は必ず `cd D:\\Tominaga\\IsaacLab`、`conda activate D:\\Tominaga\\envs\\isaac_env`、`isaaclab.bat -p scripts\\reinforcement_learning\\rsl_rl\\play.py` の順で実行する。`(base)` のままでは `h5py._errors` の DLL import error になる。
- run フォルダ名は実際のタイムスタンプを確認し、最終チェックポイントは表示された iteration に対応する `model_11998.pt` を指定する。P2/P3は `agent.policy.noise_std_type=log` を明示して読み込む。

## 手を動かした場所

- 読み取り: `README.md`、`next_chat_briefing.md`、`training_runs.md`。
- 文書追加: この記録と README 索引。

## 積み残し・次にやること

- WRS 機で P2/P3 の実run名と `model_11998.pt` の実在を確認して通常再生する。
- `_eval.ps1` で既定の評価表を取り、H_eff13p5@2999を置換できるか判断する。少なくとも P2 は gain DR を含む c06 を必ず比較する。
