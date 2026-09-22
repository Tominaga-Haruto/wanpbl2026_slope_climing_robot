# 2026-09-21 D9 T265起動ブロック

## やったこと

- D9の送信なし`--preview`を確認した。10軸ID・AK80/AK10のKp/Kd表示は手順どおりだった。
- 最初のD9実行は`can.exceptions.CanInitializationError: Cannot find device 0. Devices found: 0`で止まった。これはUSB2CANの挿し忘れで、MIT送信・T265開始・CSV作成の前だった。
- USB2CAN接続後のD9実行では、`RealT265.start()`の`candidate.start(config)`が`No device connected`で8回失敗し、`RuntimeError: T265 start failed after 8 attempts: No device connected`となった。CSVは作成されなかった。
- T265単体の`.venv310\\Scripts\\python.exe t265\\t265_check.py --raw`は3回連続で一発起動し、poseを取得できた。
- 送信なしの`ver9_integration.py --live-dry`も実施した。これはT265→両CANの入力を読むだけでCAN送信APIを持たない。ここでも`RealT265.start()`の`candidate.start(config)`が`No device connected`となり、2秒再試行待ち中にCtrl+Cで止めた。

## 決めたこと・分かったこと

- D9は未実施・開始ブロック中。MIT送信ループに一度も到達していない。
- `--duration 2`はT265開始と最初のpose取得の後に数え始める。T265起動中は画面出力もCSV作成も無いため、2秒で終わらない。
- `ver9_d8_sender.py`はCANを先に開き、`ver9_integration.py --live-dry`はT265を先に開始する。両方で同じT265開始失敗なので、CANの起動順・CAN送信は主因ではない。
- USB2CANは2台ではない。**USB2CAN V3.3 1台がch=0とch=1を公開**し、D7ログで左脚5軸／右脚5軸の全10軸を同時受信・原点設定済みである。USB2CANを2台に増やす必要はない。
- 最有力の実装差: 成功する`C:\\Users\\harut\\Connect2USB2CAN\\t265\\t265_check.py`はserial取得後に`del devs, d, ctx`してから新しいpipelineを開始する。失敗する`C:\\Users\\harut\\Connect2USB2CAN\\ver9_shell.py`の`RealT265.start()`は`ctx`と`devices`を保持したまま`candidate.start(config)`を呼ぶ。原因候補であり、未検証。

## 手を動かした場所

- 実行済み（MIT送信なし）:
  - `.venv310\\Scripts\\python.exe ver9_d8_sender.py --preview`
  - `.venv310\\Scripts\\python.exe t265\\t265_check.py --raw`（3回成功）
  - `.venv310\\Scripts\\python.exe ver9_integration.py --live-dry --package C:\\Users\\harut\\wanpbl2026_slope_climing_robot\\H_eff13p5_2999\\H_eff13p5_2999 --duration 2 --csv logs\\d9_live_dry_01.csv --fixed-vx 0 --fixed-vy 0 --fixed-wz 0`（T265開始中にCtrl+C）
- 更新した文書: `README.md`、`project_handbook.md`、`realsense_t265.md`、`deployment_roadmap.md`、`d9_吊り10軸MIT実験手順.md`、`d10_床上_平地デプロイ_実験手順.md`、`d11_jetson_無線操作_平地デプロイ実験手順.md`。

## 積み残し・次にやること

1. **主電源OFFのまま**、`ver9_shell.RealT265.start()`を成功版`t265_check.py`と同じライフサイクル（serial取得後のcontext/device参照解放、pipelineを毎回新規作成）に最小変更する。起動・例外時の後始末も確認する。
2. 変更後、主電源OFFまたはCAN未通電で`ver9_integration.py --live-dry`を実行し、T265起動・CSV・`PASS`まで確認する。この経路はCAN送信しない。
3. 乾式統合が成功して初めて、D9手順の全開始条件を再確認する。吊り支持・電源遮断担当・10/10受信・err=0を満たした場合だけ、`--vx 0 --vy 0 --wz 0 --duration 2`の初回MIT送信を再開する。
4. 修正後も単体だけ成功して統合が失敗するなら、RealSenseのnative pipeline開始を子プロセスで監督する既存`t265_check.py`方式へ統合側を寄せる。推測でUSB2CAN構成を変えない。
