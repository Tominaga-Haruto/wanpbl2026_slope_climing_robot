"""P6-1: foot-sole -30 deg pitch and stance posture (G_real_peak@2999).

1. In the default pose, how many rad must be added to FFE (per side) to zero the sole plane's
   pitch? Is that angle inside the URDF limit?
2. During S3 (cmd=0) t=2-10s and during S1's stance phase (foot contact force > 20% body weight),
   report the sole-plane pitch mean/range and the FFE joint angle mean, to see whether the policy
   flattens the foot by bending the ankle. Sole-plane pitch during locomotion is derived from the
   FFE joint angle via the linear mapping calibrated in step 1 (measuring a full world-frame mesh
   vertex plane fit at every control step of a 10s rollout is prohibitively expensive; the mapping
   itself is empirically measured, not assumed -- see calibration output).
3. With FFE preset to default+correction (from step 1) and action=0 (target = that pose) under
   default gains, does it stand for 2s (32 env, fall rate)? cfg is untouched; only the live
   default_joint_pos data buffer is patched inside this script (same technique already used by
   reset_robot_joints.params["position_range"]=(1.0,1.0) elsewhere in this project).

K1 (2026-09-17, exp07): originally ran Part1/Part2(x2 runs)/Part3 as 4 ManagerBasedRLEnv
create/close cycles inside one process. That reliably hung -- confirmed by
tools/k1_bisect.py stage2 (bare create-close-create-close hangs the same way) while stage6/9/10
(pxr mesh traversal, p6_1's own event-cfg overrides, and its exact default_joint_pos-mutation
calibration loop, each run standalone in ONE env) all completed fine. Split into one env per
process via --part {1,2,3} (Part2 additionally needs --run_name); Part1 writes a small JSON
sidecar (--calib_json) with the FFE calibration that Part2/Part3 read back. Run all three (Part2
twice, once per --run_name) via run_p6_1_all.ps1. See docs/experiments/exp07_*.md.
"""

import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--part", type=str, required=True, choices=["1", "2", "3"])
parser.add_argument("--run_name", type=str, default=None, choices=["G_real_peak", "H_eff13p5"],
                     help="required for --part 2: which of the two comparison runs to measure")
parser.add_argument("--calib_json", type=str,
                     default=r"D:\Tominaga\slope-climbing-robot\tools\logs\P6_1_calib.json",
                     help="Part1 writes FFE calibration here; Part2/Part3 read it back")
parser.add_argument("--load_run", type=str, default="2026-09-16_17-28-46_G_real_peak",
                     help="used by Part1 (calibration env's actuator params) and Part3 (hold-test env)")
parser.add_argument("--checkpoint", type=str, default="model_2999.pt")
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--experiment", type=str, default="skyentific_poclegs_rough")
parser.add_argument("--log_root", type=str, default=r"D:\Tominaga\IsaacLab\logs\rsl_rl")
parser.add_argument("--num_envs_calib", type=int, default=16, help="env count for the item-1 calibration")
parser.add_argument("--num_envs_locomotion", type=int, default=16, help="env count for the item-2 S1/S3 rollout")
parser.add_argument("--num_envs_stance", type=int, default=16, help="env count for the item-3 hold test")
parser.add_argument("--out", type=str, default=r"D:\Tominaga\slope-climbing-robot\tools\logs\P6_1_footpitch.md")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True
sys.argv = [sys.argv[0]]

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
import os  # noqa: E402
import json  # noqa: E402
import importlib.metadata as metadata  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402
import yaml  # noqa: E402
from pxr import Gf, Usd, UsdGeom, UsdPhysics  # noqa: E402
from rsl_rl.runners import OnPolicyRunner  # noqa: E402

import isaaclab.utils.math as math_utils  # noqa: E402
from isaaclab.envs import ManagerBasedRLEnv  # noqa: E402
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg, handle_deprecated_rsl_rl_checkpoint  # noqa: E402

import isaaclab_tasks  # noqa: F401,E402
import skyentific_poclegs  # noqa: F401,E402
from skyentific_poclegs.tasks.locomotion.velocity.config.skyentific_poclegs.agents.rsl_rl_cfg import (  # noqa: E402
    SkyentificPoclegsRoughPPORunnerCfg,
)
from skyentific_poclegs.tasks.locomotion.velocity.config.skyentific_poclegs.rough_env_cfg import (  # noqa: E402
    SkyentificPoclegsRoughEnvCfg,
)

INSTALLED_VERSION = metadata.version("rsl-rl-lib")
STEP_DT = 0.02
FOOT_BODIES = ("ll_ffe", "lr_ffe")
FFE_JOINTS = ("LL_FFE", "LR_FFE")
ROBOT_MASS_KG = 10.106  # from measure_crab.py's own printed "total mass"
GRAVITY = 9.81


def build_env_cfg(num_envs, seed, device):
    cfg = SkyentificPoclegsRoughEnvCfg()
    cfg.scene.num_envs = num_envs
    cfg.seed = seed
    cfg.sim.device = device
    gen = cfg.scene.terrain.terrain_generator
    for name in gen.sub_terrains:
        gen.sub_terrains[name].proportion = 0.0
    gen.sub_terrains["flat"].proportion = 1.0
    gen.num_rows = 2
    gen.num_cols = 2
    gen.curriculum = False
    cfg.scene.terrain.max_init_terrain_level = 0
    cfg.curriculum.terrain_levels = None
    cfg.curriculum.push_force_levels = None
    cfg.curriculum.command_vel = None
    cfg.observations.policy.enable_corruption = False
    cfg.events.push_robot = None
    cfg.events.base_external_force_torque = None
    cfg.events.physics_material.params["static_friction_range"] = (1.0, 1.0)
    cfg.events.physics_material.params["dynamic_friction_range"] = (1.0, 1.0)
    cfg.events.physics_material.params["restitution_range"] = (0.0, 0.0)
    cfg.events.scale_all_link_masses.params["mass_distribution_params"] = (1.0, 1.0)
    cfg.events.add_base_mass.params["mass_distribution_params"] = (0.0, 0.0)
    cfg.events.scale_all_joint_armature.params["armature_distribution_params"] = (1.0, 1.0)
    cfg.events.scale_all_joint_friction_model.params["friction_distribution_params"] = (1.0, 1.0)
    cfg.events.reset_base.params["pose_range"] = {}
    cfg.events.reset_base.params["velocity_range"] = {
        "x": (0.0, 0.0), "y": (0.0, 0.0), "z": (0.0, 0.0),
        "roll": (0.0, 0.0), "pitch": (0.0, 0.0), "yaw": (0.0, 0.0),
    }
    cfg.events.reset_robot_joints.params["position_range"] = (1.0, 1.0)
    cfg.events.reset_robot_joints.params["velocity_range"] = (0.0, 0.0)
    bv = cfg.commands.base_velocity
    bv.heading_command = False
    bv.ranges.heading = None
    bv.rel_heading_envs = 0.0
    bv.rel_standing_envs = 0.0
    bv.resampling_time_range = (1.0e6, 1.0e6)
    cfg.episode_length_s = 60.0
    return cfg


def apply_trained_actuator_params(env_cfg, run_dir):
    env_yaml = os.path.join(run_dir, "params", "env.yaml")
    if not os.path.isfile(env_yaml):
        return
    with open(env_yaml, "r", encoding="utf-8") as f:
        saved = yaml.unsafe_load(f)
    saved_actuators = saved.get("scene", {}).get("robot", {}).get("actuators", {})
    fields = ("effort_limit", "velocity_limit", "stiffness", "damping", "armature", "friction")
    for name, act in env_cfg.scene.robot.actuators.items():
        sa = saved_actuators.get(name)
        if sa is None:
            continue
        for field in fields:
            if field in sa and sa[field] is not None:
                setattr(act, field, sa[field])


def apply_trained_noise_std_type(agent_cfg, run_dir):
    agent_yaml = os.path.join(run_dir, "params", "agent.yaml")
    if not os.path.isfile(agent_yaml):
        return
    with open(agent_yaml, "r", encoding="utf-8") as f:
        saved = yaml.unsafe_load(f)
    std_type = (saved.get("actor") or {}).get("distribution_cfg", {}).get("std_type")
    if std_type is not None:
        agent_cfg.policy.noise_std_type = std_type


def link_mesh_points(stage, prim_path):
    link = stage.GetPrimAtPath(prim_path)
    if not link.IsValid():
        return None
    xf = UsdGeom.XformCache(Usd.TimeCode.Default())

    def has_collision(p):
        q = p
        while q.IsValid() and q.GetPath() != link.GetPath().GetParentPath():
            if q.HasAPI(UsdPhysics.CollisionAPI):
                return True
            q = q.GetParent()
        return False

    for want_collision in (True, False):
        pts = []
        for prim in Usd.PrimRange(link, Usd.TraverseInstanceProxies()):
            if not prim.IsA(UsdGeom.Mesh):
                continue
            if want_collision and not has_collision(prim):
                continue
            mesh = UsdGeom.Mesh(prim)
            raw = mesh.GetPointsAttr().Get()
            if not raw:
                continue
            m = xf.ComputeRelativeTransform(prim, link)[0]
            for p in raw:
                q = m.Transform(Gf.Vec3d(p[0], p[1], p[2]))
                pts.append([q[0], q[1], q[2]])
        if pts:
            return torch.tensor(pts, dtype=torch.float32)
    return None


def fit_plane_pitch(points_xyz):
    pts = points_xyz
    A = np.stack([pts[:, 0], pts[:, 1], np.ones(pts.shape[0])], axis=1)
    b = pts[:, 2]
    coef, *_ = np.linalg.lstsq(A, b, rcond=None)
    a_x, a_y, c0 = coef
    return float(np.degrees(np.arctan(a_x)))


def measure_sole_pitch(env, robot, stage, body_idx, mesh_pts_local, device):
    """World-frame vertex plane fit within 3mm of lowest point, same method as shape_diag_p5_7.py."""
    c = mesh_pts_local.to(device)
    q = robot.data.body_link_quat_w[0, body_idx].unsqueeze(0).expand(c.shape[0], -1)
    p = robot.data.body_link_pos_w[0, body_idx].unsqueeze(0)
    world = (math_utils.quat_apply(q, c) + p).cpu().numpy()
    z_min = world[:, 2].min()
    sole = world[world[:, 2] <= z_min + 0.003]
    return fit_plane_pitch(sole)


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"
    run_dir = os.path.join(args_cli.log_root, args_cli.experiment, args_cli.load_run)

    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    if args_cli.part == "1":
        run_part1(device, run_dir, emit)
    elif args_cli.part == "2":
        if args_cli.run_name is None:
            raise SystemExit("--part 2 requires --run_name {G_real_peak,H_eff13p5}")
        with open(args_cli.calib_json, "r", encoding="utf-8") as f:
            calib = json.load(f)["calib"]
        part2_runs = {
            "G_real_peak": ("2026-09-16_17-28-46_G_real_peak", "model_2999.pt"),
            "H_eff13p5": ("2026-09-17_00-08-51_H_eff13p5", "model_2999.pt"),
        }
        part2_run, part2_ckpt = part2_runs[args_cli.run_name]
        emit(f"# P6-1 Part2: {args_cli.run_name} @ {part2_ckpt}\n")
        run_part2(args_cli.run_name, part2_run, part2_ckpt, device, calib, emit)
    elif args_cli.part == "3":
        with open(args_cli.calib_json, "r", encoding="utf-8") as f:
            correction = json.load(f)["correction"]
        emit(f"# P6-1 Part3: hold-pose test -- {args_cli.load_run} @ {args_cli.checkpoint}\n")
        run_part3(device, run_dir, correction, emit)

    with open(args_cli.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[p6_1_footpitch] wrote {args_cli.out}")


def run_part1(device, run_dir, emit):
    """Part 1: calibrate FFE-angle -> sole-pitch mapping at the default pose. Single env, closed
    before this process exits; writes --calib_json for Part2/Part3 (see K1 note in the module
    docstring -- running Part1/2/3 as 3 envs in one process is what used to hang)."""
    emit(f"# P6-1 Part1: FFE calibration -- {args_cli.load_run} @ {args_cli.checkpoint}\n")

    env_cfg = build_env_cfg(args_cli.num_envs_calib, args_cli.seed, device)
    apply_trained_actuator_params(env_cfg, run_dir)

    env = ManagerBasedRLEnv(cfg=env_cfg)
    robot = env.scene["robot"]
    stage = env.scene.stage
    ffe_ids = [robot.joint_names.index(n) for n in FFE_JOINTS]
    body_ids = {n: robot.body_names.index(n) for n in FOOT_BODIES}
    mesh_pts = {n: link_mesh_points(stage, f"/World/envs/env_0/Robot/{n}") for n in FOOT_BODIES}

    default_ffe = robot.data.default_joint_pos[0, ffe_ids].clone()
    with torch.inference_mode():
        env.reset()
        pitch0 = {n: measure_sole_pitch(env, robot, stage, body_ids[n], mesh_pts[n], device) for n in FOOT_BODIES}

        # perturb FFE by +/-0.2 rad (both sides identically) via the reset default, remeasure
        delta = 0.2
        calib = {}
        for side_i, jn in enumerate(FFE_JOINTS):
            body = FOOT_BODIES[side_i]
            saved = robot.data.default_joint_pos[:, ffe_ids[side_i]].clone()
            robot.data.default_joint_pos[:, ffe_ids[side_i]] = default_ffe[side_i] + delta
            env.reset()
            pitch_plus = measure_sole_pitch(env, robot, stage, body_ids[body], mesh_pts[body], device)
            robot.data.default_joint_pos[:, ffe_ids[side_i]] = default_ffe[side_i] - delta
            env.reset()
            pitch_minus = measure_sole_pitch(env, robot, stage, body_ids[body], mesh_pts[body], device)
            robot.data.default_joint_pos[:, ffe_ids[side_i]] = saved
            slope = (pitch_plus - pitch_minus) / (2 * delta)  # deg per rad
            theta_zero = -pitch0[body] / slope  # rad, relative to default
            calib[body] = {"slope_deg_per_rad": slope, "theta_zero": theta_zero, "pitch0": pitch0[body]}
            emit(f"- {jn}({body}): pitch0={pitch0[body]:+.3f}deg, slope={slope:+.3f}deg/rad "
                 f"(from +/-{delta}rad probe), theta_zero={theta_zero:+.4f}rad")

        # verify: apply theta_zero and remeasure
        emit("\n## 1. FFEにtheta_zeroを加えたときの実測ピッチ(検証)\n")
        emit("| body | 既定FFE[rad] | 補正量[rad] | 補正後FFE[rad] | 検証後pitch[deg] | URDF内か |")
        emit("|---|---|---|---|---|---|")
        URDF_LIMIT = 3.14159 * 0.95
        for side_i, jn in enumerate(FFE_JOINTS):
            body = FOOT_BODIES[side_i]
            theta_zero = calib[body]["theta_zero"]
            corrected = float(default_ffe[side_i]) + theta_zero
            robot.data.default_joint_pos[:, ffe_ids[side_i]] = corrected
            env.reset()
            pitch_check = measure_sole_pitch(env, robot, stage, body_ids[body], mesh_pts[body], device)
            robot.data.default_joint_pos[:, ffe_ids[side_i]] = default_ffe[side_i]
            inside = abs(corrected) <= URDF_LIMIT
            emit(f"| {body} | {float(default_ffe[side_i]):+.4f} | {theta_zero:+.4f} | {corrected:+.4f} | "
                 f"{pitch_check:+.3f} | {'Yes' if inside else 'NO'} |")
        env.reset()

    correction = {FOOT_BODIES[i]: calib[FOOT_BODIES[i]]["theta_zero"] for i in range(2)}
    env.close()

    with open(args_cli.calib_json, "w", encoding="utf-8") as f:
        json.dump({"calib": calib, "correction": correction}, f, indent=2)
    emit(f"\n(calibration written to {args_cli.calib_json} for --part 2/3)")


def run_part3(device, run_dir, correction, emit):
    """Part 3: hold-pose stability test (action=0, corrected FFE default). Single env; reads
    `correction` (theta_zero per foot body) from Part1's --calib_json instead of Part1's own
    default_ffe/env, since a fresh env's default_joint_pos is the same value (set by cfg, not by
    actuator params) -- read back locally below instead of importing it from Part1's process."""
    env_cfg3 = build_env_cfg(args_cli.num_envs_stance, args_cli.seed, device)
    apply_trained_actuator_params(env_cfg3, run_dir)
    env3 = ManagerBasedRLEnv(cfg=env_cfg3)
    robot3 = env3.scene["robot"]
    ffe_ids3 = [robot3.joint_names.index(n) for n in FFE_JOINTS]
    n_joints = robot3.num_joints

    with torch.inference_mode():
        for i, jn in enumerate(FFE_JOINTS):
            base_val = float(robot3.data.default_joint_pos[0, ffe_ids3[i]])
            robot3.data.default_joint_pos[:, ffe_ids3[i]] = base_val + correction[FOOT_BODIES[i]]
        env3.reset()
        zero_action = torch.zeros((args_cli.num_envs_stance, n_joints), device=device)
        ever_done = torch.zeros(args_cli.num_envs_stance, dtype=torch.bool, device=device)
        n_steps = int(round(2.0 / STEP_DT))
        for _ in range(n_steps):
            _, _, dones, _, _ = env3.step(zero_action)
            ever_done |= dones.to(torch.bool)
        fall_rate = float(ever_done.float().mean().item())

    emit("\n## 3. 補正姿勢(action=0固定)での2秒起立テスト\n")
    emit(f"- num_envs={args_cli.num_envs_stance}, FFE default = 既定+補正(Part1のtheta_zero), "
         f"action=0固定(目標角=その姿勢), gainは既定\n")
    emit(f"- 転倒率(2秒以内): {fall_rate:.4f}")
    env3.close()


def run_part2(name, load_run, checkpoint, device, calib, emit):
    run_dir2 = os.path.join(args_cli.log_root, args_cli.experiment, load_run)
    resume_path2 = os.path.join(run_dir2, checkpoint)

    env_cfg2 = build_env_cfg(args_cli.num_envs_locomotion, args_cli.seed, device)
    apply_trained_actuator_params(env_cfg2, run_dir2)
    agent_cfg2 = SkyentificPoclegsRoughPPORunnerCfg()
    agent_cfg2.seed = args_cli.seed
    agent_cfg2.device = device
    apply_trained_noise_std_type(agent_cfg2, run_dir2)
    agent_cfg2 = handle_deprecated_rsl_rl_cfg(agent_cfg2, INSTALLED_VERSION)

    env2 = ManagerBasedRLEnv(cfg=env_cfg2)
    env2w = RslRlVecEnvWrapper(env2, clip_actions=agent_cfg2.clip_actions)
    runner = OnPolicyRunner(env2w, agent_cfg2.to_dict(), log_dir=None, device=agent_cfg2.device)
    runner.load(handle_deprecated_rsl_rl_checkpoint(resume_path2, INSTALLED_VERSION))
    policy = runner.get_inference_policy(device=device)

    robot2 = env2.scene["robot"]
    ffe_ids2 = [robot2.joint_names.index(n) for n in FFE_JOINTS]
    default_ffe2 = robot2.data.default_joint_pos[0, ffe_ids2].clone()
    contact_sensor = env2.scene.sensors["contact_forces"]
    sensor_body_names = list(contact_sensor.body_names)
    sensor_body_ids = [sensor_body_names.index(n) for n in FOOT_BODIES]
    weight_n = ROBOT_MASS_KG * GRAVITY
    threshold_n = 0.2 * weight_n

    cmd_term = env2.unwrapped.command_manager.get_term("base_velocity")

    def run_scenario(vx, vy, wz, n_warm, n_meas):
        res = env2w.reset()
        obs = res[0] if isinstance(res, tuple) else res
        cmd_term.vel_command_b[:, 0] = vx
        cmd_term.vel_command_b[:, 1] = vy
        cmd_term.vel_command_b[:, 2] = wz
        cmd_term.is_standing_env[:] = False
        for _ in range(n_warm):
            obs, _, dones, _ = env2w.step(policy(obs))
            policy.reset(dones)
            cmd_term.vel_command_b[:, 0] = vx
            cmd_term.vel_command_b[:, 1] = vy
            cmd_term.vel_command_b[:, 2] = wz
        ffe_hist = []
        contact_hist = []
        for _ in range(n_meas):
            obs, _, dones, _ = env2w.step(policy(obs))
            policy.reset(dones)
            cmd_term.vel_command_b[:, 0] = vx
            cmd_term.vel_command_b[:, 1] = vy
            cmd_term.vel_command_b[:, 2] = wz
            ffe_hist.append(robot2.data.joint_pos[:, ffe_ids2].clone())
            forces = contact_sensor.data.net_forces_w[:, sensor_body_ids, :].norm(dim=-1)
            contact_hist.append(forces.clone())
        return torch.stack(ffe_hist), torch.stack(contact_hist)  # (T, N, 2)

    with torch.inference_mode():
        # S3: cmd=0, take t=2-10s of the standard 2s warmup + 10s measurement (i.e. all of the
        # measurement window, which already starts at t=2s per the fixed protocol)
        ffe_s3, _ = run_scenario(0.0, 0.0, 0.0, int(round(2.0 / STEP_DT)), int(round(8.0 / STEP_DT)))
        # S1: cmd=(0.5,0,0)
        ffe_s1, contact_s1 = run_scenario(0.5, 0.0, 0.0, int(round(2.0 / STEP_DT)), int(round(10.0 / STEP_DT)))

    emit(f"\n## 2. S3(2-10s)とS1立脚中のFFE角/推定ソールピッチ -- {name}\n")
    emit("推定ソールピッチ = pitch0 + slope*(FFE角 - 既定FFE角)  (Part1で校正した線形写像を使用。"
         "10s分の毎ステップでworld頂点フィットを行うのは非常に重く、Part1で実測した写像を適用する簡略化)\n")
    emit("| body | 区間 | FFE角 平均[rad] | 推定pitch 平均[deg] | 推定pitch 範囲[deg] |")
    emit("|---|---|---|---|---|")
    for i, body in enumerate(FOOT_BODIES):
        slope = calib[body]["slope_deg_per_rad"]
        p0 = calib[body]["pitch0"]
        d0 = float(default_ffe2[i])

        def to_pitch(ffe_t):
            return p0 + slope * (ffe_t - d0)

        # S3
        ffe_s3_i = ffe_s3[:, :, i]
        pitch_s3_i = to_pitch(ffe_s3_i)
        emit(f"| {body} | S3(2-10s) | {ffe_s3_i.mean().item():+.4f} | {pitch_s3_i.mean().item():+.3f} | "
             f"[{pitch_s3_i.min().item():+.3f},{pitch_s3_i.max().item():+.3f}] |")

        # S1 stance (contact > 20% weight)
        stance_mask = contact_s1[:, :, i] > threshold_n
        ffe_s1_i = ffe_s1[:, :, i]
        if stance_mask.any():
            ffe_stance = ffe_s1_i[stance_mask]
            pitch_stance = to_pitch(ffe_stance)
            emit(f"| {body} | S1立脚中 | {ffe_stance.mean().item():+.4f} | {pitch_stance.mean().item():+.3f} | "
                 f"[{pitch_stance.min().item():+.3f},{pitch_stance.max().item():+.3f}] |"
                 f" (stance frac={stance_mask.float().mean().item():.3f})")
        else:
            emit(f"| {body} | S1立脚中 | (no stance samples above threshold) | - | - |")

    env2.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
