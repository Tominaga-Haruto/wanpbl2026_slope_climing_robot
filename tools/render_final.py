import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

from plot_pose import mesh_world_tris, link_color, LINK_ORDER
from diag_mirror_v2 import parse_urdf_full, compute_fk

INIT_JOINT_POS = {
    "LL_HR": 0.0, "LR_HR": 0.0,
    "LL_HAA": -0.1745, "LR_HAA": -0.1745,
    "LL_HFE": -0.1745, "LR_HFE": -0.1745,
    "LL_KFE": 0.3491, "LR_KFE": 0.3491,
    "LL_FFE": -0.1745, "LR_FFE": -0.1745,
}


def render_3view(urdf_path, joint_pos, out_path, title):
    import os
    urdf_dir = os.path.dirname(os.path.abspath(urdf_path))
    joints, children_of, base, link_data = parse_urdf_full(urdf_path)
    world_T_link, world_T_joint = compute_fk(joints, children_of, base, joint_pos)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    views = [("XY (looking -Z)", 0, 1, axes[0]), ("XZ (looking -Y)", 0, 2, axes[1]), ("YZ (looking -X)", 1, 2, axes[2])]

    all_pts, tris_by_link = [], {}
    for link_name in LINK_ORDER:
        tris = mesh_world_tris(link_data, link_name, world_T_link, urdf_dir)
        if tris is not None:
            tris_by_link[link_name] = tris
            all_pts.append(tris.reshape(-1, 3))
    all_pts = np.concatenate(all_pts, axis=0)
    center = (all_pts.max(axis=0) + all_pts.min(axis=0)) / 2
    span = (all_pts.max(axis=0) - all_pts.min(axis=0)).max() / 2 * 1.3

    legend_handles = {}
    for label, i, j, ax in views:
        for link_name, tris in tris_by_link.items():
            poly2d = tris[:, :, [i, j]]
            color = link_color(link_name)
            ax.add_collection(PolyCollection(poly2d, facecolor=color, edgecolor="none", alpha=0.85, zorder=1))
            legend_handles[link_name] = color
        axis_len = span * 0.5
        for name, vec, color in [("X", [1,0,0], "red"), ("Y", [0,1,0], "green"), ("Z", [0,0,1], "blue")]:
            vec = np.array(vec)
            p0 = np.zeros(3)[[i,j]]; p1 = (vec*axis_len)[[i,j]]
            if np.allclose(p0,p1): continue
            ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="->", color=color, lw=2), zorder=5)
            ax.text(p1[0], p1[1], f"+{name}", color=color, fontsize=10, fontweight="bold", zorder=6)
        for jname, T in world_T_joint.items():
            p = T[:3,3][[i,j]]
            ax.plot(p[0], p[1], "k.", markersize=3, zorder=4)
            ax.text(p[0], p[1], jname, fontsize=6, zorder=6)
        c2 = center[[i,j]]
        ax.set_xlim(c2[0]-span, c2[0]+span); ax.set_ylim(c2[1]-span, c2[1]+span)
        ax.set_aspect("equal"); ax.set_title(label)
        ax.set_xlabel("XYZ"[i]); ax.set_ylabel("XYZ"[j]); ax.grid(True, alpha=0.3)

    handles = [plt.Rectangle((0,0),1,1,color=c) for c in legend_handles.values()]
    fig.legend(handles, list(legend_handles.keys()), loc="lower center", ncol=11, fontsize=7)
    fig.suptitle(title, fontsize=13)
    fig.tight_layout(rect=[0,0.06,1,0.95])
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {out_path}")


def render_side_overlay(urdf_path, out_path, title):
    import os
    urdf_dir = os.path.dirname(os.path.abspath(urdf_path))
    joints, children_of, base, link_data = parse_urdf_full(urdf_path)
    wl_zero, wj_zero = compute_fk(joints, children_of, base)
    wl_init, wj_init = compute_fk(joints, children_of, base, INIT_JOINT_POS)

    fig, ax = plt.subplots(figsize=(9, 8))
    i, j = 0, 2  # XZ

    all_pts = []
    for pose_label, wl, alpha in [("zero", wl_zero, 0.35), ("init", wl_init, 0.9)]:
        for link_name in LINK_ORDER:
            tris = mesh_world_tris(link_data, link_name, wl, urdf_dir)
            if tris is None:
                continue
            all_pts.append(tris.reshape(-1, 3))
            poly2d = tris[:, :, [i, j]]
            color = link_color(link_name)
            ls = "--" if pose_label == "zero" else "-"
            ax.add_collection(PolyCollection(poly2d, facecolor=color, edgecolor="none", alpha=alpha, zorder=1 if pose_label=="zero" else 2))

    all_pts = np.concatenate(all_pts, axis=0)
    center = (all_pts.max(axis=0) + all_pts.min(axis=0)) / 2
    span = (all_pts.max(axis=0) - all_pts.min(axis=0)).max() / 2 * 1.3
    axis_len = span * 0.5
    for name, vec, color in [("X", [1,0,0], "red"), ("Z", [0,0,1], "blue")]:
        vec = np.array(vec)
        p0 = np.zeros(3)[[i,j]]; p1 = (vec*axis_len)[[i,j]]
        ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="->", color=color, lw=2), zorder=5)
        ax.text(p1[0], p1[1], f"+{name}", color=color, fontsize=10, fontweight="bold", zorder=6)

    c2 = center[[i, j]]
    ax.set_xlim(c2[0]-span, c2[0]+span); ax.set_ylim(c2[1]-span, c2[1]+span)
    ax.set_aspect("equal"); ax.set_xlabel("X"); ax.set_ylabel("Z")
    ax.grid(True, alpha=0.3)
    ax.set_title(title + "\n(faint/dashed-tone = zero pose, solid/opaque = init_state pose)")

    handles = [plt.Rectangle((0,0),1,1,color=link_color(n)) for n in LINK_ORDER]
    fig.legend(handles, LINK_ORDER, loc="lower center", ncol=11, fontsize=7)
    fig.tight_layout(rect=[0,0.08,1,0.95])
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    render_3view("../onshape_export/myrobot_dummy/robot_sim_OUT.urdf", INIT_JOINT_POS,
                 "view_final_OUT.png", "Final candidate OUT (LR_HAA flipped), init_state.joint_pos")
    render_3view("../onshape_export/myrobot_dummy/robot_sim_IN.urdf", INIT_JOINT_POS,
                 "view_final_IN.png", "Final candidate IN (LL_HAA flipped), init_state.joint_pos")
    render_side_overlay("../onshape_export/myrobot_dummy/robot_sim_OUT.urdf",
                         "view_final_side.png", "OUT: zero pose vs init_state pose overlay (side/XZ)")
