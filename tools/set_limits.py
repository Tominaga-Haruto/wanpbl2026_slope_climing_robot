"""Set joint <limit velocity=.../ effort=.../> per suffix group, via XML
attribute edit. lower/upper are left untouched.

Usage:
    python set_limits.py <urdf_path> --in-place
"""
import argparse
import shutil
import xml.etree.ElementTree as ET

VELOCITY = {"HR": 23, "HAA": 15, "HFE": 20, "KFE": 20, "FFE": 23}
EFFORT = {"HR": 24, "HAA": 30, "HFE": 30, "KFE": 30, "FFE": 20}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf_path")
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("--backup", default=None)
    args = ap.parse_args()

    if args.backup:
        shutil.copy(args.urdf_path, args.backup)
        print(f"Backup written to: {args.backup}")

    tree = ET.parse(args.urdf_path)
    root = tree.getroot()

    print(f"{'joint':10s} {'old_velocity':>12s} {'new_velocity':>12s} {'old_effort':>10s} {'new_effort':>10s}")
    for j in root.findall("joint"):
        name = j.get("name")
        suffix = name.split("_")[1]
        if suffix not in VELOCITY:
            continue
        limit_el = j.find("limit")
        old_v = limit_el.get("velocity")
        old_e = limit_el.get("effort")
        new_v = str(VELOCITY[suffix])
        new_e = str(EFFORT[suffix])
        limit_el.set("velocity", new_v)
        limit_el.set("effort", new_e)
        print(f"{name:10s} {old_v:>12s} {new_v:>12s} {old_e:>10s} {new_e:>10s}")

    ET.indent(tree, space="  ")
    out_path = args.urdf_path
    tree.write(out_path, xml_declaration=True, encoding="UTF-8")
    print(f"\nWritten to: {out_path}")


if __name__ == "__main__":
    main()
