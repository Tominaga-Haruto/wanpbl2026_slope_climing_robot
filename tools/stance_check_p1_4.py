"""P1-4 continuation diagnostics (2026-09-16 instructions). Diagnostic only, does not touch training cfg.

1. confirms reset_robot_joints / reset_base velocity randomisation / push are actually disabled in the
   stance_check.py evaluation cfg (read + report, no new code needed for this part -- see build_env_cfg
   below, copied from stance_check.py).
2. near-rigid joints (stiffness=1000, damping=50 on every actuator group): does the robot still fall
   forward? If so the cause is not PD gain.
3. time-varying sole contact at t=0/0.1/0.5s: for each foot, counts sole-mesh vertices within 5mm of
   ground height (a proxy for "how much of the sole is actually touching", since Isaac Lab's ContactSensor
   does not expose individual contact points) plus their world x-range, net contact normal force (world z
   of net_forces_w) and base height.
4. left/right symmetry (reference only): per-link mass and COM in base coordinates (y sign-flipped for
   the right-side links so left/right can be compared directly), plus whole-body COM y.

Run from D:\\Tominaga\\IsaacLab.
"""

import argparse
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--out", type=str, default=r"D:\Tominaga\slope-climbing-robot\tools\logs\P1_4_followup.md")
parser.add_argument("--section", type=str, default="all", choices=["1", "2", "3", "4", "all"])
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.headless = True
sys.argv = [sys.argv[0]]

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------

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


def build_env_cfg(num_envs, seed, device, stiffness_abs=None, damping_abs=None):
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
    cfg.scene.terrain.debug_vis = False

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
    bv.debug_vis = False
    bv.heading_command = False
    bv.ranges.heading = None
    bv.rel_heading_envs = 0.0
    bv.rel_standing_envs = 0.0
    bv.resampling_time_range = (1.0e6, 1.0e6)

    cfg.episode_length_s = 15.0

    if stiffness_abs is not None:
        for act in cfg.scene.robot.actuators.values():
            act.stiffness = stiffness_abs
    if damping_abs is not None:
        for act in cfg.scene.robot.actuators.values():
            act.damping = damping_abs
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


def section_1_event_check(emit, cfg):
    emit("## 1. reset_robot_joints / reset_base 速度 / push が切れているかの確認\n")
    rj = cfg.events.reset_robot_joints.params
    rb = cfg.events.reset_base.params
    emit(f"- reset_robot_joints.position_range = {rj['position_range']} (evaluation cfg; training cfg is (0.5, 1.5))")
    emit(f"- reset_robot_joints.velocity_range = {rj['velocity_range']}")
    emit(f"- reset_base.velocity_range = {rb['velocity_range']}")
    emit(f"- reset_base.pose_range = {rb['pose_range']}")
    emit(f"- events.push_robot = {cfg.events.push_robot}")
    emit(f"- events.base_external_force_torque = {cfg.events.base_external_force_torque}")
    emit("")
    emit("この試験用cfgでは全て中立化されている(position_range=(1.0,1.0)=スケールなし、"
         "velocity_range全て0、push/external forceはNone)。よって以下の転倒試験は"
         "初期化ランダム性の影響を受けない。\n")


def section_2_high_stiffness(emit, device, seed, num_envs):
    emit("## 2. 関節をほぼ固定 (stiffness=1000, damping=50 全グループ)\n")
    cfg = build_env_cfg(num_envs, seed, device, stiffness_abs=1000.0, damping_abs=50.0)
    env = ManagerBasedRLEnv(cfg=cfg)
    robot = env.scene["robot"]
    dt = env.step_dt
    N = env.num_envs
    zero = torch.zeros(N, env.action_manager.total_action_dim, device=device)
    with torch.inference_mode():
        env.reset()
        stiff = {g: float(a.stiffness[0, 0]) for g, a in robot.actuators.items()}
        damp = {g: float(a.damping[0, 0]) for g, a in robot.actuators.items()}
        emit(f"- 実効 stiffness: {stiff}")
        emit(f"- 実効 damping: {damp}\n")

        start_pos = robot.data.root_link_pos_w[:, :2].clone()
        alive = torch.ones(N, dtype=torch.bool, device=device)
        fell_at = torch.full((N,), -1, dtype=torch.long, device=device)
        pitch_fall = torch.zeros(N, device=device)
        dx_fall = torch.zeros(N, device=device)

        def read():
            _, p, _ = math_utils.euler_xyz_from_quat(robot.data.root_link_quat_w)
            return math_utils.wrap_to_pi(p), (robot.data.root_link_pos_w[:, :2] - start_pos)[:, 0]

        prev_pitch, prev_dx = read()
        n_5s = int(round(5.0 / dt))
        for k in range(n_5s):
            _, _, dones, _, _ = env.step(zero)
            dones = dones.to(torch.bool)
            newly = alive & dones
            pitch_fall[newly] = prev_pitch[newly]
            dx_fall[newly] = prev_dx[newly]
            fell_at[newly] = k
            alive &= ~dones
            prev_pitch, prev_dx = read()
            prev_pitch = torch.where(alive, prev_pitch, pitch_fall)
            prev_dx = torch.where(alive, prev_dx, dx_fall)

        n_fell = int((~alive).sum().item())
        fwd = int((pitch_fall[~alive] > 0).sum().item()) if n_fell else 0
        emit(f"| 量 | 値 |\n|---|---|")
        emit(f"| 5s時点の転倒率 | {n_fell / N:.3f} ({n_fell}/{N}) |")
        emit(f"| 前に倒れた数 (pitch>0) | {fwd} |")
        emit(f"| 後ろに倒れた数 (pitch<0) | {n_fell - fwd} |")
        if n_fell:
            emit(f"| 転倒時 pitch 平均 [deg] | {torch.rad2deg(pitch_fall[~alive]).mean().item():+.2f} |")
            emit(f"| 転倒時 x変位 平均 [m] | {dx_fall[~alive].mean().item():+.4f} |")
        if int(alive.sum().item()):
            emit(f"| 5s生存 env の x変位 平均 [m] | {prev_dx[alive].mean().item():+.4f} |")
        emit("")
    env.close()
    return n_fell, N, fwd


def section_3_contact_timeseries(emit, device, seed, num_envs):
    emit("## 3. 足裏接地の時間変化 (0 / 0.1 / 0.5 s)\n")
    emit("Isaac Lab の ContactSensor は個々の接触点ではなく合力しか持たないため、"
         "「接地点数」の代わりに、足裏メッシュの頂点(接地面から1cm以内、stance_checkと同じ定義)のうち"
         "実際に地面高さ±5mm以内にあるものの数とx範囲を使う。合力(法線方向)はcontact sensorのnet_forces_wのz成分。\n")
    cfg = build_env_cfg(num_envs, seed, device)
    env = ManagerBasedRLEnv(cfg=cfg)
    robot = env.scene["robot"]
    sensor = env.scene.sensors["contact_forces"]
    stage = env.scene.stage
    dt = env.step_dt
    N = env.num_envs
    zero = torch.zeros(N, env.action_manager.total_action_dim, device=device)

    foot_ids, foot_names = sensor.find_bodies(".*ffe")
    robot_foot_ids = [robot.body_names.index(n) for n in foot_names]

    sole_pts = {}
    for name in foot_names:
        pts = link_mesh_points(stage, f"/World/envs/env_0/Robot/{name}")
        if pts is None:
            continue
        z = pts[:, 2]
        sole_pts[name] = pts[z <= z.min() + 0.01].to(device)

    with torch.inference_mode():
        env.reset()
        ground_z = env.scene.env_origins[:, 2]
        n_checks = [0, int(round(0.1 / dt)), int(round(0.5 / dt))]
        n_checks_sorted = sorted(n_checks)
        results = {}
        step = 0
        for target in n_checks_sorted:
            while step < target:
                env.step(zero)
                step += 1
            base_h = (robot.data.root_link_pos_w[:, 2] - ground_z).mean().item()
            row = {"base_h": base_h}
            for fname, bi in zip(foot_names, robot_foot_ids):
                pts = sole_pts.get(fname)
                if pts is None:
                    continue
                q = robot.data.body_link_quat_w[:, bi]
                p = robot.data.body_link_pos_w[:, bi]
                # env 0 only, for a concrete readout
                world = math_utils.quat_apply(q[0:1].expand(pts.shape[0], -1), pts) + p[0:1]
                gz = ground_z[0]
                near = (world[:, 2] - gz).abs() <= 0.005
                n_near = int(near.sum().item())
                if n_near:
                    xr = (world[near, 0].min().item(), world[near, 0].max().item())
                else:
                    xr = (float("nan"), float("nan"))
                fidx = foot_ids[foot_names.index(fname)]
                fz = sensor.data.net_forces_w[0, fidx, 2].item()
                row[fname] = (n_near, xr, fz)
            results[target] = row

    emit("| t [s] | base高さ [m] | 足 | 接地頂点数 | x範囲 [m] | 法線力Fz [N] |")
    emit("|---|---|---|---|---|---|")
    for target in n_checks_sorted:
        row = results[target]
        t_s = target * dt
        first = True
        for fname in foot_names:
            if fname not in row:
                continue
            n_near, xr, fz = row[fname]
            xr_s = f"{xr[0]:+.3f}..{xr[1]:+.3f}" if n_near else "-"
            emit(f"| {t_s:.2f} | {row['base_h']:.4f} | {fname} | {n_near} | {xr_s} | {fz:+.2f} |")
    emit("")
    emit(f"(P3a参考: 公称姿勢のbase高さは 0.3758 -> 0.3613 m, 1.45cm沈む)\n")
    env.close()


def section_4_symmetry(emit, device, seed, num_envs):
    emit("## 4. 左右対称性 (参考)\n")
    cfg = build_env_cfg(num_envs, seed, device)
    env = ManagerBasedRLEnv(cfg=cfg)
    robot = env.scene["robot"]
    with torch.inference_mode():
        env.reset()
        masses = robot.data.default_mass[0].to(device)
        com_w = robot.data.body_com_pos_w[0]
        base_pos = robot.data.root_link_pos_w[0]
        base_quat = robot.data.root_link_quat_w[0:1]
        total_m = masses.sum()
        com_world = (com_w * masses.unsqueeze(-1)).sum(dim=0) / total_m
        com_b = math_utils.quat_apply_inverse(base_quat, (com_world - base_pos).unsqueeze(0))[0]
        emit(f"- 全身 COM (base座標): x={com_b[0]:+.4f} y={com_b[1]:+.4f} z={com_b[2]:+.4f}, 全質量 {total_m.item():.4f} kg\n")
        emit("| 左リンク | 質量[kg] | COM x | COM y | COM z | 右リンク | 質量[kg] | COM x | COM y(反転) | COM z | 質量差 | y差(反転後) |")
        emit("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for l_name, r_name in LINK_PAIRS:
            li = robot.body_names.index(l_name)
            ri = robot.body_names.index(r_name)
            l_com_b = math_utils.quat_apply_inverse(base_quat, (com_w[li] - base_pos).unsqueeze(0))[0]
            r_com_b = math_utils.quat_apply_inverse(base_quat, (com_w[ri] - base_pos).unsqueeze(0))[0]
            lm, rm = masses[li].item(), masses[ri].item()
            r_y_flipped = -r_com_b[1].item()
            emit(
                f"| {l_name} | {lm:.4f} | {l_com_b[0]:+.4f} | {l_com_b[1]:+.4f} | {l_com_b[2]:+.4f} "
                f"| {r_name} | {rm:.4f} | {r_com_b[0]:+.4f} | {r_y_flipped:+.4f} | {r_com_b[2]:+.4f} "
                f"| {lm - rm:+.5f} | {l_com_b[1].item() - r_y_flipped:+.5f} |"
            )
        emit("")
    env.close()


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"
    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    emit("# P1-4 続き: 立位診断\n")
    sec = args_cli.section
    if sec in ("1", "all"):
        ref_cfg = build_env_cfg(args_cli.num_envs, args_cli.seed, device)
        section_1_event_check(emit, ref_cfg)
    if sec in ("2", "all"):
        section_2_high_stiffness(emit, device, args_cli.seed, args_cli.num_envs)
    if sec in ("3", "all"):
        section_3_contact_timeseries(emit, device, args_cli.seed, args_cli.num_envs)
    if sec in ("4", "all"):
        section_4_symmetry(emit, device, args_cli.seed, args_cli.num_envs)

    out = args_cli.out if sec == "all" else args_cli.out.replace(".md", f"_sec{sec}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[stance_check_p1_4] wrote {out}")


if __name__ == "__main__":
    main()
    simulation_app.close()
