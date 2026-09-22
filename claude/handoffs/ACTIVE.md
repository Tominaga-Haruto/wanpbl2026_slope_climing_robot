# Active handoff — D9 0x1C 1軸追従停止の修正

更新日: 2026-09-22

## Claude Codeへの最初の依頼

「D9の0x1C追従停止を、追加の実機送信なしで診断・修正してください。CSVと実装を根拠に、ソフトウェアの不具合があるかを確認し、無ければ機構負荷と個体特性を切り分ける次の安全な1軸診断案を作ってください。Kp/Kd、目標角、トルクを根拠なく増やさず、片脚・全身MITへ進まないでください。」

## 目的と完了条件

0x1C（LL_HR、AK10-9）が位置追従しない原因を、通信／実装と機構・個体負荷に分ける。完了は、根拠付きの修正または次の1軸診断案、更新済み手順、報告書、対象限定commit/pushである。実機送信はユーザーが明示して安全条件を確認した場合だけである。

## 確認済みの事実

- 最新CSV: `C:\Users\harut\Connect2USB2CAN\logs\d9_one_axis_0x1c.csv`。2026-09-22 18:41:33、402行（ramp 301 / policy 101）、全行`sent_motor_id=0x1C`、wire target最小−5.128°、位置−0.6°・速度0のまま、最大|電流|0.66 A。
- 方策ランプ4回と、方策/T265を除いた相対−2.5°static probeで追従0°が再現した。CSV更新、ID→ch経路確定、MIT量子化、電流受信は成立している。
- 現行送信器は`C:\Users\harut\Connect2USB2CAN\ver9_d8_sender.py`、build `D9_RAMP_20260922_1745`。1軸以外へMITを送らず、停止時は零MIT cleanupを行う。
- 「現行実効PDトルクが吊り姿勢の負荷を越えない」と整合するが、CSVだけでは静止摩擦、干渉、支持具、ケーブル、重力モーメント、個体特性の内訳は決められない。

## 最初に読むもの

1. `../CONTEXT.md`
2. `../reports/2026-09-22_d9-0x1c-stall-analysis.md`
3. `../motor_can_findings.md`
4. `../reports/2026-09-20_d4-m5-joint-map-and-origin-procedure.md`
5. 必要な範囲だけ`C:\Users\harut\Connect2USB2CAN\ver9_d8_sender.py`と最新CSV

## 安全境界と記録

- 同じ方策ランプ／static probeの反復、Kp/Kd・目標角・トルク前置の増加、片脚／全身MITは行わない。
- 追加の実機送信は行わない。無通電の目視・手回し確認を提案する場合も、主電源OFF・吊り支持維持を明記する。
- CSV、生ログ、モデル、鍵はGitに入れない。実測の要約と絶対パスを`../reports/`へ記録する。
- 作業後は`ACTIVE.md`と`../CONTEXT.md`を更新し、自分が触ったファイルだけをcommit/pushする。
