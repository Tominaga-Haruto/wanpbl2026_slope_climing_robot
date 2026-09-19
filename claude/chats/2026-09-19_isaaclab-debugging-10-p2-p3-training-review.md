# 2026-09-19 Isaac Lab debugging #10 — P2/P3 学習ログの判定

## やったこと

- `README.md` と `next_chat_briefing.md` を確認し、H_eff13p5@2999 から再開した P2/P3 の最終学習統計を比較した。
- P2 は stiffness x0.85〜1.15・damping x0.8〜1.25 の gain DR（seed 2）、P3 は同 stiffness DR・damping x1.0固定（seed 1）で、どちらも iteration 11998/11999 まで完走した。

## 決めたこと・分かったこと

- どちらも NaN・発散のない正常完走である。
- P3 は mean reward 6.94、episode length 628.74 で P2（5.39、558.50）を上回る。しかし比較時点のカリキュラムが異なる（P3: terrain 5.075 / push 2.8 / command 1.0、P2: 4.714 / 0.0 / 1.5）うえ、seed も異なる。最終ログだけで P3 の方策が優れる、または damping DR が悪いとは結論できない。
- P2 は damping DR 下で学習を維持できたことを示す。一方、候補の採否は再生の見た目や学習報酬ではなく、既定の平地 S1〜S11 と c01/c03/c04/c06/c07/c08/c09/c10/c16、および速度観測途絶の評価表で H_eff13p5@2999 と比較して決める。
- `_play.ps1` の有無をWRS機上で確認せずに案内したのは誤りだった。さらに、`conda activate` だけで `h5py._errors` の DLL error が解消すると断定したが、再生で同じエラーが継続しており未確認だった。修復・再生は保留し、h5py単体 import と起動スクリプトの実在・内容を読む二段階診断へ戻した。
- P2/P3 の train 行には、平地用の `sub_terrains` 上書きが無かった。最終ログの terrain level（P2 4.714、P3 5.075）と、`Play-v0` の既定再生で rough 地形が出たことは一致する。よって P2/P3 は「平地の gain DR 比較」としては不成立であり、H_eff13p5@2999 の平地候補を置換する根拠に使わない。再生コマンドは rough を正しく可視化しただけで、根本の逸脱はトレイン条件である。

## 手を動かした場所

- 読み取り: `README.md`、`next_chat_briefing.md`、`training_runs.md`。
- 文書追加: この記録と README 索引。

## 積み残し・次にやること

- WRS機で Codex が利用可能になった（2026-09-19）。再生コマンドの作成はWRS側 Codex に、実在する `tools\\runs` と既存の起動スクリプトを読ませてから行う。
- P2/P3を平地候補として評価・採用しない。再学習の要否は、平地上書きを含む新しい実験設計をユーザーが決めてから判断する。
