"""Dump SkyentificPoclegsRoughEnvCfg() with ZERO Hydra overrides, using the exact same dump_yaml
mechanism train.py itself uses (isaaclab.utils.io.dump_yaml), so it is directly diff-able against a
real run's params/env.yaml. Used to find every override actually applied at launch time for a given
run (2026-09-17, exp06).
"""

import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_envs", type=int, default=4096)
parser.add_argument("--seed", type=int, default=1)
parser.add_argument("--out", type=str, required=True)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True
sys.argv = [sys.argv[0]]

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
import os  # noqa: E402

from isaaclab.utils.io import dump_yaml  # noqa: E402

import isaaclab_tasks  # noqa: F401,E402
import skyentific_poclegs  # noqa: F401,E402
from skyentific_poclegs.tasks.locomotion.velocity.config.skyentific_poclegs.rough_env_cfg import (  # noqa: E402
    SkyentificPoclegsRoughEnvCfg,
)


def main():
    cfg = SkyentificPoclegsRoughEnvCfg()
    cfg.scene.num_envs = args_cli.num_envs
    cfg.seed = args_cli.seed
    os.makedirs(os.path.dirname(args_cli.out), exist_ok=True)
    dump_yaml(args_cli.out, cfg)
    print(f"[dump_baseline_env_yaml] wrote {args_cli.out}")


if __name__ == "__main__":
    main()
    simulation_app.close()
