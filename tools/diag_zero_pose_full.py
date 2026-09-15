"""Read-only zero-pose diagnostics on the (base-rotated) robot_sim.urdf:
  a) all 10 joint axes in base frame vs +-X/+-Y/+-Z
  b) knee angle (thigh vs shin) and leg tilt from vertical, per leg
  c) sole mesh lowest-band (within 5mm of min Z) PCA long-axis direction,
     which end is farther from the ankle, and sole normal tilt from vertical
  d) base mesh longest direction, and left-right hip direction
"""
import os
import numpy as np
from stl import mesh as stlmesh
from diag_mirror_v2 import parse_urdf_full, compute_fk, rpy_to_matrix


def mesh_world_verts(link_data, link_name, world_T_link, urdf_dir):
    m = link_data[link_name]["meshes"][0]
    mesh_path = os.path.join(urdf_dir, m["filename"])
    stl_data = stlmesh.Mesh.from_file(mesh_path)
    verts = stl_data.vectors.reshape(-1, 3)
    R_visual = rpy_to_matrix(*m["rpy"])
    verts_link = (R_visual @ verts.T).T + m["xyz"]
    T = world_T_link[link_name]
    R_link = T[:3, :3]
    t_link = T[:3, 3]
    return (R_link @ verts_link.T).T + t_link


def main():
    urdf_path = "../onshape_export/myrobot_dummy/robot_sim.urdf"
    urdf_dir = os.path.dirname(os.path.abspath(urdf_path))
    joints, children_of, base, link_data = parse_urdf_full(urdf_path)
    world_T_link, world_T_joint = compute_fk(joints, children_of, base)

    axes6 = {
        "+X": np.array([1, 0, 0]), "-X": np.array([-1, 0, 0]),
        "+Y": np.array([0, 1, 0]), "-Y": np.array([0, -1, 0]),
        "+Z": np.array([0, 0, 1]), "-Z": np.array([0, 0, -1]),
    }

    print("=" * 100)
    print("a) Joint axis in base frame vs +-X/+-Y/+-Z (degrees)")
    print("=" * 100)
    header = f"{'joint':10s}" + "".join(f"{k:>8s}" for k in axes6)
    print(header)
    for jname in ["LR_HR", "LR_HAA", "LR_HFE", "LR_KFE", "LR_FFE",
                  "LL_HR", "LL_HAA", "LL_HFE", "LL_KFE", "LL_FFE"]:
        R = world_T_joint[jname][:3, :3]
        sign = joints[jname]["axis_z_sign"]
        world_axis = R @ np.array([0, 0, sign])
        row = f"{jname:10s}"
        for k, v in axes6.items():
            ang = np.degrees(np.arccos(np.clip(np.dot(world_axis, v), -1, 1)))
            row += f"{ang:8.2f}"
        print(row)

    print("\n" + "=" * 100)
    print("b) Knee angle (180=straight) and leg tilt from vertical")
    print("=" * 100)
    for side, hfe, kfe, ffe in [("LR", "lr_hfe", "lr_kfe", "lr_ffe"), ("LL", "ll_hfe", "ll_kfe", "ll_ffe")]:
        P_hfe = world_T_link[hfe][:3, 3]
        P_kfe = world_T_link[kfe][:3, 3]
        P_ffe = world_T_link[ffe][:3, 3]
        v1 = P_hfe - P_kfe  # knee->hip
        v2 = P_ffe - P_kfe  # knee->ankle
        knee_angle = np.degrees(np.arccos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1)))
        leg_vec = P_ffe - P_hfe
        tilt_from_vertical = np.degrees(np.arccos(np.clip(abs(leg_vec[2]) / np.linalg.norm(leg_vec), -1, 1)))
        print(f"  {side}: knee_angle={knee_angle:.2f} deg   leg(hip->ankle) tilt from vertical={tilt_from_vertical:.2f} deg   "
              f"leg_vec={leg_vec.round(4)}")

    print("\n" + "=" * 100)
    print("c) Sole mesh lowest-band PCA direction, far-end from ankle, sole normal tilt")
    print("=" * 100)
    for side, link_name in [("LR", "lr_ffe"), ("LL", "ll_ffe")]:
        verts = mesh_world_verts(link_data, link_name, world_T_link, urdf_dir)
        ankle_origin = world_T_link[link_name][:3, 3]
        min_z = verts[:, 2].min()
        low_pts = verts[verts[:, 2] <= min_z + 0.005]
        xy = low_pts[:, :2]
        centroid_xy = xy.mean(axis=0)
        xy_c = xy - centroid_xy
        cov = xy_c.T @ xy_c
        eigvals, eigvecs = np.linalg.eigh(cov)
        long_axis = eigvecs[:, np.argmax(eigvals)]  # unit vector in XY, sign arbitrary
        angle_deg = np.degrees(np.arctan2(long_axis[1], long_axis[0])) % 180

        proj = xy_c @ long_axis
        pt_pos = low_pts[np.argmax(proj)]
        pt_neg = low_pts[np.argmin(proj)]
        dist_pos = np.linalg.norm(pt_pos[:2] - ankle_origin[:2])
        dist_neg = np.linalg.norm(pt_neg[:2] - ankle_origin[:2])
        far_pt = pt_pos if dist_pos > dist_neg else pt_neg
        far_dir = far_pt[:2] - ankle_origin[:2]
        far_angle = np.degrees(np.arctan2(far_dir[1], far_dir[0]))

        # sole normal from plane fit (full low band, 3D)
        pts3 = low_pts - low_pts.mean(axis=0)
        cov3 = pts3.T @ pts3
        eigvals3, eigvecs3 = np.linalg.eigh(cov3)
        normal = eigvecs3[:, np.argmin(eigvals3)]
        if normal[2] < 0:
            normal = -normal
        normal_tilt = np.degrees(np.arccos(np.clip(normal[2], -1, 1)))

        print(f"  {side} ({link_name}): n_low_pts={len(low_pts)}  long_axis_angle(from +X, 0-180)={angle_deg:.1f} deg")
        print(f"       far-end point (farther from ankle in XY) = {far_pt.round(4)}  "
              f"direction from ankle = {far_angle:.1f} deg (0=+X,90=+Y)")
        print(f"       sole normal = {normal.round(4)}  tilt from vertical(+Z) = {normal_tilt:.2f} deg")

    print("\n" + "=" * 100)
    print("d) Base mesh longest direction, and left-right hip direction")
    print("=" * 100)
    verts_base = mesh_world_verts(link_data, "base", world_T_link, urdf_dir)
    centroid = verts_base.mean(axis=0)
    pts_c = verts_base - centroid
    cov = pts_c.T @ pts_c
    eigvals, eigvecs = np.linalg.eigh(cov)
    long_axis3 = eigvecs[:, np.argmax(eigvals)]
    print(f"  base mesh bbox extents: {(verts_base.max(axis=0)-verts_base.min(axis=0)).round(4)}")
    print(f"  base mesh PCA long axis (3D, base frame) = {long_axis3.round(4)}")
    for k, v in axes6.items():
        ang = np.degrees(np.arccos(np.clip(abs(np.dot(long_axis3, v)), -1, 1)))
    lr_hr = world_T_joint["LR_HR"][:3, 3]
    ll_hr = world_T_joint["LL_HR"][:3, 3]
    hip_dir = ll_hr - lr_hr
    print(f"  LR_HR - LL_HR vector = {(lr_hr-ll_hr).round(4)}  (dominant axis = {'XYZ'[np.argmax(np.abs(hip_dir))]})")


if __name__ == "__main__":
    main()
