"""Verify an onshape-to-robot exported URDF: tree structure, mass, inertia,
left-right symmetry, joint limits, and mesh path sanity.

Usage:
    python verify_export.py <path-to-urdf> [--fk-out <path>]

No Isaac Sim / pxr dependency -- only numpy and stdlib xml, so it runs inside
the lightweight onshape_env.
"""
import sys
import os
import argparse
import xml.etree.ElementTree as ET
import numpy as np


def rpy_to_matrix(r, p, y):
    # Extrinsic XYZ: R = Rz(yaw) @ Ry(pitch) @ Rx(roll)
    cr, sr = np.cos(r), np.sin(r)
    cp, sp = np.cos(p), np.sin(p)
    cy, sy = np.cos(y), np.sin(y)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def parse_xyz_rpy(origin_elem):
    if origin_elem is None:
        return np.zeros(3), np.zeros(3)
    xyz = origin_elem.get("xyz", "0 0 0")
    rpy = origin_elem.get("rpy", "0 0 0")
    xyz = np.array([float(v) for v in xyz.split()])
    rpy = np.array([float(v) for v in rpy.split()])
    return xyz, rpy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf_path")
    ap.add_argument("--fk-out", default=None)
    args = ap.parse_args()

    urdf_path = args.urdf_path
    urdf_dir = os.path.dirname(os.path.abspath(urdf_path))
    tree = ET.parse(urdf_path)
    root = tree.getroot()

    links = {}
    for link in root.findall("link"):
        name = link.get("name")
        inertial = link.find("inertial")
        mass = None
        inertia = None
        origin = None
        if inertial is not None:
            mass_el = inertial.find("mass")
            if mass_el is not None:
                mass = float(mass_el.get("value"))
            inertia_el = inertial.find("inertia")
            if inertia_el is not None:
                inertia = {k: float(inertia_el.get(k)) for k in ["ixx", "ixy", "ixz", "iyy", "iyz", "izz"]}
            origin_el = inertial.find("origin")
            if origin_el is not None:
                origin = origin_el.get("xyz")
        meshes = []
        for geom in link.findall(".//geometry/mesh"):
            meshes.append(geom.get("filename"))
        links[name] = {"mass": mass, "inertia": inertia, "com": origin, "meshes": meshes}

    joints = []
    for joint in root.findall("joint"):
        name = joint.get("name")
        jtype = joint.get("type")
        parent = joint.find("parent").get("link")
        child = joint.find("child").get("link")
        axis_el = joint.find("axis")
        axis = axis_el.get("xyz") if axis_el is not None else None
        origin_el = joint.find("origin")
        xyz, rpy = parse_xyz_rpy(origin_el)
        limit_el = joint.find("limit")
        limit = None
        if limit_el is not None:
            limit = {k: limit_el.get(k) for k in ["lower", "upper", "effort", "velocity"] if limit_el.get(k) is not None}
        joints.append({
            "name": name, "type": jtype, "parent": parent, "child": child,
            "axis": axis, "xyz": xyz, "rpy": rpy, "limit": limit,
        })

    print("=" * 70)
    print(f"URDF: {urdf_path}")
    print(f"Link count: {len(links)}  Joint count: {len(joints)}")
    type_counts = {}
    for j in joints:
        type_counts[j["type"]] = type_counts.get(j["type"], 0) + 1
    print(f"Joint types: {type_counts}")

    # ---- Tree structure ----
    children_of = {}
    child_to_joint = {}
    all_children = set()
    for j in joints:
        children_of.setdefault(j["parent"], []).append(j["child"])
        child_to_joint[j["child"]] = j["name"]
        all_children.add(j["child"])
    all_link_names = set(links.keys())
    roots = list(all_link_names - all_children)
    print(f"\nRoot link(s): {roots}")

    print("\n--- Tree ---")

    def print_tree(node, depth=0, joint_name=None):
        prefix = "  " * depth
        jn = f" (joint {joint_name})" if joint_name else ""
        mass = links.get(node, {}).get("mass")
        print(f"{prefix}{node}{jn}  mass={mass}")
        for child in children_of.get(node, []):
            print_tree(child, depth + 1, child_to_joint[child])

    for r in roots:
        print_tree(r)

    # ---- Base mass ----
    if len(roots) == 1:
        base = roots[0]
        print(f"\nBase link: {base}  mass={links[base]['mass']}")
    else:
        base = None
        print(f"\nWARNING: {len(roots)} root links, expected 1")

    # ---- Total mass ----
    total_mass = sum(v["mass"] for v in links.values() if v["mass"] is not None)
    print(f"\nTotal mass: {total_mass:.6f} kg")
    print("\n--- All link masses ---")
    for name, v in links.items():
        print(f"  {name}: mass={v['mass']}")

    # ---- Off-diagonal inertia check ----
    print("\n--- Off-diagonal inertia (nonzero check) ---")
    for name, v in links.items():
        if v["inertia"] is None:
            print(f"  {name}: NO INERTIA")
            continue
        i = v["inertia"]
        nonzero = any(abs(i[k]) > 1e-12 for k in ["ixy", "ixz", "iyz"])
        print(f"  {name}: ixy={i['ixy']:.3e} ixz={i['ixz']:.3e} iyz={i['iyz']:.3e}  nonzero={nonzero}")

    # ---- Left-right pair mass comparison ----
    print("\n--- Left-right pair mass comparison ---")
    lr_joints = {j["name"]: j for j in joints if j["name"].startswith("LR_")}
    ll_joints = {j["name"]: j for j in joints if j["name"].startswith("LL_")}
    for suffix in ["HR", "HAA", "HFE", "KFE", "FFE"]:
        lr_name = f"LR_{suffix}"
        ll_name = f"LL_{suffix}"
        if lr_name in lr_joints and ll_name in ll_joints:
            lr_child = lr_joints[lr_name]["child"]
            ll_child = ll_joints[ll_name]["child"]
            lr_mass = links[lr_child]["mass"]
            ll_mass = links[ll_child]["mass"]
            diff = abs(lr_mass - ll_mass) if (lr_mass is not None and ll_mass is not None) else None
            print(f"  {suffix}: LR({lr_child})={lr_mass}  LL({ll_child})={ll_mass}  diff={diff}")
        else:
            print(f"  {suffix}: MISSING (LR present={lr_name in lr_joints}, LL present={ll_name in ll_joints})")

    # ---- Joint details ----
    print("\n--- Joint details ---")
    for j in joints:
        print(f"  {j['name']} ({j['type']}): parent={j['parent']} child={j['child']} axis={j['axis']} "
              f"xyz={j['xyz'].tolist()} rpy={j['rpy'].tolist()} limit={j['limit']}")

    # ---- Mesh path check ----
    print("\n--- Mesh path check ---")
    missing = 0
    total_mesh = 0
    backslash_count = 0
    package_prefix_count = 0
    for name, v in links.items():
        for m in v["meshes"]:
            total_mesh += 1
            if "\\" in m:
                backslash_count += 1
            if m.startswith("package://"):
                package_prefix_count += 1
            rel = m.replace("package://", "")
            rel = rel.replace("\\", "/")
            full_path = os.path.join(urdf_dir, rel)
            exists = os.path.isfile(full_path)
            if not exists:
                missing += 1
                print(f"  MISSING: {m}  (resolved: {full_path})")
    print(f"  Total mesh refs: {total_mesh}  backslash: {backslash_count}  package://: {package_prefix_count}  MISSING: {missing}")

    # ---- FK at zero pose ----
    print("\n--- FK at zero pose ---")
    world_T = {}

    def compute_fk(node, T_parent):
        world_T[node] = T_parent
        for child in children_of.get(node, []):
            jn = child_to_joint[child]
            j = [jj for jj in joints if jj["name"] == jn][0]
            R = rpy_to_matrix(*j["rpy"])
            T_joint = np.eye(4)
            T_joint[:3, :3] = R
            T_joint[:3, 3] = j["xyz"]
            T_child = T_parent @ T_joint
            compute_fk(child, T_child)

    if base is not None:
        compute_fk(base, np.eye(4))

    fk_lines = []
    for name in links:
        if name in world_T:
            pos = world_T[name][:3, 3]
            fk_lines.append(f"{name}: xyz=[{pos[0]:.6f}, {pos[1]:.6f}, {pos[2]:.6f}]")
        else:
            fk_lines.append(f"{name}: NOT REACHED FROM BASE")

    for line in fk_lines:
        print(f"  {line}")

    print("\n--- Left-right symmetry (y sign flip, x/z match) ---")
    for suffix in ["HR", "HAA", "HFE", "KFE", "FFE"]:
        lr_name = f"LR_{suffix}"
        ll_name = f"LL_{suffix}"
        if lr_name in lr_joints and ll_name in ll_joints:
            lr_child = lr_joints[lr_name]["child"]
            ll_child = ll_joints[ll_name]["child"]
            if lr_child in world_T and ll_child in world_T:
                p_lr = world_T[lr_child][:3, 3]
                p_ll = world_T[ll_child][:3, 3]
                print(f"  {suffix}: LR={p_lr.round(6).tolist()}  LL={p_ll.round(6).tolist()}  "
                      f"x_diff={abs(p_lr[0]-p_ll[0]):.6f}  y_sum={p_lr[1]+p_ll[1]:.6f}  z_diff={abs(p_lr[2]-p_ll[2]):.6f}")

    fk_out = args.fk_out
    if fk_out is None:
        fk_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fk_new.txt")
    with open(fk_out, "w", encoding="utf-8") as f:
        f.write(f"FK at zero pose for {urdf_path}\n")
        for line in fk_lines:
            f.write(line + "\n")
    print(f"\nFK saved to: {fk_out}")


if __name__ == "__main__":
    main()
