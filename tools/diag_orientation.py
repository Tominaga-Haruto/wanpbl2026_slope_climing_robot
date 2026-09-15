"""Read-only diagnostic: determine which base-frame axis is forward/left/up,
and check left-right mirror symmetry at (a) the skyentific_poclegs.py init
pose and (b) single-joint-group +0.3 rad test poses.

Does not write to any file.
"""
import argparse
import xml.etree.ElementTree as ET
import numpy as np
from stl import mesh as stlmesh
import os


def rpy_to_matrix(r, p, y):
    cr, sr = np.cos(r), np.sin(r)
    cp, sp = np.cos(p), np.sin(p)
    cy, sy = np.cos(y), np.sin(y)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def rot_z(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def parse_urdf(path):
    tree = ET.parse(path)
    root = tree.getroot()
    joints = {}
    children_of = {}
    link_meshes = {}
    for link in root.findall("link"):
        name = link.get("name")
        meshes = []
        for visual in link.findall("visual"):
            origin_el = visual.find("origin")
            xyz = np.array([float(v) for v in origin_el.get("xyz", "0 0 0").split()]) if origin_el is not None else np.zeros(3)
            rpy = np.array([float(v) for v in origin_el.get("rpy", "0 0 0").split()]) if origin_el is not None else np.zeros(3)
            mesh_el = visual.find(".//geometry/mesh")
            if mesh_el is not None:
                meshes.append({"filename": mesh_el.get("filename"), "xyz": xyz, "rpy": rpy})
        link_meshes[name] = meshes

    for j in root.findall("joint"):
        name = j.get("name")
        parent = j.find("parent").get("link")
        child = j.find("child").get("link")
        origin_el = j.find("origin")
        xyz = np.array([float(v) for v in origin_el.get("xyz", "0 0 0").split()]) if origin_el is not None else np.zeros(3)
        rpy = np.array([float(v) for v in origin_el.get("rpy", "0 0 0").split()]) if origin_el is not None else np.zeros(3)
        joints[name] = {"parent": parent, "child": child, "xyz": xyz, "rpy": rpy}
        children_of.setdefault(parent, []).append(name)

    link_names = {j.find("child").get("link") for j in root.findall("joint")} | {j.find("parent").get("link") for j in root.findall("joint")}
    child_links = {j["child"] for j in joints.values()}
    base = next(iter(link_names - child_links))
    return joints, children_of, base, link_meshes


def compute_fk(joints, children_of, base, joint_pos=None):
    """joint_pos: dict joint_name -> theta (radians), default 0."""
    if joint_pos is None:
        joint_pos = {}
    world_T_link = {base: np.eye(4)}
    world_T_joint = {}

    def recurse(link):
        T_link = world_T_link[link]
        for jname in children_of.get(link, []):
            j = joints[jname]
            R_origin = rpy_to_matrix(*j["rpy"])
            theta = joint_pos.get(jname, 0.0)
            R = R_origin @ rot_z(theta)
            T_origin = np.eye(4)
            T_origin[:3, :3] = R
            T_origin[:3, 3] = j["xyz"]
            T_joint = T_link @ T_origin
            world_T_joint[jname] = T_joint
            world_T_link[j["child"]] = T_joint
            recurse(j["child"])

    recurse(base)
    return world_T_link, world_T_joint


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf_path")
    args = ap.parse_args()
    urdf_dir = os.path.dirname(os.path.abspath(args.urdf_path))

    joints, children_of, base, link_meshes = parse_urdf(args.urdf_path)

    print("=" * 70)
    print("A-1. Axis identification (base frame)")
    print("=" * 70)

    world_T_link, world_T_joint = compute_fk(joints, children_of, base)

    lr_hr = world_T_joint["LR_HR"][:3, 3]
    ll_hr = world_T_joint["LL_HR"][:3, 3]
    lr_ffe = world_T_link["lr_ffe"][:3, 3]
    ll_ffe = world_T_link["ll_ffe"][:3, 3]

    left_right_vec = ll_hr - lr_hr  # LL - LR, assuming LL=leg-left, LR=leg-right -> points toward left
    print(f"LR_HR pos = {lr_hr.round(6)}")
    print(f"LL_HR pos = {ll_hr.round(6)}")
    print(f"Left-right vector (LL_HR - LR_HR) = {left_right_vec.round(6)}  (dominant axis = "
          f"{'XYZ'[np.argmax(np.abs(left_right_vec))]})")

    ankle_mid = (lr_ffe + ll_ffe) / 2
    down_vec = ankle_mid - world_T_link[base][:3, 3]
    print(f"\nAnkle midpoint (lr_ffe+ll_ffe)/2 = {ankle_mid.round(6)}")
    print(f"Torso->ankle vector = {down_vec.round(6)}  (dominant axis = "
          f"{'XYZ'[np.argmax(np.abs(down_vec))]}, sign={'positive' if down_vec[np.argmax(np.abs(down_vec))]>0 else 'negative'})")

    # front cue: bbox of ffe (foot) link mesh transformed into base frame
    print("\n--- Front cue: foot (ffe) mesh bounding box in base frame ---")
    for side, link_name in [("LR", "lr_ffe"), ("LL", "ll_ffe")]:
        meshes = link_meshes[link_name]
        if not meshes:
            print(f"  {link_name}: no visual mesh found")
            continue
        m = meshes[0]
        mesh_path = os.path.join(urdf_dir, m["filename"])
        if not os.path.isfile(mesh_path):
            print(f"  {link_name}: mesh file not found at {mesh_path}")
            continue
        stl_data = stlmesh.Mesh.from_file(mesh_path)
        verts = stl_data.vectors.reshape(-1, 3)  # local mesh frame

        R_visual = rpy_to_matrix(*m["rpy"])
        verts_link = (R_visual @ verts.T).T + m["xyz"]

        T_link_world = world_T_link[link_name]
        R_link = T_link_world[:3, :3]
        t_link = T_link_world[:3, 3]
        verts_world = (R_link @ verts_link.T).T + t_link

        mins = verts_world.min(axis=0)
        maxs = verts_world.max(axis=0)
        extents = maxs - mins
        print(f"  {link_name}: bbox extents (base frame) X={extents[0]:.4f} Y={extents[1]:.4f} Z={extents[2]:.4f}  "
              f"-> longest axis = {'XYZ'[np.argmax(extents)]}")

    print("\n=" * 1)
    print("=" * 70)
    print("A-2. init_state.joint_pos (same sign LR/LL) mirror check")
    print("=" * 70)
    init_joint_pos = {
        "LL_HR": 0.0, "LR_HR": 0.0,
        "LL_HAA": -0.1745, "LR_HAA": -0.1745,
        "LL_HFE": -0.1745, "LR_HFE": -0.1745,
        "LL_KFE": 0.3491, "LR_KFE": 0.3491,
        "LL_FFE": -0.1745, "LR_FFE": -0.1745,
    }
    world_T_link2, world_T_joint2 = compute_fk(joints, children_of, base, init_joint_pos)
    lr_hr0 = world_T_joint["LR_HR"][:3, 3]
    ll_hr0 = world_T_joint["LL_HR"][:3, 3]
    mirror_axis = np.argmax(np.abs(left_right_vec))  # axis index for left-right
    c = (lr_hr0[mirror_axis] + ll_hr0[mirror_axis]) / 2  # mirror plane location on that axis

    lr_ffe2 = world_T_link2["lr_ffe"][:3, 3]
    ll_ffe2 = world_T_link2["ll_ffe"][:3, 3]

    def mirror_point(p, axis, c):
        p2 = p.copy()
        p2[axis] = 2 * c - p2[axis]
        return p2

    expected_ll = mirror_point(lr_ffe2, mirror_axis, c)
    diff_mm = np.linalg.norm(expected_ll - ll_ffe2) * 1000
    print(f"mirror axis = {'XYZ'[mirror_axis]}, plane at {c:.6f}")
    print(f"lr_ffe (init pose) = {lr_ffe2.round(6)}")
    print(f"ll_ffe (init pose) = {ll_ffe2.round(6)}")
    print(f"expected ll_ffe (mirror of lr_ffe) = {expected_ll.round(6)}")
    print(f"mismatch = {diff_mm:.3f} mm")

    print("\n" + "=" * 70)
    print("A-3. Per-joint-group +0.3 rad mirror test")
    print("=" * 70)
    for suffix in ["HR", "HAA", "HFE", "KFE", "FFE"]:
        jp = {f"LL_{suffix}": 0.3, f"LR_{suffix}": 0.3}
        wl, wj = compute_fk(joints, children_of, base, jp)
        lr_p = wl["lr_ffe"][:3, 3]
        ll_p = wl["ll_ffe"][:3, 3]
        expected = mirror_point(lr_p, mirror_axis, c)
        diff = np.linalg.norm(expected - ll_p) * 1000
        status = "MIRROR (OK)" if diff < 5.0 else "NOT MIRROR (sign likely flipped)"
        print(f"  {suffix}: lr_ffe={lr_p.round(4)}  ll_ffe={ll_p.round(4)}  expected_ll={expected.round(4)}  "
              f"diff={diff:.2f}mm  -> {status}")


if __name__ == "__main__":
    main()
