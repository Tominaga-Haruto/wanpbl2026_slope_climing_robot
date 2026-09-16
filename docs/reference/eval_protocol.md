# 固定の評価プロトコル（measure_crab.py）

実装: `tools/measure_crab.py`。ラッパー: `tools/runs/_eval.ps1`。
**全ランで同じ条件**にしてあるので、学習時の地形・報酬が違っても横に並べて比較できる。

```powershell
D:\Tominaga\slope-climbing-robot\tools\runs\_eval.ps1 -Run <run フォルダ名> -Ckpt model_XXXX.pt -NumEnvs 64
```

出力: `tools/logs/eval_<run>_<iter>.md` と `.csv`。

## 評価環境

| 項目 | 設定 |
|---|---|
| 地形 | 全面平地（`sub_terrains` の flat を proportion 1.0、他 0.0）。※ `terrain_type="plane"` は使えない（後述） |
| 観測ノイズ | OFF（`enable_corruption = False`） |
| 外乱 | `push_robot` と `base_external_force_torque` を None |
| ドメインランダム化 | 全部中立値に固定（摩擦 1.0、質量スケール 1.0、base 質量加算 0、armature 1.0、関節摩擦 1.0） |
| リセット時の初速 | 全成分 0（姿勢の yaw ランダムと関節スケール 0.5〜1.5 は残す＝env ごとの多様性のため） |
| 指令 | 再サンプルなし（`resampling_time_range = (1e6, 1e6)`）、`heading_command=False`、`rel_standing_envs=0`、`rel_heading_envs=0`。さらに `_resample_command` を差し替えて固定値を強制 |
| エピソード長 | 60 s（12 s の計測窓でタイムアウトしないように） |
| seed | 1234 固定 |
| env 数 | 既定 64 |

## シナリオ（毎回リセット、最初の 2 s を捨てて 10 s 計測）

| | 指令 (vx, vy, wz) |
|---|---|
| S1 | (0.5, 0, 0) |
| S2 | (1.0, 0, 0) |
| S3 | (0, 0, 0) |
| S4 | (-0.3, 0, 0) |
| S5 | (0, 0.3, 0) |
| S6 | (0, 0, 0.5) |

実際に env に届いた指令はスクリプトが毎回出力する（`command actually seen` の行）。

## 指標

速度は **base の COM 速度を base の yaw だけで回した水平速度**（roll/pitch の揺れを混ぜない）。
`root_com_lin_vel_w` を `yaw_quat(root_link_quat_w)` で逆回転して求めている。

| 指標 | 定義 |
|---|---|
| v_x / v_y 平均 | 上記の水平速度の時間平均（符号付き） |
| \|v_y − cmd_y\| 平均 | 毎ステップの絶対誤差の時間平均 |
| yaw rate 平均 | `root_ang_vel_w[:, 2]` の時間平均（符号付き） |
| heading ずれ [deg] | 計測 10 s の `heading_w` の差を ±π に丸めたもの |
| 進行方向角 [deg] | `atan2(Δy, Δx) − yaw(計測開始時)`。S1・S2 のみ |
| 静止率 | 「10 s 平均の速度ベクトル」の大きさ < 0.1 m/s の env の割合。S1・S2・S4・S5 のみ |
| 転倒率 | 計測中に終了した env の割合（time_out ではなく `terminated`） |
| LR_HR / LL_HR 平均角 | 該当関節角の時間平均（符号付き） |
| 左右の足の平均滞空時間 | 接地イベント時の `last_air_time` の平均 |
| \|qd\| p95 | 全関節・全ステップ・生存 env の関節速度絶対値の 95 パーセンタイル |
| トルク ≥95% 上限 | `applied_torque` が actuator の `effort_limit` の 95% 以上になった割合 |
| **遊脚の最大高さ [cm]**（参考） | 空中にいる間の足リンク原点の高さ（接地面基準）の走行最大値を、接地の瞬間に 1 回ぶんとして計上した平均 |
| **着地回数 [回/s]**（参考） | 計測中の接地イベント総数（左右合計）÷ 生存時間 |

参考指標 2 つは **判定には使わない**。2026-09-16 に追加したので、それ以前に取った
eval ファイル（A/B/C の 1000・1600・2400）には列が無い。

### 転倒した env の扱い

終了した env は `step()` の中で自動リセットされるので、その後のデータは混ぜない。
`alive` マスクで累積を止め、平均は生存していた時間で割る。
heading ずれ・進行方向角・静止率は 10 s 生き残った env のみで計算する。

## 判定基準（実験01 で事前に決めた暫定値。変えないこと）

- **カニ歩き無し**: S1 と S2 の両方で `|v_y 平均| ≤ 0.05`、`|v_y − cmd_y| 平均 ≤ 0.10`、
  `|yaw rate 平均| ≤ 0.10`、進行方向角が ±10° 以内。**かつ** S5 で `v_y 平均 ≥ +0.15`
- **立ち往生無し**: S1 で静止率 ≤ 5% かつ `v_x 平均 ≥ 0.35`、S2 で静止率 ≤ 5%
- **転倒合格**: S1 の転倒率 ≤ 5%
- 参考: 学習ログの正規化 error_vel_xy ≤ 0.3

### 読むときの注意

立ち往生している方策は 10 s の正味変位がほぼ 0 になるので、**進行方向角という量自体が意味を持たない**
（A や C_noflat が −63°、+84° などの値を出すのはこれ）。カニ歩き判定が「有」になっても、
静止率が 100 % なら実態は立ち往生のほう。

## 関連する環境の落とし穴

- `terrain_type="plane"` は使えない。`TerrainImporter.import_ground_plane` が
  `GroundPlaneCfg` のデフォルト usd_path（S3 の `Isaac/.../Grid/default_environment.usd`）を
  必ず引きに行き `FileNotFoundError` で落ちる。URL 自体は HTTP 200 で届くので Omniverse 側の
  resolver の問題。このパスは importer 内にハードコードされていて cfg から差し替えられない。
  → 全面 flat の generator で代用している。物理的には平面と同じ。
- トルク飽和率は `robot.data.joint_effort_limits`（sim 側、1e9）ではなく
  `robot.actuators[*].effort_limit` から計算している。DelayedPDActuator は explicit actuator なので
  クリップは actuator 内で行われる。実値は HR 24 / HAA 30 / HFE,KFE 30 / FFE 20 N·m。
