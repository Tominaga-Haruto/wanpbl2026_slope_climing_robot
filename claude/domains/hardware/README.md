# ハードウェア・CAN

実機ID、関節対応、MITゲイン、原点、T265、電源の根拠を扱う。数値・配線・符号を使う前に以下を読む。

- CAN、MIT、原点: `../../motor_can_findings.md`
- 関節ID・符号: `../../reports/2026-09-20_d4-m5-joint-map-and-origin-procedure.md`
- アクチュエータ諸元: `../../actuator_params.md`
- T265: `../../realsense_t265.md`
- D9停止の最新根拠: `../../reports/2026-09-22_d9-0x1c-current-vs-error.md`（MITの Kp 欄は「1 radあたりの電流」。不感帯 = 動き出し電流 ÷ 指令Kp）

現行の実機作業の禁止事項・次の一手は、`../../CONTEXT.md`が名指しする引き継ぎ書が優先する。
