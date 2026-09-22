# 実験10 A/B 最終評価

ユーザー提示のA/B `model_29997.pt`最終評価を確認し、`reports/2026-09-22_exp10-autoturn-directturn-assessment.md`に記録した。

- A自動headingは不要yawが直進・静止・後退にも混入し不採用。
- B直接`(vx,vy,wz)`は64 env/seed 1234でS6/S9純旋回基準を満たすが、256 env×2 seed・連続300 iter・頑健性の事前採用規則は未達。
- 第一回実機はH_eff13p5@2999を維持し、Bの追加学習より先に既存保存点を資格評価する。
- B採用時は方策パッケージを全量再生成する。制御Pythonはpackage指定方式なので改修不要、D10/D11のパスだけ更新する。

## 夜間GPU枠の追加判断

ユーザーの約10時間のGPU空きを使うため、B@29997から追加9000 iterの2本を並走する設計を作成した。対照はB設定を完全維持する`B_continue_H30000`、実験は純旋回38%を維持して横移動10%を追加する`B_lateral10_H30000`。CLIには64 env smoke test後、ユーザーが前景PowerShellで起動する完成コマンドだけを返させる。
