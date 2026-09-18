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
- 冒頭の定数: `R_CB`（取り付け向き）、`R_OFFSET`（base 原点 → T265、base 座標、今は 0）、`VEL_IN_WORLD`、`STALE_S` 0.05、`MIN_CONFIDENCE` 2。
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

1. **ロボットへの取り付け向きを決めて R_CB を確定**（同じ 5 動作）。
2. **取り付け位置の補正 `R_OFFSET`**（CAD から。base 原点は脚より約 9 cm 前・左右中心から約 2 cm ずれ、`robot_model_conventions.md` §1）。
3. **振動・衝撃**: ロボットに載せて揺らし・吊り下ろしで confidence と途絶を見る。
4. **制御ループ（ver9）: T265 は別プロセス**で読み、最新値＋時刻を共有。途絶（`STALE_S`）・confidence 低下で方策を止める。学習側の許容: 0 埋めは 0.2 s、直前値保持は 0.5 s まで転倒 0%（実験04 P6-2）。
5. （小）CAD / URDF に T265 を載せる（約 55 g）。

出典: [librealsense v2.54.1 リリースノート](https://github.com/IntelRealSense/librealsense/releases/tag/v2.54.1) ／ [T265 ドキュメント（v2.53.1）](https://github.com/realsenseai/librealsense/blob/v2.53.1/doc/t265.md)
