"""K3 (exp07): how much yaw torque about the WORLD z-axis can the policy (H_eff13p5@2999, S3,
policy running) resist before the base actually rotates, and before a stance foot starts slipping?
Single env per process (see K1 note in t0_3_s6_diag.py / p6_1_footpitch.py).

Protocol: reset, let the policy settle for 2s under S3 (cmd=0,0,0), then ramp an external world-
frame torque on the base body from 0 to 10 N*m at 1 N*m/s (10s, matching STEP_DT*0.5*num_steps),
applied via Articulation.set_external_force_and_torque(..., is_global=True) called every control
step before envw.step() (isaaclab.assets.articulation.Articulation.set_external_force_and_torque,
see D:\\Tominaga\\IsaacLab\\source\\isaaclab\\isaaclab\\assets\\articulation\\articulation.py:1003;
this is the deprecated-but-functional API -- the replacement is
Articulation.permanent_wrench_composer.set_forces_and_torques, not used here since this is a
one-off diagnostic script, not tracked cfg). cfg itself is untouched; only this script's own
env_cfg overrides (same terrain/event neutralization as the other diagnostic scripts) and a
per-step live wrench-buffer write.

Reports per env: torque at which |base world yaw rate| first exceeds 0.2 rad/s, torque at which
either in-contact foot's world yaw angular velocity first exceeds 0.2 rad/s (foot starts slipping
under the base), and time of fall (if any) -- median and [min,max] across envs. Also reports the
whole-body z-axis moment of inertia about the base's COM (world-z, reference pose == first S3
reset) and the HR joints' effort_limit/stiffness as currently enforced (post apply_trained_actuator_
params), for context. The z-inertia is an approximation: each body's own inertia (PhysX
get_inertias(), local/principal frame) rotated into world frame plus its parallel-axis contribution
from body ORIGIN offset (not COM) to the base's position -- adequate for an order-of-magnitude
reference number, not an exact COM-based figure.
"""

import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--load_run", type=str, default="2026-09-17_00-08-51_H_eff13p5")
parser.add_argument("--checkpoint", type=str, default="model_2999.pt")
parser.add_argument("--num_envs", type=int, default=32)
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--noise_std_type", type=str, default="log", choices=["scalar", "log"])
parser.add_argument("--log_root", type=str, default=r"D:\Tominaga\IsaacLab\logs\rsl_rl")
parser.add_argument("--experiment", type=str, default="skyentific_poclegs_rough")
parser.add_argument("--torque_rate", type=float, default=1.0, help="N*m per second")
parser.add_argument("--torque_max", type=float, default=10.0, help="N*m")
parser.add_argument("--rot_threshold", type=float, default=0.2, help="rad/s, base yaw rate")
parser.add_argument("--slip_threshold", type=float, default=0.2, help="rad/s, stance-foot yaw rate")
parser.add_argument("--out", type=str, default=r"D:\Tominaga\slope-climbing-robot\tools\logs\K3_torque_ramp.md")
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
STEP_DT = 0.02
FOOT_BODIES = ("ll_ffe", "lr_ffe")
HR_JOINTS = ("LL_HR", "LR_HR")


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


def compute_z_inertia_reference(robot, env_idx=0):
    """Approximate whole-body world-z moment of inertia about the base position, at the current
    pose. Sum over bodies of (R_i @ I_i_local @ R_i^T)[z,z] + m_i*(dx^2+dy^2), dx/dy = body ORIGIN
    (not COM) offset from base origin in world xy. See module docstring for the approximation."""
    import isaaclab.utils.math as math_utils

    dev = robot.data.root_pos_w.device
    root_pos = robot.data.root_pos_w[env_idx].to(dev)  # (3,)
    body_pos = robot.data.body_pos_w[env_idx].to(dev)  # (B,3)
    body_quat = robot.data.body_quat_w[env_idx].to(dev)  # (B,4)
    masses = robot.data.default_mass[env_idx].to(dev)  # (B,)
    inertias = robot.data.default_inertia[env_idx].to(dev)  # (B,9)

    B = body_pos.shape[0]
    total_izz = 0.0
    for i in range(B):
        R = math_utils.matrix_from_quat(body_quat[i].unsqueeze(0))[0].to(dev)  # (3,3)
        I_local = inertias[i].reshape(3, 3).to(dev)
        I_world = R @ I_local @ R.T
        r = body_pos[i] - root_pos
        m = float(masses[i])
        total_izz += float(I_world[2, 2]) + m * (float(r[0]) ** 2 + float(r[1]) ** 2)
    total_mass = float(masses.sum())
    return total_izz, total_mass


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"
    run_dir = os.path.join(args_cli.log_root, args_cli.experiment, args_cli.load_run)
    resume_path = os.path.join(run_dir, args_cli.checkpoint)

    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    emit(f"# K3: 旋回可能トルク調査 -- {args_cli.load_run} @ {args_cli.checkpoint}, "
         f"{args_cli.num_envs}env, S3固定, world z軸トルクを0->{args_cli.torque_max}N*mまで"
         f"{args_cli.torque_rate}N*m/sで漸増\n")

    env_cfg = build_env_cfg(args_cli.num_envs, args_cli.seed, device)
    apply_trained_actuator_params(env_cfg, run_dir)
    agent_cfg = SkyentificPoclegsRoughPPORunnerCfg()
    agent_cfg.seed = args_cli.seed
    agent_cfg.device = device
    agent_cfg.policy.noise_std_type = args_cli.noise_std_type
    apply_trained_noise_std_type(agent_cfg, run_dir)
    agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, INSTALLED_VERSION)

    env = ManagerBasedRLEnv(cfg=env_cfg)
    envw = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
    runner = OnPolicyRunner(envw, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    runner.load(handle_deprecated_rsl_rl_checkpoint(resume_path, INSTALLED_VERSION))
    policy = runner.get_inference_policy(device=device)

    robot = env.scene["robot"]
    hr_ids = [robot.joint_names.index(n) for n in HR_JOINTS]
    contact_sensor = env.scene.sensors["contact_forces"]
    sensor_body_names = list(contact_sensor.body_names)
    sensor_body_ids = [sensor_body_names.index(n) for n in FOOT_BODIES]
    foot_body_ids = [robot.body_names.index(n) for n in FOOT_BODIES]

    base_candidates = [n for n in robot.body_names if "base" in n.lower()]
    base_name = base_candidates[0] if base_candidates else robot.body_names[0]
    base_idx = robot.body_names.index(base_name)
    emit(f"- base body used for external torque: `{base_name}` (index {base_idx}, "
         f"body_names={list(robot.body_names)})\n")

    cmd_term = env.unwrapped.command_manager.get_term("base_velocity")

    with torch.inference_mode():
        res = envw.reset()
        obs = res[0] if isinstance(res, tuple) else res
        cmd_term.vel_command_b[:, 0] = 0.0
        cmd_term.vel_command_b[:, 1] = 0.0
        cmd_term.vel_command_b[:, 2] = 0.0
        cmd_term.is_standing_env[:] = False

        izz_ref, mass_ref = compute_z_inertia_reference(robot, env_idx=0)

        n_warm = int(round(2.0 / STEP_DT))
        for _ in range(n_warm):
            obs, _, dones, _ = envw.step(policy(obs))
            policy.reset(dones)
            cmd_term.vel_command_b[:, 0] = 0.0
            cmd_term.vel_command_b[:, 1] = 0.0
            cmd_term.vel_command_b[:, 2] = 0.0

        n_ramp = int(round(args_cli.torque_max / args_cli.torque_rate / STEP_DT))
        rot_torque = torch.full((args_cli.num_envs,), float("nan"), device=device)
        slip_torque = torch.full((args_cli.num_envs,), float("nan"), device=device)
        fall_time = torch.full((args_cli.num_envs,), float("nan"), device=device)
        rot_hit = torch.zeros(args_cli.num_envs, dtype=torch.bool, device=device)
        slip_hit = torch.zeros(args_cli.num_envs, dtype=torch.bool, device=device)
        fell = torch.zeros(args_cli.num_envs, dtype=torch.bool, device=device)

        forces_zero = torch.zeros((args_cli.num_envs, 1, 3), device=device)
        for step_i in range(n_ramp):
            current_torque = args_cli.torque_rate * (step_i + 1) * STEP_DT
            torques = torch.zeros((args_cli.num_envs, 1, 3), device=device)
            torques[:, 0, 2] = current_torque
            robot.set_external_force_and_torque(forces_zero, torques, body_ids=[base_idx], is_global=True)

            obs, _, dones, _ = envw.step(policy(obs))
            policy.reset(dones)
            cmd_term.vel_command_b[:, 0] = 0.0
            cmd_term.vel_command_b[:, 1] = 0.0
            cmd_term.vel_command_b[:, 2] = 0.0

            new_fall = dones.to(torch.bool) & (~fell)
            fall_time[new_fall] = (step_i + 1) * STEP_DT
            fell |= dones.to(torch.bool)

            yaw_rate = robot.data.root_ang_vel_w[:, 2].abs()
            newly_rot = (yaw_rate > args_cli.rot_threshold) & (~rot_hit)
            rot_torque[newly_rot] = current_torque
            rot_hit |= newly_rot

            forces = contact_sensor.data.net_forces_w[:, sensor_body_ids, :].norm(dim=-1)
            in_contact = forces > 1.0
            foot_yaw = robot.data.body_ang_vel_w[:, foot_body_ids, 2].abs()
            slipping_now = ((foot_yaw > args_cli.slip_threshold) & in_contact).any(dim=1)
            newly_slip = slipping_now & (~slip_hit)
            slip_torque[newly_slip] = current_torque
            slip_hit |= newly_slip

    env.close()

    def stats(t, label):
        valid = t[~torch.isnan(t)]
        if valid.numel() == 0:
            return f"{label}: 到達なし(全{args_cli.num_envs}env未到達)"
        return (f"{label}: 中央値={valid.median().item():.3f}, 範囲=[{valid.min().item():.3f},"
                f"{valid.max().item():.3f}], 到達env数={valid.numel()}/{args_cli.num_envs}")

    # NOTE: robot.data.joint_effort_limits / joint_stiffness reflect the PhysX-solver-level
    # (effort_limit_sim) values, which DelayedPDActuatorCfg deliberately sets very high (~1e9) so
    # the actuator's own Python-side model does the real clipping -- reading those fields here
    # gave a meaningless 1e9/0.0 on the first pass. The ACTUATOR object's own .effort_limit /
    # .stiffness (set from my_robot_code/skyentific_poclegs.py's cfg, effort_limit=53.0 for "hr")
    # is the value actually enforced on computed_torque. Same caveat applies to K2's "HR飽和率"
    # column, which used the solver-level field and should be read as uninformative (always 0),
    # not as "never saturates" -- see docs/experiments/exp07_*.md.
    hr_actuator = robot.actuators["hr"]
    hr_act_ids = [hr_actuator.joint_names.index(n) for n in HR_JOINTS]
    hr_effort = hr_actuator.effort_limit[0, hr_act_ids].cpu().tolist()
    hr_stiff = hr_actuator.stiffness[0, hr_act_ids].cpu().tolist()

    emit("## 結果\n")
    emit(f"- {stats(rot_torque, f'胴体yaw角速度が{args_cli.rot_threshold}rad/sを超えたトルク[N*m]')}")
    emit(f"- {stats(slip_torque, f'立脚足のyaw角速度が{args_cli.slip_threshold}rad/sを超えたトルク[N*m](滑り出し)')}")
    emit(f"- {stats(fall_time, '転倒した時刻[s]')}")
    emit(f"\n## 参考値\n")
    emit(f"- 胴体z軸まわり慣性モーメント(全身、base原点基準、近似): {izz_ref:.5f} kg*m^2 (全身質量 {mass_ref:.4f} kg)")
    emit(f"- HR effort_limit(LL/LR、actuatorオブジェクト実値): {hr_effort[0]:.3f}/{hr_effort[1]:.3f} N*m")
    emit(f"- HR stiffness(LL/LR、actuatorオブジェクト実値): {hr_stiff[0]:.3f}/{hr_stiff[1]:.3f}")

    with open(args_cli.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[k3_torque_ramp] wrote {args_cli.out}")


if __name__ == "__main__":
    main()
    simulation_app.close()
