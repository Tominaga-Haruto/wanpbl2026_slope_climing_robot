"""P3 shape diagnostics (2026-09-16 instructions). Diagnostic only, does not touch training cfg.

1. Default pose: sole-plane tilt (pitch/roll vs ground) and x-range of the lowest collision points,
   per foot, in base coordinates. Also each foot's minimum world z at the exact spawn state (before
   any physics step), to explain why exp03 saw 0 vs 6 near-ground sole vertices at t=0.
2. Left/right asymmetry source: LL_HR / LR_HR joint origins in base coordinates, the midpoint y of
   the hip spacing, and whole-body COM (x,y,z) -- to separate "base origin off-centre" from
   "leg geometry itself asymmetric".
3. USD collision approximation type + vertex count for ll_ffe / lr_ffe.

Run from D:\\Tominaga\\IsaacLab.
"""

import argparse
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_envs", type=int, default=4)
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--out", type=str, default=r"D:\Tominaga\slope-climbing-robot\tools\logs\P3_shape_diag.md")
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
        return None, None
    xf = UsdGeom.XformCache(Usd.TimeCode.Default())

    def has_collision(p):
        q = p
        while q.IsValid() and q.GetPath() != link.GetPath().GetParentPath():
            if q.HasAPI(UsdPhysics.CollisionAPI):
                return True
            q = q.GetParent()
        return False

    def approximation_of(p):
        q = p
        while q.IsValid() and q.GetPath() != link.GetPath().GetParentPath():
            if q.HasAPI(UsdPhysics.MeshCollisionAPI):
                api = UsdPhysics.MeshCollisionAPI(q)
                attr = api.GetApproximationAttr()
                if attr and attr.HasAuthoredValue():
                    return attr.Get()
            q = q.GetParent()
        return None

    for want_collision in ([True, False] if collision_only else [False]):
        pts = []
        approx = None
        for prim in Usd.PrimRange(link, Usd.TraverseInstanceProxies()):
            if not prim.IsA(UsdGeom.Mesh):
                continue
            if want_collision and not has_collision(prim):
                continue
            if approx is None:
                approx = approximation_of(prim)
            mesh = UsdGeom.Mesh(prim)
            raw = mesh.GetPointsAttr().Get()
            if not raw:
                continue
            m = xf.ComputeRelativeTransform(prim, link)[0]
            for p in raw:
                q = m.Transform(Gf.Vec3d(p[0], p[1], p[2]))
                pts.append([q[0], q[1], q[2]])
        if pts:
            return torch.tensor(pts, dtype=torch.float32), approx
    return None, None


def fit_plane_tilt(points_xyz):
    """Least-squares plane z = a*x + b*y + c through points (N,3); returns (pitch_deg, roll_deg).
    pitch = tilt about the y-axis (from the x-slope a), roll = tilt about the x-axis (from the
    y-slope b), small-angle atan approximation."""
    pts = points_xyz.numpy()
    A = np.stack([pts[:, 0], pts[:, 1], np.ones(pts.shape[0])], axis=1)
    b = pts[:, 2]
    coef, *_ = np.linalg.lstsq(A, b, rcond=None)
    a_x, a_y, _ = coef
    pitch_deg = np.degrees(np.arctan(a_x))
    roll_deg = np.degrees(np.arctan(a_y))
    return float(pitch_deg), float(roll_deg)


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
        base_pos = robot.data.root_link_pos_w.clone()
        base_quat = robot.data.root_link_quat_w.clone()
        ground_z = env.scene.env_origins[0, 2].item()

        emit("# P3 形状診断\n")
        emit("## 1. 既定姿勢: 足裏の傾きとx範囲、初期の地面クリアランス\n")
        emit("| body | 接地面 pitch[deg] | roll[deg] | x範囲(sole)[m] | 最下点の世界z(spawn直後)[m] | 地面までの隙間[m] |")
        emit("|---|---|---|---|---|---|")
        min_z_by_foot = {}
        for name in ("ll_ffe", "lr_ffe"):
            bi = robot.body_names.index(name)
            pts, approx = link_mesh_points(stage, f"/World/envs/env_0/Robot/{name}")
            if pts is None:
                emit(f"| {name} | - | - | - | - | (mesh not found) |")
                continue
            c = pts.to(device)
            q = robot.data.body_link_quat_w[0, bi].unsqueeze(0).expand(c.shape[0], -1)
            p = robot.data.body_link_pos_w[0, bi].unsqueeze(0)
            world = math_utils.quat_apply(q, c) + p
            qb = base_quat[0].unsqueeze(0).expand(c.shape[0], -1)
            inb = math_utils.quat_apply_inverse(qb, world - base_pos[0].unsqueeze(0))
            sole_mask = inb[:, 2] <= inb[:, 2].min() + 0.01
            sole_b = inb[sole_mask].cpu()
            pitch_deg, roll_deg = fit_plane_tilt(sole_b)
            xr = (sole_b[:, 0].min().item(), sole_b[:, 0].max().item())
            min_world_z = world[:, 2].min().item()
            min_z_by_foot[name] = min_world_z
            clearance = min_world_z - ground_z
            emit(f"| {name} | {pitch_deg:+.3f} | {roll_deg:+.3f} | {xr[0]:+.4f}..{xr[1]:+.4f} | {min_world_z:.5f} | {clearance:+.5f} |")
        if len(min_z_by_foot) == 2:
            zs = list(min_z_by_foot.values())
            emit(f"\n最下点の左右差 (ll - lr) = {zs[0]-zs[1]:+.5f} m。")
            emit("実験03の t=0 で片足0点・もう片足6点だった理由: 上表の「地面までの隙間」が左右で異なれば、"
                 "隙間が小さい/負の側から先に接地点(頂点)が地面±5mm以内に入るため。"
                 "隙間がほぼ同じであれば、足裏メッシュの傾き(pitch/roll)自体の左右差が"
                 "「頂点が一様な高さでなく稜線状に地面へ近づく」原因になっている。\n")

        emit("## 2. 左右非対称の出どころ\n")
        for name in ("LL_HR", "LR_HR"):
            ji = robot.joint_names.index(name)
            # joint origin: use the parent body (base) frame position of the joint via body_link_pos of
            # the child link's parent-relative offset is not directly exposed; approximate with the
            # child link (ll_hr/lr_hr) origin in base coordinates, which is co-located with the joint
            # for a revolute joint with zero offset in this URDF.
            bname = name.lower()
            bi = robot.body_names.index(bname)
            rel = math_utils.quat_apply_inverse(base_quat[0:1], robot.data.body_link_pos_w[0:1, bi] - base_pos[0:1])
            emit(f"- {name} (={bname} link origin, base座標): x={rel[0,0].item():+.4f} y={rel[0,1].item():+.4f} z={rel[0,2].item():+.4f}")
        ll_bi = robot.body_names.index("ll_hr")
        lr_bi = robot.body_names.index("lr_hr")
        ll_rel = math_utils.quat_apply_inverse(base_quat[0:1], robot.data.body_link_pos_w[0:1, ll_bi] - base_pos[0:1])
        lr_rel = math_utils.quat_apply_inverse(base_quat[0:1], robot.data.body_link_pos_w[0:1, lr_bi] - base_pos[0:1])
        mid_y = (ll_rel[0, 1].item() + lr_rel[0, 1].item()) / 2.0
        emit(f"- 股関節間隔の中点 y (base座標) = {mid_y:+.4f} m （base原点=0との差が「base原点が中心からずれている」量）")

        masses = robot.data.default_mass[0].to(device)
        com_w = robot.data.body_com_pos_w[0]
        total_m = masses.sum()
        com_world = (com_w * masses.unsqueeze(-1)).sum(dim=0) / total_m
        com_b = math_utils.quat_apply_inverse(base_quat[0:1], (com_world - base_pos[0]).unsqueeze(0))[0]
        emit(f"- 全身COM (base座標) = ({com_b[0].item():+.4f}, {com_b[1].item():+.4f}, {com_b[2].item():+.4f})")
        emit(f"\n判定: 股関節間隔の中点yが0に近ければ「base原点は中心にある」→ P1-4で見た-0.038〜-0.040mの")
        emit("系統的オフセットは股関節から先の脚(リンク)の形状自体が左右非対称であることに由来する。")
        emit("中点yが0から大きくずれていれば、base原点そのものが中心から外れていることが主因。\n")

        emit("## 3. 足の衝突形状\n")
        emit("| body | 近似の種類 | 頂点数 |")
        emit("|---|---|---|")
        for name in ("ll_ffe", "lr_ffe"):
            pts, approx = link_mesh_points(stage, f"/World/envs/env_0/Robot/{name}")
            n = pts.shape[0] if pts is not None else 0
            emit(f"| {name} | {approx if approx else '(MeshCollisionAPIのapproximation属性なし=デフォルト/トライアングルメッシュの可能性)'} | {n} |")

    env.close()
    with open(args_cli.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[shape_diag_p3] wrote {args_cli.out}")


if __name__ == "__main__":
    main()
    simulation_app.close()
