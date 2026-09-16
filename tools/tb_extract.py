"""Pull selected scalars out of an rsl_rl TensorBoard event file at given iterations."""

import argparse
import os
import sys

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

DEFAULT_ITERS = [500, 1000, 1600]
PREFIXES = ("Metrics/", "Episode_Reward/", "Episode_Termination/", "Curriculum/", "Policy/")
EXTRA_SUBSTR = ("Train/mean_episode_length", "Train/mean_reward")


def wanted(tag: str) -> bool:
    if tag.endswith("/time"):
        return False
    if tag.startswith(PREFIXES):
        return True
    return any(s in tag for s in EXTRA_SUBSTR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--iters", type=int, nargs="*", default=DEFAULT_ITERS)
    ap.add_argument("--out", type=str, default=None)
    ap.add_argument("--list", action="store_true", help="just print all available tags")
    args = ap.parse_args()

    acc = EventAccumulator(args.run_dir, size_guidance={"scalars": 0})
    acc.Reload()
    tags = acc.Tags()["scalars"]

    if args.list:
        for t in sorted(tags):
            print(t)
        return

    sel = sorted(t for t in tags if wanted(t))
    if not sel:
        print("no matching tags; available:", sorted(tags), file=sys.stderr)
        return

    table = {}
    max_step = 0
    for t in sel:
        series = {e.step: e.value for e in acc.Scalars(t)}
        if series:
            max_step = max(max_step, max(series))
        row = []
        for it in args.iters:
            if not series:
                row.append(None)
                continue
            # nearest available step at or below the requested iteration
            cands = [s for s in series if s <= it]
            k = max(cands) if cands else min(series)
            row.append((k, series[k]))
        table[t] = row

    lines = [f"# tensorboard scalars: {os.path.basename(args.run_dir)}", "",
             f"last logged step: {max_step}", "",
             "| tag | " + " | ".join(f"iter {i}" for i in args.iters) + " |",
             "|---|" + "---|" * len(args.iters)]
    for t in sel:
        cells = []
        for cell in table[t]:
            if cell is None:
                cells.append("-")
            else:
                step, val = cell
                mark = "" if step == args.iters[len(cells)] else f" @{step}"
                cells.append(f"{val:.4g}{mark}")
        lines.append(f"| {t} | " + " | ".join(cells) + " |")
    text = "\n".join(lines) + "\n"
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
