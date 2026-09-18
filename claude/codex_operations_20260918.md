# Codex 二台運用（2026-09-18）

## 結論

- 正本は GitHub `main`、文章の正本はリポジトリ内の `claude/` とする。
- 共有するルールは Git ルートの短い `AGENTS.md`、機械の役割は各 PC の `C:\\Users\\<ユーザー>\\.codex\\AGENTS.md` に分ける。端末固有ファイルは Git に入れない。
- WRS の Codex は **実行・事実調査・結果記録だけ**を担う。方針決定、実機操作、結果の採否はノートPC側で行う。
- WRS は必要な指示書をプロンプトで指定して初めて読む。毎回 README や handbook 全文を読む運用にはしない。

## 現在の Git 判定

2026-09-18 時点で `main` と `origin/main` のコミット差は 0。本当の問題は同期遅れではなく、ノートPC作業ツリーに 48 件の未整理変更（既存ファイルの変更・削除と追加）があること。

この状態で `git add .`、一括 commit、push はしない。まず「今回移した md の正しい内容」と「残すべき既存の変更」を差分で仕分ける。仕分けが済むまで、WRS側では Git を更新せず、調査結果だけ新規 `claude/chats/` または `claude/reports/` の md としてコミットする。

## 置く指示

### 1. Git 共有: リポジトリルート `AGENTS.md`

`C:\\Users\\harut\\wanpbl2026_slope_climing_robot\\AGENTS.md` と WRS の `D:\\Tominaga\\slope-climbing-robot\\AGENTS.md` は、同じ内容を Git 管理する。本文は次の程度でよい。

```md
# 坂登坂ロボット

目的は平地での実機デプロイ。GitHub `main` とリポジトリ内の `claude/` が正本。

- 作業前に `git status --short` を確認し、他人または別PCの未整理変更を上書きしない。
- 機械固有の役割は `~/.codex/AGENTS.md` に従う。役割外の実行はしない。
- 数値・配線・関節符号は推測せず、必要時だけ該当する `claude/*.md` を読む。
- 実機モーターは、ユーザーが明示して安全条件を確認した場合だけ操作する。1モーター→片脚→全身の順。
- 重み・モデル・生ログ・鍵を Git に入れない。
- 作業結果は `claude/chats/` または `claude/reports/` に記録し、対象を絞って commit/push する。
```

このファイルには現在地、環境の詳細、長い読書順、実験史を書かない。Codex は起動時に読むため、短いほどよい。

### 2. ノートPCだけ: `C:\\Users\\harut\\.codex\\AGENTS.md`

```md
# このPCの役割

ここはノートPC側の統括・実機側 Codex。方針決定、Git整理、WRS報告の確認、CAN/T265/制御ループを担当する。

- WRS作業は、必要な調査または実行を完結したプロンプトとして依頼する。WRSの結果mdを pull してから判断する。
- 実機を動かす前は、安全条件と予想動作を説明し、ユーザーの明示指示を待つ。
- 実機の数値は `claude/motor_can_findings.md`、T265は `claude/realsense_t265.md` を必要時に読む。
```

### 3. WRSだけ: `C:\\Users\\<WRSのログイン名>\\.codex\\AGENTS.md`

```md
# このPCの役割

ここは WRS 共用PC（`D:\\Tominaga\\slope-climbing-robot`）。Isaac Lab の調査・学習・評価・ONNX書き出しだけを担当する実行役。

- 実機CAN、T265、ノートPCのコード、方針の最終決定には触れない。
- ユーザーのプロンプトで指定された md だけを読む。指定がなければ、まず対象ファイルと Git 状態だけ調べる。
- 実行前に、コマンド、変更対象、判定規則を短く復唱する。規則が無ければ実行せず要求する。
- 結果は事実・実行コマンド・commit・未解決点を `claude/reports/YYYY-MM-DD_短い件名.md` に記録する。結果mdと必要なコードだけを commit/push する。
- 学習の採否は決めない。結果と事前規則への機械的な照合だけを報告する。
- 重み、ONNX、USD、npz、生ログを Git に追加しない。
```

WRSのプロンプト例:

```text
あなたはWRS実行役です。`claude/wrs_pc_environment.md` と `claude/next_chat_briefing.md` の指定節だけを読み、P_gainDR_narrow の現在の状態を調査してください。学習やファイル変更はしないでください。結果を `claude/reports/2026-09-18_p1_status.md` に、確認したコマンド・事実・未確定点だけ記録して commit/push してください。
```

## 実施チェックリスト

- [ ] ノートPCで Git ルートに共通の短い `AGENTS.md` を置く（今ある `claude/AGENTS.md` はルートではないため移設対象）。
- [ ] ノートPCとWRSの各 `~/.codex/AGENTS.md` に上の端末別文を置く。Gitには追加しない。
- [ ] 各PCでリポジトリルートから Codex を再起動し、「読み込んだ instruction files と自分の役割だけを3行で示して」と確認する。
- [ ] WRSでは Tier 1 の13ファイルだけを維持し、以後は必要な結果mdを pull する。全履歴・旧実験指示書を同期しない。
- [ ] ノートPCの未整理48件を、`git diff --name-status` と各ファイル差分で「保持」「不要」「要確認」に分類する。削除・復元は分類後に行う。
- [ ] 仕分け済みの文書を小さな1コミットにし、`git status --short` が空であることを確認してから push する。
- [ ] WRSは作業開始時に `git pull --ff-only origin main`、作業終了時は対象だけ commit/push する。push失敗時は再試行せずノートPCへ報告する。
- [ ] ノートPCは WRS の commit hash を受け取ってから `git pull --ff-only origin main` し、結果mdを読んで判断・記録する。
- [ ] ONNX等の受け渡しは SHA-256 を添え、Git以外（USBまたは共有フォルダ）で行う。

## 補足

Codex は Git ルートから現在の作業ディレクトリまでの `AGENTS.md` と、各ユーザーの `~/.codex/AGENTS.md` を重ねて読み込む。よって端末固有の自己認識を共有リポジトリに入れる必要はない。公式手順: [AGENTS.md によるカスタム指示](https://developers.openai.com/ja-JP/docs/agent-configuration/agents-md)。
