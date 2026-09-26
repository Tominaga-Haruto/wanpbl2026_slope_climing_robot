# WRS 実験20: 左右交互の歩き方を教える2本（X20a 詰め込み版・X20b 適度版）

作成 2026-09-27。背景は `../../reports/2026-09-25_学習し直しX18の結果と考察.md`（H はすり足、X18 は立往生、X18h は両足跳び。どの報酬も「左右交互」を教えていなかった）と、引き継ぎ書 `../../handoffs/active/2026-09-27_X20_左右交互の歩行を教える学習_引き継ぎ.md`。
コードの正本は `my_robot_code/stand_env_cfg.py` の末尾「X20」節（下に全文を埋め込んだ）。**下の「CLI に渡すもの」ブロックと、その下の「追記するコード」をまとめて新しい CLI チャットに貼る。** 終わったらこのファイルを `../inactive/` へ移す。

```
# 依頼: 実験20。タスクを4つ追加し、足の高さを測り、スモークして、学習コマンド2本を渡して止まる

## このプロンプトの前提
- このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。
- 長時間の学習をバックグラウンドで回さない。やってよいのは、ファイルの追記、下の S1・S2（各数分）だけ。
  本番の学習はユーザーが別々の PowerShell で前景実行する。
- 既存のクラスの中身は変えない（追記だけ）。追記するファイルは先に .bak_20260927_x20 を取る。
  何も削除しない。pip で何も入れない。git の commit・push はしない。
- 推測で直さない。import が通らない・API 名が違う（例: SceneEntityCfg の preserve_order、current_contact_time、
  compute_first_contact、mdp.is_terminated、episode_length_buf）ときは、Isaac Lab のソースを見て同じ意味の名前に
  直すのはよい。直した箇所は報告に全部書く。意味が変わる修正が要るなら止まって報告。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\（run名）
- 学習・再生は train.py / play.py を直接呼ぶ（_train_foreground.ps1・_play.ps1 は task が rough 固定なので使わない）。
  起動行の形は tools\logs\run_X18h_bold_from_c.txt の先頭と同じ（_preload_h5py_and_run.py 経由、conda activate、
  OMNI_KIT_ACCEPT_EULA、agent.policy.noise_std_type=log）。
- 評価は tools\runs\x18_eval.py（--task 引数あり）。
- stand_env_cfg.py は references\...\config\skyentific_poclegs\ と my_robot_code\ がハードリンク。
  末尾には X18 の StandBold 節（lin_vel_error_l1・double_support_while_moving の関数）まで入っている前提。
  無ければ止まって報告。
- GPU は RTX 3090 Ti が1枚。

## S0 追加
1. stand_env_cfg.py の末尾に、下の「追記するコード」をそのまま追記する。
2. __init__.py に4つ追記（形は StandBold-v0 と同じ、rsl_rl 側も同じ）:
   - "Skyentific-Poclegs-GaitFull-v0" → stand_env_cfg:SkyentificPoclegsGaitFullEnvCfg
   - "Skyentific-Poclegs-GaitFull-Play-v0" → stand_env_cfg:SkyentificPoclegsGaitFullEnvCfg_PLAY
   - "Skyentific-Poclegs-GaitMod-v0" → stand_env_cfg:SkyentificPoclegsGaitModEnvCfg
   - "Skyentific-Poclegs-GaitMod-Play-v0" → stand_env_cfg:SkyentificPoclegsGaitModEnvCfg_PLAY

## S1 足の高さを測る（GaitFull-Play-v0、16 env、行動 0、押しなし）
- リセット直後（最初の 1 step）の ll_ffe・lr_ffe のボディ原点の z（床からの高さ、m）の中央値を FOOT_Z_STAND とし、
  mm で丸めて stand_env_cfg.py の FOOT_Z_STAND = 0.075 を書き換える。値を報告。
- あわせて確認: FEET_ORDERED・FEET_BODIES_ORDERED で解決された body_ids の名前が ["ll_ffe", "lr_ffe"] の順か
  （センサー側とロボット側の両方）。順が違えば止まって報告。
- 同じ 16 env で 1 s（50 step）回し、gait_contact_match・flight_phase・swing_clearance_deficit・
  feet_air_time_single・stand_still_pose が NaN を出さず、値の範囲がおかしくない（contact_match は 0〜1）ことを確かめる。

## S2 スモーク（各 64 env・10 iter、ゼロから）
- TEST_X20a: GaitFull-v0。確かめて表に:
  - **観測の次元が 44**（最後の2つが gait_phase の sin・cos）。
  - 報酬の項目と重み（env.yaml）: track_lin_vel_xy_exp 2.0 / std 0.25、gait_contact 2.0、swing_clearance −20、
    feet_single_air_time 1.0（0.2〜0.4）、stand_still −0.5、no_flight −2.0、lin_vel_error_l1 −1.0、termination −10、
    feet_air_time 0、feet_air_time_biped 0、正則化（flat −0.5、height −2、knee −0.01、torque −1e-5、action_rate −0.01、
    vel −1e-4、acc −2.5e-8）。
  - effort ffe/hfe 13.5・他 53、HAA 制限 −16〜30（実テンソル）、指令 vx −0.2〜0.6・vy ±0.1・wz ±0.3・standing 0.1。
- TEST_X20b: GaitMod-v0。
  - **観測の次元が 42**（H と同じ）。
  - track_lin_vel_xy_exp 2.0 / std 0.35、feet_single_air_time 2.0（0.15〜0.4）、feet_air_time_biped 1.0、
    double_support −1.0（min_time 0.4）、no_flight −1.0、lin_vel_error_l1 −1.0、termination −10、
    feet_air_time 0、standing 0.05、正則化は X20a と同じ。
- どちらもログに新しい報酬の項目が出ること。TEST_ run は消さない。

## 報告（これで止まる）
1. 冒頭3行: S1 の FOOT_Z_STAND と足の順、S2 の合否（観測 44 / 42 を含む）、進めてよいか。
2. S2 の表、直した API 名、変えたファイル。
3. **ユーザーが前景で打つ学習コマンド2本**（別々の PowerShell、train.py を直接、ゼロから、seed 1、
   num_envs 4096、max_iterations 3000、save_interval 100、noise_std_type=log、entropy_coef は H と同じ 0.005、
   --device cuda:0）。run名 X20a_gait_full / X20b_gait_mod。
   先頭に nvidia-smi の1行。「1本目を起動して 1〜2 iter 進んだら nvidia-smi で空きを見て、学習1本分より多ければ
   2本目を起動」と書き添える。実行フォルダ付き・プレースホルダ無し・改行なしの1行版。
4. 再生コマンド2本（GaitFull-Play-v0 / GaitMod-Play-v0、checkpoint 名だけ差し替える形、例 model_500.pt）。
5. 評価コマンド2本（x18_eval.py --task ...-Play-v0、vx 0.3、10 s、例 model_1000.pt、--out の名前も run と checkpoint 入り）。
```

## 追記するコード

```python
# =====================================================================================================
# X20 (2026-09-27): two runs from scratch, both with the upright stand pose of X18 and H's physics.
#   X20a GaitFull : gait clock in the observation (42 -> 44 dims) + left/right contact schedule reward,
#                   swing-foot clearance, no flight phase, single-foot air time, termination penalty.
#   X20b GaitMod  : observation unchanged (42 dims, current transmitter works); StandBold without the
#                   hopping loopholes and with moderate weights.
# Why: H shuffled at 5 Hz, X18 v1..X18c stood still, X18h hopped with both feet. None of the reward sets
# ever asked for alternating feet (claude/reports/2026-09-25_学習し直しX18の結果と考察.md).
# =====================================================================================================
from isaaclab.managers import ObservationTermCfg as ObsTerm  # noqa: E402

GAIT_PERIOD_S = 0.7            # one full left+right cycle
GAIT_STANCE_BAND = 0.1         # |sin| below this: both feet may be down (short double support)
# measured by exp20 step S1: z of the ll_ffe/lr_ffe body origin (ankle axis) when standing at INIT_Z.
FOOT_Z_STAND = 0.075
SWING_CLEARANCE_M = 0.04
FEET_ORDERED = SceneEntityCfg("contact_forces", body_names=["ll_ffe", "lr_ffe"], preserve_order=True)
FEET_BODIES_ORDERED = SceneEntityCfg("robot", body_names=["ll_ffe", "lr_ffe"], preserve_order=True)


def _gait_sin(env, period: float) -> torch.Tensor:
    t = env.episode_length_buf.float() * env.step_dt
    return torch.sin(2.0 * math.pi * t / period)


def _is_moving(env, command_name: str) -> torch.Tensor:
    cmd = env.command_manager.get_command(command_name)
    return (torch.norm(cmd[:, :2], dim=1) > 0.1) | (cmd[:, 2].abs() > 0.1)


def _feet_in_contact(env, sensor_cfg: SceneEntityCfg) -> torch.Tensor:
    cs = env.scene.sensors[sensor_cfg.name]
    return cs.data.current_contact_time[:, sensor_cfg.body_ids] > 0.0  # (N, 2) left, right


def gait_phase_obs(env, period: float) -> torch.Tensor:
    t = env.episode_length_buf.float() * env.step_dt
    ph = 2.0 * math.pi * t / period
    return torch.stack([torch.sin(ph), torch.cos(ph)], dim=1)


def gait_contact_match(env, period: float, command_name: str, sensor_cfg: SceneEntityCfg) -> torch.Tensor:
    """Fraction of feet (0, 0.5, 1) whose contact matches the clock: sin >= -band -> left stance,
    sin <= +band -> right stance. When not moving, both feet down is the target."""
    s = _gait_sin(env, period)
    want = torch.stack([s >= -GAIT_STANCE_BAND, s <= GAIT_STANCE_BAND], dim=1)
    want = torch.where(_is_moving(env, command_name).unsqueeze(1), want, torch.ones_like(want))
    contact = _feet_in_contact(env, sensor_cfg)
    return (contact == want).float().mean(dim=1)


def swing_clearance_deficit(env, period: float, command_name: str, asset_cfg: SceneEntityCfg,
                            target_z: float) -> torch.Tensor:
    """Sum over swing feet of how far [m] the foot is below target_z. Zero when not moving."""
    s = _gait_sin(env, period)
    swing = torch.stack([s < -GAIT_STANCE_BAND, s > GAIT_STANCE_BAND], dim=1).float()
    z = env.scene[asset_cfg.name].data.body_pos_w[:, asset_cfg.body_ids, 2]
    deficit = torch.clamp(target_z - z, min=0.0)
    return (deficit * swing).sum(dim=1) * _is_moving(env, command_name).float()


def flight_phase(env, sensor_cfg: SceneEntityCfg) -> torch.Tensor:
    """1 when both feet are in the air (hopping / running)."""
    return (~_feet_in_contact(env, sensor_cfg).any(dim=1)).float()


def feet_air_time_single(env, command_name: str, sensor_cfg: SceneEntityCfg, threshold_min: float,
                         threshold_max: float) -> torch.Tensor:
    """feet_air_time, but a touchdown only counts while the OTHER foot is on the ground (no hop bonus)."""
    cs = env.scene.sensors[sensor_cfg.name]
    first_contact = cs.compute_first_contact(env.step_dt)[:, sensor_cfg.body_ids].float()
    last_air = cs.data.last_air_time[:, sensor_cfg.body_ids]
    other_down = _feet_in_contact(env, sensor_cfg).flip(dims=[1]).float()
    air = torch.clamp(last_air - threshold_min, max=threshold_max - threshold_min)
    return (air * first_contact * other_down).sum(dim=1) * _is_moving(env, command_name).float()


def stand_still_pose(env, command_name: str, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    """sum |q - q_default| while the command is ~zero."""
    asset = env.scene[asset_cfg.name]
    dev = torch.sum(torch.abs(asset.data.joint_pos - asset.data.default_joint_pos), dim=1)
    return dev * (~_is_moving(env, command_name)).float()


@configclass
class _X20BaseEnvCfg(SkyentificPoclegsStandEnvCfg):
    """Upright pose, calm start, knee/HR limits from X18; H's physics (efforts, HAA to -16)."""

    def __post_init__(self):
        super().__post_init__()
        for name, eff in {"ffe": 13.5, "hfe": 13.5, "kfe": 53.0, "haa": 53.0, "hr": 53.0}.items():
            self.scene.robot.actuators[name].effort_limit = eff
        limits = dict(JOINT_LIMITS_DEG)
        limits[".*_HAA"] = (-16.0, 30.0)
        self.events.set_joint_limits.params["limits_deg"] = limits
        self.commands.base_velocity.ranges.lin_vel_x = (-0.2, 0.6)
        self.commands.base_velocity.ranges.lin_vel_y = (-0.1, 0.1)
        self.commands.base_velocity.ranges.ang_vel_z = (-0.3, 0.3)
        r = self.rewards
        # regularization back to H level (plus light joint vel/acc)
        r.flat_orientation_l2.weight = -0.5
        r.base_height_l2.weight = -2.0
        r.joint_deviation_knee.weight = -0.01
        r.joint_torques_l2.weight = -1.0e-5
        r.action_rate_l2.weight = -0.01
        r.joint_vel_l2.weight = -1.0e-4
        r.joint_acc_l2.weight = -2.5e-8
        # remove the per-foot air-time terms that paid for hopping; replaced below
        r.feet_air_time.weight = 0.0
        r.feet_air_time_biped.weight = 0.0
        r.lin_vel_error_l1 = RewTerm(func=lin_vel_error_l1, weight=-1.0, params={"command_name": "base_velocity"})
        r.no_flight = RewTerm(func=flight_phase, weight=-1.0, params={"sensor_cfg": FEET_ORDERED})
        r.termination = RewTerm(func=mdp.is_terminated, weight=-10.0)


@configclass
class SkyentificPoclegsGaitModEnvCfg(_X20BaseEnvCfg):
    """X20b: moderate. Observation unchanged (42 dims)."""

    def __post_init__(self):
        super().__post_init__()
        self.commands.base_velocity.rel_standing_envs = 0.05
        r = self.rewards
        r.track_lin_vel_xy_exp.weight = 2.0
        r.track_lin_vel_xy_exp.params["std"] = 0.35
        r.feet_single_air_time = RewTerm(
            func=feet_air_time_single, weight=2.0,
            params={"command_name": "base_velocity", "sensor_cfg": FEET_ORDERED,
                    "threshold_min": 0.15, "threshold_max": 0.4},
        )
        r.feet_air_time_biped.weight = 1.0  # single-stance time, 0.2..0.4 s (from X18)
        r.double_support = RewTerm(
            func=double_support_while_moving, weight=-1.0,
            params={"command_name": "base_velocity", "sensor_cfg": FEET_ORDERED, "min_time": 0.4},
        )


@configclass
class SkyentificPoclegsGaitFullEnvCfg(_X20BaseEnvCfg):
    """X20a: everything. Gait clock in the observation (44 dims)."""

    def __post_init__(self):
        super().__post_init__()
        self.commands.base_velocity.rel_standing_envs = 0.1
        self.observations.policy.gait_phase = ObsTerm(func=gait_phase_obs, params={"period": GAIT_PERIOD_S})
        r = self.rewards
        r.track_lin_vel_xy_exp.weight = 2.0
        r.track_lin_vel_xy_exp.params["std"] = 0.25
        r.gait_contact = RewTerm(
            func=gait_contact_match, weight=2.0,
            params={"period": GAIT_PERIOD_S, "command_name": "base_velocity", "sensor_cfg": FEET_ORDERED},
        )
        r.swing_clearance = RewTerm(
            func=swing_clearance_deficit, weight=-20.0,
            params={"period": GAIT_PERIOD_S, "command_name": "base_velocity",
                    "asset_cfg": FEET_BODIES_ORDERED, "target_z": FOOT_Z_STAND + SWING_CLEARANCE_M},
        )
        r.feet_single_air_time = RewTerm(
            func=feet_air_time_single, weight=1.0,
            params={"command_name": "base_velocity", "sensor_cfg": FEET_ORDERED,
                    "threshold_min": 0.2, "threshold_max": 0.4},
        )
        r.stand_still = RewTerm(func=stand_still_pose, weight=-0.5, params={"command_name": "base_velocity"})
        r.no_flight.weight = -2.0


def _play(cfg):
    cfg.scene.num_envs = 50
    cfg.scene.env_spacing = 2.5
    cfg.observations.policy.enable_corruption = False
    cfg.events.base_external_force_torque = None
    cfg.events.push_robot = None


@configclass
class SkyentificPoclegsGaitModEnvCfg_PLAY(SkyentificPoclegsGaitModEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)


@configclass
class SkyentificPoclegsGaitFullEnvCfg_PLAY(SkyentificPoclegsGaitFullEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)
```
