"""Read-only diagnostic: separate "shape is symmetric but mounting angle
(zero-point) differs" from "shape itself differs" between the LR and LL legs.

1. Pose-independent check: segment length between adjacent joint origins
   along each leg chain (base->HR, HR->HAA, HAA->HFE, HFE->KFE, KFE->FFE),
   compared LR vs LL, in mm. This does not depend on any mirror-axis
   assumption at all -- it is just link-to-link distance.

2. World-frame joint rotation axis at zero pose for every joint, compared
   LR vs LL under the empirically-determined mirror plane (X = const,
   found in Step 5: legs separate mostly along local X, not Y). Reports
   the residual angle (degrees) between LL's axis and the two candidate
   mirrored versions of LR's axis (polar-vector mirror vs axial-vector
   mirror), and picks whichever is smaller.

3. If (1) matches within ~1mm for all segments, estimates the per-joint
   "zero-point" rotation offset needed to align the two legs: the angle,
   about each joint's own world axis, between LL's next-segment direction
   and the mirrored LR's next-segment direction.

Does not write to the URDF. Only reads.
"""
import argparse
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


def parse_urdf(path):
    tree = ET.parse(path)
    root = tree.getroot()

    joints = {}
    children_of = {}
    for j in root.findall("joint"):
        name = j.get("name")
        parent = j.find("parent").get("link")
        child = j.find("child").get("link")
        origin_el = j.find("origin")
        xyz = np.array([float(v) for v in origin_el.get("xyz", "0 0 0").split()]) if origin_el is not None else np.zeros(3)
        rpy = np.array([float(v) for v in origin_el.get("rpy", "0 0 0").split()]) if origin_el is not None else np.zeros(3)
        axis_el = j.find("axis")
        axis_local = np.array([float(v) for v in axis_el.get("xyz").split()]) if axis_el is not None else np.array([0, 0, 1])
        joints[name] = {"parent": parent, "child": child, "xyz": xyz, "rpy": rpy, "axis_local": axis_local}
        children_of.setdefault(parent, []).append(name)

    link_names = {j.find("child").get("link") for j in root.findall("joint")} | {j.find("parent").get("link") for j in root.findall("joint")}
    child_links = {j["child"] for j in joints.values()}
    base = next(iter(link_names - child_links))
    return joints, children_of, base


def compute_fk(joints, children_of, base):
    """Returns dict: link_name -> (world_T 4x4), and joint_name -> world_T of joint frame."""
    world_T_link = {base: np.eye(4)}
    world_T_joint = {}

    def recurse(link):
        T_link = world_T_link[link]
        for jname in children_of.get(link, []):
            j = joints[jname]
            R = rpy_to_matrix(*j["rpy"])
            T_origin = np.eye(4)
            T_origin[:3, :3] = R
            T_origin[:3, 3] = j["xyz"]
            T_joint = T_link @ T_origin
            world_T_joint[jname] = T_joint
            # at zero pose, child link frame == joint frame (no joint-variable rotation applied)
            world_T_link[j["child"]] = T_joint
            recurse(j["child"])

    recurse(base)
    return world_T_link, world_T_joint


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf_path")
    args = ap.parse_args()

    joints, children_of, base = parse_urdf(args.urdf_path)
    world_T_link, world_T_joint = compute_fk(joints, children_of, base)

    print(f"Base link: {base}")

    chain_suffixes = ["HR", "HAA", "HFE", "KFE", "FFE"]

    # ---- Part 1: pose-independent segment lengths ----
    print("\n=== 1. Segment lengths between adjacent joint origins (pose-independent) ===")

    def chain_positions(prefix):
        # prefix e.g. "LR"
        names = [f"{prefix}_{s}" for s in chain_suffixes]
        positions = [world_T_link[base][:3, 3]]  # start at base origin
        for n in names:
            positions.append(world_T_joint[n][:3, 3])
        return names, positions

    lr_names, lr_pos = chain_positions("LR")
    ll_names, ll_pos = chain_positions("LL")

    seg_labels = ["base->HR", "HR->HAA", "HAA->HFE", "HFE->KFE", "KFE->FFE"]
    print(f"{'segment':12s} {'LR_mm':>10s} {'LL_mm':>10s} {'diff_mm':>10s}")
    all_within_1mm = True
    for i, label in enumerate(seg_labels):
        d_lr = np.linalg.norm(lr_pos[i + 1] - lr_pos[i]) * 1000
        d_ll = np.linalg.norm(ll_pos[i + 1] - ll_pos[i]) * 1000
        diff = abs(d_lr - d_ll)
        if diff >= 1.0:
            all_within_1mm = False
        print(f"{label:12s} {d_lr:10.4f} {d_ll:10.4f} {diff:10.4f}")

    print(f"\nAll segments within 1mm: {all_within_1mm}")

    # ---- Part 2: world-frame joint axis comparison ----
    print("\n=== 2. World-frame joint rotation axis: LR vs mirrored LL ===")
    print("(mirror plane determined empirically in Step 5: X = const, legs separate along local X)")
    print(f"{'joint':10s} {'LR_axis_world':>28s} {'LL_axis_world':>28s} {'angle_polar_deg':>16s} {'angle_axial_deg':>16s} {'best_deg':>10s}")

    def world_axis(jname):
        T = world_T_joint[jname]
        R = T[:3, :3]
        local = joints[jname]["axis_local"]
        return R @ local

    def angle_deg(a, b):
        a = a / np.linalg.norm(a)
        b = b / np.linalg.norm(b)
        cos_a = np.clip(np.dot(a, b), -1.0, 1.0)
        return np.degrees(np.arccos(cos_a))

    mismatches = []
    for s in chain_suffixes:
        lr_j = f"LR_{s}"
        ll_j = f"LL_{s}"
        a_lr = world_axis(lr_j)
        a_ll = world_axis(ll_j)
        polar_mirror = np.array([-a_lr[0], a_lr[1], a_lr[2]])
        axial_mirror = np.array([a_lr[0], -a_lr[1], -a_lr[2]])
        ang_polar = angle_deg(a_ll, polar_mirror)
        ang_axial = angle_deg(a_ll, axial_mirror)
        best = min(ang_polar, ang_axial)
        if best > 2.0:
            mismatches.append((s, best))
        print(f"{s:10s} {np.round(a_lr,4)} {np.round(a_ll,4)} {ang_polar:16.3f} {ang_axial:16.3f} {best:10.3f}")

    print(f"\nJoints with >2 deg mismatch after best mirror hypothesis: {mismatches if mismatches else 'none'}")

    # ---- Part 3: full-orientation mirror residual (mathematically proper) ----
    # For a true mirror through world plane X=c, a rotation matrix R at a point mirrors
    # to F @ R @ F (conjugation by the reflection F=diag(-1,1,1)), NOT F @ R (which is not
    # even a proper rotation, det=-1). This directly tests the FULL 3D orientation of each
    # joint frame, not just its Z axis -- so it also catches a "180 deg flipped zero point"
    # if one exists.
    print("\n=== 3. Full-orientation mirror residual per joint (proper conjugation F@R@F) ===")
    F = np.diag([-1.0, 1.0, 1.0])

    def rotation_angle_deg(R):
        # angle of rotation matrix R via trace
        c = np.clip((np.trace(R) - 1) / 2, -1.0, 1.0)
        return np.degrees(np.arccos(c))

    print(f"{'joint':10s} {'residual_angle_deg':>20s}")
    for s in chain_suffixes:
        lr_j = f"LR_{s}"
        ll_j = f"LL_{s}"
        R_lr = world_T_joint[lr_j][:3, :3]
        R_ll = world_T_joint[ll_j][:3, :3]
        R_lr_mirrored = F @ R_lr @ F
        R_residual = R_ll.T @ R_lr_mirrored
        ang = rotation_angle_deg(R_residual)
        print(f"{s:10s} {ang:20.3f}")
    print("\n(near 0 deg = LL is exactly the mirror image of LR at this joint; near 180 deg would")
    print(" indicate a genuinely flipped zero-point convention on one side)")


if __name__ == "__main__":
    main()
