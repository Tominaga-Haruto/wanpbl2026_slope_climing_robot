"""Dump the observation/action contract of the trained policy for deployment.

Builds the real training env config (SkyentificPoclegsRoughEnvCfg, unmodified) with a small
number of envs, and reads the actual manager objects (no guessing from source reading alone).
Writes tools/logs/obs_contract.md.
"""

import argparse
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Dump observation/action contract.")
parser.add_argument("--num_envs", type=int, default=2)
parser.add_argument("--out", type=str, default=r"D:\Tominaga\slope-climbing-robot\tools\logs\obs_contract.md")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True
sys.argv = [sys.argv[0]]

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------

import torch  # noqa: E402

import isaaclab_tasks  # noqa: F401,E402
import skyentific_poclegs  # noqa: F401,E402
from skyentific_poclegs.tasks.locomotion.velocity.config.skyentific_poclegs.rough_env_cfg import (  # noqa: E402
    SkyentificPoclegsRoughEnvCfg,
)
from isaaclab.envs import ManagerBasedRLEnv  # noqa: E402


def main():
    cfg = SkyentificPoclegsRoughEnvCfg()
    cfg.scene.num_envs = args_cli.num_envs
    cfg.sim.device = args_cli.device if args_cli.device is not None else "cuda:0"

    env = ManagerBasedRLEnv(cfg=cfg)
    uenv = env.unwrapped
    robot = uenv.scene["robot"]

    lines = []

    def w(s=""):
        lines.append(s)

    w("# 観測・行動の契約 (obs_contract)")
    w("")
    w("`tools/dump_contract.py` が実物の manager から読み出した値。学習 cfg (`SkyentificPoclegsRoughEnvCfg`) をそのまま構築。")
    w("")

    # -- timing --------------------------------------------------------
    w("## 制御周期")
    w("")
    w(f"- sim.dt = {uenv.cfg.sim.dt}")
    w(f"- decimation = {uenv.cfg.decimation}")
    step_dt = uenv.step_dt
    w(f"- step_dt (実効) = {step_dt}")
    w(f"- 制御周期 = {1.0 / step_dt:.4f} Hz")
    w(f"- episode_length_s = {uenv.cfg.episode_length_s}")
    w("")

    # -- observation terms ----------------------------------------------
    om = uenv.observation_manager
    policy_group = om.active_terms["policy"]
    policy_cfg = uenv.cfg.observations.policy
    dims = om.group_obs_term_dim["policy"]

    w("## 観測 (policy group), 項の順番")
    w("")
    w("| # | 項 | 関数 | 次元 | 対象関節/対象 | scale | clip | 学習時ノイズ (n_min,n_max) |")
    w("|---|---|---|---|---|---|---|---|")
    total_dim = 0
    for i, name in enumerate(policy_group):
        term_cfg = getattr(policy_cfg, name)
        d = dims[i]
        d_flat = 1
        for x in d:
            d_flat *= x
        total_dim += d_flat
        func_name = getattr(term_cfg.func, "__name__", str(term_cfg.func))
        joint_names = "-"
        params = term_cfg.params or {}
        if "asset_cfg" in params:
            ac = params["asset_cfg"]
            jn = getattr(ac, "joint_names", None)
            if jn:
                # resolve actual matched + ordered joint names from the articulation
                ids, names = robot.find_joints(jn if isinstance(jn, list) else [jn], preserve_order=True)
                joint_names = ", ".join(names)
        scale = term_cfg.scale if term_cfg.scale is not None else "-"
        clip = term_cfg.clip if term_cfg.clip is not None else "-"
        noise = term_cfg.noise
        noise_s = f"({noise.n_min},{noise.n_max})" if noise is not None else "-"
        w(f"| {i} | {name} | {func_name} | {d_flat} | {joint_names} | {scale} | {clip} | {noise_s} |")
    w("")
    w(f"**合計次元 = {total_dim}**")
    w("")

    # -- action term ------------------------------------------------------
    am = uenv.action_manager
    w("## 行動 (action)")
    w("")
    for name in am.active_terms:
        term = am.get_term(name)
        term_cfg = getattr(uenv.cfg.actions, name)
        ids, names = robot.find_joints(
            term_cfg.joint_names if isinstance(term_cfg.joint_names, list) else [term_cfg.joint_names],
            preserve_order=True,
        )
        w(f"- 項名: `{name}`, クラス: `{type(term).__name__}`")
        w(f"- 関節名の並び ({len(names)}): {names}")
        scale = term._scale
        offset = term._offset
        scale_l = scale[0].tolist() if isinstance(scale, torch.Tensor) else scale
        offset_l = offset[0].tolist() if isinstance(offset, torch.Tensor) else offset
        w(f"- scale: {scale_l}")
        w(f"- offset (use_default_offset={term_cfg.use_default_offset}): {offset_l}")
        w(f"- clip: {getattr(term_cfg, 'clip', None)}")
    w("")

    # -- default joint pose ----------------------------------------------
    w("## 既定関節角 (init_state.joint_pos)")
    w("")
    w("| 関節名 | 既定角 [rad] |")
    w("|---|---|")
    default_pos = robot.data.default_joint_pos[0].tolist()
    for n, p in zip(robot.joint_names, default_pos):
        w(f"| {n} | {p:.4f} |")
    w("")

    # -- velocity_commands term content -----------------------------------
    w("## velocity_commands 観測項の中身")
    w("")
    vc_term_cfg = policy_cfg.velocity_commands
    w(f"- 関数: `{vc_term_cfg.func.__name__}`")
    w("- 中身は command_manager の `base_velocity` コマンドをそのまま: 順番は (lin_vel_x, lin_vel_y, ang_vel_z)")
    cmd_term = uenv.command_manager.get_term("base_velocity")
    cmd_cfg = uenv.cfg.commands.base_velocity
    w(f"- heading_command 有効時は heading は観測に含まれない (command テンソルは3列のまま、内部でheadingからang_vel_zへ変換される): 実測 command shape = {list(cmd_term.command.shape)}")
    w("")

    # -- command config -----------------------------------------------------
    w("## 指令の設定 (commands.base_velocity)")
    w("")
    w(f"- ranges.lin_vel_x = {cmd_cfg.ranges.lin_vel_x}")
    w(f"- ranges.lin_vel_y = {cmd_cfg.ranges.lin_vel_y}")
    w(f"- ranges.ang_vel_z = {cmd_cfg.ranges.ang_vel_z}")
    w(f"- ranges.heading = {cmd_cfg.ranges.heading}")
    w(f"- heading_command = {cmd_cfg.heading_command}")
    w(f"- heading_control_stiffness = {cmd_cfg.heading_control_stiffness}")
    w(f"- rel_heading_envs = {cmd_cfg.rel_heading_envs}")
    w(f"- rel_standing_envs = {cmd_cfg.rel_standing_envs}")
    w(f"- resampling_time_range = {cmd_cfg.resampling_time_range}")
    w("")

    with open(args_cli.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[dump_contract] wrote {args_cli.out}")
    print(f"[dump_contract] total obs dim = {total_dim}")

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
