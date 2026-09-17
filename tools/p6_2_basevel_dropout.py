"""P6-2: how long can the policy tolerate a lost base_lin_vel signal (e.g. a T265 dropout)?

Protocol: run S1 (0.5,0,0) normally for 3s after the usual 2s warmup, then corrupt the policy's
base_lin_vel slice (assumed obs[...,0:3]) for a fixed duration D in {0.1,0.2,0.5,1.0,2.0}s using
either (a) zero or (b) hold-last-value, then restore the true value. Report the fall rate measured
over the 3s window starting at dropout onset (regardless of D, so recovery time after restoration
is included). Physics/other observation terms are untouched; only the observed base_lin_vel is
corrupted, same mechanism as measure_crab.py's --basevel_mode.
"""

import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--load_run", type=str, required=True)
parser.add_argument("--checkpoint", type=str, required=True)
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--noise_std_type", type=str, default="log", choices=["scalar", "log"])
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--experiment", type=str, default="skyentific_poclegs_rough")
parser.add_argument("--log_root", type=str, default=r"D:\Tominaga\IsaacLab\logs\rsl_rl")
parser.add_argument("--durations", type=str, default="0.1,0.2,0.5,1.0,2.0", help="comma-separated dropout durations [s]")
parser.add_argument("--out", type=str, required=True)
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
STEP_DT = 0.02  # 20ms control period (sim.dt=0.005 * decimation=4)


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


def apply_trained_obs_overrides(env_cfg, run_dir):
    env_yaml = os.path.join(run_dir, "params", "env.yaml")
    if not os.path.isfile(env_yaml):
        return
    with open(env_yaml, "r", encoding="utf-8") as f:
        saved = yaml.unsafe_load(f)
    saved_obs = saved.get("observations", {}).get("policy", {})
    if saved_obs.get("base_lin_vel") is None:
        env_cfg.observations.policy.base_lin_vel = None


def apply_trained_noise_std_type(agent_cfg, run_dir):
    """Read the actor's actually-trained distribution std parameterization ('log' vs 'scalar') back
    out of params/agent.yaml instead of trusting the launch line / CLI default (see measure_crab.py's
    same-named helper for the H_gainDR incident this guards against)."""
    agent_yaml = os.path.join(run_dir, "params", "agent.yaml")
    if not os.path.isfile(agent_yaml):
        return
    with open(agent_yaml, "r", encoding="utf-8") as f:
        saved = yaml.unsafe_load(f)
    std_type = (saved.get("actor") or {}).get("distribution_cfg", {}).get("std_type")
    if std_type is not None:
        agent_cfg.policy.noise_std_type = std_type


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"
    run_dir = os.path.join(args_cli.log_root, args_cli.experiment, args_cli.load_run)
    resume_path = os.path.join(run_dir, args_cli.checkpoint)

    env_cfg = build_env_cfg(args_cli.num_envs, args_cli.seed, device)
    apply_trained_actuator_params(env_cfg, run_dir)
    apply_trained_obs_overrides(env_cfg, run_dir)
    if env_cfg.observations.policy.base_lin_vel is None:
        raise RuntimeError(
            "This run has base_lin_vel dropped from observations already (H_nolinvel-style) -- "
            "P6-2's dropout probe assumes obs[...,0:3] is base_lin_vel and is not meaningful here."
        )

    agent_cfg = SkyentificPoclegsRoughPPORunnerCfg()
    agent_cfg.seed = args_cli.seed
    agent_cfg.device = device
    agent_cfg.policy.noise_std_type = args_cli.noise_std_type
    apply_trained_noise_std_type(agent_cfg, run_dir)
    agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, INSTALLED_VERSION)

    env = ManagerBasedRLEnv(cfg=env_cfg)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
    runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    runner.load(handle_deprecated_rsl_rl_checkpoint(resume_path, INSTALLED_VERSION))
    policy = runner.get_inference_policy(device=device)

    cmd_term = env.unwrapped.command_manager.get_term("base_velocity")
    durations = [float(x) for x in args_cli.durations.split(",")]

    def set_cmd():
        cmd_term.vel_command_b[:, 0] = 0.5
        cmd_term.vel_command_b[:, 1] = 0.0
        cmd_term.vel_command_b[:, 2] = 0.0
        cmd_term.is_standing_env[:] = False

    n_warm = int(round(2.0 / STEP_DT))
    n_pre = int(round(3.0 / STEP_DT))
    n_window = int(round(3.0 / STEP_DT))

    results = []
    with torch.inference_mode():
        for mode in ("zero", "hold"):
            for dur in durations:
                res = env.reset()
                obs = res[0] if isinstance(res, tuple) else res
                set_cmd()
                for _ in range(n_warm):
                    obs, _, dones, _ = env.step(policy(obs))
                    policy.reset(dones)
                    set_cmd()
                for _ in range(n_pre):
                    obs, _, dones, _ = env.step(policy(obs))
                    policy.reset(dones)
                    set_cmd()

                n_dropout = int(round(dur / STEP_DT))
                held = obs["policy"][:, 0:3].clone()
                ever_done = torch.zeros(args_cli.num_envs, dtype=torch.bool, device=device)
                steps_done = 0
                for _ in range(n_dropout):
                    if mode == "zero":
                        obs["policy"][:, 0:3] = 0.0
                    else:
                        obs["policy"][:, 0:3] = held
                    obs, _, dones, _ = env.step(policy(obs))
                    policy.reset(dones)
                    set_cmd()
                    ever_done |= dones.to(torch.bool)
                    steps_done += 1
                for _ in range(n_window - steps_done):
                    obs, _, dones, _ = env.step(policy(obs))
                    policy.reset(dones)
                    set_cmd()
                    ever_done |= dones.to(torch.bool)

                fall_rate = float(ever_done.float().mean().item())
                print(f"[p6_2] mode={mode} duration={dur}s fall_rate(3s window)={fall_rate:.4f}")
                results.append((mode, dur, fall_rate))

    env.close()
    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    emit(f"# P6-2: base_lin_vel dropout tolerance -- {args_cli.load_run} @ {args_cli.checkpoint}\n")
    emit(f"- num_envs={args_cli.num_envs}, S1(0.5,0,0), warmup 2s + normal 3s, then dropout, "
         f"fall rate measured over the 3s window starting at dropout onset\n")
    emit("| mode | duration[s] | fall_rate(3s window) |")
    emit("|---|---|---|")
    for mode, dur, fr in results:
        emit(f"| {mode} | {dur} | {fr:.4f} |")

    with open(args_cli.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[p6_2] wrote {args_cli.out}")


if __name__ == "__main__":
    main()
    simulation_app.close()
