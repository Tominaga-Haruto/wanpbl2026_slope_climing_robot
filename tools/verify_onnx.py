"""P2-3: verify the exported ONNX policy against the torch policy used by play.py's own inference
path (same runner.get_inference_policy()), on random observations and on real observations collected
from an actual evaluation rollout (same protocol as measure_crab.py, S1).

Runs its own tiny env instance (flat ground, neutral randomisation) purely to collect 200 real
observation vectors; does not touch the training run's checkpoint/config.
"""

import argparse
import sys

# import onnx (and its protobuf runtime) before Kit ever starts -- otherwise Kit's own bundled
# protobuf appears to get grabbed first and onnx's import crashes with a native access violation.
# Same class of "whoever initializes shared native state first wins" issue as the h5py DLL race
# documented in _preload_h5py_and_run.py (2026-09-16).
import onnx  # noqa: E402,F401
import onnx.reference  # noqa: E402,F401

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--load_run", type=str, required=True)
parser.add_argument("--checkpoint", type=str, required=True)
parser.add_argument("--onnx_path", type=str, required=True)
parser.add_argument("--noise_std_type", type=str, default="log", choices=["scalar", "log"])
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--num_envs", type=int, default=16)
parser.add_argument("--n_random", type=int, default=200)
parser.add_argument("--experiment", type=str, default="skyentific_poclegs_rough")
parser.add_argument("--log_root", type=str, default=r"D:\Tominaga\IsaacLab\logs\rsl_rl")
parser.add_argument("--out", type=str, default=r"D:\Tominaga\slope-climbing-robot\tools\logs\verify_onnx.md")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True
sys.argv = [sys.argv[0]]

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
import os  # noqa: E402
import importlib.metadata as metadata  # noqa: E402

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


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"

    onnx_model = onnx.load(args_cli.onnx_path)
    onnx.checker.check_model(onnx_model)
    session = onnx.reference.ReferenceEvaluator(onnx_model)
    obs_dim = onnx_model.graph.input[0].type.tensor_type.shape.dim[1].dim_value
    act_dim = onnx_model.graph.output[0].type.tensor_type.shape.dim[1].dim_value

    env_cfg = build_env_cfg(args_cli.num_envs, args_cli.seed, device)
    agent_cfg = SkyentificPoclegsRoughPPORunnerCfg()
    agent_cfg.seed = args_cli.seed
    agent_cfg.device = device
    agent_cfg.policy.noise_std_type = args_cli.noise_std_type
    agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, INSTALLED_VERSION)

    run_dir = os.path.join(args_cli.log_root, args_cli.experiment, args_cli.load_run)
    resume_path = os.path.join(run_dir, args_cli.checkpoint)
    apply_trained_actuator_params(env_cfg, run_dir)

    env = ManagerBasedRLEnv(cfg=env_cfg)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
    runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    runner.load(handle_deprecated_rsl_rl_checkpoint(resume_path, INSTALLED_VERSION))
    policy = runner.get_inference_policy(device=device)

    def torch_infer(obs_np):
        # MLPModel expects a dict/TensorDict with a "policy" key (matches the observation group
        # name), not a raw flat tensor -- RslRlVecEnvWrapper.reset()/step() wrap it the same way.
        with torch.inference_mode():
            t = torch.as_tensor(obs_np, dtype=torch.float32, device=device)
            return policy({"policy": t}).cpu().numpy()

    def onnx_infer(obs_np):
        out = []
        for row in obs_np:
            (a,) = session.run(None, {"obs": row[None, :].astype(np.float32)})
            out.append(a[0])
        return np.stack(out)

    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    emit("# ONNX verification")
    emit("")
    emit(f"- onnx model: `{args_cli.onnx_path}`")
    emit(f"- onnx obs_dim={obs_dim}, act_dim={act_dim}")

    # -- random observations --------------------------------------------------
    rng = np.random.default_rng(args_cli.seed)
    obs_random = rng.uniform(-3.0, 3.0, size=(args_cli.n_random, obs_dim)).astype(np.float32)
    torch_out_r = torch_infer(obs_random)
    onnx_out_r = onnx_infer(obs_random)
    err_r = np.abs(torch_out_r - onnx_out_r).max()
    emit(f"- random obs (n={args_cli.n_random}, uniform[-3,3]): max abs error = {err_r:.3e}")

    # -- real observations from an actual rollout (S1: 0.5,0,0) ----------------
    cmd_term = env.unwrapped.command_manager.get_term("base_velocity")
    with torch.inference_mode():
        res = env.reset()
        obs = res[0] if isinstance(res, tuple) else res
        cmd_term.vel_command_b[:, 0] = 0.5
        cmd_term.vel_command_b[:, 1] = 0.0
        cmd_term.vel_command_b[:, 2] = 0.0
        cmd_term.is_standing_env[:] = False
        real_obs_chunks = []
        steps_needed = -(-args_cli.n_random // args_cli.num_envs)  # ceil
        for _ in range(steps_needed):
            real_obs_chunks.append(obs["policy"].cpu().numpy().copy())
            obs, _, dones, _ = env.step(policy(obs))
            policy.reset(dones)
    obs_real = np.concatenate(real_obs_chunks, axis=0)[: args_cli.n_random]
    torch_out_real = torch_infer(obs_real)
    onnx_out_real = onnx_infer(obs_real)
    err_real = np.abs(torch_out_real - onnx_out_real).max()
    emit(f"- real eval obs (n={obs_real.shape[0]}, S1 rollout): max abs error = {err_real:.3e}")

    threshold = 1e-4
    verdict = "PASS" if max(err_r, err_real) <= threshold else "FAIL"
    emit("")
    emit(f"**判定 (閾値 {threshold:.0e}): {verdict}**")

    env.close()
    os.makedirs(os.path.dirname(args_cli.out), exist_ok=True)
    with open(args_cli.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[verify_onnx] wrote {args_cli.out}")


if __name__ == "__main__":
    main()
    simulation_app.close()
