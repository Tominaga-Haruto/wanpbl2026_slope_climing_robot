"""Rotate the base link's own coordinate frame by a Z rotation R (relabeling
axes only -- the physical robot does not move). Only touches:
  - base link's inertial/visual/collision <origin>
  - joints whose parent is base (LR_HR, LL_HR) <origin>
Everything else is untouched (child frames are relative, so unaffected).

new_origin_xyz = R @ old_xyz
new_origin_R   = R @ old_R      (rotation part, re-expressed as rpy)

Usage:
    python rotate_base_frame.py <urdf_path> --degrees 90 --in-place
"""
import argparse
import os
import shutil
import xml.etree.ElementTree as ET
import numpy as np


def rpy_to_matrix(r, p, y):
    cr, sr = np.cos(r), np.sin(r)
    cp, sp = np.cos(p), np.sin(p)
    cy, sy = np.cos(y), np.sin(y)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def matrix_to_rpy(R):
    pitch = np.arcsin(np.clip(-R[2, 0], -1.0, 1.0))
    cp = np.cos(pitch)
    if abs(cp) > 1e-8:
        roll = np.arctan2(R[2, 1], R[2, 2])
        yaw = np.arctan2(R[1, 0], R[0, 0])
    else:
        # gimbal lock fallback
        roll = np.arctan2(-R[1, 2], R[1, 1])
        yaw = 0.0
    return np.array([roll, pitch, yaw])


def rot_z(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def transform_origin_element(origin_el, R):
    xyz = np.array([float(v) for v in origin_el.get("xyz", "0 0 0").split()])
    rpy = np.array([float(v) for v in origin_el.get("rpy", "0 0 0").split()])
    R_old = rpy_to_matrix(*rpy)

    new_xyz = R @ xyz
    new_R = R @ R_old
    new_rpy = matrix_to_rpy(new_R)

    origin_el.set("xyz", f"{new_xyz[0]:.10g} {new_xyz[1]:.10g} {new_xyz[2]:.10g}")
    origin_el.set("rpy", f"{new_rpy[0]:.10g} {new_rpy[1]:.10g} {new_rpy[2]:.10g}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf_path")
    ap.add_argument("--degrees", type=float, required=True)
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("--backup-suffix", default=".bak_frame")
    args = ap.parse_args()

    if args.in_place:
        backup_path = args.urdf_path + args.backup_suffix
        shutil.copy(args.urdf_path, backup_path)
        print(f"Backup written to: {backup_path}")

    tree = ET.parse(args.urdf_path)
    root = tree.getroot()

    links = {link.get("name"): link for link in root.findall("link")}
    joints = root.findall("joint")

    child_names = {j.find("child").get("link") for j in joints}
    link_names = set(links.keys()) | {j.find("parent").get("link") for j in joints}
    base_name = next(iter(link_names - child_names))
    print(f"Base link: {base_name}")

    theta = np.radians(args.degrees)
    R = rot_z(theta)
    print(f"Rotation: {args.degrees} deg about Z\nR =\n{R}")

    base_link = links[base_name]
    n_touched = 0
    for tag in ["inertial", "visual", "collision"]:
        for el in base_link.findall(tag):
            origin_el = el.find("origin")
            if origin_el is None:
                origin_el = ET.SubElement(el, "origin")
                origin_el.set("xyz", "0 0 0")
                origin_el.set("rpy", "0 0 0")
                el.insert(0, origin_el)
            transform_origin_element(origin_el, R)
            n_touched += 1
            print(f"  base/{tag}: origin updated")

    for j in joints:
        parent = j.find("parent").get("link")
        if parent == base_name:
            origin_el = j.find("origin")
            if origin_el is None:
                origin_el = ET.SubElement(j, "origin")
                origin_el.set("xyz", "0 0 0")
                origin_el.set("rpy", "0 0 0")
                j.insert(0, origin_el)
            transform_origin_element(origin_el, R)
            n_touched += 1
            print(f"  joint {j.get('name')} (parent=base): origin updated")

    print(f"\nTotal origins touched: {n_touched}")

    ET.indent(tree, space="  ")
    out_path = args.urdf_path if args.in_place else args.urdf_path + ".framerotated"
    tree.write(out_path, xml_declaration=True, encoding="UTF-8")
    print(f"Written to: {out_path}")


if __name__ == "__main__":
    main()
