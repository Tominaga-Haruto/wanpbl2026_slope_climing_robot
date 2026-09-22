# Codex への引き継ぎ手順（2026-09-18）

> **背景:** 週間制限に到達したため、発表（9-25 ごろ）までの1週間は Codex で進める。Claude はほぼ使わない。
> **この文書のゴール:** 「Claude のチャットに溜まっている前提」を、Claude 抜きで読める形に落とすこと。
> 関連: `AGENTS.md`（リポジトリ直下に置く入口）、`archive/next_chat_briefing.md`、`archive/next_chat_briefing_motor.md`

---

## 0. いちばん大事な事実

このプロジェクトで Claude が持っていた価値は、モデルそのものではなく**`claude/` 以下の 66 本の md**。
Codex はこれを**ファイルとして読めれば**、ほぼ同じ状態から続けられる。逆に、md が claude.ai の中にしか無いと何も引き継げない。

**2026-09-18 に確認した結果: `D:\\Tominaga\\slope-climbing-robot\\claude\\` は存在しない。**
つまり 66 本の md は **claude.ai のプロジェクトの中にしか無い**。これを取り出すのが引き継ぎの本体で、**他の全作業より先**にやる。

引き継ぎは次の4つに分解される。

1. **md を claude.ai から取り出してリポジトリに入れる**（→ §1）※最優先
2. **入口ファイル `AGENTS.md` を置く**（Codex が自動で読む。プロジェクト指示欄の代わり。→ §2）
3. **機械をまたぐ同期先を claude.ai から GitHub に切り替える**（→ §3）
4. **失われる「第三者の目」を埋める**（→ §4）

---

## 1. 手順1: md を claude.ai から取り出す（確定・最優先）

### 1a. 確認済みの事実（2026-09-18）

```
dir : Cannot find path 'D:\\Tominaga\\slope-climbing-robot\\claude' because it does not exist.
```

- リポジトリには `docs/` はあるが（`docs/experiments/exp09_turn_reproducibility.md` が未追跡で存在）、`claude/` は無い。
- したがって **66 本の md はすべて claude.ai 側にしか無い**。Claude のアカウントを使わなくなると読めなくなる。
- 同時に判明: `.bak` 類・`references/`・`tools/view_*.png`・`onshape_export/...bak_*` が大量に未追跡。**push には含まれない**（`??` なので）が、`docs/experiments/exp09_turn_reproducibility.md` は成果物なので commit する。

### 1b. 取り出す優先度

全 66 本を一度に Claude に読ませると、それ自体が制限を食う。上から必要な分だけ取る。

**Tier 1 ── これが無いと続けられない（13 本）**

`README.md`, `legacy/project_handbook.md`, `legacy/handover.md`,
`archive/next_chat_briefing.md`, `archive/next_chat_briefing_motor.md`, `archive/controller_prep_briefing.md`,
`reference/robot_model_conventions.md`, `reference/motor_can_findings.md`, `reference/realsense_t265.md`, `reference/actuator_params.md`,
`reference/wrs_pc_environment.md`, `reference/motor_bench_checklist.md`, `reference/training_runs.md`
（＋この `reference/codex_migration.md`）

**Tier 2 ── 判断の根拠。余裕があれば（8 本）**

`reference/crab_standstill_countermeasures.md`, `reference/wrs_training_strategy.md`, `reference/wrs_training_history.md`,
`reference/motor_mit_official_notes.md`, `reference/project_structure_map.md`, `reference/rough_env_cfg_walkthrough.md`,
`reference/urdf_asymmetry_finding.md`, `reference/template_code_reference.md`

**Tier 3 ── 経緯の保存。1週間の作業には要らない**

`chats/*`（24 本）、`wrs_experiment01〜09_instruction.md`、旧版（`instructions/urdf_reexport_instruction.md`, `instructions/wrs_pc_operator_instruction.md`, `archive/mit_implementation_briefing.md`, `instructions/alienware_repair_instruction.md`, `instructions/wrs_pc_host_instruction.md`, `archive/wrs_new_chat_start.md`, `instructions/wrs_overnight_20260918_instruction.md`, `reference/isaaclab_edit_guide.md`, `instructions/onshape_cad_fix_instruction.md`）

### 1c. 取り出し方（安い順）

| 方法 | Claude の消費 | 向き |
|---|---|---|
| ① claude.ai の画面から1本ずつ開いてコピー | **ゼロ** | Tier 1 の 13 本だけなら現実的 |
| ② 並列サブエージェント（haiku）に書き出させる | 小（親の文脈が増えない） | **66 本まとめて取るならこれ** |
| ③ Sonnet の新チャットに順に読ませる | 中（文脈が積み上がる） | ②が使えないとき |

②を使う場合の指示（Cowork の新チャットに貼る。**Opus では始めない**）:

```
このプロジェクトの claude/ 以下の md を、要約せずそのまま書き出してほしい。
- haiku のサブエージェントを 6 本ほど並列で立て、担当ファイルを重複なく割り振る。
- 各エージェントは担当分を project_read し、中身をそのまま
  /mnt/user-data/outputs/claude/<元と同じ相対パス> に書く。chats/ の階層も保つ。
- 要約・整形・コメント・講評は一切しない。親は「done」以外を受け取らない。
- 最後に /mnt/user-data/outputs/claude_docs.zip にまとめて渡す。
```

取り出したら:

```
cd D:\\Tominaga\\slope-climbing-robot
Expand-Archive -Path $HOME\\Downloads\\claude_docs.zip -DestinationPath . -Force
(Get-ChildItem claude -Recurse -Filter *.md).Count
git add claude docs/experiments/exp09_turn_reproducibility.md
git commit -m "docs: import project docs from claude.ai project"
```

1行版:

```
cd D:\\Tominaga\\slope-climbing-robot; Expand-Archive -Path $HOME\\Downloads\\claude_docs.zip -DestinationPath . -Force; (Get-ChildItem claude -Recurse -Filter *.md).Count; git add claude docs/experiments/exp09_turn_reproducibility.md; git commit -m "docs: import project docs from claude.ai project"
```

本数が 66 前後になっていることを確認してから push（§3a）。

---

## 2. 手順2: `AGENTS.md` をリポジトリ直下に置く

claude.ai の「プロジェクト指示欄」は Codex から見えない。
これを `D:\\Tominaga\\slope-climbing-robot\\AGENTS.md` として置く（Codex はセッション開始時に自動で読む）。中身は配布済みの `AGENTS.md` のとおり。要点:

- 読む順番（`claude/README.md` → `legacy/project_handbook.md` → 担当の引き継ぎ書 → 正本の md）
- 機械の地図（WRS機 / ノートPC / Alienware）と、**受け渡しは GitHub の `main` が唯一の正本**
- 掟（実行ディレクトリを明示・プレースホルダ禁止・`.bak`・秘密鍵を貼らせない・実機は吊って1モーターから・推測で直さない）
- `chats/` への記録ルール
- **走らせる前に書いた判定規則で採点する**（→ §4）

**短く保つ。** 長いと Codex の毎回のコンテキストを食い、肝心の md を読む余裕が減る。変わる情報は md 側に書く。

---

## 3. 手順3: 同期先を claude.ai から GitHub に切り替える

いままでは「claude.ai のプロジェクト」が2台の機械をまたぐハブだった。Codex にはそれが無いので、**GitHub がハブになる**。

### 3a. 未 push を全部出す

未 push: `664105a` 〜 `f7131f4`、`6f70dfd`、夜間の commit、＋§1c の docs import。
実行ディレクトリ `D:\\Tominaga\\slope-climbing-robot`：

```
cd D:\\Tominaga\\slope-climbing-robot; git status --short; git log --oneline origin/main..main; git diff --stat origin/main..main | Select-String -Pattern \"\\.pt|\\.onnx|\\.npz|\\.usd|\\.stl|\\.env|\\.bak\"; git push origin main; git log -3 --format=\"%h %ad %s\" --date=iso origin/main
```

- 3番目で何か出たら push しない（重みファイルが混ざっている）。
- PAT はチャットに貼らない。push 後にハードリンク5組の `Get-FileHash` を確認（`reference/wrs_pc_environment.md`）。
- `.bak` 類は未追跡のまま残っている。**消さない**（掟）。`.gitignore` に `*.bak_*` を足して静かにする。

### 3b. ノートPC 側（実機のコード）をリポジトリに入れる

`C:\\Users\\harut\\Connect2USB2CAN` はいま git の外にある＝Codex から見ると「文書と繋がっていないコード」になる。
1週間だけなら、同じリポジトリの下にコピーで取り込むのが早い。**移動ではなくコピー。元は消さない。**

ノートPC の PowerShell（リポジトリを `C:\\Users\\harut\\slope-climbing-robot` に clone した前提）:

```
cd C:\\Users\\harut\\slope-climbing-robot
mkdir hardware\\connect2usb2can
Copy-Item C:\\Users\\harut\\Connect2USB2CAN\\*.py hardware\\connect2usb2can\\ -Force
Copy-Item C:\\Users\\harut\\Connect2USB2CAN\\t265 hardware\\connect2usb2can\\t265 -Recurse -Force
git status --short
```

- **`.venv310` と `logs` はコピーしない**（容量と秘密情報）。`.gitignore` に `hardware/connect2usb2can/.venv*` と `logs/` を足す。
- 実測ログ（`session_214916.txt` など）は、必要な数行だけ `reference/motor_can_findings.md` に転記する。生ログは git に入れない。

### 3c. deploy_pkg（重み）は git で運ばない

`D:\\Tominaga\\deploy_pkg\\deploy_pkg_20260918.zip`（4.71 MB）は**USB か共有フォルダ**でノートPC に運び、`Get-FileHash` を SHA256SUMS.txt と突き合わせる。
`DEPLOY_README.md` と `obs_contract.md` は**テキストなので `claude/` にコピーして git に入れる**。実機側の Codex がこれを読めることが仮デプロイの前提。

---

## 4. 手順4: 失われる「第三者の目」を埋める

いままでの構図は **WRS の Claude Code が実行 → Cowork の Claude が講評**、で二重化されていた。効いた例:

- 停止点4 で WRS の「G_real_peak 推し」が事前の規則と食い違っていたのを外から指摘した
- 実験06 の起動行から地形の上書きと `rel_heading_envs` が抜けているのを外から見つけた
- 「合格 1 点」を採用候補にしない判断（実験08 → 09 の連続 300 iter 規則）

Codex で1本にすると**実行した本人が採点する**構図になり、この検出力が落ちる。1週間だけの埋め方:

1. **判定規則を走らせる前にファイルに書く**（いまの運用どおり）。採点の直前に必ずその節を読み直させる。
2. **採点だけ別セッションにする。** もう1つ `codex` を立ち上げ、「実行しない。`REPORT_*.md` と規則の md だけ読んで、規則に照らして合否と食い違いを指摘する」と指示する。人格ではなくコンテキストが分かれていることに意味がある。
3. **夜間の自走はやらない。** 09-18 朝の6時間空回り（03:20 の通知が届かず 09:38 まで再開しなかった）と同じ壊れ方をする。長い学習は Windows のタスクスケジューラか単純なポーリングスクリプトで回し、**エージェントを待機させない**。

---

## 5. ChatGPT のプロジェクト機能と Codex CLI の使い分け

**両方使ってよいが、正本はリポジトリの md 1か所にする。** 二重管理が今回いちばん起きやすい事故。

| | できること | このプロジェクトでの役割 |
|---|---|---|
| **Codex CLI**（端末） | ファイルを読む・書く・コマンドを実行する。`AGENTS.md` を自動で読む | **作業の本体。** WRS の Claude Code と Cowork の両方を兼ねる |
| **Codex の IDE 拡張 / クラウド版** | 同上を別の入口から | 好みで。CLI と同じリポジトリを見る |
| **ChatGPT のプロジェクト**（web / アプリ） | 会話とアップロードしたファイル。**機械には触れない** | 相談・設計・発表資料づくり。§4-2 の「採点役」にも使える |

運用の決め:

- **md を ChatGPT のプロジェクトに常時アップロードしない。** リポジトリと ChatGPT の両方に置くと、どちらが新しいか分からなくなる（いま claude.ai で起きているのと同じ状態を作り直すことになる）。
- ChatGPT で相談したいときは、**そのとき必要な 2〜3 本だけ**をその会話に貼る／上げる。結論は Codex CLI に `claude/chats/` と正本の md へ書かせる。
- 発表資料だけは例外。ChatGPT のプロジェクトに置いてよい（リポジトリと役割が重ならない）。

---

## 6. Codex の立ち上げ手順（実務）

前提: WRS機・ノートPC とも Windows。Node.js（18 以上）が要る。

### 6a. インストール

PowerShell（管理者でなくてよい）:

```
node -v
npm install -g @openai/codex
codex --version
```

1行版: `node -v; npm install -g @openai/codex; codex --version`

- `node -v` が出なければ先に Node.js を入れる。
- `codex` が見つからない場合は npm のグローバル bin が PATH に無い。`npm config get prefix` で出た場所を PATH に足す。
- Windows ネイティブで動くが、うまくいかなければ WSL でも動く。**ただし WSL からは USB-CAN と RealSense が見えない**ので、**実機のノートPC ではネイティブ**を使う。

### 6b. サインインと設定

```
cd D:\\Tominaga\\slope-climbing-robot
codex
```

- 初回に ChatGPT アカウントでのサインインを求められる（ブラウザが開く）。API キーを使う方式もあるが、**キーはチャットにもリポジトリにも置かない**。
- 承認モード・サンドボックスは `~/.codex/config.toml`（Windows は `C:\\Users\\harut\\.codex\\config.toml`）で設定する。オプション名は版で変わるので `codex --help` と公式ドキュメントで確認する。
- **実機のモーターを触るセッションでは自動承認にしない。** 掟どおり、動かす前に何が起きるか説明させる。

### 6c. 最初の1回の流し方

リポジトリ直下（`AGENTS.md` が置いてある場所）で `codex` を起動し、最初にこう言う:

```
AGENTS.md と claude/README.md、claude/next_chat_briefing.md を読んで、
いまの現在地と今日やることを10行以内で要約して。まだ何も変更しないで。
```

要約が正しければ引き継ぎは成功。ずれていたら、ずれた分だけ md を直す。

- **`archive/wrs_new_chat_start.md` を貼る儀式は不要になる**（あれは Claude Code 向け）。
- **WRS機とノートPCで別々に立ち上げる。** 作業の切りで push / pull する。片方が push し忘れると、もう片方が古い md を正しいと思い込む ── これが今回いちばん起きやすい事故。

---

## 7. 発表（1週間後）に向けた割り切り

- **方策は H_eff13p5@2999 で凍結する。** 予備 G_real_peak@2999。
- **その場旋回は打ち切る。** 実験06・08・09 と3回続けて「合格が点でしか出ない＝汎化していない」。原因（①その場旋回の指令が学習中 0.38% しか出ていなかった ②足上げ報酬の判定が並進だけ）は特定済みなので、**発表では「未達・原因は特定済み」として出す**のがいちばん誠実で、時間も減らない。
- **今日回すなら P1（`P_gainDR_narrow`）だけ。** stiffness ×0.7 で転倒 6.2% という**実機で実際に効く弱点**を直接潰す1本。旋回の2巡目（`O_turn35` / `O_w2`）は回さない。
- **保険の動画を先に撮る。** 実行ディレクトリ `D:\\Tominaga\\slope-climbing-robot\\tools\\runs`：
  `.\\_play.ps1 -Run 2026-09-17_00-08-51_H_eff13p5 -Ckpt model_2999.pt -Terrain flat -NumEnvs 16 -Video -VideoLength 500`
- **残りの時間は実機に寄せる。** 制御ループ ver9 の乾式テスト → 吊った状態で1モーター → 脚1本 → 全身（`archive/next_chat_briefing_motor.md` の M1〜M9）。

---

## 8. チェックリスト（上から順に）

- [ ] **md を claude.ai から書き出す**（§1c）── これが終わるまで他は意味がない
- [ ] リポジトリの `claude/` に展開して commit、本数を確認（§1c）
- [ ] `AGENTS.md` をリポジトリ直下に置いて commit（§2）
- [ ] 未 push（`664105a`〜`f7131f4`, `6f70dfd`, 夜間分, docs import）を push（§3a）
- [ ] `.gitignore` に `*.bak_*` を足す（§3a）
- [ ] WRS機に Codex を入れて `codex` 起動 → §6c の要約が正しいか確認
- [ ] ノートPC にリポジトリを clone、`hardware/connect2usb2can/` に実機コードをコピー（§3b）
- [ ] `DEPLOY_README.md` と `obs_contract.md` を `claude/` にコピーして commit（§3c）
- [ ] `deploy_pkg_20260918.zip` を USB でノートPC へ。SHA256 照合（§3c）
- [ ] 保険の動画を撮る（§7）

## 出典

- [@openai/codex - npm](https://www.npmjs.com/package/@openai/codex)
- [openai/codex - GitHub](https://github.com/openai/codex)
- [Advanced Configuration | ChatGPT Learn](https://developers.openai.com/codex/config-advanced)
- [How to Run Codex CLI on Windows: Native Install or WSL](https://www.codeagentswarm.com/en/guides/codex-cli-on-windows)
