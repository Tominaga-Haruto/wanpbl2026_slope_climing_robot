"""T0-2: statistics of the commands actually sampled during training (same command cfg as
training, rel_heading_envs=0.5), action=0, 64 env, 1000 steps, recorded every step.
Splits by is_heading_env vs direct-ang_vel_z env.
"""

import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--seed", type=int, default=1)
parser.add_argument("--n_steps", type=int, default=1000)
parser.add_argument("--rel_turn_in_place_envs", type=float, default=0.0)
parser.add_argument("--rel_translate_only_envs", type=float, default=0.0)
parser.add_argument("--out", type=str, default=r"D:\Tominaga\slope-climbing-robot\tools\logs\T0_2_command_stats.md")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True
sys.argv = [sys.argv[0]]

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
import torch  # noqa: E402

from isaaclab.envs import ManagerBasedRLEnv  # noqa: E402

import isaaclab_tasks  # noqa: F401,E402
import skyentific_poclegs  # noqa: F401,E402
from skyentific_poclegs.tasks.locomotion.velocity.config.skyentific_poclegs.rough_env_cfg import (  # noqa: E402
    SkyentificPoclegsRoughEnvCfg,
)


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"
    cfg = SkyentificPoclegsRoughEnvCfg()
    cfg.scene.num_envs = args_cli.num_envs
    cfg.seed = args_cli.seed
    cfg.sim.device = device
    # match G_real_peak's actual launch-line override (not the code default of 1.0)
    cfg.commands.base_velocity.rel_heading_envs = 0.5
    cfg.commands.base_velocity.rel_turn_in_place_envs = args_cli.rel_turn_in_place_envs
    cfg.commands.base_velocity.rel_translate_only_envs = args_cli.rel_translate_only_envs

    env = ManagerBasedRLEnv(cfg=cfg)
    cmd_term = env.unwrapped.command_manager.get_term("base_velocity")
    n_j = env.scene["robot"].num_joints

    lin_thresh = 0.1
    ang_thresh = 0.3

    counts = {
        "heading": {"turn_in_place": 0, "standing": 0, "walk_turn": 0, "translate_only": 0, "total": 0},
        "direct": {"turn_in_place": 0, "standing": 0, "walk_turn": 0, "translate_only": 0, "total": 0},
    }

    with torch.inference_mode():
        env.reset()
        zero_action = torch.zeros((args_cli.num_envs, n_j), device=device)
        for _ in range(args_cli.n_steps):
            env.step(zero_action)
            cmd = cmd_term.command  # (N, 3): lin_vel_x, lin_vel_y, ang_vel_z
            lin_mag = torch.norm(cmd[:, :2], dim=1)
            ang_mag = cmd[:, 2].abs()
            is_heading = cmd_term.is_heading_env

            for group_name, mask in (("heading", is_heading), ("direct", ~is_heading)):
                g_lin = lin_mag[mask]
                g_ang = ang_mag[mask]
                turn_in_place = (g_lin < lin_thresh) & (g_ang > ang_thresh)
                standing = (g_lin < lin_thresh) & (g_ang <= ang_thresh)
                walk_turn = (g_lin >= lin_thresh) & (g_ang > ang_thresh)
                translate_only = (g_lin >= lin_thresh) & (g_ang <= ang_thresh)
                counts[group_name]["turn_in_place"] += int(turn_in_place.sum().item())
                counts[group_name]["standing"] += int(standing.sum().item())
                counts[group_name]["walk_turn"] += int(walk_turn.sum().item())
                counts[group_name]["translate_only"] += int(translate_only.sum().item())
                counts[group_name]["total"] += int(mask.sum().item())

    env.close()

    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    emit(f"# T0-2: 学習時の指令の組み合わせ統計 (action=0, 64env, 1000step, rel_heading_envs=0.5, "
         f"rel_turn_in_place_envs={args_cli.rel_turn_in_place_envs}, rel_translate_only_envs={args_cli.rel_translate_only_envs})\n")
    emit(f"- 閾値: \\|(vx,vy)\\| < {lin_thresh} を「並進なし」、\\|wz\\| > {ang_thresh} を「大きな旋回指令」\n")
    emit("| グループ | サンプル数 | その場旋回(並進小&旋回大) | 立ち止まり(並進小&旋回小) | 歩きながら旋回(並進大&旋回大) | 並進だけ(並進大&旋回小) |")
    emit("|---|---|---|---|---|---|")
    grand_total = 0
    for group_name in ("heading", "direct"):
        c = counts[group_name]
        total = c["total"]
        grand_total += total
        if total == 0:
            emit(f"| {group_name} | 0 | - | - | - | - |")
            continue
        emit(f"| {group_name} | {total} | {c['turn_in_place']/total*100:.2f}% | "
             f"{c['standing']/total*100:.2f}% | {c['walk_turn']/total*100:.2f}% | {c['translate_only']/total*100:.2f}% |")
    c_all = {k: counts["heading"][k] + counts["direct"][k] for k in counts["heading"]}
    total_all = c_all["total"]
    emit(f"| **全体** | {total_all} | {c_all['turn_in_place']/total_all*100:.2f}% | "
         f"{c_all['standing']/total_all*100:.2f}% | {c_all['walk_turn']/total_all*100:.2f}% | "
         f"{c_all['translate_only']/total_all*100:.2f}% |")

    with open(args_cli.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[t0_2] wrote {args_cli.out}")


if __name__ == "__main__":
    main()
    simulation_app.close()
