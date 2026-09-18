# 【完了】Onshape の木構造非対称を直す（2026-09-14 完了）

> **この作業は完了した。新しく着手することは無い。**
> 経緯・真因・再発防止は `claude/urdf_asymmetry_finding.md` にまとめてある。
> 次の工程は `claude/urdf_reexport_instruction.md`（Alienware 復旧待ち）。

---

## 結論（1分で読む用）

**CAD は壊れていなかった。** Mate 構造は最初から左右対称で、`dof_` も10個ちょうど揃っていた。

非対称の正体は **onshape-to-robot の「木の根の選ばれ方」**だった。

> The **first instance** in the assembly list will be considered as the base link
> （onshape-to-robot 公式ドキュメント）

修正前の先頭インスタンスは `Part 1 <3>`（右股回転の出力側ブラケット 0.0649 kg）で、胴体ではなかった。
左右対称な木をそこを根にして辿り直すと、観測されていた「右4関節・左6関節」の形にそのまま化ける。

**修正はインスタンス一覧で `Part 1 <6>`（胴体 0.7871 kg）を先頭にドラッグしただけ。Mate は1つも触っていない。**

---

## 修正後の実測（Onshape API）

| 項目 | 値 |
|---|---|
| 先頭インスタンス | `Part 1 <6>` |
| 根リンクの構成 | `Part 1 <6>` + `Part 1 <12>` + AK10-9 ×2 = **2.918 kg**（胴体） |
| 木構造 | 深さ1〜5 に HR / HAA / HFE / KFE / FFE が**左右対称** |
| 総質量 | **10.1058 kg**（修正前と同じ） |
| インスタンス / `dof_` / 剛体グループ | 22 / 10 / 11（すべて変化なし） |

バージョン: `before_tree_fix_20260914` / `after_tree_fix_20260914`

```
胴体 ─┬─ LR_HR → LR_HAA → LR_HFE → LR_KFE → LR_FFE
      └─ LL_HR → LL_HAA → LL_HFE → LL_KFE → LL_FFE
```

---

## この CAD を今後触るときの注意

- **インスタンス一覧の先頭は胴体 `Part 1 <6>` でなければならない。** これが `base` の定義。
  再エクスポートの前に毎回確認する。新規部品の挿入は末尾に入るので通常は安全。
- **Onshape の「固定（Fixed）」は使わない。** onshape-to-robot ではそれが「地面に固定されたロボット」の指定になる。
  二足歩行では致命的。**固定インスタンス0個**が正しい状態。
- **config.json に根を指定するオプションは無い**（公式オプション一覧で確認済み）。根は並び順でしか決められない。
- 本物モーター版（004）は触らない。作業対象は **004_sim（ダミー円柱版）** のみ。
- モーターのサブアセンブリは外部参照。編集しない。
- パーツの材質を変えない（2026-09-06 に正した状態が入っている）。
- **Onshape 公式の URDF エクスポート機能は使わない**（link 1299 / joint 1298 の異常出力になった前例）。

---

## 診断に使った方法（他の CAD 問題にも効く）

Onshape の Assembly API をブラウザのセッションから叩けば、**Ubuntu 機が無くても木構造を実測できる。**

- `GET /api/v6/assemblies/d/{did}/w/{wid}/e/{eid}?includeMateFeatures=true`
- `rootAssembly.features[].featureData.matedEntities[].matedOccurrence` が「どのインスタンスを繋いでいるか」
- Fastened 系 mate で union-find → 剛体グループ（＝link）、`dof_` mate を辺にして木を組む

**決め手は「URDF を無向グラフに直して CAD と突き合わせる」こと。** 親子の向きを外すと、根の選び方の違いと構造そのものの違いが分離できる。今回は無向グラフが完全一致した＝ CAD は正しく根だけずれていた、と確定できた。
