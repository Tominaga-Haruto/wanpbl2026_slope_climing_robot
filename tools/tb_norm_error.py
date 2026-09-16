"""Normalised velocity-tracking error across runs.

Isaac Lab accumulates `error_vel_xy` as  sum_t ||cmd - v|| / (resampling_time_range[1] / step_dt)
over an episode (velocity_command.py:114-124), so the logged value scales with episode length.
The per-step mean error is therefore  raw * (max_command_step) / episode_length_steps,
with max_command_step = 10.0 / 0.02 = 500 for this config.
"""

import argparse
import os

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

MAX_COMMAND_STEP = 500.0
TAGS = ("Metrics/base_velocity/error_vel_xy", "Metrics/base_velocity/error_vel_yaw")
LEN_TAG = "Train/mean_episode_length"


def series(acc, tag):
    try:
        return {e.step: e.value for e in acc.Scalars(tag)}
    except KeyError:
        return {}


def at(s, it):
    if not s:
        return None
    cands = [k for k in s if k <= it]
    k = max(cands) if cands else min(s)
    return k, s[k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="label=path pairs")
    ap.add_argument("--iters", type=int, nargs="*", default=[500, 1000, 1600, 2000, 2999])
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    data = {}
    for spec in args.runs:
        label, path = spec.split("=", 1)
        acc = EventAccumulator(path, size_guidance={"scalars": 0})
        acc.Reload()
        data[label] = {t: series(acc, t) for t in TAGS + (LEN_TAG,)}

    lines = [
        "# normalised velocity tracking error",
        "",
        f"normalised = raw x {MAX_COMMAND_STEP:.0f} / Train/mean_episode_length  (per-step mean error)",
        "",
    ]
    for tag in TAGS:
        short = tag.rsplit("/", 1)[1]
        lines.append(f"## {short}")
        lines.append("")
        lines.append("| run | " + " | ".join(f"iter {i}" for i in args.iters) + " |")
        lines.append("|---|" + "---|" * len(args.iters))
        for label, d in data.items():
            cells = []
            for it in args.iters:
                r = at(d[tag], it)
                L = at(d[LEN_TAG], it)
                if r is None or L is None or L[1] == 0:
                    cells.append("-")
                    continue
                step, raw = r
                norm = raw * MAX_COMMAND_STEP / L[1]
                mark = "" if step == it else f"@{step}"
                cells.append(f"{norm:.3f} ({raw:.3f}){mark}")
            lines.append(f"| {label} | " + " | ".join(cells) + " |")
        lines.append("")
        lines.append("cells show `normalised (raw)`.")
        lines.append("")

    lines.append("## Train/mean_episode_length (steps, max 1000)")
    lines.append("")
    lines.append("| run | " + " | ".join(f"iter {i}" for i in args.iters) + " |")
    lines.append("|---|" + "---|" * len(args.iters))
    for label, d in data.items():
        cells = []
        for it in args.iters:
            L = at(d[LEN_TAG], it)
            cells.append("-" if L is None else f"{L[1]:.1f}")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("")

    text = "\n".join(lines)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
