# 2026-09-20 D7 両CANチャネル原点設定の引き継ぎ

## やったこと

- D7の実施前に、棒にまたがらせた機体を機械的に支持した状態で、全10軸の定期フィードバックを確認した。
- 既存の `motor_console_ver8.py` は `CHANNEL = 1` の単一チャネル実装だったため、ch=1で右脚5軸しか見えないことを確認した。
- 受信専用の `listen.py`（ch=0）で残り5軸が見えることを確認した。送信・原点設定・位置指令・方策送信は実施していない。
- ch=0/ch=1を同時に受信し、原点設定だけを行うD7専用 `C:\Users\harut\Connect2USB2CAN\d7_origin_console.py` を追加した。ID入力・表示は16進数へ統一し、`o 0x..` の後に対象と同じ `YES 0x..` を要求する。
- D7手順書を両チャネル・16進数版に更新した。

## 決めたこと・分かったこと

### CANの確定対応

| ch | H関節 | ID | 機種 |
|---:|---|---|---|
| 0 | LL_HR | `0x13` | AK10-9 |
| 0 | LL_HAA | `0x1B` | AK10-9 |
| 0 | LL_HFE | `0x2A` | AK80-9 |
| 0 | LL_KFE | `0x12` | AK10-9 |
| 0 | LL_FFE | `0x22` | AK80-9 |
| 1 | LR_HR | `0x1C` | AK10-9 |
| 1 | LR_HAA | `0x11` | AK10-9 |
| 1 | LR_HFE | `0x21` | AK80-9 |
| 1 | LR_KFE | `0x1A` | AK10-9 |
| 1 | LR_FFE | `0x2B` | AK80-9 |

- ch=1では `0x11, 0x1A, 0x1C, 0x21, 0x2B` を50 Hz・`err=0`で確認済み。
- ch=0では `0x1B, 0x22, 0x2A, 0x12, 0x13` の定期フィードバックを受信済み。D7専用コンソールの`scan 3`で、10軸すべてについて`err=0`と新鮮なフィードバックを改めて確認してから原点設定に進む。
- D7専用コンソールは、原点設定時だけサーボモード5の一時原点設定（`kind=0`）を1フレーム送る。位置・速度・トルク・MIT指令を送らず、`q`／例外終了時も送信しない。非常停止は主電源OFF。
- D7で使うID表記は16進数に統一した。実機→Hの符号は全軸`+1`。

## 手を動かした場所

- `C:\Users\harut\Connect2USB2CAN\d7_origin_console.py`
  - `py -3.13 -m py_compile d7_origin_console.py`、ID解析とch対応の静的検証がPASS。
  - Connect2USB2CANの`feat/mit-mode`へcommit/push済み: `582cb67 Add dual-channel D7 origin console`。
- `claude/d7_棒支持_全関節原点設定_実験手順.md`
  - 両チャネルの対応表、16進数の操作列、記録表、ログ保存先を追記。
  - 親リポジトリ`main`へcommit/push済み: `49adc66 docs: use dual-channel D7 origin console`。
- 既存の未整理変更（README、H成果物、他の未追跡ファイル）は変更していない。

## 積み残し・次にやること

1. ユーザーがD6の開始判定（最終構成固定、棒支持、主電源遮断位置、再現用の写真・寸法）を満たすことを確認する。
2. 旧 `motor_console_ver8.py` が開いていれば終了してから、ノートPCのPowerShellで次を実行する。

   ```powershell
   cd C:\Users\harut\Connect2USB2CAN
   py -3.13 d7_origin_console.py
   ```

3. `scan 3` で10軸が見え、`err=0`かつ`age<=0.3s`であることを確認する。1台でも不足・異常なら主電源OFFで終了し、`o`は送らない。
4. [D7手順書](../d7_棒支持_全関節原点設定_実験手順.md)の順に、各軸で `s 0x..` → `o 0x..` → `YES 0x..` → `s 0x..` を実施する。設定前後角度、`err`、写真・支持点・寸法、`logs\d7_origin\session_*.txt`を残す。
5. 次のチャットでは、上記ログの内容、10軸の設定前後角度、写真・寸法、途中中止の有無を提示する。D7が完了ならD4の原点変換表へ転記し、次はD8のPC上統合へ進む。方策送信や全身動作には進まない。
