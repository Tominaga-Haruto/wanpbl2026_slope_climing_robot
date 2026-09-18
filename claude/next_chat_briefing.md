# 次チャットへの引継ぎ書 — Isaac Lab 学習の判定と修正（2026-09-18 P1@4498完走後）

## このチャットの役割と禁止事項

- 役割は WRS 機の Isaac Lab 学習の評価・判断・必要最小限の再学習の指示を作ること。
- **WRS 側の Claude Code はクレジット切れで使えない。Claude Code に指示して実行させる案は出さない。** ユーザーが WRS 機の PowerShell で直接実行するため、完成した PowerShell コマンドを渡す。
- 実機モーターは動かさない。モデル重み・ONNX・動画・生ログを Git に入れない。
- 学習は必ず画面出力が見える **フォアグラウンド**。`tools\\runs\\_train_foreground.ps1` 以外で新規学習を起動しない。`_launch.ps1`、`Start-Process`、リダイレクト、バックグラウンド起動は禁止。
- WRS は共用PC。他人のプロセスは触らない。開始前に `nvidia-smi` を確認し、他人の計算プロセスがあれば新規起動しない。

## 現在地

- 目標は平地での実機デプロイ。直進の第一候補は `H_eff13p5@2999`、予備は `G_real_peak@2999`。
- 旋回の追加学習は打ち切り。`N_w1_seed2` は合格点ゼロ、`N_w1p5` は4400だけ合格で、連続300 iterという採用条件を満たさない。
- `P_gainDR_narrow` は `H_eff13p5@2999` から、stiffness x0.85〜1.15・damping x0.8〜1.25 をランダム化して再開した直進頑健化ラン。P1は **4498/4499まで完走**した。
- P1最終ログ: Mean reward 18.86、mean episode length 982.53、timeout 94.42%、base contact 4.71%、bad orientation 1.00%、action std 0.27、NaN/発散なし。これは学習プロセスが正常というだけで、候補昇格の根拠にはならない。

## 最初にすること

WRS機で次を実行して、出力をこのチャットへ貼ってもらう。これはフォアグラウンドの確認だけで、学習は起動しない。

```powershell
cd D:\Tominaga\IsaacLab
git -C D:\Tominaga\slope-climbing-robot status --short
nvidia-smi
Get-ChildItem D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 8 Name,LastWriteTime
Get-Content .\tools\runs\_eval.ps1
Get-Content .\tools\runs\_train_foreground.ps1
```

`P_gainDR_narrow` の実runフォルダと、`model_3600.pt`、`model_4000.pt`、`model_4498.pt` の実在を確認する。**スクリプトの実引数を確認せず、推測した評価コマンドを出さない。**

## まず行う3時間枠: P1の評価だけ

新規学習は起動しない。最大2本の評価を並列にしてよいが、両方とも表示したPowerShellを閉じず、フォアグラウンドのままにする。

1. `model_3600.pt`、`model_4000.pt`、`model_4498.pt` 各々で、平地S1〜S11・64 env・関節別トルクを評価する。
2. `model_4498.pt` で、c01/c03/c04/c06/c07/c08/c09/c10/c16 と、base_lin_velの0埋め0.2 s・直前値保持0.5 sを評価する。
3. H_eff13p5@2999 の既存表と並べる。必ず出す数値はS1の前進速度・静止率・転倒率・S7/S8・関節RMS/最大/飽和率、c06の転倒率、Hに無い不合格。

評価の実行には `tools\\runs\\_eval.ps1` の既存の実引数を使う。評価の起動前に、次チャットの担当者が上の `Get-Content` 出力から完成形を組み立てること。実装や報酬・地形・アクチュエータ設定を修正しない。

## 評価後の夜間学習: 固定した分岐

P1の評価表を受けて、次の規則から外れない。

| 条件 | 夜間に回すもの |
|---|---|
| P1が既存基準合格、c06転倒率≤5%、H_eff13p5に無い不合格なし | `P2_seed2` だけ。P1と同じ設定、seed=2、H_eff13p5@2999から+1500 iter |
| S1静止率>50% | `P2_stiffonly` だけ。stiffness x0.9〜1.1、damping固定、H_eff13p5@2999から+1500 iter |
| 上記以外 | 新規学習なし。第一候補をH_eff13p5@2999のまま凍結 |

- 2本目のGPU枠を埋める目的の学習はしない。
- `O_turn35`、`O_w2`を含む旋回2巡目は起動しない。
- 新規学習の完成コマンドは、P1の実際の起動行・`_train_foreground.ps1`の引数・元runのparamsを確認してから出す。必ず `noise_std_type=log` を含める。
- ユーザーが8時間寝る前に、run名、起動コマンド、予想終了時刻、Ctrl+Cで止めること、画面のPowerShellを閉じないことを1画面で示す。

## このチャットで必要な最終成果物

1. P1の3 checkpointと4498頑健性の判定表。
2. H_eff13p5@2999を置換するかの結論。
3. 上の分岐に基づく、プレースホルダなしのフォアグラウンド学習コマンド1本、または学習停止の明示。
4. 結果を `training_runs.md` と `chats/` に記録し、対象を絞ってcommit/pushする。
