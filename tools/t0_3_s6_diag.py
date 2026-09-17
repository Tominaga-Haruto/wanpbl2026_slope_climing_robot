"""T0-3: what is the policy actually doing during S6 (pure in-place turn), compared to S1/S3.
G_real_peak@2999 and H_eff13p5@2999, 64 env each, S6/S1/S3.

Reports: foot contact rate, air time per step, steps per 10s, HR joint angle stats, HR torque
stats, per-step reward term averages (weight included), and foot yaw slip during contact.
"""

import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--noise_std_type", type=str, default="log", choices=["scalar", "log"])
parser.add_argument("--log_root", type=str, default=r"D:\Tominaga\IsaacLab\logs\rsl_rl")
parser.add_argument("--experiment", type=str, default="skyentific_poclegs_rough")
parser.add_argument("--out", type=str, default=r"D:\Tominaga\slope-climbing-robot\tools\logs\T0_3_s6_diag.md")
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
SCENARIOS = [("S1", 0.5, 0.0, 0.0), ("S3", 0.0, 0.0, 0.0), ("S6", 0.0, 0.0, 0.5)]


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


def run_one(load_run, checkpoint, device):
    run_dir = os.path.join(args_cli.log_root, args_cli.experiment, load_run)
    resume_path = os.path.join(run_dir, checkpoint)

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
    reward_mgr = env.reward_manager
    term_names = list(reward_mgr.active_terms)

    cmd_term = env.unwrapped.command_manager.get_term("base_velocity")

    results = {}
    with torch.inference_mode():
        for tag, vx, vy, wz in SCENARIOS:
            res = envw.reset()
            obs = res[0] if isinstance(res, tuple) else res
            cmd_term.vel_command_b[:, 0] = vx
            cmd_term.vel_command_b[:, 1] = vy
            cmd_term.vel_command_b[:, 2] = wz
            cmd_term.is_standing_env[:] = False
            n_warm = 100
            n_meas = 500
            for _ in range(n_warm):
                obs, _, dones, _ = envw.step(policy(obs))
                policy.reset(dones)
                cmd_term.vel_command_b[:, 0] = vx
                cmd_term.vel_command_b[:, 1] = vy
                cmd_term.vel_command_b[:, 2] = wz

            hr_pos_hist = []
            hr_tau_hist = []
            sat_hist = []
            contact_hist = []
            reward_hist = []
            foot_yaw_vel_hist = []
            landings = torch.zeros(args_cli.num_envs, device=device)
            air_time_sum = torch.zeros(args_cli.num_envs, device=device)

            for _ in range(n_meas):
                obs, _, dones, _ = envw.step(policy(obs))
                policy.reset(dones)
                cmd_term.vel_command_b[:, 0] = vx
                cmd_term.vel_command_b[:, 1] = vy
                cmd_term.vel_command_b[:, 2] = wz

                hr_pos_hist.append(robot.data.joint_pos[:, hr_ids].clone())
                hr_tau_hist.append(robot.data.computed_torque[:, hr_ids].clone())
                effort = robot.data.joint_effort_limits[:, hr_ids]
                sat_hist.append((robot.data.computed_torque[:, hr_ids].abs() >= effort - 1e-3).float())

                forces = contact_sensor.data.net_forces_w[:, sensor_body_ids, :].norm(dim=-1)
                contact_hist.append((forces > 1.0).float())

                first_contact = contact_sensor.compute_first_contact(env.step_dt)[:, sensor_body_ids]
                last_air = contact_sensor.data.last_air_time[:, sensor_body_ids]
                landings += first_contact.float().sum(dim=1)
                air_time_sum += (last_air * first_contact.float()).sum(dim=1)

                reward_hist.append(reward_mgr._step_reward.clone())

                foot_ang_vel = robot.data.body_ang_vel_w[:, foot_body_ids, 2]  # yaw component
                in_contact = forces > 1.0
                foot_yaw_vel_hist.append(torch.where(in_contact, foot_ang_vel.abs(), torch.full_like(foot_ang_vel, float("nan"))))

            hr_pos = torch.stack(hr_pos_hist)  # (T, N, 2)
            hr_tau = torch.stack(hr_tau_hist)
            sat = torch.stack(sat_hist)
            contact = torch.stack(contact_hist)  # (T, N, 2)
            reward_all = torch.stack(reward_hist)  # (T, N, n_terms)
            foot_yaw = torch.stack(foot_yaw_vel_hist)

            n_landings_total = float(landings.sum().item())
            mean_air_time_per_step = float((air_time_sum.sum() / max(n_landings_total, 1)).item())
            steps_per_10s = float(landings.mean().item())  # landings per env over the 10s window

            results[tag] = {
                "contact_rate": contact.mean(dim=(0, 1)).cpu().tolist(),  # per-foot
                "air_time_per_step": mean_air_time_per_step,
                "steps_per_10s": steps_per_10s,
                "hr_pos_mean": hr_pos.mean(dim=(0, 1)).cpu().tolist(),
                "hr_pos_range": (hr_pos.amin(dim=(0, 1)).cpu().tolist(), hr_pos.amax(dim=(0, 1)).cpu().tolist()),
                "hr_pos_absp95": torch.quantile(hr_pos.abs().reshape(-1, 2), 0.95, dim=0).cpu().tolist(),
                "hr_tau_p95": torch.quantile(hr_tau.abs().reshape(-1, 2), 0.95, dim=0).cpu().tolist(),
                "hr_sat_frac": sat.mean(dim=(0, 1)).cpu().tolist(),
                "reward_terms": {name: float(reward_all[:, :, i].mean().item()) for i, name in enumerate(term_names)},
                "foot_yaw_slip_mean": float(torch.nanmean(foot_yaw).item()),
                "foot_yaw_slip_p95": float(torch.nanquantile(foot_yaw[~torch.isnan(foot_yaw)], 0.95).item()) if (~torch.isnan(foot_yaw)).any() else float("nan"),
            }

    env.close()
    return results, term_names


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"
    runs = {
        "G_real_peak": ("2026-09-16_17-28-46_G_real_peak", "model_2999.pt"),
        "H_eff13p5": ("2026-09-17_00-08-51_H_eff13p5", "model_2999.pt"),
    }
    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    emit("# T0-3: S6での挙動診断 (G_real_peak@2999 / H_eff13p5@2999, 64env, S1/S3/S6)\n")

    all_results = {}
    for name, (run, ckpt) in runs.items():
        print(f"=== running {name} ===")
        results, term_names = run_one(run, ckpt, device)
        all_results[name] = results

    for name in runs:
        emit(f"\n## {name}\n")
        emit("| scenario | 接地率(LL/LR) | 歩あたり滞空[s] | 歩数/10s | HR平均角(LL/LR) | HR範囲(LL/LR) | HR\\|角\\|p95(LL/LR) | HR tau p95(LL/LR) | HR飽和率(LL/LR) | 足yaw滑りmean/p95[rad/s] |")
        emit("|---|---|---|---|---|---|---|---|---|---|")
        for tag, *_ in SCENARIOS:
            r = all_results[name][tag]
            emit(f"| {tag} | {r['contact_rate'][0]:.3f}/{r['contact_rate'][1]:.3f} | "
                 f"{r['air_time_per_step']:.3f} | {r['steps_per_10s']:.2f} | "
                 f"{r['hr_pos_mean'][0]:+.4f}/{r['hr_pos_mean'][1]:+.4f} | "
                 f"[{r['hr_pos_range'][0][0]:+.3f},{r['hr_pos_range'][1][0]:+.3f}]/[{r['hr_pos_range'][0][1]:+.3f},{r['hr_pos_range'][1][1]:+.3f}] | "
                 f"{r['hr_pos_absp95'][0]:.4f}/{r['hr_pos_absp95'][1]:.4f} | "
                 f"{r['hr_tau_p95'][0]:.3f}/{r['hr_tau_p95'][1]:.3f} | "
                 f"{r['hr_sat_frac'][0]:.4f}/{r['hr_sat_frac'][1]:.4f} | "
                 f"{r['foot_yaw_slip_mean']:.4f}/{r['foot_yaw_slip_p95']:.4f} |")

        emit(f"\n### {name}: 報酬項ごとの1step平均(weight込み)\n")
        emit("| term | S1 | S3 | S6 |")
        emit("|---|---|---|---|")
        for term in term_names:
            vals = [all_results[name][tag]["reward_terms"][term] for tag, *_ in SCENARIOS]
            emit(f"| {term} | {vals[0]:+.5f} | {vals[1]:+.5f} | {vals[2]:+.5f} |")

    with open(args_cli.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[t0_3] wrote {args_cli.out}")


if __name__ == "__main__":
    main()
    simulation_app.close()
