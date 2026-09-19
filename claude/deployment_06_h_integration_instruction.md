# D6: Hをver9へ接続して正しい10目標角を作る

## 対応するロードマップ

- §4 完了条件1・2
- §1 完了物の消費側

## 目的

D1、D3、D4の成果を使い、HのONNXに正しい42次元観測を入れ、10行動を10関節の目標角に変換する。

## 待つもの

D1のすべて、特に `policy.onnx`、`obs_contract.md`、golden npz、アクチュエータ表を待つ。これらが無ければ実装の並び・尺度・action scaleを推測しない。

## 実施内容

1. `obs_contract.md` の項目順で、D3のbase観測、D4のjoint pos/vel、重力投影などの42要素を組み立てる。
2. ONNX Runtimeで推論し、10要素のraw actionを得る。
3. 契約のdefault joint poseとaction scaleで目標角を作り、D4の逆変換へ渡す。
4. golden npzの観測を与え、出力actionと目標角がgoldenと一致することを自動テストする。
5. mit_simへ10目標角を渡して、順番・角度範囲・ゲイン表の適用を確認する。

## 完了条件

golden npzからONNX action、目標角、H順10関節配列が再現されること。ここまでは実機へ送信しない。

