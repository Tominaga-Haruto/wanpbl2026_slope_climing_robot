"""Static stance diagnostics: where the COM sits relative to the feet, and which way the robot topples
when the policy is replaced by a zero action (i.e. hold the default joint pose).

Run from D:\\Tominaga\\IsaacLab.
"""

import argparse
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Support-polygon and passive-fall diagnostics.")
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--seed", type=int, default=1234)
parser.add_argument("--hold_s", type=float, default=5.0, help="zero-action hold used for the fall test")
parser.add_argument("--long_s", type=float, default=10.0, help="total horizon for the survivor pitch")
parser.add_argument("--out", type=str, default=r"D:\Tominaga\slope-climbing-robot\tools\logs\stance_check.md")
parser.add_argument("--stiffness_scale", type=float, default=1.0,
                    help="diagnostic only: multiply every actuator group's stiffness by this")
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


def build_env_cfg(num_envs, seed, device, horizon_s):
    """Same neutral evaluation environment measure_crab.py uses, but with the reset noise removed
    so every env starts from the identical nominal pose."""
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
    # nominal pose only: no yaw spread, no velocity, no joint scaling
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

    cfg.episode_length_s = horizon_s + 5.0

    # diagnostic knob only. The training configs are never launched through this script.
    if args_cli.stiffness_scale != 1.0:
        for act in cfg.scene.robot.actuators.values():
            act.stiffness = act.stiffness * args_cli.stiffness_scale
    return cfg


def link_mesh_points(stage, prim_path, collision_only=True):
    """Every mesh vertex under a link, expressed in that link's own frame.

    Walks the link's subtree for UsdGeom.Mesh prims. When ``collision_only`` is set, only meshes that
    carry (or sit under) a PhysicsCollisionAPI are used; if that finds nothing the search falls back to
    all meshes, which is correct here because the URDF->USD conversion shares one mesh between the
    visual and the collision representation.
    """
    link = stage.GetPrimAtPath(prim_path)
    if not link.IsValid():
        return None, False
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
        # the converted robot USD is instanceable, so the geometry lives in a prototype and a plain
        # PrimRange walks straight past it
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
            return torch.tensor(pts, dtype=torch.float32), want_collision
    return None, False


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"
    env = ManagerBasedRLEnv(cfg=build_env_cfg(args_cli.num_envs, args_cli.seed, device, args_cli.long_s))
    robot = env.scene["robot"]

    dt = env.step_dt
    n_hold = int(round(args_cli.hold_s / dt))
    n_long = int(round(args_cli.long_s / dt))
    N = env.num_envs
    lines = []

    def emit(s):
        print(s)
        lines.append(s)

    with torch.inference_mode():
        env.reset()
        # let the articulation settle onto the ground for a moment before reading the nominal pose
        zero = torch.zeros(N, env.action_manager.total_action_dim, device=device)
        for _ in range(10):
            env.step(zero)

        base_pos = robot.data.root_link_pos_w.clone()
        base_quat = robot.data.root_link_quat_w.clone()

        # -- whole-body COM in base coordinates
        masses = robot.data.default_mass.to(device)
        total_m = masses.sum(dim=1, keepdim=True)
        com_w = (robot.data.body_com_pos_w * masses.unsqueeze(-1)).sum(dim=1) / total_m
        com_b = math_utils.quat_apply_inverse(base_quat, com_w - base_pos)

        emit(f"# stance_check (stiffness x{args_cli.stiffness_scale:g})")
        emit("")
        emit(f"- num_envs {N}, flat ground, all randomisation neutralised, nominal joint pose (scale 1.0)")
        emit(f"- total mass {total_m[0].item():.3f} kg, step_dt {dt}")
        stiff = {g: float(a.stiffness[0, 0]) if torch.is_tensor(a.stiffness) else float(a.stiffness)
                 for g, a in robot.actuators.items()}
        damp = {g: float(a.damping[0, 0]) if torch.is_tensor(a.damping) else float(a.damping)
                for g, a in robot.actuators.items()}
        emit(f"- actuator stiffness in effect: {stiff}")
        emit(f"- actuator damping in effect: {damp}")
        emit("")
        emit("## 1. whole-body COM in base coordinates [m]")
        emit("")
        emit("| x | y | z |")
        emit("|---|---|---|")
        emit(f"| {com_b[0,0].item():+.4f} | {com_b[0,1].item():+.4f} | {com_b[0,2].item():+.4f} |")
        emit("")

        # -- foot collision extents in base coordinates
        stage = env.scene.stage
        ground_z = env.scene.env_origins[0, 2].item()
        emit(f"- base height above ground at the nominal pose: {base_pos[0,2].item() - ground_z:+.4f} m")
        emit("")
        emit("## 2. foot geometry extent in base coordinates [m]")
        emit("")
        emit("mesh vertices of each foot link, taken in the link frame and transformed by the simulated")
        emit("link pose into base coordinates. 'sole' rows keep only the vertices within 1 cm of that")
        emit("foot's lowest point, which is the part that actually forms the support polygon.")
        emit("")
        emit("| body | set | x min | x max | y min | y max | z min | z max |")
        emit("|---|---|---|---|---|---|---|---|")
        sole_x = []
        for name in ("lr_ffe", "ll_ffe"):
            bi = robot.body_names.index(name)
            pts, used_collision = link_mesh_points(stage, f"/World/envs/env_0/Robot/{name}")
            if pts is None:
                kinds = sorted({p.GetTypeName() for p in Usd.PrimRange(
                    stage.GetPrimAtPath(f"/World/envs/env_0/Robot/{name}"), Usd.TraverseInstanceProxies())})
                emit(f"| {name} | - | (no mesh found; prim types: {kinds}) | | | | | |")
                continue
            c = pts.to(device)
            q = robot.data.body_link_quat_w[0, bi].unsqueeze(0).expand(c.shape[0], -1)
            p = robot.data.body_link_pos_w[0, bi].unsqueeze(0)
            world = math_utils.quat_apply(q, c) + p
            qb = base_quat[0].unsqueeze(0).expand(c.shape[0], -1)
            inb = math_utils.quat_apply_inverse(qb, world - base_pos[0].unsqueeze(0))
            for label, sel in (("whole link", torch.ones(inb.shape[0], dtype=torch.bool, device=device)),
                               ("sole", inb[:, 2] <= inb[:, 2].min() + 0.01)):
                s = inb[sel]
                lo, hi = s.min(dim=0)[0], s.max(dim=0)[0]
                emit(
                    f"| {name} | {label} | {lo[0]:+.4f} | {hi[0]:+.4f} | {lo[1]:+.4f} | {hi[1]:+.4f} "
                    f"| {lo[2]:+.4f} | {hi[2]:+.4f} |"
                )
                if label == "sole":
                    sole_x.append((lo[0].item(), hi[0].item()))
            emit(f"| {name} | (source) | {'collision meshes' if used_collision else 'all meshes'} "
                 f"| {c.shape[0]} verts | | | | |")
        emit("")
        if sole_x:
            xmin = min(v[0] for v in sole_x)
            xmax = max(v[1] for v in sole_x)
            cx = com_b[0, 0].item()
            emit(f"- support polygon in x (soles): {xmin:+.4f} .. {xmax:+.4f} m, width {xmax - xmin:.4f} m")
            emit(f"- centre of support x = {(xmin + xmax) / 2:+.4f} m, COM x = {cx:+.4f} m")
            emit(f"- margin from COM to front edge (+x): {xmax - cx:+.4f} m")
            emit(f"- margin from COM to rear edge (-x): {cx - xmin:+.4f} m")
            emit("")

        emit("## 3. foot body origin in base coordinates [m]")
        emit("")
        emit("| body | x | y | z |")
        emit("|---|---|---|---|")
        for name in ("lr_ffe", "ll_ffe"):
            bi = robot.body_names.index(name)
            rel = math_utils.quat_apply_inverse(base_quat[0:1], robot.data.body_link_pos_w[0:1, bi] - base_pos[0:1])
            emit(f"| {name} | {rel[0,0].item():+.4f} | {rel[0,1].item():+.4f} | {rel[0,2].item():+.4f} |")
        emit("")

        # -- passive fall test: hold the default pose and see which way it goes
        env.reset()
        start_pos = robot.data.root_link_pos_w[:, :2].clone()

        def read_state():
            _, p, _ = math_utils.euler_xyz_from_quat(robot.data.root_link_quat_w)
            return math_utils.wrap_to_pi(p), (robot.data.root_link_pos_w[:, :2] - start_pos)[:, 0]

        alive = torch.ones(N, dtype=torch.bool, device=device)
        fell_at = torch.full((N,), -1, dtype=torch.long, device=device)
        # a terminated env is auto-reset before step() returns, so the last pre-reset sample is the
        # one that describes the fall; keep the previous step's reading and bank that.
        pitch_at_fall = torch.zeros(N, device=device)
        dx_at_fall = torch.zeros(N, device=device)
        prev_pitch, prev_dx = read_state()
        hold_pitch = prev_pitch.clone()
        hold_dx = prev_dx.clone()
        n_sag = int(round(0.5 / dt))
        sag = None
        for k in range(n_long):
            _, _, dones, _, _ = env.step(zero)
            dones = dones.to(torch.bool)
            newly = alive & dones
            pitch_at_fall[newly] = prev_pitch[newly]
            dx_at_fall[newly] = prev_dx[newly]
            fell_at[newly] = k
            alive &= ~dones
            cur_pitch, cur_dx = read_state()
            # freeze the reading for envs that have already fallen
            prev_pitch = torch.where(alive, cur_pitch, pitch_at_fall)
            prev_dx = torch.where(alive, cur_dx, dx_at_fall)
            if k == n_sag - 1:
                # how far each joint has sagged away from its PD target while holding the pose
                sag = (robot.data.joint_pos_target - robot.data.joint_pos)[alive].mean(dim=0).clone()
                sag_n = int(alive.sum().item())
            if k == n_hold - 1:
                hold_alive = alive.clone()
                hold_fell = (~alive).clone()
                hold_pitch = prev_pitch.clone()
                hold_dx = prev_dx.clone()

        pitch, _ = read_state()
        pitch = torch.where(alive, pitch, pitch_at_fall)

    n_fell_hold = int(hold_fell.sum().item())
    fwd = int((pitch_at_fall[hold_fell] > 0).sum().item()) if n_fell_hold else 0
    bwd = n_fell_hold - fwd
    emit(f"## 4. zero-action hold ({args_cli.hold_s:.0f} s, then {args_cli.long_s:.0f} s total)")
    emit("")
    emit("action = 0 means the PD target equals the default joint pose (use_default_offset=True).")
    emit("values for a fallen env are the last reading before it terminated (the env is auto-reset")
    emit("inside step(), so the post-step state would be the fresh pose, not the fall).")
    emit("pitch is the base pitch from euler_xyz_from_quat, wrapped to +-pi; the base x displacement")
    emit("is the independent check on which way it went.")
    emit("")
    emit("| quantity | value |")
    emit("|---|---|")
    emit(f"| fall rate at {args_cli.hold_s:.0f} s | {n_fell_hold / N:.3f} ({n_fell_hold}/{N}) |")
    emit(f"| of those, pitch > 0 at fall | {fwd} |")
    emit(f"| of those, pitch < 0 at fall | {bwd} |")
    emit(f"| mean base x displacement at {args_cli.hold_s:.0f} s [m] | {hold_dx.mean().item():+.4f} |")
    n_hold_alive = int(hold_alive.sum().item())
    if n_hold_alive:
        emit(f"| mean base x displacement at {args_cli.hold_s:.0f} s, survivors [m] | "
             f"{hold_dx[hold_alive].mean().item():+.4f} |")
        emit(f"| mean pitch at {args_cli.hold_s:.0f} s, survivors [rad] | "
             f"{hold_pitch[hold_alive].mean().item():+.4f} |")
    if n_fell_hold:
        emit(f"| mean base x displacement at {args_cli.hold_s:.0f} s, fallers [m] | "
             f"{hold_dx[hold_fell].mean().item():+.4f} |")
        emit(f"| mean pitch at fall, fallers [deg] | "
             f"{torch.rad2deg(pitch_at_fall[hold_fell]).mean().item():+.2f} |")
    n_alive_long = int(alive.sum().item())
    emit(f"| survivors at {args_cli.long_s:.0f} s | {n_alive_long}/{N} |")
    if n_alive_long:
        emit(f"| mean pitch at {args_cli.long_s:.0f} s, survivors [rad] | {pitch[alive].mean().item():+.4f} |")
        emit(f"| mean pitch at {args_cli.long_s:.0f} s, survivors [deg] | "
             f"{torch.rad2deg(pitch[alive]).mean().item():+.2f} |")
    emit("")

    if sag is not None:
        emit("## 5. joint sag at 0.5 s of the hold")
        emit("")
        emit("target minus actual joint angle [rad], averaged over the left/right pair and over the")
        emit(f"{sag_n} envs still alive at 0.5 s. A large magnitude means the PD gain is not holding the pose.")
        emit("")
        names = list(robot.joint_names)
        emit("| | HR | HAA | HFE | KFE | FFE |")
        emit("|---|---|---|---|---|---|")
        cells = []
        for p in ("HR", "HAA", "HFE", "KFE", "FFE"):
            idx = [i for i, n in enumerate(names) if n.endswith("_" + p)]
            cells.append(f"{sag[idx].mean().item():+.4f}")
        emit("| target - actual | " + " | ".join(cells) + " |")
        emit("")
        emit("per joint:")
        emit("")
        emit("| " + " | ".join(names) + " |")
        emit("|" + "---|" * len(names))
        emit("| " + " | ".join(f"{v:+.4f}" for v in sag.tolist()) + " |")
        emit("")

    env.close()
    with open(args_cli.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[stance_check] wrote {args_cli.out}")


if __name__ == "__main__":
    main()
    simulation_app.close()
