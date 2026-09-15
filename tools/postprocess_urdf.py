"""Post-process an onshape-to-robot raw export (robot.urdf) into the final
robot_sim.urdf used for USD conversion. Combines, in order, everything that
was previously done as separate manual steps:

  1) Rename links mechanically from tree structure (root -> "base", every
     other link -> lowercased name of the joint whose child it is). Joint
     names and mesh filenames are left untouched by this step.
  2) Mesh path cleanup: strip "package://", normalize "\\" to "/".
  3) Rotate the base link's own frame by +90 deg about Z (toe = +X, up = +Z
     convention decided after visual inspection). Only base's own
     inertial/visual/collision origins and the origins of joints whose
     parent is base are touched; everything else is relative and unaffected.
  4) Flip <axis> sign on LR_HR, LL_HAA, LL_HFE, LR_KFE, LL_FFE so that a
     positive joint command swings both legs outward symmetrically.
  5) Set velocity/effort limits per joint-suffix group. lower/upper left at
     +-pi (Onshape mates carry no limit).
  6) Self-check: tree is base -> 2x5 chain, MISSING mesh count is 0, and all
     10 joint axes (in base frame, zero pose) match the target directions.
     Exits non-zero if anything is off.

Usage:
    python postprocess_urdf.py <input_robot.urdf> <output_robot_sim.urdf>
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET
import numpy as np

# ---------------------------------------------------------------------------
# Fixed decisions (see chat history for how these were derived/verified)
# ---------------------------------------------------------------------------
AXIS_FLIP_JOINTS = ["LR_HR", "LL_HAA", "LL_HFE", "LR_KFE", "LL_FFE"]
BASE_ROTATION_DEG = 90.0
VELOCITY = {"HR": 23, "HAA": 15, "HFE": 20, "KFE": 20, "FFE": 23}
EFFORT = {"HR": 24, "HAA": 30, "HFE": 30, "KFE": 30, "FFE": 20}
AXIS_TARGET = {
    "LR_HR": "-Z", "LL_HR": "+Z", "LR_HAA": "-X", "LL_HAA": "+X",
    "LR_HFE": "+Y", "LL_HFE": "+Y", "LR_KFE": "+Y", "LL_KFE": "+Y",
    "LR_FFE": "+Y", "LL_FFE": "+Y",
}


# ---------------------------------------------------------------------------
# Rotation helpers (extrinsic XYZ rpy, matching URDF / onshape-to-robot)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Step 1: rename links from tree structure
# ---------------------------------------------------------------------------
def step1_rename_links(root):
    links = root.findall("link")
    joints = root.findall("joint")

    link_names = {link.get("name") for link in links}
    child_names = set()
    child_to_joint_name = {}
    for j in joints:
        child = j.find("child").get("link")
        child_names.add(child)
        child_to_joint_name[child] = j.get("name")

    root_candidates = link_names - child_names
    if len(root_candidates) != 1:
        print(f"ERROR: expected exactly 1 root link, found {root_candidates}")
        sys.exit(1)
    root_link_name = next(iter(root_candidates))

    mapping = {root_link_name: "base"}
    for child, joint_name in child_to_joint_name.items():
        mapping[child] = joint_name.lower()

    new_names = list(mapping.values())
    if len(new_names) != len(set(new_names)):
        print("ERROR: rename mapping produces duplicate names, aborting")
        sys.exit(1)

    print("--- Step 1: rename mapping (old -> new) ---")
    for old, new in mapping.items():
        print(f"  {old} -> {new}")

    for link in links:
        link.set("name", mapping[link.get("name")])
    for j in joints:
        parent_el = j.find("parent")
        child_el = j.find("child")
        parent_el.set("link", mapping[parent_el.get("link")])
        child_el.set("link", mapping[child_el.get("link")])


# ---------------------------------------------------------------------------
# Step 2: mesh path cleanup
# ---------------------------------------------------------------------------
def step2_fix_mesh_paths(root):
    count = 0
    for mesh in root.findall(".//geometry/mesh"):
        old = mesh.get("filename")
        new = old.replace("package://", "").replace("\\", "/")
        if new != old:
            mesh.set("filename", new)
            count += 1
    print(f"--- Step 2: mesh paths fixed ({count} changed) ---")


# ---------------------------------------------------------------------------
# Step 3: rotate base frame by +90 deg about Z
# ---------------------------------------------------------------------------
def step3_rotate_base_frame(root, degrees=BASE_ROTATION_DEG):
    links = {link.get("name"): link for link in root.findall("link")}
    joints = root.findall("joint")
    base_name = "base"
    if base_name not in links:
        print("ERROR: step 3 expected link 'base' (run step 1 first)")
        sys.exit(1)

    R = rot_z(np.radians(degrees))
    base_link = links[base_name]
    n = 0
    for tag in ["inertial", "visual", "collision"]:
        for el in base_link.findall(tag):
            origin_el = el.find("origin")
            if origin_el is None:
                origin_el = ET.SubElement(el, "origin")
                origin_el.set("xyz", "0 0 0")
                origin_el.set("rpy", "0 0 0")
                el.insert(0, origin_el)
            transform_origin_element(origin_el, R)
            n += 1

    for j in joints:
        if j.find("parent").get("link") == base_name:
            origin_el = j.find("origin")
            if origin_el is None:
                origin_el = ET.SubElement(j, "origin")
                origin_el.set("xyz", "0 0 0")
                origin_el.set("rpy", "0 0 0")
                j.insert(0, origin_el)
            transform_origin_element(origin_el, R)
            n += 1

    print(f"--- Step 3: base frame rotated {degrees} deg about Z ({n} origins touched) ---")


# ---------------------------------------------------------------------------
# Step 4: flip axis sign on selected joints
# ---------------------------------------------------------------------------
def step4_flip_axes(root, flip_joints=AXIS_FLIP_JOINTS):
    flipped = []
    for j in root.findall("joint"):
        name = j.get("name")
        if name in flip_joints:
            axis_el = j.find("axis")
            vals = [float(v) for v in axis_el.get("xyz").split()]
            new_vals = [-v if abs(v) > 1e-9 else v for v in vals]
            axis_el.set("xyz", f"{new_vals[0]:.10g} {new_vals[1]:.10g} {new_vals[2]:.10g}")
            flipped.append(name)
    print(f"--- Step 4: axis flipped on {flipped} ---")
    missing = set(flip_joints) - set(flipped)
    if missing:
        print(f"ERROR: joints to flip not found: {missing}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Step 5: set limits
# ---------------------------------------------------------------------------
def step5_set_limits(root):
    print("--- Step 5: limits ---")
    for j in root.findall("joint"):
        name = j.get("name")
        suffix = name.split("_")[1]
        if suffix not in VELOCITY:
            continue
        limit_el = j.find("limit")
        limit_el.set("velocity", str(VELOCITY[suffix]))
        limit_el.set("effort", str(EFFORT[suffix]))
        print(f"  {name}: velocity={VELOCITY[suffix]} effort={EFFORT[suffix]} "
              f"lower={limit_el.get('lower')} upper={limit_el.get('upper')}")


# ---------------------------------------------------------------------------
# Step 6: self-check
# ---------------------------------------------------------------------------
def parse_for_check(root, urdf_dir):
    links = {}
    for link in root.findall("link"):
        name = link.get("name")
        mass = None
        inertial = link.find("inertial")
        if inertial is not None:
            mass_el = inertial.find("mass")
            if mass_el is not None:
                mass = float(mass_el.get("value"))
        meshes = [g.get("filename") for g in link.findall(".//geometry/mesh")]
        links[name] = {"mass": mass, "meshes": meshes}

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
        axis_local = np.array([float(v) for v in axis_el.get("xyz").split()])
        joints[name] = {"parent": parent, "child": child, "xyz": xyz, "rpy": rpy, "axis_local": axis_local}
        children_of.setdefault(parent, []).append(name)

    return links, joints, children_of


def compute_fk(joints, children_of, base):
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
            world_T_link[j["child"]] = T_joint
            recurse(j["child"])

    recurse(base)
    return world_T_link, world_T_joint


def step6_selfcheck(root, urdf_dir):
    print("--- Step 6: self-check ---")
    links, joints, children_of = parse_for_check(root, urdf_dir)
    ok = True

    link_names = set(links.keys())
    child_links = {j["child"] for j in joints.values()}
    roots = list(link_names - child_links)
    if roots != ["base"] and roots != [] and len(roots) == 1 and roots[0] == "base":
        pass
    if len(roots) != 1 or roots[0] != "base":
        print(f"  FAIL: root link(s) = {roots}, expected ['base']")
        ok = False
        base = roots[0] if len(roots) == 1 else None
    else:
        base = "base"

    # tree structure 5/5
    chain_ok = True
    if base is not None:
        for prefix in ["LR", "LL"]:
            cur = base
            depth = 0
            for suffix in ["HR", "HAA", "HFE", "KFE", "FFE"]:
                jname = f"{prefix}_{suffix}"
                if jname not in joints or joints[jname]["parent"] != cur:
                    chain_ok = False
                    break
                cur = joints[jname]["child"]
                depth += 1
            if depth != 5:
                chain_ok = False
        print(f"  Tree structure (2x5 chain from base): {'OK' if chain_ok else 'FAIL'}")
        if not chain_ok:
            ok = False

        root_mass = links[base]["mass"]
        print(f"  Root ({base}) mass: {root_mass}")

    total_mass = sum(v["mass"] for v in links.values() if v["mass"] is not None)
    print(f"  Total mass: {total_mass:.6f} kg")

    missing = 0
    total_mesh = 0
    for name, v in links.items():
        for m in v["meshes"]:
            total_mesh += 1
            full_path = os.path.join(urdf_dir, m.replace("\\", "/"))
            if not os.path.isfile(full_path):
                missing += 1
                print(f"  MISSING: {m}")
    print(f"  Mesh refs: {total_mesh}  MISSING: {missing}")
    if missing != 0:
        ok = False

    if base is not None:
        world_T_link, world_T_joint = compute_fk(joints, children_of, base)
        axes6 = {"+X": np.array([1, 0, 0]), "-X": np.array([-1, 0, 0]),
                 "+Y": np.array([0, 1, 0]), "-Y": np.array([0, -1, 0]),
                 "+Z": np.array([0, 0, 1]), "-Z": np.array([0, 0, -1])}
        print("  Axis directions (base frame, zero pose):")
        for jname, target in AXIS_TARGET.items():
            R = world_T_joint[jname][:3, :3]
            local = joints[jname]["axis_local"]
            vec = R @ local
            bestname = max(axes6.items(), key=lambda kv: np.dot(vec, kv[1]))[0]
            match = bestname == target
            print(f"    {jname:10s} actual={bestname:>3s} target={target:>3s}  {'OK' if match else 'FAIL'}")
            if not match:
                ok = False

    print(f"\n  SELF-CHECK: {'PASS' if ok else 'FAIL'}")
    return ok


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_urdf")
    ap.add_argument("output_urdf")
    args = ap.parse_args()

    urdf_dir = os.path.dirname(os.path.abspath(args.input_urdf))

    tree = ET.parse(args.input_urdf)
    root = tree.getroot()

    step1_rename_links(root)
    step2_fix_mesh_paths(root)
    step3_rotate_base_frame(root)
    step4_flip_axes(root)
    step5_set_limits(root)

    ET.indent(tree, space="  ")
    tree.write(args.output_urdf, xml_declaration=True, encoding="UTF-8")
    print(f"\nWritten to: {args.output_urdf}")

    # self-check reads mesh paths relative to the OUTPUT file's directory
    out_dir = os.path.dirname(os.path.abspath(args.output_urdf))
    ok = step6_selfcheck(root, out_dir)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
