# 2026-09-22 共通エージェント引き継ぎ構造

## 目的

CodexとClaude Codeが、同じGitHub `main`、同じ現在地、同じ安全境界から開始できるようにした。`claude/`はエージェント名ではなく共通文書領域として扱う。

## 追加した正本

- リポジトリ直下の`AGENTS.md`: 両エージェントの唯一の入口。最初に読む文書と不変ルールを定義する。
- リポジトリ直下の`CLAUDE.md`: Claude Codeに最初に`AGENTS.md`だけを読むよう指示する。
- `claude/START_HERE.md`: 文書種別、読み順、ローカル生ログとGitの境界を定義する。
- `claude/CONTEXT.md`: 全体の短い現在地、優先順位、正本への案内を持つ。
- `claude/handoffs/ACTIVE.md`: 次の担当の唯一のアクティブ指示書。初回Claude Code向けのD9修正指示を格納した。
- `claude/handoffs/README.md`: ACTIVEの更新規則を定義する。

## 移行方針

既存の`README.md`、`project_handbook.md`、`next_chat_*`、`chats/`は削除・移動していない。過去の根拠・詳細手順として保全し、新規セッションの開始点から外した。新しい実測は`reports/`へ根拠を残し、優先作業が変われば`CONTEXT.md`と`handoffs/ACTIVE.md`を同じcommitで更新する。

## 同期の境界

GitHub `main`は文書・ソースの共有正本である。一方、`C:\Users\harut\Connect2USB2CAN`のCSV・重み・ONNXなどはローカル実行物であり、Gitに入れない。報告書へ絶対パス、更新時刻、集計値を残すことで、別PC・別エージェントでも同じ根拠を確認できるようにする。
