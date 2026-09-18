# 2026-09-14 Alienware の故障切り分けと、WRS機への移設決定

## やったこと

1. **Alienware の症状を時系列で取り直した。** 9/13 の「約1分で落ちる」から始まり、この日のうちに「3分持つ」「起動ループ」「十数分持つ」と変化した。
2. **電源ボタンLEDを確認した。** ケース照明（赤→黄のグラデーション）と完全に同期しており、**Dell の診断エラーコード（オレンジ⇄白の点滅）ではなかった。**
3. **TeamViewer で一度つながった。** Ubuntu が起動していることが確定した。
4. **SSH の導入を試みて失敗した。** `unattended-upgr` が dpkg のロックを握っていた。
5. **データ量とサービスタグを取るコマンドを打とうとしたところで電源が落ちた。** 以降つながっていない。
6. **代替機（WRS機）の諸元をコマンドで実測した。** RTX 3090 Ti / RAM 127GB / D: 553GB 空き。
7. **WRS機に TeamViewer で接続できた。**
8. **ドキュメントを更新した**（下記）。

---

## 決めたこと・分かったこと

### ★「熱依存」モデルは棄却された

最初、Claude は「冷やすほど長く持つ」という整理を出した。**ユーザーが「休止時間が違うだけでは」と反論し、それが正しかった。**

| 直前の休止時間 | 持った時間 |
|---|---|
| 2日 | 約3分 |
| 直後の再投入 | 数秒（起動ループ） |
| 15分＋完全放電 | 十数分 |

**冷却時間と持続時間が逆転している。** 規則性は見つかっていない＝**間欠故障**として扱う。

**教訓: ユーザーが自分の観察に基づいて反論してきたら、たいてい正しい。守りに入らずデータを並べ直す。**

### ★ ドライバ原因説の見立てを更新した

| 症状 | 見立て | 根拠 |
|---|---|---|
| **電源が落ちる** | **ほぼ 0%** | 起動ループは OS 読み込み前に起きている。落ちたときの負荷も `grep` 程度 |
| **映らない** | **20〜30%** | 9/04 のロールバックから 9/12 まで8日間正常＝ロールバック自体は無実。**ただし自動更新がカーネルを上げた経路は生きている** |

**旧版の指示書は「ドライバ説は完全に排除」と断定していた。これは言い過ぎだった。**
排除の論拠は「ドライバは電源を落とせない」に依存していたが、**電源が落ちない状態が観測された時点で、その論拠は映像側には効かない。**

また「ドライバは BIOS 画面を消せない」という論拠も弱い。**モニターの同期に2〜3秒かかると、その間に出ている Alienware ロゴを取りこぼして「信号なし」に見える**（特に DisplayPort）。

**ただし深刻なのは電源断のほうで、そちらはドライバで説明が付かない。物理側の切り分けを優先する。**

### ★ 遠隔アクセスが単一障害点だった（今回詰んだ直接の原因）

**Alienware は TeamViewer だけで、しかも「接続のたびに画面のパスワードを読む」設定だった。** 画面が映らなくなった時点で、IDもパスワードも読めなくなり、入れなくなった。

**→ 新しいマシンでは最初にこの3つをやる:**
1. **「ご使用のID」（9〜10桁）をメモする**（変わらない）
2. **個人パスワード（無人アクセス用）を設定する**
3. **TeamViewer アカウントにデバイスを割り当てる**

Linux 機なら `openssh-server` も入れる（TeamViewer は X11 依存で、X が死ぬと一緒に死ぬ）。

### ★ WRS機へ移設することにした

**買い替えは不可。** 他の人の PC を借りる線で、共有の Windows デスクトップ（WRS機）が使えることになった。

| 項目 | 値 | 判定 |
|---|---|---|
| GPU | **RTX 3090 Ti / VRAM 24,564 MiB** | Alienware の 4070 12GB より上 |
| ドライバ | 591.86 | Windows 要件 580.88 以上を満たす |
| RAM | 127.4 GB | 要件32GBを大きく超える |
| OS | Windows 11 Education | 対応 |
| C: | 41.3GB 空き | **使わない** |
| **D:** | **553.8GB 空き** | **ここに全部入れる** |

**Isaac Sim 5.1 の要件は NVIDIA 公式の要件表で確認した**（RT Cores 必須、Windows ドライバ 580.88 以上、RAM 32GB、50GB SSD）。
**VRAM の公称16GBは実態より厳しめ**（Alienware は 12GB・実使用 5.4GB で回っていた）。**譲れないのは RT Cores の有無。**

### ★ これは共有マシンである（掟を決めた）

conda 環境の一覧に `jerry_isaaclab` / `matsuuchi_env` / `unitree_sim_env` などがあり、Isaac Lab も **`C:\\Jerry\\IsaacLab`** と **`D:\\IsaacLab`（2.3.2 / b4c3210247）** の2箇所に入っていた。

1. **書き込むのは `D:\\haruto\\` の中だけ**
2. **C ドライブに大きいものを置かない**（空き41GB）。**conda 環境も `--prefix` で D: に作る**
3. **`env_isaaclab` という名前を再利用しない** ── **Isaac Lab 公式ドキュメントの手順がこの名前を使うので、そのまま打つと他人の環境を壊す**
4. **他人のプロセスを kill しない**

### ★ USD は「救出」ではなく「作り直し」が本線

GitHub に入っているのは `my_robot_code/` の5ファイルだけ。USD・STL・チェックポイントは `.gitignore` 除外。

**しかし B2 の通り、現行の USD は木構造が壊れた版で、どのみち再エクスポートが必要だった。** CAD 側は 2026-09-14 に修正済み。**救出しても捨てるものを救出することになる。**

**同じ理由で既存チェックポイント（`model_11998.pt` を含む）も全部無効になる。** 救出の価値は「過去の比較対象」としてのみ残る。**優先度は下がった。**

### Windows 特有の論点（未検証）

- **symlink に管理者権限が要る。** 借り物では頼みにくい → **同一ドライブ内なら ハードリンク（`cmd /c mklink /H`）で代替**。未検証
- **`onshape-to-robot` が Windows で動くか未確認**
- **Onshape API キーは Alienware の `.env` にしかない** → 新規発行が早い
- **Skyentific 参考実装の remote URL が未確認**
- **3090 Ti での実測基準値は未測定**（手順書 A5 の値は RTX 4070 のもの）

---

## 手を動かした場所

**確認に使ったコマンド（WRS機・PowerShell）:**

```
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=3\" | Select-Object DeviceID,FreeSpace,Size
conda env list
Get-PSDrive -PSProvider FileSystem | ForEach-Object { Get-ChildItem -Path $_.Root -Filter \"isaaclab.bat\" -Recurse -Depth 6 -ErrorAction SilentlyContinue }
```

**参照した一次資料:**
- [Isaac Sim 5.1 Requirements (NVIDIA)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)
- [Isaac Lab Local Installation](https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/index.html)
- [Alienware Aurora R16 — System diagnostic lights (Dell)](https://www.dell.com/support/manuals/en-us/alienware-aurora-r16-desktop/alienware-aurora-r16-owners-manual/system-diagnostic-lights?guid=guid-5adfbc98-7d97-419f-bfe7-d22bb93c5ee8&lang=en-us)
- [Alienware Aurora R16 — Removing the left-side cover (Dell)](https://www.dell.com/support/manuals/en-us/alienware-aurora-r16-desktop/alienware-aurora-r16-owners-manual/removing-the-left-side-cover?guid=guid-2aba09f1-07ae-4ce4-aa2b-6c47dc9d571e&lang=en-us)

**更新した文書:**
- `claude/project_handbook.md` ── A0 現在地／**A2 を2台構成に**／**A2a（Alienware 故障）と A2b（WRS機）を新設**／A3 に遠隔アクセスの運用ルール／A4・A5 に Windows 版／B6 にトラブル4行追加／B9 の優先順位を入れ替え
- `claude/next_chat_briefing.md` ── 全面書き直し
- `claude/alienware_repair_instruction.md` ── 全面書き直し（熱依存の棄却、ドライバ説の再評価、サイドパネルの外し方、優先度の引き下げ）
- `claude/README.md` ── 現在の状況、新しい指示書2件を索引に追加

**新規作成:**
- `claude/wrs_pc_operator_instruction.md` ── 操作する側（haruto）
- `claude/wrs_pc_host_instruction.md` ── 操作される側（デスクトップの持ち主）

---

## 積み残し・次にやること

### WRS機（最優先）

1. **持ち主に許可を取る**（`wrs_pc_host_instruction.md` を渡す）── D: に50〜100GB、GPU長時間、TeamViewer の個人パスワード設定、スリープ無効化
2. **TeamViewer の ID をメモし、個人パスワードを設定してもらう**
3. **環境構築**（`wrs_pc_operator_instruction.md` の段階1〜4）── **素の Isaac Lab が動くことを先に確認する**
4. **Onshape API キーを新規発行 → 再エクスポート**（`urdf_reexport_instruction.md`）

### Alienware

5. **ケースを開ける**（つまみネジ1本。工具不要）→ 写真1枚
6. **サービスタグを取る**（保証が残っていれば修理費ゼロ）
7. **水冷ポンプの動作確認**（一度も確認できていない）
8. **挿し直し4点 + ホコリ除去**

### 文書の食い違い（次に柱Bを触るとき）

9. **手順書 A7 の「実機で動いているのはサーボモード。MIT は未検証」は、`motor_can_findings.md`（MIT がモード8で確定）と食い違っている。** 実測の正本は後者。**A7 を書き換える。**
