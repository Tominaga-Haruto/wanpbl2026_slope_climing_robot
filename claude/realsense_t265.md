# RealSense T265（実機の姿勢・速度センサ）

> **これは何:** 実機の観測（`base_lin_vel` / `base_ang_vel` / `projected_gravity`）を作るセンサ T265 の現在地と残作業。
> 作成: 2026-09-11 ／ 更新: 2026-09-17 夜（Windows ノートPC で動作・符号と座標系を確定）
> 経緯: `chats/2026-09-17_motor-kd-separation-t265.md`

---

## 1. 現在地

- **IMU/姿勢センサは RealSense T265 で確定。** 観測から base_lin_vel を外した方策（H_nolinvel）は不採用なので、**T265 の速度は必須**（途絶検出と停止も必須）。
- **2026-09-17: ノートPC（Windows）で pose を 200 Hz で取得でき、符号・座標系を確定した。** 何度挿し直しても起動する（ユーザー確認）。
- 機体: シリアル 15322110478、FW 0.2.0.951。

## 2. 環境（ノートPC）

- Python 3.10 を winget で追加（既存は 3.13）。**pyrealsense2 2.53.1 の Windows wheel は cp39 / cp310 まで**（3.11 以上は無い）。
- 仮想環境 `C:\\Users\\harut\\Connect2USB2CAN\\.venv310`: pyrealsense2 **2.53.1.4623**、numpy 2.2.6、onnxruntime 1.23.2、python-can 4.6.1、pyserial、pyusb、gs_usb。
- **librealsense / pyrealsense2 を 2.54 以降に上げない**（v2.54.1 で T265 サポート削除）。`pyrealsense2.__version__` 属性は無い。
- ⚠ 3.10 を入れてから `python` が 3.10 本体を指す → モーターの ver8 は `py -3.13` で起動。

## 3. 確認スクリプト `t265\\t265_check.py`

```
cd C:\\Users\\harut\\Connect2USB2CAN
.venv310\\Scripts\\python t265\\t265_check.py --raw
```
- 表示（既定 10 Hz、`--hz`）: confidence、v_b / w_b / g_b（base 座標）、`--raw` で T265 の生の速度。Ctrl+C で終了、CSV は `t265\\logs\\t265_日付_時刻.csv`（t_host, frame, conf, 観測9個, 生の速度6個, translation）。
- 冒頭の定数: `R_CB`（取り付け向き）、`R_OFFSET`（base 原点 → T265 tracking center、base 座標。ver9ではCAD記録から設定する）、`VEL_IN_WORLD`、`STALE_S` 0.05、`MIN_CONFIDENCE` 2。
- **起動の癖と対策:**
  - 最初はブートローダとして見え、`pipe.start` が \"No device connected\" で数回失敗してから通る → pipeline を毎回作り直し＋serial 指定で最大 8 回再試行（2 秒おき）。
  - **同じ context で `query_devices` し直すと \"Unable to create USB device\" で全滅する**（09-17 に一度この版にして悪化、`.bak_v2`）。
  - 失敗後・抜き差しでネイティブ側がトレースバックなしに落ちることがある → 親プロセス（supervise）が子プロセスを最大 10 回起動し直す。
  - 受信は `wait_for_frames`（`poll_for_frames` ＋ sleep だと Windows で 70 Hz に落ちた）。
- バックアップ: `.bak_ver` `.bak_retry` `.bak_v2` `.bak_v3`。

## 4. 確定した変換（2026-09-17、`t265\\logs\\t265_20260917_213011.csv`）

T265 座標: X 右・Y 上・Z 後ろ。world は起動時の姿勢が原点で Y が重力と逆。Isaac Lab の base: x 前・y 左・z 上。

```
R_wc = quat → 回転行列（T265 本体 → world）
v_c = R_wc^T · velocity,  w_c = R_wc^T · angular_velocity      ← velocity / angular_velocity は world 表現（確定）
R_CB = [[0,-1,0],[0,0,1],[-1,0,0]]   （列 = base の x,y,z を T265 座標で。x_b = −z_t, y_b = −x_t, z_b = +y_t）
w_b = R_CB^T · w_c
v_b = R_CB^T · v_c − w_b × R_OFFSET
g_b = R_CB^T · (R_wc^T · (0,−1,0))
```

| 確認 | 結果 |
|---|---|
| 水平に静止 | g_b = (0.00, 0.00, −1.00) ✓ |
| 前を下げる | w_y ＋・g_b.x が先に ＋ ✓（逆回転で両方 −） |
| 左を下げる | w_x −・g_b.y が先に ＋ ✓（逆回転で w_x ＋・g_b.y −） |
| 上から見て反時計回り | w_z ＋（積算 +570°）✓、逆回転で戻る ✓ |
| 前へ動かす | v_b.x +0.23 → 戻り −0.27、v_b.y ±0.03 ✓ |
| **world 表現の判定** | 開始から yaw +86° 回った状態で前進が v_b.x に出た（本体表現なら v_b.y に漏れる）→ **`VEL_IN_WORLD = True`** |
| 受信 | 200.4 Hz、最大間隔 13 ms、手で振り回して confidence 3 が 81%・2 が 18%・1 が 1% |
| 静止時の偏り | v_b.x 約 −0.03 m/s（方策はバイアス +0.1 に耐性あり） |

- **R_CB はレンズ前向き・水平取り付けの場合。** ロボットへの取り付け向きが違えば差し替える（同じ 5 動作で確認）。
- 20:38 の最初の CSV で静止時 g_b.z ≈ +0.96 だったのは上下逆に置いていた可能性が高い。

## 5. 残作業

T265の実験は完了している。ver9で、CAD記録済みのbase原点→tracking centerの `R_OFFSET` と既存の `R_CB` を使い、`v_b = R_CB^T · v_c − w_b × R_OFFSET` を適用する実装だけが残る。初回デプロイの前提に、再度の5動作、振動・衝撃、confidence・途絶の試験や、それらに応じたソフトウェア停止処理を置かない。停止手段は手元のモーター電源遮断とする。

## 6. 取付け位置のCAD記録（2026-09-20）

- 正面は、waist前面のT265用長方形開口が向く方向とする。T265はレンズをこの正面へ向け、水平に固定する。
- CADの外形基準では、waist下辺→開口下辺は55.000 mm、開口は高さ25.500 mm・幅154.000 mm、waist右辺→開口左辺は189.000 mmである。
- 開口左辺から左右レンズ中心は13.000 / 77.000 mm。公式データシートの左右イメージャ間隔64.00 ± 0.15 mm、およびtracking centerが両イメージャの中点という定義と一致する。したがってtracking centerは開口左辺から45.000 mm、waist右端から234.000 mm、開口上下中央（waist下辺から67.750 mm）に置く。
- T265は開口に対して左・前へ詰め、カメラ面を開口のbase前方向の面に合わせて剛固定済みである。前後位置を含む固定位置はCAD記録を正本とし、ver9がこの記録をbase原点基準の `R_OFFSET` に変換して使う。固定後の実測は不要である。
- 既存の前向き・水平の符号確認CSVは `C:\Users\harut\Connect2USB2CAN\t265\logs\t265_20260917_213011.csv` などにある。`R_CB` はその既定値を使い、5動作は再実施しない。

出典: [librealsense v2.54.1 リリースノート](https://github.com/IntelRealSense/librealsense/releases/tag/v2.54.1) ／ [T265 ドキュメント（v2.53.1）](https://github.com/realsenseai/librealsense/blob/v2.53.1/doc/t265.md)
