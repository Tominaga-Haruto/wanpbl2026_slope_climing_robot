"""Read-only: determine whether the foot (ffe) points toward +Y or -Y in the
base frame, using the sole mesh centroid/bbox-center relative to the ankle
joint origin. Also reports a weaker corroborating cue from the knee (kfe)
mesh offset direction.
"""
import argparse
import os
import numpy as np
from stl import mesh as stlmesh

from diag_orientation import parse_urdf, compute_fk, rpy_to_matrix


def mesh_world_points(link_meshes, link_name, world_T_link, urdf_dir):
    meshes = link_meshes[link_name]
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
    return verts_world


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf_path")
    args = ap.parse_args()
    urdf_dir = os.path.dirname(os.path.abspath(args.urdf_path))

    joints, children_of, base, link_meshes = parse_urdf(args.urdf_path)
    world_T_link, world_T_joint = compute_fk(joints, children_of, base)

    print("=" * 70)
    print("Toe direction check (sole mesh centroid / bbox-center vs ankle origin, Y component)")
    print("=" * 70)

    for side, link_name in [("LR", "lr_ffe"), ("LL", "ll_ffe")]:
        ankle_origin = world_T_link[link_name][:3, 3]
        verts_world = mesh_world_points(link_meshes, link_name, world_T_link, urdf_dir)
        centroid = verts_world.mean(axis=0)
        bbox_center = (verts_world.min(axis=0) + verts_world.max(axis=0)) / 2

        centroid_vec = centroid - ankle_origin
        bbox_vec = bbox_center - ankle_origin

        print(f"\n{side} ({link_name}):")
        print(f"  ankle origin (base frame) = {ankle_origin.round(6)}")
        print(f"  mesh centroid (base frame) = {centroid.round(6)}  vec_from_ankle = {centroid_vec.round(6)}")
        print(f"  mesh bbox center (base frame) = {bbox_center.round(6)}  vec_from_ankle = {bbox_vec.round(6)}")
        print(f"  Y component: centroid={centroid_vec[1]:.6f}  bbox={bbox_vec[1]:.6f}  "
              f"-> toe direction = {'+Y' if centroid_vec[1] > 0 else '-Y'} (by centroid)")

    print("\n" + "=" * 70)
    print("Corroborating cue: knee (kfe) mesh offset direction relative to its joint origin")
    print("=" * 70)
    for side, link_name in [("LR", "lr_kfe"), ("LL", "ll_kfe")]:
        joint_origin = world_T_link[link_name][:3, 3]
        verts_world = mesh_world_points(link_meshes, link_name, world_T_link, urdf_dir)
        centroid = verts_world.mean(axis=0)
        vec = centroid - joint_origin
        print(f"{side} ({link_name}): joint_origin={joint_origin.round(4)}  mesh_centroid_vec={vec.round(4)}  "
              f"Y={vec[1]:.4f}")


if __name__ == "__main__":
    main()
