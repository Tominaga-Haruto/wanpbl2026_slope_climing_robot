# 2026-09-17 夜 実機: Kd 分離（AK80-9 / AK10-9）と T265 の立ち上げ

## やったこと
- `next_chat_briefing_motor.md` から再開。ユーザーの今日のゴール:「残りはデプロイだけ」の状態まで（明日も作業可）。残りのモーターの配線は 09-18。ONNX 等は ver9 に着手するときでよい（ユーザー確認）。
- 脚を外した ID34（AK80-9）と ID18（AK10-9）で ver8 の `vscale` → `morg` → `overify` → `kpscale`（M2/M3）。
  - 最初 `sniff 3` で 0 フレーム（`logs\\v7_20260917\\session_195044.txt`）→ ユーザー側で復旧。本番は `session_195414.txt`（ID34）、`session_201212.txt`（ID18）。
- `jit 5`（ID34・ID18）: `session_213720.txt`。AK10-9 の電源入れ直し 3 回（動かさず、大元の電源を確かに切った＝ユーザー確認）: `session_213427.txt`。
- 最後の実験: ID18 で `jog 30`×3（+90°）→ 電源入れ直し → `jog -30`×3 → 電源入れ直し。**ログは `session_214916.txt`（ユーザーは `213720` と伝えたが時刻からこちら）。ユーザーの意向で読まずに次チャットへ。**
- T265: ノートPC に Python 3.13 しか無く、pyrealsense2 2.53.1 の Windows wheel は cp39/cp310 まで → `winget` で 3.10、`.venv310` に pyrealsense2 2.53.1.4623 / numpy / onnxruntime 1.23.2 / python-can ほか。
  - **副作用: `python` が 3.10 本体を指し、ver8 が `No module named 'can'` → 以後 `py -3.13 motor_console_ver8.py`。**
- `t265\\t265_check.py` を新設（pose → base 座標の base_lin_vel / base_ang_vel / projected_gravity を表示・CSV、途絶検出）。版の変遷:
  - `.bak_ver`: `rs.__version__` が無い → getattr。
  - `.bak_retry`: `pipe.start` が \"No device connected\" → serial 指定＋pipeline 作り直しで再試行 → 5 回目で成功。初回失敗後にトレースバックなしで落ちることがあった。
  - `.bak_v2` → **失敗版（Cowork が推測で変更）**: 同じ context で query_devices し直す → \"Unable to create USB device\" で 10 回全滅。
  - `.bak_v3` → **現行**: 開始は `.bak_retry` の方式に戻し、子プロセス＋自動再起動（supervise）、受信を `wait_for_frames`（70 Hz → 200 Hz）。**何回挿し直しても起動する（ユーザー確認）。**
- ユーザーの「引き継ぐ」で、引き継ぎ書と正本を更新。

## 決めたこと・分かったこと

### モーター
| | ID34 AK80-9 | ID18 AK10-9 |
|---|---|---|
| 関節（ユーザー申告） | **LR_FFE（右足首、上位機 22番）** | **LR_KFE（右膝、上位機 12番）** |
| r_v（速度レンジ） | 1.003 → **±65** | 0.996 → **±28（V3.0.0）** |
| ERPM換算/位置差分 | 0.999 | 1.000 |
| c_d | **0.523** | **1.216** |
| c_p | **0.523**（0.521〜0.529） | **1.258**（1.229〜1.262） |
| \\|I\\|/トルク指令 | 1.79 A/(N·m) | 0.77 A/(N·m) |
| \\|I\\|/(指令Kp·rad) | 0.94 | 0.97 |
| 摩擦/c_d | 0.30 | 0.36 |
| 原点 | offset −0.0017 rad、残差 +0.28° | offset −0.0053 rad、残差 −0.10° |
| jit 5 | 平均 20.00・σ0.78・p99 21.7・最大 23.2 ms | 平均 20.01・σ0.82・p99 21.9・最大 22.0 ms |

- **Kd の分離は決着: c_p ≈ c_d → 機種別に割れば stiffness:damping 比が保たれ、実効 damping ×1.0。**
- **ゲインは機種によらず電流で出ていて、トルク指令の目盛りが機種で 2.3 倍違う → 「指令トルク単位 = 物理 N·m」かは機種ごとに違いうる。Kt（F5b）の優先度が上がった。** 重り＋棒で持ち上がり/下がり始めの平均から当てる案を提示（道具の有無は未回答）。
- jit は目安 25 ms 以内で合格（D1）。
- AK10-9 を動かさずに電源入れ直し 3 回: 177.4° のまま（AK80-9 の「動かさなければ同じ」と同じ）。

### T265（`t265\\logs\\t265_20260917_213011.csv`、59 s、200.4 Hz、最大間隔 13 ms）
- 水平静止 g_b = (0, 0, −1)、前を下げる w_y ＋・g_b.x ＋、左を下げる w_x −・g_b.y ＋、反時計回り w_z ＋、前へ v_b.x ＋。
- **yaw +86° の状態で前進が v_b.x に出た → velocity / angular_velocity は world 表現（VEL_IN_WORLD = True）。R_CB（レンズ前向き・水平）の符号は正しい。**
- 静止時 v_b.x に約 −0.03 m/s の偏り。

### 運用
- **ユーザー指示: 「引き継ぐ」と言ったら、新しい解析を始めずに引き継ぎ書ともろもろの更新をやる**（今回、渡されたログを読む前に先に作業を進めかけてトークンを無駄にしたと指摘）→ README の絶対ルール2 に追加。

## 手を動かした場所
- ノートPC `C:\\Users\\harut\\Connect2USB2CAN`: `t265\\t265_check.py`（新規、`.bak_ver` `.bak_retry` `.bak_v2` `.bak_v3`）、`t265\\logs\\*.csv`、`.venv310\\`（新規）、`mit_calib.json`（ver8 が自動保存、ID34 更新・ID18 追加）。ver8 は無変更。
- プロジェクト文書: `next_chat_briefing_motor.md`（夜版に書き直し: 状況の整理・コマンド解説・やり残し）、`motor_can_findings.md`、`motor_bench_checklist.md`、`realsense_t265.md`、`README.md`（絶対ルール2・現在の状況・資料表・索引）。

## 積み残し・次にやること
- **次チャットの最初: `logs\\v7_20260917\\session_214916.txt` を読み、AK10-9 の電源再投入の窓を判定**（`next_chat_briefing_motor.md` §0）。
- 配線（09-18）→ M1 の表（符号の列込み）→ M5 原点姿勢。
- Kt（M3b）、上位機の設定読み（B10）。
- T265: 取り付け向き・位置、載せての振動。
- ver9（WRS から ONNX・golden npz・obs_contract・アクチュエータ設定）。
- `actuator_params.md` §0c、`project_handbook.md` A7、`mit_implementation_briefing.md` の書き換え。git コミット（`.venv310` は除外）。
