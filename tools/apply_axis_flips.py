"""Flip <axis xyz="0 0 1"/> to "0 0 -1" for named joints, via XML attribute
edit (not string replace). Writes to a new output path, optionally taking a
backup of the source first.

Usage:
    python apply_axis_flips.py <urdf_path> --flip JOINT1 JOINT2 ... --out <out_path> [--backup <bak_path>]
"""
import argparse
import shutil
import xml.etree.ElementTree as ET


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf_path")
    ap.add_argument("--flip", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--backup", default=None)
    args = ap.parse_args()

    if args.backup:
        shutil.copy(args.urdf_path, args.backup)
        print(f"Backup written to: {args.backup}")

    tree = ET.parse(args.urdf_path)
    root = tree.getroot()

    flipped = []
    for j in root.findall("joint"):
        name = j.get("name")
        if name in args.flip:
            axis_el = j.find("axis")
            old = axis_el.get("xyz")
            vals = [float(v) for v in old.split()]
            new_vals = [-v if abs(v) > 1e-9 else v for v in vals]
            new_str = f"{new_vals[0]:.10g} {new_vals[1]:.10g} {new_vals[2]:.10g}"
            axis_el.set("xyz", new_str)
            flipped.append((name, old, new_str))

    print(f"Flipped {len(flipped)} joints:")
    for name, old, new in flipped:
        print(f"  {name}: {old} -> {new}")

    missing = set(args.flip) - {n for n, _, _ in flipped}
    if missing:
        print(f"WARNING: requested joints not found: {missing}")

    ET.indent(tree, space="  ")
    tree.write(args.out, xml_declaration=True, encoding="UTF-8")
    print(f"Written to: {args.out}")


if __name__ == "__main__":
    main()
