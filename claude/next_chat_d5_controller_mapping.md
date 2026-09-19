# D5: 左スティックをHの速度指令へ最小接続する

> 担当はJetson上のコントローラー入力部品。CAN、モーター、T265、ONNX実行とは接続しない。
>
> この指示書はD5だけを扱う。M7（ONNX golden乾式再生）は `next_chat_m7_dry_loop.md` に分離している。

## ゴール

既存のSwitch 2 Pro入力を、ver9が消費できる3要素のコマンド入力として出せる形にする。

- 左スティックのみを候補にする。
- 出力の並びは `(vx, vy, wz)`、`wz=0` 固定。
- 固定コマンド入力を残し、コントローラーなしでもM7以後を試せるようにする。
- 今回の完了は画面・ログ・ユニットテストまで。どのハードウェアにも接続しない。

## 最初に読むもの

1. `claude/README.md` と `claude/project_handbook.md`。
2. この文書。
3. `claude/controller_next_chat_briefing.md` と `claude/controller_prep_briefing.md`。
4. 読み取り専用で `C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999\obs_contract.md`。
5. Jetsonの既存実装 `Connect2USB2CAN/controller/pad_probe.py`。

作業前に `claude` と `Connect2USB2CAN` の両方で `git status --short` を確認する。`H_eff13p5_2999` は重みを含む未追跡の成果物なので、移動・上書き・Gitへの追加をしない。

## 確定事項

- Hの観測のindex 9--11は `velocity_commands = (lin_vel_x, lin_vel_y, ang_vel_z)`。
- 各要素の学習時レンジは `[-1.0, +1.0]`。
- H成果物には、このコマンドの物理単位を明記した記述がない。
- 左スティックの実測入力は `ABS_X`（左右）と `ABS_Y`（前後）、範囲はおよそ -32768--32767。安定パスは既存 `pad_probe.py` にある。
- 初回は並進だけなので `wz=0`。旋回ボタンは追加しない。

## 実装範囲

1. 固定コマンドとコントローラー由来コマンドを同じ型／同じ出力境界から得る小部品を作る。少なくとも `fixed` を既定にし、明示指定時だけ `controller` を選ぶ。
2. `fixed` は `(vx, vy, wz)` を引数または設定からそのまま供給する。範囲外は拒否し、暗黙にクリップしない。
3. `controller` は既存の正規化済みスティック値を入力にし、`wz=0` を返す。
4. スティック軸からbase座標の `vx` / `vy` への符号は、**今回の時点では未確定**として設定値または明示フラグに留める。未確定状態での出力は必ずゼロにする。
5. 出力には、入力源、時刻、正規化スティック値、3要素コマンド、`mapping_unconfirmed` / `fixed` / `mapped` の状態を含め、画面とCSVで確認できるようにする。
6. pure functionのテストを追加し、固定入力、ゼロ入力、未確定マッピング、範囲外拒否を検証する。

物理単位を勝手にm/sとして固定しない。仮の数値上限をUI表示で使う場合も `unit_unconfirmed` と記録し、M7やCANへ接続しない。

## 今回は禁止

- CANのopen/send、`python-can`、モーターコンソール、`mit_sim`のimport。
- ONNX Runtime、`policy.onnx`、`golden.npz`のimport。
- T265、UDP、共有メモリ等による他プロセスとの統合。
- デッドマン、非常停止、200 ms途絶停止、変化率制限、USB抜線試験。これらは次段階で別に扱う。
- パッケージの無断導入、既存の未追跡ver8系の上書き、重み・CSVログのGit追加。

## 照合してから決めること

スティックの前後／左右とbaseの `+x`／`+y` の対応、符号、実単位は成果物だけでは確定しない。次チャットで座標系の正本と照合し、ユーザーと確認してから一度だけ定義する。それまでは実機へ出す経路を作らない。

## 完了条件

- コントローラーなしで固定 `(vx, vy, 0)` をログ出力できる。
- コントローラー使用時も未確定マッピングなら必ずゼロになる。
- `wz` は常にゼロ。
- テストと画面／CSVの乾式確認を残す。
- 実機CAN、モーター、T265、ONNXへの接続がコード上にも実行上にもない。

## 終了時

- `claude/chats/YYYY-MM-DD_d5-controller-mapping.md` を作り、README索引へ加える。
- 対象を絞ってGit状態を確認する。重み、CSV、生ログ、仮想環境をステージしない。
- 次のM7担当へ、固定コマンドの呼出し方と未確定の符号・単位を明記して引き継ぐ。
