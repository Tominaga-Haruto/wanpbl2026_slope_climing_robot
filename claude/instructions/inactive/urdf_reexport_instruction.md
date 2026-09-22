# 指示書: Onshape 再エクスポートで機体を作り直す（Alienware 側 Claude Code 向け）

> **更新 2026-09-14。** CAD 側の木構造修正が完了したので、本文書の位置づけが変わった。
> **これが機体を正す唯一の工程になった。** `claude/urdf_tree_fix_instruction.md`（URDF の親付け替えパッチ）は**廃止**。当てる必要はない。
>
> **★前提: Alienware が 2026-09-13 から故障中。** 復旧するまで本作業は着手できない（`claude/alienware_repair_instruction.md`）。

---

## 背景（何がどう直ったか）

### ① 木構造の非対称 ── CAD 側で解決済み（2026-09-14）

**真因は CAD の Mate ではなく、onshape-to-robot の「木の根の選ばれ方」だった。**

> The **first instance** in the assembly list will be considered as the base link
> （onshape-to-robot 公式ドキュメント）

修正前のインスタンス並び順の先頭が `Part 1 <3>`（右股回転の出力ブラケット 0.0649 kg）だったため、**左右対称な CAD が「右脚4関節・左脚6関節」の URDF に化けていた。**

**Onshape のインスタンス一覧で胴体 `Part 1 <6>` を先頭にドラッグして解決。Mate は1つも触っていない。**
修正後（API 実測）: 木構造は深さ1〜5に HR/HAA/HFE/KFE/FFE が左右対称、根リンク = 胴体 2.918 kg、総質量 **10.1058 kg**。

**→ 再エクスポートすれば正しい木が出るはず。それを検証するのが本作業の主目的。**

詳細: `claude/urdf_asymmetry_finding.md` / `claude/onshape_cad_fix_instruction.md`

### ② 質量・慣性 ── CAD 側は正しい

- 2026-09-06 に Onshape 側（**004_sim = ダミー円柱版**）の材質を設定し直した。**ダミー円柱にも正しい質量が入っている**（AK10-9 = 0.96 kg / AK80-9 = 0.485 kg）
- 現在の `robot_sim.urdf` は「9/6 にスクリプトで書き換えた質量 × 旧 CAD 由来の慣性」というちぐはぐな状態
- **再エクスポートすれば質量も慣性（非対角成分込み）も CAD から一括で入る。密度逆算スクリプトの再適用は不要**
- **STEP / STL は質量を運ばない**（9/6 に実測確認済み）。質量・慣性は onshape-to-robot が Onshape API から直接取る経路でしか入らない

### ③ 関節 limit / effort / velocity ── 再エクスポートで消える。実機値へ入れ直す

9/6 に Skyentific 準拠にしたが、**モーターが違う（AK10-9 / AK80-9）。** 入れ直すが、**値の決定はユーザー判断**（定格かピークか。引き継ぎ書 未決#3）。

---

## 鉄則

- **推測で進めない。** 文書ではなく実ファイルを見て確認してから動く。
- **破壊的操作の前に必ずバックアップ。** 上書き後に気づいても手遅れな操作がある。
- **複数行 Python をターミナルに直貼りしない。** `tools/` に `.py` として書いてから実行する。
- Python は **venv 有効化必須**（`source ~/projects/slope-climbing-robot/isaac_env/bin/activate`）。素の `python` は存在しない。
- **`IsaacLab/` 本体は触らない。** 既存の `.bak` と過去チェックポイントは消さない。
- **★指定した停止点（Step 2 / Step 5 / Step 8）では必ず報告して指示を待つ。** 勝手に先へ進まない。

---

## Step 0 — 過去の作業の退避

①（URDF の親付け替えパッチ）は**廃止**したが、途中まで作った成果物が残っている可能性がある。

1. `git status --short` と `ls -la tools/` で何が残っているか確認する。
2. `dump_tree.py` / `fix_tree.py` / `fk_before.txt` / `fk_after.txt` / `*.bak_treefix` があれば **`tools/step1_archive/` へ移して保存**する。FK 検証のロジックは後で再利用できる。
3. **`*.bak_treefix` が `robot_sim.urdf` に適用済みでないか確認する。** 適用済みなら、再エクスポートで上書きされるので実害はないが、状態として報告する。

**報告してから次へ。**

## Step 1 — ★ 前提確認（1つでも違えば止めて報告）

### (a) onshape-to-robot の版と「根の選び方」の実装を確認する ★最重要・新規

**「最初のインスタンス＝base」は最新版ドキュメントの記述。手順書には 1.8.2 とあり、実物がその挙動かは未確認。**

```
source ~/projects/slope-climbing-robot/isaac_env/bin/activate && onshape-to-robot --version && python -c "import onshape_to_robot, os; print(os.path.dirname(onshape_to_robot.__file__))"
```

出たディレクトリに対して、根をどう選んでいるか grep する（ファイル名は版で違うので両方試す）:

```
grep -rn "root_nodes\\|base_links\\|first\\|trunk\\|fixed" --include="*.py" <上で出たディレクトリ> | head -40
```

> ※ここだけは実パスが事前に分からないので、**上のコマンドで出た実名を埋めてから**実行すること（山括弧のまま打たない）。

**判定:**
- **「インスタンス順の先頭を根にする」実装なら → そのまま Step 2 へ**
- **「fixed なインスタンスを根にする」実装だった場合 → 止めて報告。** Onshape 側は固定インスタンス0個なので、別の対応が要る
- **どちらとも読めない場合 → 止めて報告**

### (b) config.json

`onshape_export/myrobot_dummy/config.json` を表示し、次を確認する。

| 項目 | あるべき値 |
|---|---|
| `url` | **004_sim（ダミー円柱版）の Assembly タブ**を指していること |
| `no_dynamics` | **`false`**（`true` だと質量ゼロで出る） |
| `merge_stls` | `\"all\"` |
| `output_format` | `\"urdf\"` |
| `simplify_stls` | `false` |
| `use_collisions_configuration` | `true` |

`df -h` で空き容量も確認する（過去にディスク100%の事故あり）。

## Step 2 — ★ ここで報告して止まる

Step 1(a) の判定結果を報告する。**ユーザーの確認を得てから Step 3 へ。**

## Step 3 — バックアップ

`onshape_export/myrobot_dummy/bak_prereexport/` を作り、`robot.urdf` / `robot_sim.urdf` / `config.json` と **既存の `usd/` 一式**をコピーする。
`assets/merged/*.stl` は再生成されるのでコピー不要（容量が大きい）。

**旧 `robot_sim.urdf` は Step 6 のリンク名対応表を作るのに使うので、必ず残す。**

## Step 4 — 再エクスポート

```
source ~/projects/slope-climbing-robot/isaac_env/bin/activate && cd ~/projects/slope-climbing-robot/onshape_export && onshape-to-robot myrobot_dummy 2>&1 | tail -40
```

242 部品のメッシュ取得で数分かかる。`tail` にパイプしているので**完了まで無出力が正常**。
`KeyError: 'mass'` が出たら 004_sim ではなく本物モーター版を見ている → **止めて報告**。

## Step 5 — ★★ 検算（ここで必ず報告して止まる。今回の成果の検証）

新しい `robot.urdf` に対して `tools/verify_export.py` を書いて実行する。

1. **木構造（`parent -> child`）** → **base から2本の枝がそれぞれ5関節なら成功。** 6関節と4関節に分かれていたら**失敗なので止めて報告**
2. **base になったリンクの質量** → **胴体なので 2.9 kg 前後のはず。1 kg を切っていたら根がずれている**
3. link 数 / joint 数 / type 内訳 → **11 / 10 / revolute 10 / fixed 0**
4. 全リンクの質量と**合計** → **Onshape 実測の 10.1058 kg と一致するか**
5. 慣性テンソルの非対角成分（`ixy` / `ixz` / `iyz`）が全部ゼロでないこと → **`no_dynamics:false` で実値が取れた証拠**
6. 左右の対になるリンクの質量が一致するか → **`*_hr` の左右が一致すれば、旧 URDF の 2.13倍の差が解消した証拠**
7. ゼロ姿勢の順運動学（全リンクのワールド座標）を `tools/fk_new.txt` に保存

URDF の rpy は**外因性 XYZ（固定軸）** ＝ `R = Rz(yaw) @ Ry(pitch) @ Rx(roll)`。

**報告して止まる。**

## Step 6 — link 名の改名（★最大の落とし穴）

- **`rename_links_dummy.py` のハードコード表は絶対に流用しない。** 再エクスポートで `part_1_N` の連番が変わり、**古い表は黙って別のリンクに名前を付ける。エラーは出ない。**
- **今回は木構造が変わっているので、旧 URDF との位置照合も使えない可能性がある。** 木構造ダンプ（Step 5-1）を見て、**base から辿った順で機械的に名前を割り当てるのが確実**:
  - base から HR → HAA → HFE → KFE → FFE と辿り、joint 名（`LR_*` / `LL_*`）に対応する小文字のリンク名を child に付ける
  - joint 名は Onshape の `dof_` Mate 名がそのまま入っているので信用できる
- 対応が付いたら `robot.urdf` を `robot_sim.urdf` にコピーしてから改名する。
- 目標命名: `base` ＋ `lr_hr / lr_haa / lr_hfe / lr_kfe / lr_ffe`（右）、`ll_*`（左）。**link 名は小文字、joint 名は大文字**（`LR_HR` 等）。
- **mesh の `filename` は触らない**（触ると MISSING）。
- 改名後に **もう一度 Step 5-1 の木構造ダンプを実行**し、link 一覧と STL の MISSING チェックを出す。

## Step 7 — 相対パス化

STL 参照の `package://` を除去して `assets/...` にする。実行後に MISSING チェック。

## Step 8 — ★ joint limit / effort / velocity（ここで止まって指示を待つ）

- 再エクスポート直後の値をそのまま報告する。
- **9/6 の Skyentific 値を再適用してはいけない。** モーターが違う（AK10-9 / AK80-9）。
- 実機値を入れる方針だが、**定格を使うかピークを使うかは未決**（引き継ぎ書 未決#3）。**勝手に決めず指示を仰ぐ。**
- 参考（手順書 B7）: AK10-9 = 定格18 / ピーク53 N·m、AK80-9 = 定格9 / ピーク22 N·m。**HR・HAA・KFE = AK10-9、HFE・FFE = AK80-9。**

## Step 9 — USD 変換とコピー

1. 変換前に `usd/` を `usd.bak_prereexport2` として退避（Step 3 とは別に、直前の状態を確実に残す）。
2. `convert_urdf.py` で `robot_sim.urdf` → `usd/robot.usd` を再生成（手順書 B3 段階5）。
3. 出力先を `ls -la` して実在とタイムスタンプ更新を確認。
4. **見本アセットフォルダへコピーし直す**（手順書 B3 段階7a）:
   `references/BipedalRobotSim/skyentific_poclegs/skyentific_poclegs/assets/robots/myrobot_dummy/`
   **忘れると古い USD で学習が回る。エラーは一切出ない。**
   **コピー前に既存のフォルダをバックアップする**（ここが学習の読む本体）。

## Step 10 — テスト起動

```
source ~/projects/slope-climbing-robot/isaac_env/bin/activate && cd ~/projects/slope-climbing-robot/IsaacLab && ./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py --task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 64 --max_iterations 20 --headless
```

20 iter 完走でロード成功。`ValueError: ... base: []` は改名漏れ。

## 注意

- **既存チェックポイントは機体が変わるので全部無効。学習はやり直しになる。** 避けられない。
- **質量分布が変わるので、2026-09-08 のトルク実測（HFE 43.55〜48 / KFE 60 など）は取り直しになる。** B12 の診断はこの後で。
- **`base` が本当に胴体になるので、`base_contact` 終了条件と `add_base_mass` イベントの効き方が変わる**（手順書 B4）。転倒判定の挙動が変わっても異常ではない。
- 通ったら `git status --short` で `.env` / `*.usd` / `*.stl` / `*.part` が混ざっていないか確認してからコミット。

## 報告してほしいこと

1. Step 0: 旧パッチの残骸がどこまであったか
2. **Step 2: onshape-to-robot の版と、根の選び方の実装（grep の結果）**
3. **Step 5: 木構造が 5/5 になったか／base の質量／合計質量／非対角慣性の有無／左右の `*_hr` の質量が一致したか**
4. Step 6: 新しいリンク名の対応表
5. Step 8: 再エクスポート直後の limit / effort / velocity
6. Step 10: テスト起動が通ったか
