"""K1: bisect what makes t0_3_s6_diag.py / p6_1_footpitch.py hang, starting from
p6_2_basevel_dropout.py's always-succeeding skeleton and adding one piece of their behavior at a
time, selected by --stage. Every step prints a timestamped [k1_bisect] line so a hang's last
completed step is visible in the redirected stdout log even if the process never exits.

stage 1: create env (t0_3/p6_1-style build_env_cfg, flat terrain), close it. Baseline lifecycle.
stage 2: like 1, but create+close TWO envs in the same process (t0_3 does this across 2 runs,
         p6_1 across 4 parts).
stage 3: stage1 + construct OnPolicyRunner, runner.load(checkpoint), get_inference_policy. No
         env.reset()/step.
stage 4: stage3 + envw.reset() + 5 policy steps (no extra per-step data pulls).
stage 5: stage4 + the extra per-step data t0_3 pulls: robot.data.computed_torque, contact_sensor
         (net_forces_w / compute_first_contact / last_air_time), reward_manager._step_reward.
stage 6: p6_1-specific -- create env, then immediately do the pxr/UsdGeom stage traversal
         (link_mesh_points) that p6_1's Part 1 does before its first env.reset().
stage 8: replicate t0_3_s6_diag.py's real run_one() loop verbatim (single env, single run:
         H_eff13p5@2999, 3 scenarios S1/S3/S6, 100 warmup + 500 measurement steps each, same
         per-step data pulls as stage5) with progress logged every 100 steps, to see whether the
         hang needs the full step count / multiple mid-run resets that stage3-5's short runs did
         not reach.
stage 9: p6_1 Part1-specific -- build_env_cfg WITH p6_1's extra reset_base.params["pose_range"]={}
         and reset_robot_joints.params["position_range"/"velocity_range"] overrides (absent from
         t0_3/p6_2), then pxr mesh_pts (stage6, confirmed fine), then env.reset() +
         measure_sole_pitch (body_link_quat_w/math_utils.quat_apply/numpy plane fit) once.
stage 10: p6_1 Part1's exact calibration loop -- same env as stage9, but now mutate
          robot.data.default_joint_pos[:, ffe_id] directly (write, not cfg) before each of 3
          env.reset() calls (baseline, +delta, -delta), matching p6_1's untested last remaining
          difference from stage8/9 (which never touch that buffer between resets).
"""
import argparse
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--load_run", type=str, default="2026-09-16_17-28-46_G_real_peak")
parser.add_argument("--checkpoint", type=str, default="model_2999.pt")
parser.add_argument("--num_envs", type=int, default=16)
parser.add_argument("--noise_std_type", type=str, default="log", choices=["scalar", "log"])
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--experiment", type=str, default="skyentific_poclegs_rough")
parser.add_argument("--log_root", type=str, default=r"D:\Tominaga\IsaacLab\logs\rsl_rl")
parser.add_argument("--stage", type=int, required=True)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True
sys.argv = [sys.argv[0]]

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
import os  # noqa: E402
import importlib.metadata as metadata  # noqa: E402

import torch  # noqa: E402
import yaml  # noqa: E402
from rsl_rl.runners import OnPolicyRunner  # noqa: E402

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
T0 = time.time()


def log(s):
    print(f"[k1_bisect] t={time.time() - T0:6.1f}s {s}", flush=True)


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
    cfg.events.reset_base.params["velocity_range"] = {
        "x": (0.0, 0.0), "y": (0.0, 0.0), "z": (0.0, 0.0),
        "roll": (0.0, 0.0), "pitch": (0.0, 0.0), "yaw": (0.0, 0.0),
    }
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


def make_env(device, num_envs, run_dir, p6_1_style=False):
    env_cfg = build_env_cfg(num_envs, args_cli.seed, device)
    if p6_1_style:
        env_cfg.events.reset_base.params["pose_range"] = {}
        env_cfg.events.reset_robot_joints.params["position_range"] = (1.0, 1.0)
        env_cfg.events.reset_robot_joints.params["velocity_range"] = (0.0, 0.0)
    apply_trained_actuator_params(env_cfg, run_dir)
    env = ManagerBasedRLEnv(cfg=env_cfg)
    return env


def load_policy(env, run_dir, device):
    agent_cfg = SkyentificPoclegsRoughPPORunnerCfg()
    agent_cfg.seed = args_cli.seed
    agent_cfg.device = device
    agent_cfg.policy.noise_std_type = args_cli.noise_std_type
    apply_trained_noise_std_type(agent_cfg, run_dir)
    agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, INSTALLED_VERSION)
    envw = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
    log("OnPolicyRunner construct start")
    runner = OnPolicyRunner(envw, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    log("OnPolicyRunner construct done")
    resume_path = os.path.join(run_dir, args_cli.checkpoint)
    log("runner.load start")
    runner.load(handle_deprecated_rsl_rl_checkpoint(resume_path, INSTALLED_VERSION))
    log("runner.load done")
    policy = runner.get_inference_policy(device=device)
    log("get_inference_policy done")
    return envw, policy


def link_mesh_points(stage, prim_path):
    from pxr import Gf, Usd, UsdGeom, UsdPhysics
    import numpy as np

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


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"
    stage = args_cli.stage
    run_dir = os.path.join(args_cli.log_root, args_cli.experiment, args_cli.load_run)

    log(f"stage={stage} num_envs={args_cli.num_envs} load_run={args_cli.load_run} start")

    if stage == 9:
        import isaaclab.utils.math as math_utils
        import numpy as np

        env = make_env(device, args_cli.num_envs, run_dir, p6_1_style=True)
        log("first env created (p6_1-style event overrides)")
        stage_usd = env.scene.stage
        robot = env.scene["robot"]
        FOOT_BODIES = ("ll_ffe", "lr_ffe")
        body_ids = {n: robot.body_names.index(n) for n in FOOT_BODIES}
        mesh_pts = {n: link_mesh_points(stage_usd, f"/World/envs/env_0/Robot/{n}") for n in FOOT_BODIES}
        log("mesh_pts done")

        def fit_plane_pitch(points_xyz):
            pts = points_xyz
            A = np.stack([pts[:, 0], pts[:, 1], np.ones(pts.shape[0])], axis=1)
            b = pts[:, 2]
            coef, *_ = np.linalg.lstsq(A, b, rcond=None)
            a_x, a_y, c0 = coef
            return float(np.degrees(np.arctan(a_x)))

        def measure_sole_pitch(body_idx, mesh_pts_local):
            c = mesh_pts_local.to(device)
            q = robot.data.body_link_quat_w[0, body_idx].unsqueeze(0).expand(c.shape[0], -1)
            p = robot.data.body_link_pos_w[0, body_idx].unsqueeze(0)
            world = (math_utils.quat_apply(q, c) + p).cpu().numpy()
            z_min = world[:, 2].min()
            sole = world[world[:, 2] <= z_min + 0.003]
            return fit_plane_pitch(sole)

        with torch.inference_mode():
            log("env.reset() start")
            env.reset()
            log("env.reset() done")
            pitch0 = {n: measure_sole_pitch(body_ids[n], mesh_pts[n]) for n in FOOT_BODIES}
            log(f"measure_sole_pitch done: {pitch0}")
        env.close()
        log("env closed -- stage9 done")
        return

    if stage == 10:
        import isaaclab.utils.math as math_utils
        import numpy as np

        env = make_env(device, args_cli.num_envs, run_dir, p6_1_style=True)
        log("first env created (p6_1-style event overrides)")
        robot = env.scene["robot"]
        FFE_JOINTS = ("LL_FFE", "LR_FFE")
        FOOT_BODIES = ("ll_ffe", "lr_ffe")
        ffe_ids = [robot.joint_names.index(n) for n in FFE_JOINTS]
        body_ids = {n: robot.body_names.index(n) for n in FOOT_BODIES}
        stage_usd = env.scene.stage
        mesh_pts = {n: link_mesh_points(stage_usd, f"/World/envs/env_0/Robot/{n}") for n in FOOT_BODIES}
        log("mesh_pts done")

        def fit_plane_pitch(points_xyz):
            pts = points_xyz
            A = np.stack([pts[:, 0], pts[:, 1], np.ones(pts.shape[0])], axis=1)
            b = pts[:, 2]
            coef, *_ = np.linalg.lstsq(A, b, rcond=None)
            a_x, a_y, c0 = coef
            return float(np.degrees(np.arctan(a_x)))

        def measure_sole_pitch(body_idx, mesh_pts_local):
            c = mesh_pts_local.to(device)
            q = robot.data.body_link_quat_w[0, body_idx].unsqueeze(0).expand(c.shape[0], -1)
            p = robot.data.body_link_pos_w[0, body_idx].unsqueeze(0)
            world = (math_utils.quat_apply(q, c) + p).cpu().numpy()
            z_min = world[:, 2].min()
            sole = world[world[:, 2] <= z_min + 0.003]
            return fit_plane_pitch(sole)

        default_ffe = robot.data.default_joint_pos[0, ffe_ids].clone()
        with torch.inference_mode():
            log("baseline env.reset() start")
            env.reset()
            log("baseline env.reset() done")
            pitch0 = {n: measure_sole_pitch(body_ids[n], mesh_pts[n]) for n in FOOT_BODIES}
            log(f"baseline measure done: {pitch0}")

            delta = 0.2
            for side_i, jn in enumerate(FFE_JOINTS):
                body = FOOT_BODIES[side_i]
                saved = robot.data.default_joint_pos[:, ffe_ids[side_i]].clone()
                log(f"{jn}: mutating default_joint_pos +delta")
                robot.data.default_joint_pos[:, ffe_ids[side_i]] = default_ffe[side_i] + delta
                log(f"{jn}: +delta env.reset() start")
                env.reset()
                log(f"{jn}: +delta env.reset() done")
                pitch_plus = measure_sole_pitch(body_ids[body], mesh_pts[body])
                log(f"{jn}: +delta pitch={pitch_plus}")

                log(f"{jn}: mutating default_joint_pos -delta")
                robot.data.default_joint_pos[:, ffe_ids[side_i]] = default_ffe[side_i] - delta
                log(f"{jn}: -delta env.reset() start")
                env.reset()
                log(f"{jn}: -delta env.reset() done")
                pitch_minus = measure_sole_pitch(body_ids[body], mesh_pts[body])
                log(f"{jn}: -delta pitch={pitch_minus}")

                robot.data.default_joint_pos[:, ffe_ids[side_i]] = saved
                log(f"{jn}: restored default_joint_pos, calib done")

        env.close()
        log("env closed -- stage10 done")
        return

    env = make_env(device, args_cli.num_envs, run_dir)
    log("first env created")

    if stage == 1:
        env.close()
        log("env closed -- stage1 done")
        return

    if stage == 2:
        env.close()
        log("first env closed")
        env2 = make_env(device, args_cli.num_envs, run_dir)
        log("second env created")
        env2.close()
        log("second env closed -- stage2 done")
        return

    if stage == 6:
        stage_usd = env.scene.stage
        log("got env.scene.stage")
        pts = link_mesh_points(stage_usd, "/World/envs/env_0/Robot/ll_ffe")
        log(f"link_mesh_points(ll_ffe) done, n_pts={0 if pts is None else pts.shape[0]}")
        pts2 = link_mesh_points(stage_usd, "/World/envs/env_0/Robot/lr_ffe")
        log(f"link_mesh_points(lr_ffe) done, n_pts={0 if pts2 is None else pts2.shape[0]}")
        env.close()
        log("env closed -- stage6 done")
        return

    if stage == 8:
        envw, policy = load_policy(env, run_dir, device)
        FOOT_BODIES = ("ll_ffe", "lr_ffe")
        HR_JOINTS = ("LL_HR", "LR_HR")
        robot = env.scene["robot"]
        hr_ids = [robot.joint_names.index(n) for n in HR_JOINTS]
        contact_sensor = env.scene.sensors["contact_forces"]
        sensor_body_names = list(contact_sensor.body_names)
        sensor_body_ids = [sensor_body_names.index(n) for n in FOOT_BODIES]
        reward_mgr = env.reward_manager
        SCENARIOS = [("S1", 0.5, 0.0, 0.0), ("S3", 0.0, 0.0, 0.0), ("S6", 0.0, 0.0, 0.5)]
        with torch.inference_mode():
            for tag, vx, vy, wz in SCENARIOS:
                log(f"scenario {tag} reset start")
                res = envw.reset()
                obs = res[0] if isinstance(res, tuple) else res
                log(f"scenario {tag} reset done")
                cmd_term = env.unwrapped.command_manager.get_term("base_velocity")
                cmd_term.vel_command_b[:, 0] = vx
                cmd_term.vel_command_b[:, 1] = vy
                cmd_term.vel_command_b[:, 2] = wz
                cmd_term.is_standing_env[:] = False
                n_warm = 100
                n_meas = 500
                for i in range(n_warm):
                    obs, _, dones, _ = envw.step(policy(obs))
                    policy.reset(dones)
                    cmd_term.vel_command_b[:, 0] = vx
                    cmd_term.vel_command_b[:, 1] = vy
                    cmd_term.vel_command_b[:, 2] = wz
                    if i % 50 == 0:
                        log(f"scenario {tag} warmup step {i}")
                log(f"scenario {tag} warmup done")
                for i in range(n_meas):
                    obs, _, dones, _ = envw.step(policy(obs))
                    policy.reset(dones)
                    cmd_term.vel_command_b[:, 0] = vx
                    cmd_term.vel_command_b[:, 1] = vy
                    cmd_term.vel_command_b[:, 2] = wz
                    _ = robot.data.joint_pos[:, hr_ids].clone()
                    _ = robot.data.computed_torque[:, hr_ids].clone()
                    effort = robot.data.joint_effort_limits[:, hr_ids]
                    _ = (robot.data.computed_torque[:, hr_ids].abs() >= effort - 1e-3).float()
                    forces = contact_sensor.data.net_forces_w[:, sensor_body_ids, :].norm(dim=-1)
                    _ = (forces > 1.0).float()
                    _ = contact_sensor.compute_first_contact(env.step_dt)[:, sensor_body_ids]
                    _ = contact_sensor.data.last_air_time[:, sensor_body_ids]
                    _ = reward_mgr._step_reward.clone()
                    foot_body_ids = [robot.body_names.index(n) for n in FOOT_BODIES]
                    _ = robot.data.body_ang_vel_w[:, foot_body_ids, 2]
                    if i % 100 == 0:
                        log(f"scenario {tag} meas step {i}")
                log(f"scenario {tag} meas done")
        env.close()
        log("env closed -- stage8 done")
        return

    envw, policy = load_policy(env, run_dir, device)

    if stage == 3:
        env.close()
        log("env closed -- stage3 done (loaded, no step)")
        return

    with torch.inference_mode():
        res = envw.reset()
        obs = res[0] if isinstance(res, tuple) else res
        log("envw.reset() done")
        cmd_term = env.unwrapped.command_manager.get_term("base_velocity")
        cmd_term.vel_command_b[:, 0] = 0.0
        cmd_term.vel_command_b[:, 1] = 0.0
        cmd_term.vel_command_b[:, 2] = 0.5
        cmd_term.is_standing_env[:] = False

        FOOT_BODIES = ("ll_ffe", "lr_ffe")
        HR_JOINTS = ("LL_HR", "LR_HR")
        robot = env.scene["robot"]
        hr_ids = [robot.joint_names.index(n) for n in HR_JOINTS]
        contact_sensor = None
        sensor_body_ids = None
        reward_mgr = None
        if stage >= 5:
            contact_sensor = env.scene.sensors["contact_forces"]
            sensor_body_names = list(contact_sensor.body_names)
            sensor_body_ids = [sensor_body_names.index(n) for n in FOOT_BODIES]
            reward_mgr = env.reward_manager
            log("stage5 extras resolved (contact_sensor, reward_mgr)")

        for i in range(5):
            obs, _, dones, _ = envw.step(policy(obs))
            policy.reset(dones)
            cmd_term.vel_command_b[:, 0] = 0.0
            cmd_term.vel_command_b[:, 1] = 0.0
            cmd_term.vel_command_b[:, 2] = 0.5
            log(f"step {i} done")
            if stage >= 5:
                _ = robot.data.computed_torque[:, hr_ids].clone()
                forces = contact_sensor.data.net_forces_w[:, sensor_body_ids, :].norm(dim=-1)
                _ = (forces > 1.0).float()
                _ = contact_sensor.compute_first_contact(env.step_dt)[:, sensor_body_ids]
                _ = contact_sensor.data.last_air_time[:, sensor_body_ids]
                _ = reward_mgr._step_reward.clone()
                log(f"step {i} extra data access done")

    env.close()
    log(f"env closed -- stage{stage} done")


if __name__ == "__main__":
    main()
    simulation_app.close()
    log("simulation_app closed, exiting")
