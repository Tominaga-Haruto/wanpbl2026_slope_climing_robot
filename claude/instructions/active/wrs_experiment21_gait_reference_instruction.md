# WRS 実験21: 参照の振り足を足した2本（X21a 立ち姿勢そのまま・X21b H の姿勢）

作成 2026-09-30 11:30。X20a_gait_full・X20b_gait_mod は各 500 iter で両方とも立往生（本人の再生・目視）。
コードの正本は `my_robot_code/stand_env_cfg.py` の末尾「X21」節（下に全文）。**下の「CLI に渡すもの」を、その下の「追記するコード」と一緒に新しい CLI チャットに貼る。** 終わったらこのファイルを `../inactive/` へ移す。

## なぜ立往生したか（見立て。X20 の TB の数字は S0 で CLI が出す）

1. **X20a の時計は「接地が合っているか」の 0/1 でしか報酬にならない。** 両足を着けて立っていても gait_contact の約 55% がもらえ、足をどう上げればよいかの手がかり（勾配）が無い。X20b は時計すら無い。
2. **振り足 4 cm は届きにくい。** URDF の順運動学で、足首の点を 4 cm 上げるには股 25°・膝 50°程度が要る。届くまで罰（−20×不足）が立っているときと大差ない。
3. **足の間隔が広い。** 4番目 0°で足首の間隔は約 33 cm（URDF）。片足立ちには体を大きく横へ寄せる必要があり、4番目を閉じる動きは `joint_deviation_hip`（4番目・5番目のずれの罰）が止める向きに働く。

## 直すこと（X21a・X21b 共通）

- **参照の振り足**（humanoid-gym 方式）: 同じ 0.7 s の時計で、振り足の 3番目・2番目・1番目の目標を「股 −A、膝 +2A、足首 −A」（A = 0.35 rad → 股 20°・膝 40°、足首の点が約 25 mm 上がる、足裏は平行のまま）。報酬 exp(−2·誤差) − 0.2·誤差、重み 2.0。止まれの指令では既定姿勢が目標。符号は `robot_sim.urdf` の順運動学で確認した（+3番目 = 股を後ろへ、+2番目 = 膝を曲げる、3つとも +10°で足裏が +10°）。
- 振り足の高さの目標を 4 cm → 2.5 cm（参照と揃える）。
- `joint_deviation_hip` を 5番目だけに（4番目は自由に閉じてよい。可動域は X20 と同じ −16°まで。実機の −8°は当たりが出てからの追加学習で）。

| | X21a（`GaitRef-v0`） | X21b（`GaitRefH-v0`） |
|---|---|---|
| 既定姿勢 | X18/X20 のまっすぐ寄り | H（3番目 −10・2番目 +20・1番目 −10） |
| 開始 | 床の高さ 0.377・速度 0 | 床の高さ 0.367（FK から、S1 で確認）・速度 0 |
| 胴の高さの目標 | 0.372 | 0.362 |
| 観測 | 44 次元（時計つき） | 44 次元 |
| わかること | 報酬の直しで立ち姿勢のまま歩けるか | X21a がだめで X21b が歩けば、まっすぐ寄りの姿勢そのものが壁 |

判定: 300 iter と 500 iter で再生（vx 0.3 固定）。左右交互に足を上げて前へ進めば当たり。足踏みだけで前へ進まない・参照だけ真似て転ぶ・立往生、のどれかなら名前で記録。

## CLI に渡すもの

```
# 依頼: 実験21。X20 の数字を読み、タスクを4つ追加し、スモークして、学習・再生・動画のコマンドを渡して止まる

## このプロンプトの前提
- このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。
- 長時間の学習をバックグラウンドで回さない。やってよいのは下の S0〜S3（各数分）だけ。本番の学習・再生・動画は
  ユーザーが別々の PowerShell で前景実行する。
- 既存のクラス・関数の中身は変えない（末尾への追記だけ）。何も削除しない。pip しない。git の commit・push をしない。
  Nucleus・Kit の設定を触らない。
- stand_env_cfg.py は references\...\config\skyentific_poclegs\ と my_robot_code\ のハードリンク。**Edit ツールを使わない**。
  先に stand_env_cfg.py.bak_20260930_x21 と __init__.py.bak_20260930_x21 を取り、python で open(path, "r+") で読み、
  seek(0)・write・truncate で同じファイルを書き換える。書いたあと両パスの inode（os.stat().st_ino）が同じか確かめる。
- 推測で直さない。API 名が違う（例: SceneEntityCfg の preserve_order、joint_ids）ときは Isaac Lab のソースを見て
  同じ意味の名前に直すのはよい。直した箇所は全部報告。意味が変わる修正が要るなら止まって報告。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\（run名）
- 学習・再生は train.py / play.py を直接呼ぶ（_train_foreground.ps1・_play.ps1 は task が rough 固定なので使わない）。
  起動行の形は tools\logs\run_X18h_bold_from_c.txt の先頭と同じ（_preload_h5py_and_run.py 経由、conda activate、
  OMNI_KIT_ACCEPT_EULA、agent.policy.noise_std_type=log）。
- stand_env_cfg.py の末尾には X20 節（GaitFull / GaitMod、_gait_sin・_is_moving・_play、FOOT_Z_STAND = 0.079、
  地面のローカル生成、debug_vis = False）まで入っている前提。無ければ止まって報告。
- GPU は RTX 3090 Ti が1枚。

## S0 X20 の数字を読む（学習は回さない）
run X20a_gait_full と X20b_gait_mod の TensorBoard のイベントファイルを python（tensorboard の EventAccumulator）で読み、
iter 0・100・250・500 と最後の iter の値を表にする:
Train/mean_reward、Train/mean_episode_length、Episode_Termination/*、Policy/mean_noise_std、Episode_Reward/* の全項目
（特に track_lin_vel_xy_exp、gait_contact、swing_clearance、no_flight、feet_single_air_time、double_support、termination）。
どこまで iter が進んでいるかと、保存された model_*.pt の最大番号も書く。tensorboard が import できなければ飛ばして報告。

## S1 追加
1. stand_env_cfg.py の末尾に、下の「追記するコード」をそのまま追記する（上の書き方で）。
2. __init__.py に4つ追記（形は GaitFull-v0 と同じ、rsl_rl の entry point も GaitFull と同じ）:
   - "Skyentific-Poclegs-GaitRef-v0"       → stand_env_cfg:SkyentificPoclegsGaitRefEnvCfg
   - "Skyentific-Poclegs-GaitRef-Play-v0"  → stand_env_cfg:SkyentificPoclegsGaitRefEnvCfg_PLAY
   - "Skyentific-Poclegs-GaitRefH-v0"      → stand_env_cfg:SkyentificPoclegsGaitRefHEnvCfg
   - "Skyentific-Poclegs-GaitRefH-Play-v0" → stand_env_cfg:SkyentificPoclegsGaitRefHEnvCfg_PLAY

## S2 確かめる（Play の env、16 env、行動 0、押しなし、各 1 s）
- X21_SAGITTAL_JOINTS が解決した関節名の順が
  ["LL_HFE","LL_KFE","LL_FFE","LR_HFE","LR_KFE","LR_FFE"] か。違えば止まって報告。
- GaitRefH-Play-v0: 最初の 1 step の ll_ffe・lr_ffe のボディ原点の z の中央値が FOOT_Z_STAND（0.079）± 0.003 m か。
  外れたら INIT_Z_H を「0.367 −（実測 − 0.079）」に mm で丸めて書き換え、もう一度確かめる。値を報告。
- 両タスクで ref_joint_pos が NaN を出さず、−0.1〜1.0 の範囲か。ついでに、指令 vx 0.3 固定で、関節を
  q_ref（既定姿勢＋振り足の目標）に書き込んだ状態の振り足の足首の z が、立ったときより 15〜35 mm 高いか
  （順運動学の予想は約 25 mm）。外れたら値を報告（止まらなくてよい）。

## S3 スモーク（各 64 env・20 iter、ゼロから）
- TEST_X21a: GaitRef-v0、TEST_X21b: GaitRefH-v0。表にする:
  - 観測の次元が両方 44（最後の2つが gait_phase の sin・cos）。
  - env.yaml の報酬の重み: ref_joint_pos 2.0（amp 0.35）、swing_clearance −20（target_z 0.104）、
    joint_deviation_hip の関節が HR だけ、gait_contact 2.0、track_lin_vel_xy_exp 2.0 / std 0.25、no_flight −2.0、
    feet_single_air_time 1.0、stand_still −0.5、lin_vel_error_l1 −1.0、termination −10。
  - GaitRefH だけ: init_state の関節（HFE −0.1745・KFE 0.3491・FFE −0.1745）、init の z、base_height_l2 の target 0.362。
  - effort ffe/hfe 13.5・他 53、HAA 制限 −16〜30（実テンソル）。
- **再生と動画の起動行もここで試す**: TEST_X21a の最後の checkpoint で、下の報告 4・5 の形のコマンドを
  短く（動画は --video_length 100）実際に1回ずつ走らせ、Hydra の上書き（指令を vx 0.3 固定）が効くか・mp4 がどこに
  できるかを確かめる。上書きが play.py で効かないなら、効く書き方（play.py の引数か、Play クラスへの追記）を報告して、
  追記が要るなら止まる。
- TEST_ run は消さない。

## 報告（これで止まる。短く）
1. 冒頭3行: S0 の要点（X20a/X20b の episode 長・gait_contact など、立往生が数字でどう見えるか）、S2・S3 の合否、進めてよいか。
2. S0 の表、S3 の表、直した API 名、変えたファイル。
3. **ユーザーが前景で打つ学習コマンド2本**（別々の PowerShell、train.py を直接、ゼロから、seed 1、num_envs 4096、
   max_iterations 3000、save_interval 100、noise_std_type=log、entropy_coef 0.005、--device cuda:0）。
   run名 X21a_ref_upright（GaitRef-v0）/ X21b_ref_hpose（GaitRefH-v0）。先頭に nvidia-smi の1行。
   「1本目を起動して 1〜2 iter 進んだら nvidia-smi で空きを見て、学習1本分より多ければ2本目を起動」と書き添える。
   実行フォルダ付き・プレースホルダ無し・改行なしの1行版。
4. **再生コマンド2本**（GaitRef-Play-v0 / GaitRefH-Play-v0、checkpoint のファイル名だけ差し替えればよい形、例 model_300.pt、
   指令を vx 0.3・vy 0・wz 0 固定、止まれの指令 0: env.commands.base_velocity.ranges.lin_vel_x=[0.3,0.3]、
   lin_vel_y=[0.0,0.0]、ang_vel_z=[0.0,0.0]、heading_command=false、rel_standing_envs=0.0）。
5. **動画コマンド2本**（4 と同じ指令、--video --video_length 500 --headless、--num_envs 4、例 model_500.pt）と、
   mp4 ができるフォルダの絶対パス。
6. 見る値: ターミナルの Episode_Reward/ref_joint_pos（増える）、gait_contact（1 に近づく）、track_lin_vel_xy_exp（増える）、
   Train/mean_episode_length（下がりっぱなしなら転んでいる）。300 iter と 500 iter で再生して判定する、と書き添える。
```

## 追記するコード

```python

# =====================================================================================================
# X21 (2026-09-30): X20a_gait_full and X20b_gait_mod both stood still at 500 iter (user's replay).
# X20a paid for the clock only through binary foot contact: standing with both feet down still earns
# ~55% of gait_contact, and nothing tells the policy HOW to lift a foot. X21 adds a dense reference swing
# (humanoid-gym style) driven by the same clock, a clearance target the leg can reach, and drops HAA from
# the hip-deviation penalty so the feet may come closer (feet are ~33 cm apart at HAA 0 by URDF FK).
#   X21a GaitRef   : X20a (upright X18 pose, 44 dims) + the above.
#   X21b GaitRefH  : same rewards, H's crouched default pose (HFE -10 / KFE +20 / FFE -10), calm start.
#                    Tells whether the upright pose itself blocks stepping.
# Signs (robot_sim.urdf FK, 2026-09-30): +HFE moves the ankle back (hip extension), +KFE bends the knee,
# +10 deg on any of HFE/KFE/FFE pitches the sole +10 deg (foot parallel while HFE+KFE+FFE is constant).
# Swing shape HFE -A, KFE +2A, FFE -A: A = 0.35 rad -> hip flexion 20, knee 40 deg, ankle lift ~25 mm.
# =====================================================================================================
X21_SAGITTAL_JOINTS = SceneEntityCfg(
    "robot", joint_names=["LL_HFE", "LL_KFE", "LL_FFE", "LR_HFE", "LR_KFE", "LR_FFE"], preserve_order=True
)
REF_SWING_AMP_RAD = 0.35
REF_SWING_SHAPE = (-1.0, 2.0, -1.0)  # HFE, KFE, FFE per unit swing activation
X21_SWING_CLEARANCE_M = 0.025

# H's default pose (skyentific_poclegs.py) and its floor height: by URDF FK the ankle is ~9.8 mm closer
# to the base than in the upright pose, so INIT_Z 0.377 -> 0.367 (checked in exp21 S1).
H_STAND_JOINT_POS = {
    "LL_HR": 0.0, "LR_HR": 0.0,
    "LL_HAA": 0.0, "LR_HAA": 0.0,
    "LL_HFE": -0.1745, "LR_HFE": -0.1745,
    "LL_KFE": 0.3491, "LR_KFE": 0.3491,
    "LL_FFE": -0.1745, "LR_FFE": -0.1745,
}
INIT_Z_H = 0.367
BASE_HEIGHT_TARGET_H = 0.362


def _swing_activation(env, period: float, command_name: str) -> torch.Tensor:
    """(N, 2) in [0, 1]: left swings while sin < -band, right while sin > +band (same clock as X20a)."""
    s = _gait_sin(env, period)
    left = torch.clamp(-s - GAIT_STANCE_BAND, min=0.0) / (1.0 - GAIT_STANCE_BAND)
    right = torch.clamp(s - GAIT_STANCE_BAND, min=0.0) / (1.0 - GAIT_STANCE_BAND)
    act = torch.stack([left, right], dim=1)
    return act * _is_moving(env, command_name).float().unsqueeze(1)


def ref_joint_pos_tracking(env, period: float, command_name: str, asset_cfg: SceneEntityCfg,
                           amp: float) -> torch.Tensor:
    """exp(-2|q - q_ref|) - 0.2 clamp(|q - q_ref|, 0, 0.5) over HFE/KFE/FFE of both legs.
    q_ref = default pose + swing offset from the clock; default pose when the command is ~zero."""
    asset = env.scene[asset_cfg.name]
    ids = asset_cfg.joint_ids
    q = asset.data.joint_pos[:, ids]
    q0 = asset.data.default_joint_pos[:, ids]
    act = _swing_activation(env, period, command_name)
    shape = torch.tensor(REF_SWING_SHAPE, device=q.device, dtype=q.dtype)
    offset = torch.cat([act[:, 0:1] * shape, act[:, 1:2] * shape], dim=1) * amp
    err = torch.norm(q - (q0 + offset), dim=1)
    return torch.exp(-2.0 * err) - 0.2 * torch.clamp(err, 0.0, 0.5)


@configclass
class SkyentificPoclegsGaitRefEnvCfg(SkyentificPoclegsGaitFullEnvCfg):
    """X21a: X20a + reference swing + reachable clearance + HAA free of the hip-deviation penalty."""

    def __post_init__(self):
        super().__post_init__()
        r = self.rewards
        r.ref_joint_pos = RewTerm(
            func=ref_joint_pos_tracking, weight=2.0,
            params={"period": GAIT_PERIOD_S, "command_name": "base_velocity",
                    "asset_cfg": X21_SAGITTAL_JOINTS, "amp": REF_SWING_AMP_RAD},
        )
        r.swing_clearance.params["target_z"] = FOOT_Z_STAND + X21_SWING_CLEARANCE_M
        r.joint_deviation_hip.params["asset_cfg"] = SceneEntityCfg("robot", joint_names=[".*HR"])


@configclass
class SkyentificPoclegsGaitRefHEnvCfg(SkyentificPoclegsGaitRefEnvCfg):
    """X21b: X21a with H's crouched default pose (calm start kept)."""

    def __post_init__(self):
        super().__post_init__()
        robot = copy.deepcopy(self.scene.robot)
        robot.init_state.pos = (0.0, 0.0, INIT_Z_H)
        robot.init_state.joint_pos = dict(H_STAND_JOINT_POS)
        self.scene.robot = robot
        self.rewards.base_height_l2.params["target_height"] = BASE_HEIGHT_TARGET_H


@configclass
class SkyentificPoclegsGaitRefEnvCfg_PLAY(SkyentificPoclegsGaitRefEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)


@configclass
class SkyentificPoclegsGaitRefHEnvCfg_PLAY(SkyentificPoclegsGaitRefHEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)
```
