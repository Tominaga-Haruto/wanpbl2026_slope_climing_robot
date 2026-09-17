"""P5-4: golden deployment-verification dataset. Runs S1 (0.5,0,0) for 1 env, 500 steps, and saves
per-step: each observation term (named, with its dim range -- this env's obs terms have no configured
scale/clip, so the "physical" and "scaled" values are identical and both come straight from the
ObservationManager's own output with noise disabled), the raw policy action, the resulting joint
target angle (default + 0.5*action), joint pos/vel, applied/computed torque, and the velocity command.
"""

import argparse
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--load_run", type=str, required=True)
parser.add_argument("--checkpoint", type=str, required=True)
parser.add_argument("--noise_std_type", type=str, default="log", choices=["scalar", "log"])
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--n_steps", type=int, default=500)
parser.add_argument("--experiment", type=str, default="skyentific_poclegs_rough")
parser.add_argument("--log_root", type=str, default=r"D:\Tominaga\IsaacLab\logs\rsl_rl")
parser.add_argument("--out", type=str, required=True, help="output .npz path")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True
sys.argv = [sys.argv[0]]

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
import importlib.metadata as metadata  # noqa: E402
import os  # noqa: E402

import numpy as np  # noqa: E402
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


def build_env_cfg(seed, device):
    cfg = SkyentificPoclegsRoughEnvCfg()
    cfg.scene.num_envs = 1
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
    """H_nolinvel's checkpoint expects base_lin_vel dropped; detect and reapply from env.yaml."""
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
    env_cfg = build_env_cfg(args_cli.seed, device)

    run_dir = os.path.join(args_cli.log_root, args_cli.experiment, args_cli.load_run)
    resume_path = os.path.join(run_dir, args_cli.checkpoint)

    agent_cfg = SkyentificPoclegsRoughPPORunnerCfg()
    agent_cfg.seed = args_cli.seed
    agent_cfg.device = device
    agent_cfg.policy.noise_std_type = args_cli.noise_std_type
    apply_trained_noise_std_type(agent_cfg, run_dir)
    agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, INSTALLED_VERSION)

    apply_trained_actuator_params(env_cfg, run_dir)
    apply_trained_obs_overrides(env_cfg, run_dir)

    env = ManagerBasedRLEnv(cfg=env_cfg)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
    runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    runner.load(handle_deprecated_rsl_rl_checkpoint(resume_path, INSTALLED_VERSION))
    policy = runner.get_inference_policy(device=device)

    uenv = env.unwrapped
    robot = uenv.scene["robot"]
    om = uenv.observation_manager
    policy_group = om.active_terms["policy"]
    dims = om.group_obs_term_dim["policy"]
    joint_names = list(robot.joint_names)
    default_pos = robot.data.default_joint_pos[0].clone()
    action_term = uenv.action_manager.get_term("joint_pos")
    action_scale = action_term._scale
    action_scale = action_scale[0].cpu().numpy() if isinstance(action_scale, torch.Tensor) else action_scale
    cmd_term = uenv.command_manager.get_term("base_velocity")

    term_bounds = []
    off = 0
    for name, d in zip(policy_group, dims):
        n = 1
        for x in d:
            n *= x
        term_bounds.append((name, off, off + n))
        off += n
    total_dim = off

    n_steps = args_cli.n_steps
    n_j = robot.num_joints
    obs_flat = np.zeros((n_steps, total_dim), dtype=np.float32)
    action_raw = np.zeros((n_steps, n_j), dtype=np.float32)
    joint_target = np.zeros((n_steps, n_j), dtype=np.float32)
    joint_pos = np.zeros((n_steps, n_j), dtype=np.float32)
    joint_vel = np.zeros((n_steps, n_j), dtype=np.float32)
    applied_torque = np.zeros((n_steps, n_j), dtype=np.float32)
    computed_torque = np.zeros((n_steps, n_j), dtype=np.float32)
    command = np.zeros((n_steps, 3), dtype=np.float32)

    with torch.inference_mode():
        res = env.reset()
        obs = res[0] if isinstance(res, tuple) else res
        cmd_term.vel_command_b[:, 0] = 0.5
        cmd_term.vel_command_b[:, 1] = 0.0
        cmd_term.vel_command_b[:, 2] = 0.0
        cmd_term.is_standing_env[:] = False
        for _ in range(100):  # 2s warmup, same as measure_crab
            obs, _, dones, _ = env.step(policy(obs))
            policy.reset(dones)
            cmd_term.vel_command_b[:, 0] = 0.5
            cmd_term.vel_command_b[:, 1] = 0.0
            cmd_term.vel_command_b[:, 2] = 0.0
        for t in range(n_steps):
            obs_flat[t] = obs["policy"][0].cpu().numpy()
            a = policy(obs)
            action_raw[t] = a[0].cpu().numpy()
            joint_target[t] = (default_pos + torch.as_tensor(action_scale, device=device) * a[0]).cpu().numpy()
            obs, _, dones, _ = env.step(a)
            policy.reset(dones)
            cmd_term.vel_command_b[:, 0] = 0.5
            cmd_term.vel_command_b[:, 1] = 0.0
            cmd_term.vel_command_b[:, 2] = 0.0
            joint_pos[t] = robot.data.joint_pos[0].cpu().numpy()
            joint_vel[t] = robot.data.joint_vel[0].cpu().numpy()
            applied_torque[t] = robot.data.applied_torque[0].cpu().numpy()
            computed_torque[t] = robot.data.computed_torque[0].cpu().numpy()
            command[t] = cmd_term.command[0].cpu().numpy()

    save_kwargs = dict(
        obs_flat=obs_flat, action_raw=action_raw, joint_target=joint_target,
        joint_pos=joint_pos, joint_vel=joint_vel, applied_torque=applied_torque,
        computed_torque=computed_torque, command=command,
        joint_names=np.array(joint_names), action_scale=np.asarray(action_scale),
        default_joint_pos=default_pos.cpu().numpy(),
    )
    for name, lo, hi in term_bounds:
        save_kwargs[f"obs_term_{name}"] = obs_flat[:, lo:hi]
    np.savez(args_cli.out, **save_kwargs)

    md_path = args_cli.out.rsplit(".", 1)[0] + ".md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# golden dataset: {args_cli.load_run} @ {args_cli.checkpoint}\n\n")
        f.write(f"- S1 (0.5,0,0), 1 env, {n_steps} steps (after 100-step/2s warmup, same protocol as measure_crab.py)\n")
        f.write(f"- joint_names order: {joint_names}\n")
        f.write(f"- total obs dim: {total_dim}\n\n")
        f.write("## 観測項の並び（obs_flat / obs_term_<name> のスライス境界）\n\n")
        f.write("この環境設定では観測項にscale/clipが設定されていない（obs_contract.md参照）ため、\n")
        f.write("obs_flat / obs_term_* に保存した値は「scale・clip前の物理値」と「scale後の値」の両方を兼ねる\n")
        f.write("（noise はeval時にOFFなので、physical値=policyに入る値、そのままかつ同一）。\n\n")
        f.write("| # | 項名 | 次元範囲 [lo:hi) | 次元数 |\n|---|---|---|---|\n")
        for name, lo, hi in term_bounds:
            f.write(f"| | {name} | [{lo}:{hi}) | {hi - lo} |\n")
        f.write(f"\n- action_scale: {list(np.asarray(action_scale).tolist())}\n")
        f.write(f"- default_joint_pos: {default_pos.cpu().numpy().tolist()}\n")
        f.write("- joint_target = default_joint_pos + action_scale * action_raw\n")
    print(f"[dump_golden] wrote {args_cli.out} and {md_path}")
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
