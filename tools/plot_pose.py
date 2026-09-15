"""Render a 3-view (top/front/side) PNG of the robot at a given pose, meshes
placed in base frame. Read-only w.r.t. the URDF.
"""
import os
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from stl import mesh as stlmesh

from diag_mirror_v2 import parse_urdf_full, compute_fk, rpy_to_matrix

LINK_ORDER = ["base", "lr_hr", "lr_haa", "lr_hfe", "lr_kfe", "lr_ffe",
              "ll_hr", "ll_haa", "ll_hfe", "ll_kfe", "ll_ffe"]

LR_CMAP = plt.get_cmap("Reds")
LL_CMAP = plt.get_cmap("Blues")


def link_color(name):
    if name == "base":
        return (0.3, 0.3, 0.3, 0.9)
    order = ["hr", "haa", "hfe", "kfe", "ffe"]
    suffix = name.split("_")[1]
    idx = order.index(suffix)
    frac = 0.4 + 0.5 * idx / (len(order) - 1)
    if name.startswith("lr_"):
        return LR_CMAP(frac)
    else:
        return LL_CMAP(frac)


def mesh_world_tris(link_data, link_name, world_T_link, urdf_dir):
    meshes = link_data[link_name]["meshes"]
    if not meshes:
        return None
    m = meshes[0]
    mesh_path = os.path.join(urdf_dir, m["filename"])
    stl_data = stlmesh.Mesh.from_file(mesh_path)
    tris = stl_data.vectors  # (N, 3, 3)
    R_visual = rpy_to_matrix(*m["rpy"])
    tris_link = np.einsum("ij,ntj->nti", R_visual, tris) + m["xyz"]
    T = world_T_link[link_name]
    R_link = T[:3, :3]
    t_link = T[:3, 3]
    tris_world = np.einsum("ij,ntj->nti", R_link, tris_link) + t_link
    return tris_world


def render(urdf_path, joint_pos, axis_overrides, out_path, title):
    urdf_dir = os.path.dirname(os.path.abspath(urdf_path))
    joints, children_of, base, link_data = parse_urdf_full(urdf_path)
    world_T_link, world_T_joint = compute_fk(joints, children_of, base, joint_pos, axis_overrides)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    views = [
        ("Top (XY, looking -Z)", 0, 1, axes[0]),
        ("Front (XZ, looking -Y)", 0, 2, axes[1]),
        ("Side (YZ, looking -X)", 1, 2, axes[2]),
    ]

    all_pts = []
    tris_by_link = {}
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
            pc = PolyCollection(poly2d, facecolor=color, edgecolor="none", alpha=0.85, zorder=1)
            ax.add_collection(pc)
            legend_handles[link_name] = color

        axis_len = span * 0.5
        origin = np.zeros(3)
        arrow_defs = [("X", np.array([1, 0, 0]), "red"), ("Y", np.array([0, 1, 0]), "green"),
                      ("Z", np.array([0, 0, 1]), "blue")]
        for name, vec, color in arrow_defs:
            p0 = origin[[i, j]]
            p1 = (origin + vec * axis_len)[[i, j]]
            if np.allclose(p0, p1):
                continue
            ax.annotate("", xy=p1, xytext=p0,
                        arrowprops=dict(arrowstyle="->", color=color, lw=2), zorder=5)
            ax.text(p1[0], p1[1], f"+{name}", color=color, fontsize=10, fontweight="bold", zorder=6)

        for jname, T in world_T_joint.items():
            p = T[:3, 3][[i, j]]
            ax.plot(p[0], p[1], "k.", markersize=3, zorder=4)
            ax.text(p[0], p[1], jname, fontsize=6, zorder=6)

        c2 = center[[i, j]]
        ax.set_xlim(c2[0] - span, c2[0] + span)
        ax.set_ylim(c2[1] - span, c2[1] + span)
        ax.set_aspect("equal")
        ax.set_title(label)
        ax.set_xlabel("XYZ"[i])
        ax.set_ylabel("XYZ"[j])
        ax.grid(True, alpha=0.3)

    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in legend_handles.values()]
    labels = list(legend_handles.keys())
    fig.legend(handles, labels, loc="lower center", ncol=11, fontsize=7)
    fig.suptitle(title, fontsize=13)
    fig.tight_layout(rect=[0, 0.06, 1, 0.95])
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf_path")
    ap.add_argument("--pose", choices=["zero", "init_none", "init_L", "init_R"], required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    init_joint_pos = {
        "LL_HR": 0.0, "LR_HR": 0.0,
        "LL_HAA": -0.1745, "LR_HAA": -0.1745,
        "LL_HFE": -0.1745, "LR_HFE": -0.1745,
        "LL_KFE": 0.3491, "LR_KFE": 0.3491,
        "LL_FFE": -0.1745, "LR_FFE": -0.1745,
    }
    failing_suffixes = ["HR", "HAA", "HFE", "KFE", "FFE"]

    if args.pose == "zero":
        joint_pos, overrides, title = {}, {}, "Zero pose"
    elif args.pose == "init_none":
        joint_pos, overrides, title = init_joint_pos, {}, "init_state.joint_pos, no axis flip"
    elif args.pose == "init_L":
        joint_pos = init_joint_pos
        overrides = {f"LL_{s}": -1 for s in failing_suffixes}
        title = "init_state.joint_pos, Option L (LL axes flipped)"
    elif args.pose == "init_R":
        joint_pos = init_joint_pos
        overrides = {f"LR_{s}": -1 for s in failing_suffixes}
        title = "init_state.joint_pos, Option R (LR axes flipped)"

    render(args.urdf_path, joint_pos, overrides, args.out, title)


if __name__ == "__main__":
    main()
