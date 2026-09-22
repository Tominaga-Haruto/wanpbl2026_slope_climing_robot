# 2026-09-21 D9 T265 起動エラー修正

## 結論

`ver9_shell.RealT265.start()` が、T265を列挙したRealSense contextを保持したままpipelineを開始していたことが、D9の `No device connected` の原因だった。成功する `t265/t265_check.py` と同じライフサイクルへ合わせて修正した。

起動直後の `wait_for_frames(100)` タイムアウトも統合側だけが致命エラーとしていたため、単体確認スクリプトと同様に待機を継続するよう修正した。

## 変更

- `C:\Users\harut\Connect2USB2CAN\ver9_shell.py`
  - serial取得後に `devices` と `ctx` を解放してから、毎回新しいpipelineを開始する。
  - pipeline開始の失敗時にcandidate参照を解放してから再試行する。
  - 100 msのフレーム待ちタイムアウトを受信停止とみなさず、継続待機する。
- `C:\Users\harut\Connect2USB2CAN\test_ver9_shell.py`
  - contextを解放するまでpipelineが開始できないモック試験を追加。
  - フレーム待ちタイムアウト後も受信ループが停止しない試験を追加。

## 確認結果

- `.venv310\Scripts\python.exe -m unittest test_ver9_shell.py test_ver9_integration.py`: 13件すべてPASS。
- `.venv310\Scripts\python.exe -m py_compile ver9_shell.py ver9_integration.py ver9_d8_sender.py`: PASS。
- CANを開かない`RealT265`単体確認: pipeline起動後にT265 poseを取得してPASS。
- 送信なしの`ver9_integration.py --live-dry`: T265起動を通過。MIT送信なし。全10軸のD4/D7フィードバックが無いため `missing ... motor feedback` で停止し、CSVはヘッダーのみ作成された。

## 次の安全な確認

主電源とCANを通電し、10/10軸の受信・`err=0`を確認した状態で、`--live-dry`を再実行する。これはCAN送信を含まない。完走とCSVデータ行を確認できて初めて、D9のMIT送信再開条件を確認する。

## D9初回MIT実行後の更新

- 初回の `ver9_d8_sender.py --arm ... --duration 2 --vx 0 --vy 0 --wz 0` は、T265起動後に制御ループの `bus.feedback()` まで到達した。
- ID `0x2A`（**LR_HFE、ch=1**。旧左右表は誤り）のフィードバックが0.30秒を超えて古くなり、`RuntimeError: stale feedback 0x2A` で中止した。
- 直後の再実行はUSB2CANのresetでWindowsの「接続されたデバイスが機能していません」エラーになった。受信途絶後に直ちに再実行した影響、またはUSB/CAN経路の一時的な不調が候補であり、原因は未確定。
- 送信器を修正し、初期化失敗・受信途絶のいずれでも零MIT、T265終了、両CAN closeをすべて試みるようにした。例外でも部分CSVを保存する。
- `--vx 0 --vy 0 --wz 0` は方策への速度要求がゼロであり、MIT位置目標をゼロにする意味ではない。全身10軸の再実行には使わない。

次は主電源OFFから再開し、`d9_受信確認_実行シート.md` の `scan 3` だけで、10/10軸、特に0x2Aの新鮮なフィードバックを確認する。MIT送信は行わない。

## D9-0受信確認の更新

- T265を接続した状態では、`d7_origin_console.py` のUSB2CAN resetがWindowsの「接続されたデバイスが機能していません」エラーで失敗した。T265を外すとD9-0の`scan 3`は10/10軸、`err=0`、`age <= 0.3 s`で合格した。現行のT265＋USB2CAN同時USB構成は不合格であり、MIT送信を再試験しない。
- ユーザー確認により、D4/D7の従来の左右ID表は完全に逆と判明した。正しい対応は、ch=0左脚が`1C,11,21,1A,2B`、ch=1右脚が`13,1B,2A,12,22`である。
- `ver9_integration.py` のH順とch振り分け、D9-0実行シート、テスト期待値をこの正しい対応へ修正した。旧記述の`0x2A=LL_HFE/ch0`は誤りで、正しくは`0x2A=LR_HFE/ch1`である。
