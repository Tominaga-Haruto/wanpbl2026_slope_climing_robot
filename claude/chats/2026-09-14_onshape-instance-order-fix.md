# 2026-09-14 木構造の真因確定と Onshape 側の修正

## やったこと

1. `claude/onshape_cad_fix_instruction.md` に沿って、Onshape 004_sim の Mate 構造の診断に着手した。
2. **スクリーンショットを目で追う代わりに、ブラウザのログイン済みセッションから Onshape の Assembly API を直接叩いた。**
   - `GET /api/v6/assemblies/d/{did}/w/{wid}/e/{eid}?includeMateFeatures=true`
   - `rootAssembly.features[].featureData.matedEntities[].matedOccurrence` で「どのインスタンスを繋いでいるか」を全件取得
   - Fastened 系 mate で union-find して剛体グループ（＝link）を作り、`dof_` mate を辺にして木を組み直した
3. **CAD は壊れていなかった。** `dof_` はちょうど10個、剛体グループ11個、木は左右対称。
4. **観測されていた URDF の木と、CAD の木を「無向グラフ」として突き合わせたら完全一致した。違いは根の位置だけだった。**
5. onshape-to-robot の公式ドキュメントを確認し、**「アセンブリのインスタンス一覧の先頭が base link になる」**という仕様を見つけた。
6. 先頭が `Part 1 <3>`（右股回転のブラケット 0.0649 kg）であることを API で確認。**そこを根にすると観測された 4/6 の形に1本残らず一致する**ことを計算で確かめた。
7. ユーザーがバージョン `before_tree_fix_20260914` を切り、**インスタンス一覧で胴体 `Part 1 <6>` を先頭にドラッグ。**
8. API で検算 → 木構造が左右対称になったことを確認。
9. 古くなったプロジェクト文書6本を再構成で書き換えた。

## 決めたこと・分かったこと

### 真因

**onshape-to-robot の「木の根の選ばれ方」。CAD の Mate ではなかった。**

> The **first instance** in the assembly list will be considered as the base link
> （[onshape-to-robot: Design-time considerations](https://onshape-to-robot.readthedocs.io/en/latest/design.html)）

インスタンスの並び順は誰かが決めたものではなく、**部品を挿入した順が残っていただけ。**

### 修正前後（Onshape API 実測）

| 項目 | 修正前 | 修正後 |
|---|---|---|
| 先頭インスタンス | `Part 1 <3>`（0.0649 kg のブラケット） | **`Part 1 <6>`（胴体プレート 0.7871 kg）** |
| 根リンクの構成 | Part 1 `<3>` + AK10-9 ×1 | **Part 1 `<6>` + `<12>` + AK10-9 ×2 = 2.918 kg** |
| 木構造 | 右4関節・左6関節 | **深さ1〜5 に HR/HAA/HFE/KFE/FFE が左右対称** |
| 総質量 | 10.1058 kg | **10.1058 kg（不変）** |
| インスタンス / `dof_` / グループ | 22 / 10 / 11 | 22 / 10 / 11（不変） |

**Mate は1つも触っていない。**

### 過去の結論の訂正

| 日 | 当時の結論 | 実際 |
|---|---|---|
| 2026-09-06 | 「構造非対称が主犯。報酬をどういじっても直らない」 | 追試で否定 |
| 2026-09-08 | 「非対称の正体は CAD の mate の張り方」 | **外れ。** mate は最初から正しかった |
| 2026-09-14 | **根の選ばれ方（並び順）が原因** | 確定 |

**副産物の訂正:**
- `base` が 0.2406 kg と軽すぎたのは、**`base` が胴体ではなく小さなブラケットだったから**
- `lr_hr` が 2.1692 kg・bbox 29 cm と異常だったのは、**それがそもそも胴体だったから。** 9/08 の「胴体の形状が `lr_hr` に吸い込まれた」という解釈は逆だった
- したがって **`base_contact` 終了条件は「胴体の接地」を見ていなかった。** `add_base_mass` も 0.24 kg のリンクに ±1 kg を与えていた。**再エクスポート後は挙動が変わる**

### 再利用できる手法

1. **Onshape の Assembly API をブラウザから直接叩く。** Alienware が無くても CAD の構造を実測できる。GUI を目で追うより確実で速い。
2. **URDF を無向グラフに直して CAD と突き合わせる。** 親子の向きを外すと、**根の選び方の違いと構造そのものの違いが分離できる。** これを最初にやれば 9/08 の誤診は避けられた。

### 今後の注意

- **インスタンス一覧の先頭は胴体 `Part 1 <6>`。動かさない。** 再エクスポート前に毎回確認する
- **Onshape の「固定（Fixed）」は使わない。** onshape-to-robot ではそれが「地面に固定されたロボット」の指定になる。**固定インスタンス0個が正しい**
- **config.json に根を指定するオプションは無い**（公式オプション一覧で確認済み）

### 教訓

**ツールの暗黙の前提を一次資料で確認していなかった。** config が正しくても、ツールが何を入力とみなすかを知らなければ壊れた出力が出る。
そして **link 11 / joint 10 / revolute 10 / fixed 0 という集計値は全部目標通りだった。数を数える検証では構造の誤りは見つからない。**

## 手を動かした場所

- Onshape 004_sim（`d103e836077cf07efd7a6f0f`）の Assembly 1 ── インスタンス並び替えのみ。Mate は無変更
- バージョン: `before_tree_fix_20260914` / `after_tree_fix_20260914`
- 書き換えたプロジェクト文書:
  - `claude/urdf_asymmetry_finding.md` ── 真因を差し替え、診断手順に「無向グラフ照合」「Assembly API」を追加
  - `claude/onshape_cad_fix_instruction.md` ── 完了記録に置き換え
  - `claude/project_handbook.md` ── A0 / A1 / A2 / B1 / **B2 全面改稿** / B3 / B4 / B6 / B7 / B8 / B9 / B11 / B12
  - `claude/handover.md` ── 現在地・直近の変更・次の一歩・未決・原則
  - `claude/next_chat_briefing.md` ── 2026-09-14 版に作り直し
  - `claude/urdf_reexport_instruction.md` ── 「機体を正す唯一の工程」に位置づけ変更。版確認ステップを追加
  - `claude/urdf_tree_fix_instruction.md` ── **廃止**（技術メモとしてのみ残す）
  - `claude/README.md` ── 索引を更新

## 積み残し・次にやること

1. **Alienware の復旧**（2026-09-13 から故障中。電源は入るが映らず約1分で落ちる）
2. **再エクスポート。** その前に **onshape-to-robot のインストール済み版が本当に「最初のインスタンス＝base」規則か grep で確認する**（引用は最新版ドキュメント、手順書には 1.8.2 とある）
3. 再エクスポート後: 木構造ダンプで 5/5 と **base の質量 2.9 kg 前後**を確認 → `rename_links_dummy.py` の表を作り直す → 関節 limit（実機値。定格かピークかは未決） → USD 変換 → 見本アセットへコピー → 64env/20iter
4. **既存チェックポイントは全部無効。学習はやり直し**
5. 2026-09-08 のトルク実測も取り直し（質量分布が変わるため）
