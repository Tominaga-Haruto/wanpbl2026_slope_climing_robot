# X18 (2026-09-25): "stand-start" retrain config.
# New task only. Subclasses SkyentificPoclegsRoughEnvCfg and overrides in __post_init__,
# so the existing rough task (and every past run) is unchanged.
#
# What changes vs H_eff13p5 (reasons: claude/reports/2026-09-25_*):
#   1. default pose = physically near-straight leg (knee 8 deg), with the CAD zero-pose asymmetry
#      (URDF FK: LL HFE +2.9 / KFE -12.3 / FFE +9.4, LR -0.9 / -7.2 / +8.1 deg = physically straight)
#   2. joint limits (URDF has +-180 deg everywhere): knee cannot hyperextend, HAA cannot close the feet
#   3. start on a flat plane, feet on the floor, zero initial velocity, joints +-3 deg
#   4. rewards against the 5 Hz shuffle gait: single-stance time, joint vel/acc/torque, knee pose,
#      base height, orientation
#   5. effort limits near the real transmitter's abort currents, friction / gain DR
import copy
import math

import torch

from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils import configclass

import isaaclab_tasks.manager_based.locomotion.velocity.mdp as mdp

# CLI: fix this import to the real module path if needed (same package as rough_env_cfg.py).
from .rough_env_cfg import SkyentificPoclegsRoughEnvCfg

D = math.radians

# physical pose: knee bent 8 deg, HFE -4, FFE -4 (thigh and shank symmetric -> torso upright, foot flat).
# sim angle = physical angle from straight + CAD offset. HFE+KFE+FFE = 0 on both legs (foot parallel to torso).
# exp18 S1: zero action never stands (ankle PD 2x10 N*m/rad < m*g*h ~30 N*m/rad); the fall direction flips
# between delta=+1 and +2 (FFE +delta, HFE -delta), so delta=+1.5 is applied here as the balance point.
STAND_JOINT_POS = {
    "LL_HR": 0.0, "LR_HR": 0.0,
    "LL_HAA": 0.0, "LR_HAA": 0.0,
    "LL_HFE": D(-2.6), "LR_HFE": D(-6.4),
    "LL_KFE": D(-4.3), "LR_KFE": D(0.8),
    "LL_FFE": D(6.9), "LR_FFE": D(5.6),
}

# exp18 S1: from 0.38 the base sinks 4-5 mm before touching -> start ~1 mm above contact.
INIT_Z = 0.377
# standing height ~0.376 minus ~4 mm for walking knee bend.
BASE_HEIGHT_TARGET = 0.372

# sim joint limits [deg]. KFE lower = physically straight - 2 deg. HAA lower -6 (real feet touch at -8.5..-11).
JOINT_LIMITS_DEG = {
    ".*_HR": (-25.0, 25.0),
    ".*_HAA": (-6.0, 30.0),
    ".*_HFE": (-60.0, 60.0),
    "LL_KFE": (-14.3, 100.0),
    "LR_KFE": (-9.2, 100.0),
    ".*_FFE": (-45.0, 45.0),
}

# N*m. current = torque / c_p (AK80-9 0.523, AK10-9 1.258): FFE 19 A, HFE 15 A, KFE 16 A, HAA 9.5 A, HR 4.8 A
EFFORT_LIMITS = {"ffe": 10.0, "hfe": 8.0, "kfe": 20.0, "haa": 12.0, "hr": 6.0}


def set_joint_limits_deg(env, env_ids, asset_cfg: SceneEntityCfg, limits_deg: dict):
    """Startup event: overwrite joint position limits (and hence soft limits) for the given joints."""
    asset = env.scene[asset_cfg.name]
    limits = asset.data.joint_pos_limits.clone()
    for expr, (lo, hi) in limits_deg.items():
        ids, _ = asset.find_joints(expr)
        limits[:, ids, 0] = math.radians(lo)
        limits[:, ids, 1] = math.radians(hi)
    asset.write_joint_position_limit_to_sim(limits, warn_limit_violation=False)


@configclass
class SkyentificPoclegsStandEnvCfg(SkyentificPoclegsRoughEnvCfg):
    def __post_init__(self):
        super().__post_init__()

        # ---- robot: default pose, spawn height, effort limits
        robot = copy.deepcopy(self.scene.robot)
        robot.init_state.pos = (0.0, 0.0, INIT_Z)
        robot.init_state.joint_pos = dict(STAND_JOINT_POS)
        for name, eff in EFFORT_LIMITS.items():
            robot.actuators[name].effort_limit = eff
        self.scene.robot = robot

        # ---- flat plane only
        self.scene.terrain.terrain_type = "plane"
        self.scene.terrain.terrain_generator = None
        self.curriculum.terrain_levels = None
        self.curriculum.push_force_levels = None  # keep pushes at +-0.5 m/s

        # ---- commands (deployment range) + standing envs
        self.commands.base_velocity.ranges.lin_vel_x = (-0.3, 0.6)
        self.commands.base_velocity.ranges.lin_vel_y = (-0.2, 0.2)
        self.commands.base_velocity.ranges.ang_vel_z = (-0.6, 0.6)
        self.commands.base_velocity.rel_standing_envs = 0.15

        # ---- events: calm start, joint limits, DR
        self.events.reset_base.params["velocity_range"] = {
            "x": (0.0, 0.0), "y": (0.0, 0.0), "z": (0.0, 0.0),
            "roll": (0.0, 0.0), "pitch": (0.0, 0.0), "yaw": (0.0, 0.0),
        }
        self.events.reset_robot_joints = EventTerm(
            func=mdp.reset_joints_by_offset,
            mode="reset",
            params={"position_range": (-0.05, 0.05), "velocity_range": (0.0, 0.0)},
        )
        self.events.set_joint_limits = EventTerm(
            func=set_joint_limits_deg,
            mode="startup",
            params={"asset_cfg": SceneEntityCfg("robot"), "limits_deg": JOINT_LIMITS_DEG},
        )
        # CoM of the torso: real CoM is uncertain (thought to be a little forward of the body centre)
        self.events.randomize_base_com = EventTerm(
            func=mdp.randomize_rigid_body_com,
            mode="startup",
            params={
                "asset_cfg": SceneEntityCfg("robot", body_names="base"),
                "com_range": {"x": (-0.02, 0.03), "y": (-0.01, 0.01), "z": (-0.01, 0.01)},
            },
        )
        self.events.scale_all_joint_friction_model.params["friction_distribution_params"] = (1.0, 3.0)
        self.events.randomize_actuator_gains.params["stiffness_distribution_params"] = (0.8, 1.2)
        self.events.randomize_actuator_gains.params["damping_distribution_params"] = (0.8, 1.2)

        # ---- rewards
        r = self.rewards
        r.flat_orientation_l2.weight = -2.0
        r.joint_torques_l2.weight = -1.0e-4
        r.action_rate_l2.weight = -0.02
        r.feet_air_time.params["threshold_min"] = 0.25  # swings shorter than 0.25 s are penalized
        r.feet_air_time.params["threshold_max"] = 0.5
        r.feet_air_time_biped.weight = 0.5
        r.feet_air_time_biped.params["threshold_min"] = 0.2
        r.feet_air_time_biped.params["threshold_max"] = 0.4
        r.joint_deviation_knee.weight = -0.1
        r.undesired_contacts.params["sensor_cfg"] = SceneEntityCfg(
            "contact_forces", body_names=[".*hfe", ".*haa", ".*kfe"]
        )
        r.joint_vel_l2 = RewTerm(func=mdp.joint_vel_l2, weight=-1.0e-3)
        r.joint_acc_l2 = RewTerm(func=mdp.joint_acc_l2, weight=-2.5e-7)
        r.base_height_l2 = RewTerm(
            func=mdp.base_height_l2, weight=-30.0, params={"target_height": BASE_HEIGHT_TARGET}
        )

        # ---- terminations
        self.terminations.bad_orientation.params["limit_angle"] = 0.8


@configclass
class SkyentificPoclegsStandEnvCfg_PLAY(SkyentificPoclegsStandEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
        self.events.base_external_force_torque = None
        self.events.push_robot = None


# X18c (2026-09-25 07:30): v1@1500 and v2_soft@1300 both stood still ("立往生").
# Likely reasons (not verified): (1) track_lin_vel std 0.5 pays ~70% of the tracking reward for standing
# still at vx 0.3; (2) HAA >= -6 deg keeps the feet ~25 cm apart, so shifting the weight onto one foot is
# hard; (3) short steps are penalized before long ones can be found; (4) knee/height penalties punish
# the knee bend a swing needs. Registered as a separate task; the classes above are unchanged.
@configclass
class SkyentificPoclegsStandWalkEnvCfg(SkyentificPoclegsStandEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        r = self.rewards
        r.track_lin_vel_xy_exp.weight = 2.0
        r.track_lin_vel_xy_exp.params["std"] = 0.25
        r.feet_air_time.params["threshold_min"] = 0.15
        r.feet_air_time_biped.weight = 1.0
        r.joint_deviation_knee.weight = -0.02
        r.base_height_l2.weight = -10.0
        r.flat_orientation_l2.weight = -1.0
        r.joint_vel_l2.weight = -5.0e-4
        r.joint_acc_l2.weight = -1.25e-7
        r.joint_torques_l2.weight = -5.0e-5
        limits = dict(JOINT_LIMITS_DEG)
        limits[".*_HAA"] = (-10.0, 30.0)
        self.events.set_joint_limits.params["limits_deg"] = limits


@configclass
class SkyentificPoclegsStandWalkEnvCfg_PLAY(SkyentificPoclegsStandWalkEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
        self.events.base_external_force_torque = None
        self.events.push_robot = None


# X18e / X18f (2026-09-25 08:50): X18c (resume, 2000 it) and X18d (scratch, 400 it) still stood still,
# leaning toward the command. Suspected: the calm start removed every reason to step (H learned its
# stepping from being dropped with random velocities), and the HAA/effort limits may make a step hard.

# X18e: StandWalk from scratch, with the H-era physics back (HAA -15, H efforts) and a disturbed start.
@configclass
class SkyentificPoclegsStandWalkV2EnvCfg(SkyentificPoclegsStandWalkEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        for name, eff in {"ffe": 13.5, "hfe": 13.5, "kfe": 53.0, "haa": 53.0, "hr": 53.0}.items():
            self.scene.robot.actuators[name].effort_limit = eff
        limits = dict(JOINT_LIMITS_DEG)
        limits[".*_HAA"] = (-16.0, 30.0)
        self.events.set_joint_limits.params["limits_deg"] = limits
        self.events.reset_base.params["velocity_range"] = {
            "x": (-0.3, 0.3), "y": (-0.3, 0.3), "z": (0.0, 0.0),
            "roll": (-0.3, 0.3), "pitch": (-0.3, 0.3), "yaw": (-0.3, 0.3),
        }
        self.events.reset_robot_joints.params["position_range"] = (-0.1, 0.1)
        self.events.push_robot.interval_range_s = (5.0, 8.0)
        r = self.rewards
        r.feet_air_time.params["threshold_min"] = 0.1
        r.feet_air_time_biped.params["threshold_min"] = 0.0


@configclass
class SkyentificPoclegsStandWalkV2EnvCfg_PLAY(SkyentificPoclegsStandWalkV2EnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
        self.events.base_external_force_torque = None
        self.events.push_robot = None


# X18f: keep H_eff13p5's pose/start (it already walks) and resume it from model_2999.pt, adding only
# the anti-shuffle rewards and the knee/HAA/HR limits. Default pose and observations are H's, so the
# checkpoint loads as is.
H_JOINT_LIMITS_DEG = {
    ".*_HR": (-25.0, 25.0),
    ".*_HAA": (-10.0, 30.0),
    ".*_HFE": (-60.0, 60.0),
    "LL_KFE": (-14.3, 100.0),
    "LR_KFE": (-9.2, 100.0),
    ".*_FFE": (-45.0, 45.0),
}


@configclass
class SkyentificPoclegsHShapeEnvCfg(SkyentificPoclegsRoughEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        robot = copy.deepcopy(self.scene.robot)
        for name in ("ffe", "hfe"):
            robot.actuators[name].effort_limit = 13.5  # same as H_eff13p5
        self.scene.robot = robot
        self.scene.terrain.terrain_type = "plane"
        self.scene.terrain.terrain_generator = None
        self.curriculum.terrain_levels = None
        self.curriculum.push_force_levels = None
        self.commands.base_velocity.ranges.lin_vel_x = (-0.3, 0.6)
        self.commands.base_velocity.ranges.lin_vel_y = (-0.2, 0.2)
        self.commands.base_velocity.ranges.ang_vel_z = (-0.6, 0.6)
        self.events.reset_base.params["velocity_range"] = {
            "x": (-0.2, 0.2), "y": (-0.2, 0.2), "z": (0.0, 0.0),
            "roll": (-0.2, 0.2), "pitch": (-0.2, 0.2), "yaw": (-0.2, 0.2),
        }
        self.events.reset_robot_joints.params["position_range"] = (0.8, 1.2)
        self.events.set_joint_limits = EventTerm(
            func=set_joint_limits_deg,
            mode="startup",
            params={"asset_cfg": SceneEntityCfg("robot"), "limits_deg": H_JOINT_LIMITS_DEG},
        )
        self.events.scale_all_joint_friction_model.params["friction_distribution_params"] = (1.0, 3.0)
        r = self.rewards
        r.action_rate_l2.weight = -0.02
        r.flat_orientation_l2.weight = -1.0
        r.joint_torques_l2.weight = -5.0e-5
        r.feet_air_time.params["threshold_min"] = 0.25
        r.feet_air_time_biped.weight = 1.0
        r.feet_air_time_biped.params["threshold_min"] = 0.2
        r.feet_air_time_biped.params["threshold_max"] = 0.4
        r.joint_deviation_knee.weight = -0.05
        r.joint_vel_l2 = RewTerm(func=mdp.joint_vel_l2, weight=-5.0e-4)
        r.joint_acc_l2 = RewTerm(func=mdp.joint_acc_l2, weight=-1.25e-7)


@configclass
class SkyentificPoclegsHShapeEnvCfg_PLAY(SkyentificPoclegsHShapeEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
        self.events.base_external_force_torque = None
        self.events.push_robot = None


# X18g / X18h (2026-09-25 09:00): bold reward change instead of disturbed starts (X18e/X18f withdrawn).
# Standing must stop paying: big tracking weight, a linear velocity-error penalty that has a gradient
# even far from the command, a penalty for keeping both feet down while a velocity is commanded, big
# stepping rewards, no zero commands, H-level regularization only, H efforts and HAA -16.
def lin_vel_error_l1(env, command_name: str, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    asset = env.scene[asset_cfg.name]
    cmd = env.command_manager.get_command(command_name)
    return torch.sum(torch.abs(cmd[:, :2] - asset.data.root_lin_vel_b[:, :2]), dim=1)


def double_support_while_moving(env, command_name: str, sensor_cfg: SceneEntityCfg, min_time: float) -> torch.Tensor:
    contact_sensor = env.scene.sensors[sensor_cfg.name]
    contact_time = contact_sensor.data.current_contact_time[:, sensor_cfg.body_ids]
    both_down_long = torch.all(contact_time > min_time, dim=1)
    moving = torch.norm(env.command_manager.get_command(command_name)[:, :2], dim=1) > 0.1
    return (both_down_long & moving).float()


@configclass
class SkyentificPoclegsStandBoldEnvCfg(SkyentificPoclegsStandWalkEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        # physics that allowed H to walk
        for name, eff in {"ffe": 13.5, "hfe": 13.5, "kfe": 53.0, "haa": 53.0, "hr": 53.0}.items():
            self.scene.robot.actuators[name].effort_limit = eff
        limits = dict(JOINT_LIMITS_DEG)
        limits[".*_HAA"] = (-16.0, 30.0)
        self.events.set_joint_limits.params["limits_deg"] = limits
        # always a forward command, never "stand"
        self.commands.base_velocity.ranges.lin_vel_x = (0.15, 0.6)
        self.commands.base_velocity.ranges.lin_vel_y = (-0.1, 0.1)
        self.commands.base_velocity.ranges.ang_vel_z = (-0.3, 0.3)
        self.commands.base_velocity.rel_standing_envs = 0.0
        r = self.rewards
        # drive
        r.track_lin_vel_xy_exp.weight = 5.0
        r.track_lin_vel_xy_exp.params["std"] = 0.25
        r.lin_vel_error_l1 = RewTerm(func=lin_vel_error_l1, weight=-3.0, params={"command_name": "base_velocity"})
        r.double_support = RewTerm(
            func=double_support_while_moving, weight=-2.0,
            params={"command_name": "base_velocity",
                    "sensor_cfg": SceneEntityCfg("contact_forces", body_names=".*ffe"), "min_time": 0.3},
        )
        r.feet_air_time.weight = 5.0
        r.feet_air_time.params["threshold_min"] = 0.05
        r.feet_air_time.params["threshold_max"] = 0.4
        r.feet_air_time_biped.weight = 3.0
        r.feet_air_time_biped.params["threshold_min"] = 0.1
        r.feet_air_time_biped.params["threshold_max"] = 0.4
        # regularization back to H level (shape the gait later, after it walks)
        r.flat_orientation_l2.weight = -0.5
        r.base_height_l2.weight = -2.0
        r.joint_deviation_knee.weight = -0.01
        r.joint_torques_l2.weight = -1.0e-5
        r.action_rate_l2.weight = -0.01
        r.joint_vel_l2.weight = -1.0e-4
        r.joint_acc_l2.weight = -2.5e-8


@configclass
class SkyentificPoclegsStandBoldEnvCfg_PLAY(SkyentificPoclegsStandBoldEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
        self.events.base_external_force_torque = None
        self.events.push_robot = None


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
import isaaclab.sim as sim_utils  # noqa: E402
import isaaclab.terrains as terrain_gen  # noqa: E402
from isaaclab.terrains.terrain_generator_cfg import TerrainGeneratorCfg  # noqa: E402

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
        # 2026-09-27: terrain_type="plane" loads Grid/default_environment.usd from the Nucleus S3 URL,
        # which stopped opening on the WRS machine. Build the same flat floor locally instead:
        # a generator with one flat mesh sub-terrain, no Nucleus visual material, no sky texture.
        self.scene.terrain.terrain_type = "generator"
        self.scene.terrain.terrain_generator = TerrainGeneratorCfg(
            size=(8.0, 8.0), border_width=20.0, num_rows=10, num_cols=20,
            horizontal_scale=0.1, vertical_scale=0.005, slope_threshold=0.75, use_cache=False,
            curriculum=False,
            sub_terrains={"flat": terrain_gen.MeshPlaneTerrainCfg(proportion=1.0)},
        )
        self.scene.terrain.max_init_terrain_level = None
        self.scene.terrain.visual_material = sim_utils.PreviewSurfaceCfg(diffuse_color=(0.55, 0.55, 0.55))
        if getattr(self.scene, "sky_light", None) is not None:
            self.scene.sky_light.spawn.texture_file = None
        # the velocity-command arrows load Props/UIElements/arrow_x.usd from Nucleus as well
        self.commands.base_velocity.debug_vis = False
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
