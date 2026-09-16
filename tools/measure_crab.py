"""Fixed evaluation protocol for crab-walk / stalling diagnosis.

Runs a trained checkpoint through six fixed velocity-command scenarios on flat ground
with all randomisation disabled, and writes a metrics table to .md and .csv.
"""

import argparse
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Measure crab-walk / stalling of a trained policy.")
parser.add_argument("--load_run", type=str, required=True, help="Run folder name under logs/rsl_rl/<experiment>.")
parser.add_argument("--checkpoint", type=str, default="model_1600.pt", help="Checkpoint file name.")
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--noise_std_type", type=str, default="log", choices=["scalar", "log"])
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--experiment", type=str, default="skyentific_poclegs_rough")
parser.add_argument("--log_root", type=str, default=r"D:\Tominaga\IsaacLab\logs\rsl_rl")
parser.add_argument("--out_dir", type=str, default=r"D:\Tominaga\slope-climbing-robot\tools\logs")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True
sys.argv = [sys.argv[0]]

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------

import csv
import importlib.metadata as metadata
import math
import os

import torch
from rsl_rl.runners import OnPolicyRunner

import isaaclab.utils.math as math_utils
from isaaclab.envs import ManagerBasedRLEnv

from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg, handle_deprecated_rsl_rl_checkpoint

import isaaclab_tasks  # noqa: F401
import skyentific_poclegs  # noqa: F401
from skyentific_poclegs.tasks.locomotion.velocity.config.skyentific_poclegs.agents.rsl_rl_cfg import (
    SkyentificPoclegsRoughPPORunnerCfg,
)
from skyentific_poclegs.tasks.locomotion.velocity.config.skyentific_poclegs.rough_env_cfg import (
    SkyentificPoclegsRoughEnvCfg,
)

INSTALLED_VERSION = metadata.version("rsl-rl-lib")

WARMUP_S = 2.0
MEASURE_S = 10.0
STATIONARY_THRESH = 0.1

SCENARIOS = [
    ("S1", 0.5, 0.0, 0.0),
    ("S2", 1.0, 0.0, 0.0),
    ("S3", 0.0, 0.0, 0.0),
    ("S4", -0.3, 0.0, 0.0),
    ("S5", 0.0, 0.3, 0.0),
    ("S6", 0.0, 0.0, 0.5),
    ("S7", 0.5, 0.0, 0.3),
    ("S8", 0.5, 0.0, -0.3),
    ("S9", 0.0, 0.0, -0.5),
]


def build_env_cfg(num_envs: int, seed: int, device: str) -> SkyentificPoclegsRoughEnvCfg:
    cfg = SkyentificPoclegsRoughEnvCfg()
    cfg.scene.num_envs = num_envs
    cfg.seed = seed
    cfg.sim.device = device

    # -- flat ground. The Isaac "plane" terrain type needs a remote USD that is not reachable here,
    #    so an all-flat generated terrain is used instead: physically identical, generated locally.
    gen = cfg.scene.terrain.terrain_generator
    for name in gen.sub_terrains:
        gen.sub_terrains[name].proportion = 0.0
    gen.sub_terrains["flat"].proportion = 1.0
    gen.num_rows = 2
    gen.num_cols = 2
    gen.curriculum = False
    cfg.scene.terrain.max_init_terrain_level = 0
    cfg.scene.terrain.debug_vis = False

    # -- no curriculum
    cfg.curriculum.terrain_levels = None
    cfg.curriculum.push_force_levels = None
    cfg.curriculum.command_vel = None

    # -- no observation noise
    cfg.observations.policy.enable_corruption = False

    # -- no disturbance / no domain randomisation
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

    # -- fixed command, no resampling, no heading control, no standing envs
    bv = cfg.commands.base_velocity
    bv.debug_vis = False
    bv.heading_command = False
    bv.ranges.heading = None
    bv.rel_heading_envs = 0.0
    bv.rel_standing_envs = 0.0
    bv.resampling_time_range = (1.0e6, 1.0e6)

    # long enough that no episode times out inside the 12 s window
    cfg.episode_length_s = 60.0
    return cfg


def bind_fixed_command(term, cmd):
    """Force the velocity command term to always emit ``cmd``."""

    def _resample(env_ids):
        term.vel_command_b[env_ids, 0] = cmd[0]
        term.vel_command_b[env_ids, 1] = cmd[1]
        term.vel_command_b[env_ids, 2] = cmd[2]
        term.is_standing_env[env_ids] = False
        term.is_heading_env[env_ids] = False

    term._resample_command = _resample
    term.vel_command_b[:, 0] = cmd[0]
    term.vel_command_b[:, 1] = cmd[1]
    term.vel_command_b[:, 2] = cmd[2]
    term.is_standing_env[:] = False
    term.is_heading_env[:] = False


def wrap_pi(x):
    return torch.atan2(torch.sin(x), torch.cos(x))


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"
    env_cfg = build_env_cfg(args_cli.num_envs, args_cli.seed, device)

    agent_cfg = SkyentificPoclegsRoughPPORunnerCfg()
    agent_cfg.seed = args_cli.seed
    agent_cfg.device = device
    agent_cfg.policy.noise_std_type = args_cli.noise_std_type
    agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, INSTALLED_VERSION)

    run_dir = os.path.join(args_cli.log_root, args_cli.experiment, args_cli.load_run)
    resume_path = os.path.join(run_dir, args_cli.checkpoint)
    if not os.path.isfile(resume_path):
        raise FileNotFoundError(f"checkpoint not found: {resume_path}")

    env = ManagerBasedRLEnv(cfg=env_cfg)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    runner.load(handle_deprecated_rsl_rl_checkpoint(resume_path, INSTALLED_VERSION))
    policy = runner.get_inference_policy(device=device)

    uenv = env.unwrapped
    robot = uenv.scene["robot"]
    sensor = uenv.scene.sensors["contact_forces"]
    cmd_term = uenv.command_manager.get_term("base_velocity")

    dt = uenv.step_dt
    n_warm = int(round(WARMUP_S / dt))
    n_meas = int(round(MEASURE_S / dt))
    N = uenv.num_envs

    foot_ids, foot_names = sensor.find_bodies(".*ffe")
    # the contact sensor keeps its own body ordering, so resolve the articulation indices separately
    robot_foot_ids = [robot.body_names.index(n) for n in foot_names]
    joint_names = list(robot.joint_names)
    hr_idx = {n: joint_names.index(n) for n in ("LR_HR", "LL_HR") if n in joint_names}

    # effort limits come from the actuator models: with explicit actuators the simulation-side
    # limits are left at infinity, so joint_effort_limits would be useless here.
    limits = torch.full((1, robot.num_joints), float("inf"), device=device)
    for act in robot.actuators.values():
        idx = act.joint_indices
        el = act.effort_limit
        el = el[0] if isinstance(el, torch.Tensor) and el.dim() > 1 else el
        limits[0, idx] = torch.as_tensor(el, device=device, dtype=limits.dtype)

    print("=" * 78)
    print(f"[measure_crab] run          : {args_cli.load_run}")
    print(f"[measure_crab] checkpoint   : {args_cli.checkpoint}")
    print(f"[measure_crab] num_envs     : {N}   step_dt={dt}  warm={n_warm} meas={n_meas}")
    print(f"[measure_crab] joint order  : {joint_names}")
    print(f"[measure_crab] body order   : {list(robot.body_names)}")
    print(f"[measure_crab] foot bodies  : {foot_names} ids={foot_ids}")
    print(f"[measure_crab] effort limit : {limits[0].tolist()}")

    # whole-body COM in base frame at the default pose (P1-13)
    masses = robot.data.default_mass.to(device)
    com_w = robot.data.body_com_pos_w
    total_m = masses.sum(dim=1, keepdim=True)
    com_world = (com_w * masses.unsqueeze(-1)).sum(dim=1) / total_m
    com_b = math_utils.quat_apply_inverse(robot.data.root_link_quat_w, com_world - robot.data.root_link_pos_w)
    print(f"[measure_crab] total mass   : {total_m[0].item():.3f} kg")
    print(f"[measure_crab] COM in base  : {com_b[0].tolist()}")
    print("=" * 78)

    rows = []
    for tag, cvx, cvy, cwz in SCENARIOS:
        cmd = (cvx, cvy, cwz)
        with torch.inference_mode():
            res = env.reset()
            obs = res[0] if isinstance(res, tuple) else res
            bind_fixed_command(cmd_term, cmd)

            for _ in range(n_warm):
                obs, _, dones, _ = env.step(policy(obs))
                policy.reset(dones)
            bind_fixed_command(cmd_term, cmd)

            actual_cmd = cmd_term.command[0].tolist()

            alive = torch.ones(N, dtype=torch.bool, device=device)
            ever_done = torch.zeros(N, dtype=torch.bool, device=device)
            steps = torch.zeros(N, device=device)
            s_vx = torch.zeros(N, device=device)
            s_vy = torch.zeros(N, device=device)
            s_vyerr = torch.zeros(N, device=device)
            s_wz = torch.zeros(N, device=device)
            s_hr = {n: torch.zeros(N, device=device) for n in hr_idx}
            air_sum = torch.zeros(N, len(foot_ids), device=device)
            air_cnt = torch.zeros(N, len(foot_ids), device=device)
            sat_hit = torch.zeros(N, device=device)
            qd_chunks = []
            # per-joint (all 10 joints, in robot.joint_names order): applied/computed torque, joint speed
            n_j = robot.num_joints
            tau_app_sumsq = torch.zeros(n_j, device=device)
            tau_app_cnt = torch.zeros(n_j, device=device)
            sat_hit_j = torch.zeros(n_j, device=device)
            tau_app_chunks = []
            tau_cmp_chunks = []
            qdj_chunks = []
            # swing apex: running max of foot height while airborne, banked at each touch-down
            swing_max = torch.zeros(N, len(foot_ids), device=device)
            apex_sum = torch.zeros(N, len(foot_ids), device=device)
            apex_cnt = torch.zeros(N, len(foot_ids), device=device)
            land_cnt = torch.zeros(N, len(foot_ids), device=device)
            ground_z = uenv.scene.env_origins[:, 2]

            yaw0 = robot.data.heading_w.clone()
            pos0 = robot.data.root_link_pos_w[:, :2].clone()

            for _ in range(n_meas):
                obs, _, dones, _ = env.step(policy(obs))
                policy.reset(dones)
                m = alive & (~dones.to(torch.bool))
                mf = m.float()

                yq = math_utils.yaw_quat(robot.data.root_link_quat_w)
                v_yaw = math_utils.quat_apply_inverse(yq, robot.data.root_com_lin_vel_w)
                wz = robot.data.root_ang_vel_w[:, 2]

                steps += mf
                s_vx += v_yaw[:, 0] * mf
                s_vy += v_yaw[:, 1] * mf
                s_vyerr += (v_yaw[:, 1] - cvy).abs() * mf
                s_wz += wz * mf
                for n, j in hr_idx.items():
                    s_hr[n] += robot.data.joint_pos[:, j] * mf

                fc = sensor.compute_first_contact(dt)[:, foot_ids].float()
                la = sensor.data.last_air_time[:, foot_ids]
                air_sum += la * fc * mf.unsqueeze(-1)
                air_cnt += fc * mf.unsqueeze(-1)

                foot_h = robot.data.body_link_pos_w[:, robot_foot_ids, 2] - ground_z.unsqueeze(-1)
                swing_max = torch.maximum(swing_max, foot_h)
                # bank the apex at touch-down, then clear it for the next swing
                apex_sum += swing_max * fc * mf.unsqueeze(-1)
                apex_cnt += fc * mf.unsqueeze(-1)
                land_cnt += fc * mf.unsqueeze(-1)
                swing_max = swing_max * (sensor.data.current_air_time[:, foot_ids] > 0.0).float()

                qd = robot.data.joint_vel.abs()
                if m.any():
                    qd_chunks.append(qd[m].flatten().clone())
                tau_app_abs = robot.data.applied_torque.abs()
                tau_cmp_abs = robot.data.computed_torque.abs()
                sat = (tau_app_abs >= 0.95 * limits).float().mean(dim=1)
                sat_hit += sat * mf

                if m.any():
                    tau_app_chunks.append(tau_app_abs[m].clone())
                    tau_cmp_chunks.append(tau_cmp_abs[m].clone())
                    qdj_chunks.append(qd[m].clone())
                tau_app_sumsq += (tau_app_abs**2 * mf.unsqueeze(-1)).sum(dim=0)
                tau_app_cnt += mf.sum()
                sat_hit_j += ((tau_app_abs >= 0.95 * limits).float() * mf.unsqueeze(-1)).sum(dim=0)

                ever_done |= dones.to(torch.bool)
                alive &= ~dones.to(torch.bool)

            yaw1 = robot.data.heading_w.clone()
            pos1 = robot.data.root_link_pos_w[:, :2].clone()

        cnt = steps.clamp(min=1.0)
        vx_m = s_vx / cnt
        vy_m = s_vy / cnt
        wz_m = s_wz / cnt
        vyerr_m = s_vyerr / cnt
        valid = steps > 0

        surv = alive & valid
        n_surv = int(surv.sum().item())

        def avg(t, mask):
            return float(t[mask].mean().item()) if int(mask.sum().item()) > 0 else float("nan")

        speed_mean = torch.sqrt(vx_m**2 + vy_m**2)
        stationary = float((speed_mean[surv] < STATIONARY_THRESH).float().mean().item()) if n_surv else float("nan")

        head_drift = torch.rad2deg(wrap_pi(yaw1 - yaw0))
        d = pos1 - pos0
        travel = torch.rad2deg(wrap_pi(torch.atan2(d[:, 1], d[:, 0]) - yaw0))

        air_mean = (air_sum / air_cnt.clamp(min=1.0))
        air_valid = air_cnt > 0
        apex_mean = (apex_sum / apex_cnt.clamp(min=1.0)) * 100.0  # cm
        apex_valid = apex_cnt > 0
        land_rate = land_cnt.sum(dim=1) / (cnt * dt)

        qd_all = torch.cat(qd_chunks) if qd_chunks else torch.zeros(1, device=device)
        qd_p95 = float(torch.quantile(qd_all.float(), 0.95).item())

        # per-joint (all 10 joints): applied/computed torque, joint speed
        tau_app_all = torch.cat(tau_app_chunks) if tau_app_chunks else torch.zeros(1, n_j, device=device)
        tau_cmp_all = torch.cat(tau_cmp_chunks) if tau_cmp_chunks else torch.zeros(1, n_j, device=device)
        qdj_all = torch.cat(qdj_chunks) if qdj_chunks else torch.zeros(1, n_j, device=device)
        tau_app_p95_j = torch.quantile(tau_app_all.float(), 0.95, dim=0)
        tau_app_max_j = tau_app_all.max(dim=0).values
        tau_app_rms_j = torch.sqrt(tau_app_sumsq / tau_app_cnt.clamp(min=1.0))
        tau_cmp_p95_j = torch.quantile(tau_cmp_all.float(), 0.95, dim=0)
        tau_cmp_max_j = tau_cmp_all.max(dim=0).values
        sat_frac_j = sat_hit_j / tau_app_cnt.clamp(min=1.0)
        qdj_p95_j = torch.quantile(qdj_all.float(), 0.95, dim=0)
        qdj_max_j = qdj_all.max(dim=0).values

        row = {
            "scenario": tag,
            "cmd_vx": cvx, "cmd_vy": cvy, "cmd_wz": cwz,
            "cmd_seen_vx": round(actual_cmd[0], 4),
            "cmd_seen_vy": round(actual_cmd[1], 4),
            "cmd_seen_wz": round(actual_cmd[2], 4),
            "n_envs": N, "n_survivors": n_surv,
            "vx_mean": avg(vx_m, valid),
            "vy_mean": avg(vy_m, valid),
            "vy_err_mean": avg(vyerr_m, valid),
            "yawrate_mean": avg(wz_m, valid),
            "heading_drift_deg": avg(head_drift, surv),
            "travel_dir_deg": avg(travel, surv) if tag in ("S1", "S2") else float("nan"),
            "stationary_rate": stationary if tag in ("S1", "S2", "S4", "S5") else float("nan"),
            "fall_rate": float(ever_done.float().mean().item()),
            "qd_p95": qd_p95,
            "torque_sat_frac": avg(sat_hit / cnt, valid),
        }
        for n in ("LR_HR", "LL_HR"):
            row[f"{n}_mean_rad"] = avg(s_hr[n] / cnt, valid) if n in hr_idx else float("nan")
        for k, fname in enumerate(foot_names):
            row[f"air_time_{fname}"] = avg(air_mean[:, k], air_valid[:, k] & valid)
            row[f"swing_apex_cm_{fname}"] = avg(apex_mean[:, k], apex_valid[:, k] & valid)
        row["landings_per_s"] = avg(land_rate, valid)
        for j, jn in enumerate(joint_names):
            row[f"tau_app_p95_{jn}"] = float(tau_app_p95_j[j].item())
            row[f"tau_app_max_{jn}"] = float(tau_app_max_j[j].item())
            row[f"tau_app_rms_{jn}"] = float(tau_app_rms_j[j].item())
            row[f"tau_cmp_p95_{jn}"] = float(tau_cmp_p95_j[j].item())
            row[f"tau_cmp_max_{jn}"] = float(tau_cmp_max_j[j].item())
            row[f"sat_frac_{jn}"] = float(sat_frac_j[j].item())
            row[f"qd_p95_{jn}"] = float(qdj_p95_j[j].item())
            row[f"qd_max_{jn}"] = float(qdj_max_j[j].item())

        rows.append(row)
        print(
            f"[{tag}] cmd={actual_cmd}  vx={row['vx_mean']:+.3f} vy={row['vy_mean']:+.3f} "
            f"wz={row['yawrate_mean']:+.3f} stat={row['stationary_rate']} fall={row['fall_rate']:.3f} "
            f"surv={n_surv}/{N}"
        )

    env.close()
    write_outputs(rows, foot_names)


def write_outputs(rows, foot_names):
    it = "".join(ch for ch in args_cli.checkpoint if ch.isdigit()) or "unknown"
    os.makedirs(args_cli.out_dir, exist_ok=True)
    base = os.path.join(args_cli.out_dir, f"eval_{args_cli.load_run}_{it}")

    fields = list(rows[0].keys())
    with open(base + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    metrics = [
        ("v_x mean [m/s]", "vx_mean", "{:+.3f}"),
        ("v_y mean [m/s]", "vy_mean", "{:+.3f}"),
        ("|v_y - cmd_y| mean", "vy_err_mean", "{:.3f}"),
        ("yaw rate mean [rad/s]", "yawrate_mean", "{:+.3f}"),
        ("heading drift 10s [deg]", "heading_drift_deg", "{:+.1f}"),
        ("travel dir [deg]", "travel_dir_deg", "{:+.1f}"),
        ("stationary rate", "stationary_rate", "{:.3f}"),
        ("fall rate", "fall_rate", "{:.3f}"),
        ("LR_HR mean [rad]", "LR_HR_mean_rad", "{:+.4f}"),
        ("LL_HR mean [rad]", "LL_HR_mean_rad", "{:+.4f}"),
    ]
    for fname in foot_names:
        metrics.append((f"air time {fname} [s]", f"air_time_{fname}", "{:.3f}"))
    for fname in foot_names:
        metrics.append((f"swing apex {fname} [cm] (ref)", f"swing_apex_cm_{fname}", "{:.2f}"))
    metrics.append(("landings per s (ref)", "landings_per_s", "{:.2f}"))
    metrics += [
        ("|qd| p95 [rad/s]", "qd_p95", "{:.2f}"),
        ("torque >=95% limit", "torque_sat_frac", "{:.3f}"),
        ("survivors", "n_survivors", "{:d}"),
    ]

    def fmt(v, spec):
        if isinstance(v, float) and math.isnan(v):
            return "-"
        try:
            return spec.format(v)
        except (ValueError, TypeError):
            return str(v)

    lines = [
        f"# eval {args_cli.load_run} @ {args_cli.checkpoint}",
        "",
        f"- num_envs: {rows[0]['n_envs']}, warmup {WARMUP_S}s discarded, {MEASURE_S}s measured, seed {args_cli.seed}",
        "- flat ground (all-flat generated terrain), obs noise OFF, push/disturbance OFF, no command resampling,",
        "  heading_command=False, rel_standing_envs=0, domain randomisation neutralised.",
        "- velocities are base COM velocity rotated into the yaw-only base frame.",
        "",
        "| command (vx,vy,wz) | " + " | ".join(f"{r['scenario']} ({r['cmd_vx']},{r['cmd_vy']},{r['cmd_wz']})" for r in rows) + " |",
        "|---|" + "---|" * len(rows),
        "| command actually seen | "
        + " | ".join(f"({r['cmd_seen_vx']},{r['cmd_seen_vy']},{r['cmd_seen_wz']})" for r in rows)
        + " |",
    ]
    for label, key, spec in metrics:
        lines.append("| " + label + " | " + " | ".join(fmt(r.get(key, float("nan")), spec) for r in rows) + " |")
    lines.append("")

    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[measure_crab] wrote {base}.md and {base}.csv")


if __name__ == "__main__":
    main()
    simulation_app.close()
