# 2026-09-18 デプロイ工程とKt治具の状態

## やったこと
- controller_prep_briefing.mdが実装範囲に反映されているか確認し、pad_probe.pyの実装済み・Jetson未試験・teleop未実装を明記した。
- 学習、入力、実機設定、ver9乾式、段階的な実機試験をつなぐ deployment_roadmap.md を追加した。
- Kt測定の固定治具が現時点で無いというユーザー確認を、実機側の引き継ぎとチェックリストへ反映した。

## 決めたこと・分かったこと
- Ktは重り・アーム・固定治具を製作または確保するまで保留する。脚付き全身を代用した測定はしない。
- 平地デプロイの初回は左スティックの並進だけで進め、坂と安定したその場旋回は後段に分ける。

## 手を動かした場所
- deployment_roadmap.md
- controller_prep_briefing.md
- next_chat_briefing_motor.md
- motor_bench_checklist.md
- README.md

## 積み残し・次にやること
- WRSのデプロイパッケージを検品し、Jetsonでpad_probe.pyの乾式試験を行う。
- パッケージと実機設定がそろってからver9の乾式実装へ進む。
