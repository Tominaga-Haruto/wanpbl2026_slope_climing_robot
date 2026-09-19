# M7: Hのgolden再生・ONNX乾式ループ

> 担当はWindowsノートPCの `Connect2USB2CAN`。CANなしでHのONNX入出力と目標角計算を再現する。
>
> D5のコントローラー入力は不要。固定コマンドやT265の実測値も、この乾式ループには入れない。

## 完了（2026-09-19）

`Connect2USB2CAN/policy_dry_run.py` と最小テストを実装し、H_eff13p5@2999の読み取り専用パッケージで確認した。

- manifestの6必須ファイルはすべてSHA256一致。
- 500 stepのaction最大絶対誤差は `1.1920929e-06`（step 335）、目標角は `5.96046448e-07`（step 113）。いずれも閾値 `1e-4` 以下。
- `--realtime` の500行CSVを保存。周期平均20.026 ms、最大40.687 ms、最大deadline遅れ22.104 ms、推論最大4.409 ms。Windowsの乾式測定値であり、実機統合の周期合格とは扱わない。
- CAN、モーター、T265、コントローラー、USB機器への接続はしていない。

実装・数値の記録は `reports/2026-09-19_m7-onnx-golden-dry-run.md`。この文書は完了記録として残し、次の統合タスクはここでは開始しない。

## ゴール

`golden.npz` の既知観測を50 Hzで再生し、`policy.onnx` の10 actionと10目標角をgoldenデータと比較する、送信不能な乾式ツールを実装する。

成功してもCAN接続、モーター通電、T265接続、コントローラー接続には進まない。

## 最初に読むもの

1. `claude/README.md` と `claude/project_handbook.md`。
2. この文書と `claude/next_chat_briefing_motor.md`。
3. 読み取り専用で、成果物フォルダの `SHA256SUMS.txt`、`obs_contract.md`、`golden.md`、`verify_onnx.md`、`DEPLOY_README.md`。
4. `C:\Users\harut\Connect2USB2CAN\mit_sim.py` は将来の境界確認用としてのみ読む。今回importしない。

成果物の実在パスは `C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999\`。作業前に `claude` と `Connect2USB2CAN` の両方で `git status --short` を確認する。成果物フォルダは読み取り専用で使い、コピー、移動、上書き、Git追加をしない。

## 固定された契約

- ONNX入力は42、出力は10。
- 制御周期は50 Hz（20 ms）。
- goldenは500 stepで、`obs_flat` は `(500, 42)`、`action_raw` は `(500, 10)`、`joint_target` は `(500, 10)`。
- actionの順は `LL_HR, LR_HR, LL_HAA, LR_HAA, LL_HFE, LR_HFE, LL_KFE, LR_KFE, LL_FFE, LR_FFE`。
- `joint_target = default_joint_pos + action_scale * action_raw`、`action_scale = 0.5`。
- ONNXの既知の照合閾値は最大絶対誤差 `1e-4`。この値をaction比較の判定閾値にする。
- M4を独立工程にしない。AK80-9／AK10-9の実測Kp/Kd係数は将来のMIT送信時に参照する既知設定であり、この乾式ツールはゲインを送信・検証しない。

## 実装範囲

`Connect2USB2CAN` に、CANライブラリに依存しない新規スクリプト（例: `policy_dry_run.py`）と、必要最小限のテストを作る。

1. CLIで成果物フォルダを受け取り、6必須ファイルのSHA256を`SHA256SUMS.txt`と照合する。1件でも不一致なら推論せず非ゼロ終了する。
2. `numpy.load` でgoldenを読む。キー・shape・dtypeを検査し、契約外なら非ゼロ終了する。
3. `onnxruntime.InferenceSession` の実際の入力／出力名とshapeを取得し、42→10でないなら非ゼロ終了する。名前を推測で固定しない。
4. `obs_flat` の各行をfloat32で推論し、`action_raw` と最大絶対誤差を比較する。全500行の最大値と最悪stepをログ／CSVへ出す。
5. 実行actionから `default_joint_pos + action_scale * action` を計算し、`joint_target` と比較する。同じく最大誤差と最悪stepを出す。
6. `--realtime` 時だけ20 ms予定表で500 stepを再生し、deadlineとの差、推論時間、周期をCSVへ記録する。既定は高速照合でよい。
7. 成功はaction／目標角の両方が`1e-4`以下で、実行中にCAN・USB・T265・入力デバイスへ触れていないこと。

実行Pythonはまず `.venv310\Scripts\python.exe` で`numpy`と`onnxruntime`のimportを確認する。足りない依存を勝手に追加しない。

## 今回は禁止

- `can`、`pyrealsense2`、`evdev`、`motor_console_ver*.py`、`mit_sim.py`のimport。
- CANアダプタのopen、送信、受信、モーター通電。
- T265とコントローラーの接続。
- golden観測を実機観測に差し替えること、42観測を合成すること、固定コマンドを注入すること。
- 関節原点変換、ソフトリミット、Kp/Kd適用、MITフレーム生成。これらは後続統合の範囲。
- `policy.onnx`、`golden.npz`、CSVログ、`.venv310`をGitに追加すること。

## 実行・確認の最小形

実装後は、`C:\Users\harut\Connect2USB2CAN` で `.venv310\Scripts\python.exe policy_dry_run.py --package C:\Users\harut\wanpbl2026_slope_climing_robot\H_eff13p5_2999\H_eff13p5_2999` の形で実行できるようにする。続いて同じ入力で `--realtime` を実行し、周期ログを確認する。CANケーブルやモーター電源の有無に依存してはならない。

## 完了条件

- manifestの必須6ファイルが一致することをプログラムで確認できる。
- golden 500件でONNX actionの最大誤差が`1e-4`以下。
- golden 500件で目標角の最大誤差が`1e-4`以下。
- 50 Hz再生の周期ログが残る。
- 実装がCAN・モーター・T265・コントローラーに依存せず、接続もしない。

## 終了時

- 完了済み。引き継ぎ記録は `chats/2026-09-19_m7-onnx-golden-dry-run.md` を参照。
- `Connect2USB2CAN` では対象スクリプトとテストだけをcommit/push済み（`e0a9448`）。重み、CSVログ、仮想環境はGitに追加していない。
