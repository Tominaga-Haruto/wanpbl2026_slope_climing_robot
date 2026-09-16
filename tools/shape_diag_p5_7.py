"""P5-7: redo the P3 shape diagnostics correctly per user's corrections (2026-09-17).

1. Mirror axis at the hip midpoint y=c=-0.0206 (not y=0): for each left/right link pair, compare
   link origin AND COM (x,y,z), reflecting the right side about y=c, and report the residual.
2. Sole plane: fit a plane to WORLD-frame collision-mesh vertices within 3mm of the lowest point
   (not the link-local-frame vertex "pitch" reported before, which was a link-frame artifact, not
   necessarily the sole's own plane against the ground). Report pitch/roll of that plane's normal
   vs the ground and how many vertices were used.
3. That vertex group's x-range (base coords) and whole-body COM position (base coords), and whether
   COM x sits ahead of (in front of) the support x-range.

Run from D:\\Tominaga\\IsaacLab.
"""

import argparse
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_envs", type=int, default=4)
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--out", type=str, default=r"D:\Tominaga\slope-climbing-robot\tools\logs\P5_7_shape_redo.md")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True
sys.argv = [sys.argv[0]]

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------

import numpy as np
import torch
from pxr import Gf, Usd, UsdGeom, UsdPhysics

import isaaclab.utils.math as math_utils
from isaaclab.envs import ManagerBasedRLEnv

import isaaclab_tasks  # noqa: F401
import skyentific_poclegs  # noqa: F401
from skyentific_poclegs.tasks.locomotion.velocity.config.skyentific_poclegs.rough_env_cfg import (
    SkyentificPoclegsRoughEnvCfg,
)

LINK_PAIRS = [
    ("ll_hr", "lr_hr"), ("ll_haa", "lr_haa"), ("ll_hfe", "lr_hfe"),
    ("ll_kfe", "lr_kfe"), ("ll_ffe", "lr_ffe"),
]

# hip midpoint y found in P3 (LL_HR y=+0.0544, LR_HR y=-0.0956 -> midpoint c = (0.0544-0.0956)/2)
MIRROR_C_Y = -0.0206


def build_env_cfg(num_envs, seed, device):
    cfg = SkyentificPoclegsRoughEnvCfg()
    cfg.scene.num_envs = num_envs
    cfg.seed = seed
    cfg.sim.device = device
    gen = cfg.scene.terrain.terrain_generator
    for name in gen.sub_terrains:
        gen.sub_terrains[name].proportion = 0.0
    gen.sub_terrains["flat"].proportion = 1.0
    gen.num_rows = 2
    gen.num_cols = 2
    gen.curriculum = False
    cfg.scene.terrain.max_init_terrain_level = 0
    cfg.curriculum.terrain_levels = None
    cfg.curriculum.push_force_levels = None
    cfg.curriculum.command_vel = None
    cfg.observations.policy.enable_corruption = False
    cfg.events.push_robot = None
    cfg.events.base_external_force_torque = None
    cfg.events.physics_material.params["static_friction_range"] = (1.0, 1.0)
    cfg.events.physics_material.params["dynamic_friction_range"] = (1.0, 1.0)
    cfg.events.physics_material.params["restitution_range"] = (0.0, 0.0)
    cfg.events.scale_all_link_masses.params["mass_distribution_params"] = (1.0, 1.0)
    cfg.events.add_base_mass.params["mass_distribution_params"] = (0.0, 0.0)
    cfg.events.scale_all_joint_armature.params["armature_distribution_params"] = (1.0, 1.0)
    cfg.events.scale_all_joint_friction_model.params["friction_distribution_params"] = (1.0, 1.0)
    cfg.events.reset_base.params["pose_range"] = {}
    cfg.events.reset_base.params["velocity_range"] = {
        "x": (0.0, 0.0), "y": (0.0, 0.0), "z": (0.0, 0.0),
        "roll": (0.0, 0.0), "pitch": (0.0, 0.0), "yaw": (0.0, 0.0),
    }
    cfg.events.reset_robot_joints.params["position_range"] = (1.0, 1.0)
    cfg.events.reset_robot_joints.params["velocity_range"] = (0.0, 0.0)
    bv = cfg.commands.base_velocity
    bv.heading_command = False
    bv.ranges.heading = None
    bv.rel_heading_envs = 0.0
    bv.rel_standing_envs = 0.0
    bv.resampling_time_range = (1.0e6, 1.0e6)
    cfg.episode_length_s = 60.0
    return cfg


def link_mesh_points(stage, prim_path, collision_only=True):
    link = stage.GetPrimAtPath(prim_path)
    if not link.IsValid():
        return None
    xf = UsdGeom.XformCache(Usd.TimeCode.Default())

    def has_collision(p):
        q = p
        while q.IsValid() and q.GetPath() != link.GetPath().GetParentPath():
            if q.HasAPI(UsdPhysics.CollisionAPI):
                return True
            q = q.GetParent()
        return False

    for want_collision in ([True, False] if collision_only else [False]):
        pts = []
        for prim in Usd.PrimRange(link, Usd.TraverseInstanceProxies()):
            if not prim.IsA(UsdGeom.Mesh):
                continue
            if want_collision and not has_collision(prim):
                continue
            mesh = UsdGeom.Mesh(prim)
            raw = mesh.GetPointsAttr().Get()
            if not raw:
                continue
            m = xf.ComputeRelativeTransform(prim, link)[0]
            for p in raw:
                q = m.Transform(Gf.Vec3d(p[0], p[1], p[2]))
                pts.append([q[0], q[1], q[2]])
        if pts:
            return torch.tensor(pts, dtype=torch.float32)
    return None


def fit_plane_normal(points_xyz):
    """Least-squares plane z = a*x + b*y + c through points (N,3); returns unit normal (a,b,-1)/norm
    and (pitch_deg, roll_deg) of that normal vs +z, plus the residual RMS [m]."""
    pts = points_xyz
    A = np.stack([pts[:, 0], pts[:, 1], np.ones(pts.shape[0])], axis=1)
    b = pts[:, 2]
    coef, *_ = np.linalg.lstsq(A, b, rcond=None)
    a_x, a_y, c0 = coef
    resid = A @ coef - b
    rms = float(np.sqrt((resid**2).mean()))
    pitch_deg = float(np.degrees(np.arctan(a_x)))
    roll_deg = float(np.degrees(np.arctan(a_y)))
    return pitch_deg, roll_deg, rms


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"
    env = ManagerBasedRLEnv(cfg=build_env_cfg(args_cli.num_envs, args_cli.seed, device))
    robot = env.scene["robot"]
    stage = env.scene.stage
    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    with torch.inference_mode():
        env.reset()
        base_pos = robot.data.root_link_pos_w[0].clone()
        base_quat = robot.data.root_link_quat_w[0:1].clone()
        ground_z = env.scene.env_origins[0, 2].item()
        masses = robot.data.default_mass[0].to(device)
        com_w = robot.data.body_com_pos_w[0]

        emit(f"# P5-7 形状の出し直し (鏡映軸 y={MIRROR_C_Y})\n")
        emit("## 1. 鏡映軸を股の中点にした左右差\n")
        emit("| リンク対 | 左origin(x,y,z) | 右origin反転後(x,y,z) | 差(x,y,z) | 左COM(x,y,z) | 右COM反転後(x,y,z) | 差(x,y,z) |")
        emit("|---|---|---|---|---|---|---|")
        for l_name, r_name in LINK_PAIRS:
            li = robot.body_names.index(l_name)
            ri = robot.body_names.index(r_name)
            l_origin = math_utils.quat_apply_inverse(base_quat, (robot.data.body_link_pos_w[0, li] - base_pos).unsqueeze(0))[0]
            r_origin = math_utils.quat_apply_inverse(base_quat, (robot.data.body_link_pos_w[0, ri] - base_pos).unsqueeze(0))[0]
            l_com = math_utils.quat_apply_inverse(base_quat, (com_w[li] - base_pos).unsqueeze(0))[0]
            r_com = math_utils.quat_apply_inverse(base_quat, (com_w[ri] - base_pos).unsqueeze(0))[0]

            def reflect_y(v):
                return torch.tensor([v[0].item(), 2 * MIRROR_C_Y - v[1].item(), v[2].item()])

            r_origin_ref = reflect_y(r_origin)
            r_com_ref = reflect_y(r_com)
            d_origin = l_origin.cpu() - r_origin_ref
            d_com = l_com.cpu() - r_com_ref
            fmt = lambda v: f"({v[0]:+.4f},{v[1]:+.4f},{v[2]:+.4f})"
            emit(
                f"| {l_name}/{r_name} | {fmt(l_origin)} | {fmt(r_origin_ref)} | {fmt(d_origin)} | "
                f"{fmt(l_com)} | {fmt(r_com_ref)} | {fmt(d_com)} |"
            )
        emit("")

        emit("## 2. 足裏の平面フィット (world座標、最下点から3mm以内の頂点)\n")
        emit("| body | pitch[deg] | roll[deg] | 残差RMS[m] | 使用頂点数 | x範囲(base座標)[m] |")
        emit("|---|---|---|---|---|---|")
        sole_x_ranges = {}
        for name in ("ll_ffe", "lr_ffe"):
            bi = robot.body_names.index(name)
            pts_local = link_mesh_points(stage, f"/World/envs/env_0/Robot/{name}")
            if pts_local is None:
                emit(f"| {name} | - | - | - | - | (mesh not found) |")
                continue
            c = pts_local.to(device)
            q = robot.data.body_link_quat_w[0, bi].unsqueeze(0).expand(c.shape[0], -1)
            p = robot.data.body_link_pos_w[0, bi].unsqueeze(0)
            world = (math_utils.quat_apply(q, c) + p).cpu().numpy()
            z_min = world[:, 2].min()
            sole_mask = world[:, 2] <= z_min + 0.003
            sole_world = world[sole_mask]
            pitch_deg, roll_deg, rms = fit_plane_normal(sole_world)
            # base-frame x range of that same vertex set
            sole_world_t = torch.as_tensor(sole_world, dtype=torch.float32, device=device)
            qb = base_quat.expand(sole_world_t.shape[0], -1)
            inb = math_utils.quat_apply_inverse(qb, sole_world_t - base_pos.unsqueeze(0))
            xr = (float(inb[:, 0].min().item()), float(inb[:, 0].max().item()))
            sole_x_ranges[name] = xr
            emit(f"| {name} | {pitch_deg:+.3f} | {roll_deg:+.3f} | {rms:.5f} | {sole_mask.sum()} | {xr[0]:+.4f}..{xr[1]:+.4f} |")
        emit("")

        emit("## 3. 支持範囲とCOMの前後関係\n")
        total_m = masses.sum()
        com_world = (com_w * masses.unsqueeze(-1)).sum(dim=0) / total_m
        com_b = math_utils.quat_apply_inverse(base_quat, (com_world - base_pos).unsqueeze(0))[0]
        emit(f"- 全身COM (base座標): x={com_b[0].item():+.4f} y={com_b[1].item():+.4f} z={com_b[2].item():+.4f}")
        if sole_x_ranges:
            xmin = min(v[0] for v in sole_x_ranges.values())
            xmax = max(v[1] for v in sole_x_ranges.values())
            com_x = com_b[0].item()
            ahead = "前(+x)に出ている" if com_x > xmax else ("後ろ(-x)に出ている" if com_x < xmin else "支持範囲の内側")
            emit(f"- 支持範囲(x, 両足合成): {xmin:+.4f}..{xmax:+.4f} m")
            emit(f"- COM xは支持範囲に対して: **{ahead}** (COM x={com_x:+.4f}, 支持範囲前端={xmax:+.4f}, 後端={xmin:+.4f})")

    env.close()
    with open(args_cli.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[shape_diag_p5_7] wrote {args_cli.out}")


if __name__ == "__main__":
    main()
    simulation_app.close()
