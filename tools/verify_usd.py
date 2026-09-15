"""Verify a converted robot USD: joint count/names/types, axes, limits,
maxJointVelocity, per-body mass and total, no fixed joints.

Must run inside Isaac Sim (SimulationApp) since it needs pxr.

Usage:
    isaaclab.bat -p tools/verify_usd.py <usd_path> --headless
"""
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("usd_path")
args, _ = ap.parse_known_args()

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import sys
import functools
from pxr import Usd, UsdPhysics, UsdGeom, PhysxSchema

print = functools.partial(print, flush=True)

print("=" * 70, flush=True)
print(f"USD: {args.usd_path}", flush=True)
print("=" * 70, flush=True)

stage = Usd.Stage.Open(args.usd_path)
if stage is None:
    print("ERROR: Usd.Stage.Open returned None", flush=True)
    simulation_app.close()
    sys.exit(1)
print(f"Stage opened OK. Root layer: {stage.GetRootLayer().identifier}", flush=True)

joints = []
bodies = []
for prim in stage.Traverse():
    type_name = prim.GetTypeName()
    if type_name in ("PhysicsRevoluteJoint", "PhysicsFixedJoint", "PhysicsPrismaticJoint", "PhysicsSphericalJoint"):
        joints.append((prim, type_name))
    if prim.HasAPI(UsdPhysics.MassAPI):
        bodies.append(prim)

print(f"\nJoint count: {len(joints)}")
type_counts = {}
for prim, tname in joints:
    type_counts[tname] = type_counts.get(tname, 0) + 1
print(f"Joint types: {type_counts}")

print("\n--- Joint details ---")
for prim, tname in joints:
    name = prim.GetName()
    joint_api = UsdPhysics.RevoluteJoint(prim) if tname == "PhysicsRevoluteJoint" else None
    axis = joint_api.GetAxisAttr().Get() if joint_api else None
    lower = joint_api.GetLowerLimitAttr().Get() if joint_api else None
    upper = joint_api.GetUpperLimitAttr().Get() if joint_api else None

    body0_rel = UsdPhysics.Joint(prim).GetBody0Rel().GetTargets()
    body1_rel = UsdPhysics.Joint(prim).GetBody1Rel().GetTargets()
    body0 = body0_rel[0].name if body0_rel else None
    body1 = body1_rel[0].name if body1_rel else None

    max_vel = None
    if prim.HasAPI(PhysxSchema.PhysxJointAPI):
        physx_joint = PhysxSchema.PhysxJointAPI(prim)
        max_vel = physx_joint.GetMaxJointVelocityAttr().Get()

    drive_max_force = None
    drive = UsdPhysics.DriveAPI.Get(prim, "angular")
    if drive:
        drive_max_force = drive.GetMaxForceAttr().Get()

    print(f"  {name} ({tname}): parent={body0} child={body1} axis={axis} lower={lower} upper={upper} "
          f"maxJointVelocity={max_vel} driveMaxForce={drive_max_force}")

print(f"\n--- Body masses ({len(bodies)} bodies with MassAPI) ---")
total_mass = 0.0
for prim in bodies:
    mass_api = UsdPhysics.MassAPI(prim)
    mass = mass_api.GetMassAttr().Get()
    print(f"  {prim.GetName()}: mass={mass}")
    if mass:
        total_mass += mass
print(f"\nTotal mass: {total_mass:.6f} kg")

print("\n--- All prim names containing 'base'/'hr'/'haa'/'hfe'/'kfe'/'ffe' (body check) ---")
for prim in stage.Traverse():
    n = prim.GetName().lower()
    if any(k in n for k in ["base", "_hr", "_haa", "_hfe", "_kfe", "_ffe"]) and prim.GetTypeName() in ("Xform",):
        print(f"  {prim.GetPath()}  type={prim.GetTypeName()}")

simulation_app.close()
