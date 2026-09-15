import os
import numpy as np
from diag_mirror_v2 import parse_urdf_full, compute_fk, link_com_world, sole_bbox_center_world, mirror_point

INIT_JOINT_POS = {
    "LL_HR": 0.0, "LR_HR": 0.0,
    "LL_HAA": -0.1745, "LR_HAA": -0.1745,
    "LL_HFE": -0.1745, "LR_HFE": -0.1745,
    "LL_KFE": 0.3491, "LR_KFE": 0.3491,
    "LL_FFE": -0.1745, "LR_FFE": -0.1745,
}


def matrix_to_rpy(R):
    pitch = np.arcsin(np.clip(-R[2, 0], -1, 1))
    cp = np.cos(pitch)
    if abs(cp) > 1e-8:
        roll = np.arctan2(R[2, 1], R[2, 2])
        yaw = np.arctan2(R[1, 0], R[0, 0])
    else:
        roll = np.arctan2(-R[1, 2], R[1, 1]); yaw = 0.0
    return np.array([roll, pitch, yaw])


def evaluate(label, urdf_path):
    urdf_dir = os.path.dirname(os.path.abspath(urdf_path))
    joints, children_of, base, link_data = parse_urdf_full(urdf_path)

    wl0, wj0 = compute_fk(joints, children_of, base)  # zero pose (axis sign already baked into file)
    lr_hr_y = wj0["LR_HR"][:3, 3][1]
    ll_hr_y = wj0["LL_HR"][:3, 3][1]
    mirror_axis = 1
    c = (lr_hr_y + ll_hr_y) / 2

    wl, wj = compute_fk(joints, children_of, base, INIT_JOINT_POS)

    print(f"\n{'='*70}\n{label}\n{'='*70}")

    # a) mirror mismatch
    com_lr = link_com_world(link_data, "lr_ffe", wl)
    com_ll = link_com_world(link_data, "ll_ffe", wl)
    bbox_lr, verts_lr = sole_bbox_center_world(link_data, "lr_ffe", wl, urdf_dir)
    bbox_ll, verts_ll = sole_bbox_center_world(link_data, "ll_ffe", wl, urdf_dir)
    com_diff = np.linalg.norm(mirror_point(com_lr, mirror_axis, c) - com_ll) * 1000
    bbox_diff = np.linalg.norm(mirror_point(bbox_lr, mirror_axis, c) - bbox_ll) * 1000
    print(f"a) mirror mismatch: COM={com_diff:.2f}mm  bbox={bbox_diff:.2f}mm")

    # b) knee position relative to HFE-FFE line
    for side, hfe, kfe, ffe in [("LR", "lr_hfe", "lr_kfe", "lr_ffe"), ("LL", "ll_hfe", "ll_kfe", "ll_ffe")]:
        P_hfe = wl[hfe][:3, 3]; P_kfe = wl[kfe][:3, 3]; P_ffe = wl[ffe][:3, 3]
        d = P_ffe - P_hfe
        t = np.dot(P_kfe - P_hfe, d) / np.dot(d, d)
        P_line = P_hfe + t * d
        resid = P_kfe - P_line
        side_label = "+X (front)" if resid[0] > 0 else "-X (behind)"
        print(f"b) {side} knee X-offset from HFE-FFE line: {resid[0]*1000:+.2f}mm -> {side_label}")

    # c) sole pitch/roll change from zero pose
    for side, ffe in [("LR", "lr_ffe"), ("LL", "ll_ffe")]:
        R_zero = wl0[ffe][:3, :3]
        R_now = wl[ffe][:3, :3]
        dR = R_zero.T @ R_now
        rpy = np.degrees(matrix_to_rpy(dR))
        print(f"c) {side} sole orientation change from zero: roll(X)={rpy[0]:+.2f} deg  pitch(Y)={rpy[1]:+.2f} deg  "
              f"yaw(Z)={rpy[2]:+.2f} deg")

    # d) left-right foot separation
    sep = wl["ll_ffe"][:3, 3][1] - wl["lr_ffe"][:3, 3][1]
    print(f"d) foot separation (ll_ffe.y - lr_ffe.y) = {sep*1000:.2f} mm")

    # e) lowest sole point & needed base height
    min_z = min(verts_lr[:, 2].min(), verts_ll[:, 2].min())
    needed_height = -min_z
    print(f"e) lowest sole point z = {min_z:.4f} m  -> needed base spawn height = {needed_height:.4f} m  "
          f"(current init_state.pos.z = 0.449)")


evaluate("OUT (LR_HAA flipped)", "../onshape_export/myrobot_dummy/robot_sim_OUT.urdf")
evaluate("IN (LL_HAA flipped)", "../onshape_export/myrobot_dummy/robot_sim_IN.urdf")
