"""Mirror-symmetry diagnostics measured via link COM (inertial origin) and
sole-mesh bbox center, mirror axis = Y (left-right, after base frame
rotation). Supports overriding a joint's effective rotation sign (to
evaluate flipping <axis> on one side).

Read-only unless used as a library by other scripts.
"""
import os
import numpy as np
import xml.etree.ElementTree as ET
from stl import mesh as stlmesh


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


def parse_urdf_full(path):
    tree = ET.parse(path)
    root = tree.getroot()
    joints = {}
    children_of = {}
    link_data = {}
    for link in root.findall("link"):
        name = link.get("name")
        inertial = link.find("inertial")
        com_xyz = np.zeros(3)
        mass = None
        if inertial is not None:
            mass_el = inertial.find("mass")
            if mass_el is not None:
                mass = float(mass_el.get("value"))
            origin_el = inertial.find("origin")
            if origin_el is not None:
                com_xyz = np.array([float(v) for v in origin_el.get("xyz", "0 0 0").split()])
        meshes = []
        for visual in link.findall("visual"):
            origin_el = visual.find("origin")
            xyz = np.array([float(v) for v in origin_el.get("xyz", "0 0 0").split()]) if origin_el is not None else np.zeros(3)
            rpy = np.array([float(v) for v in origin_el.get("rpy", "0 0 0").split()]) if origin_el is not None else np.zeros(3)
            mesh_el = visual.find(".//geometry/mesh")
            if mesh_el is not None:
                meshes.append({"filename": mesh_el.get("filename"), "xyz": xyz, "rpy": rpy})
        link_data[name] = {"com_xyz": com_xyz, "mass": mass, "meshes": meshes}

    for j in root.findall("joint"):
        name = j.get("name")
        parent = j.find("parent").get("link")
        child = j.find("child").get("link")
        origin_el = j.find("origin")
        xyz = np.array([float(v) for v in origin_el.get("xyz", "0 0 0").split()]) if origin_el is not None else np.zeros(3)
        rpy = np.array([float(v) for v in origin_el.get("rpy", "0 0 0").split()]) if origin_el is not None else np.zeros(3)
        axis_el = j.find("axis")
        axis_z_sign = 1.0
        if axis_el is not None:
            axis_vals = [float(v) for v in axis_el.get("xyz").split()]
            axis_z_sign = 1.0 if axis_vals[2] >= 0 else -1.0
        joints[name] = {"parent": parent, "child": child, "xyz": xyz, "rpy": rpy, "axis_z_sign": axis_z_sign}
        children_of.setdefault(parent, []).append(name)

    link_names = {j.find("child").get("link") for j in root.findall("joint")} | {j.find("parent").get("link") for j in root.findall("joint")}
    child_links = {j["child"] for j in joints.values()}
    base = next(iter(link_names - child_links))
    return joints, children_of, base, link_data


def compute_fk(joints, children_of, base, joint_pos=None, axis_overrides=None):
    """joint_pos: dict joint_name -> commanded theta.
    axis_overrides: dict joint_name -> +1/-1, overrides the URDF axis sign for testing."""
    if joint_pos is None:
        joint_pos = {}
    if axis_overrides is None:
        axis_overrides = {}
    world_T_link = {base: np.eye(4)}
    world_T_joint = {}

    def recurse(link):
        T_link = world_T_link[link]
        for jname in children_of.get(link, []):
            j = joints[jname]
            R_origin = rpy_to_matrix(*j["rpy"])
            theta_cmd = joint_pos.get(jname, 0.0)
            sign = axis_overrides.get(jname, j["axis_z_sign"])
            R = R_origin @ rot_z(sign * theta_cmd)
            T_origin = np.eye(4)
            T_origin[:3, :3] = R
            T_origin[:3, 3] = j["xyz"]
            T_joint = T_link @ T_origin
            world_T_joint[jname] = T_joint
            world_T_link[j["child"]] = T_joint
            recurse(j["child"])

    recurse(base)
    return world_T_link, world_T_joint


def link_com_world(link_data, link_name, world_T_link):
    T = world_T_link[link_name]
    R = T[:3, :3]
    t = T[:3, 3]
    return R @ link_data[link_name]["com_xyz"] + t


def sole_bbox_center_world(link_data, link_name, world_T_link, urdf_dir):
    meshes = link_data[link_name]["meshes"]
    m = meshes[0]
    mesh_path = os.path.join(urdf_dir, m["filename"])
    stl_data = stlmesh.Mesh.from_file(mesh_path)
    verts = stl_data.vectors.reshape(-1, 3)
    R_visual = rpy_to_matrix(*m["rpy"])
    verts_link = (R_visual @ verts.T).T + m["xyz"]
    T = world_T_link[link_name]
    R_link = T[:3, :3]
    t_link = T[:3, 3]
    verts_world = (R_link @ verts_link.T).T + t_link
    return (verts_world.min(axis=0) + verts_world.max(axis=0)) / 2, verts_world


def mirror_point(p, axis, c):
    p2 = p.copy()
    p2[axis] = 2 * c - p2[axis]
    return p2
