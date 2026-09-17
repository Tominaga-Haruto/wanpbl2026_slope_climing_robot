# Copyright (c) 2022-2024, The Berkeley Humanoid Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import ContactSensor

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def feet_air_time(
    env: ManagerBasedRLEnv, command_name: str, sensor_cfg: SceneEntityCfg, threshold_min: float, threshold_max: float,
    yaw_gate: bool = False,
) -> torch.Tensor:
    """Reward long steps taken by the feet using L2-kernel.

    This function rewards the agent for taking steps that are longer than a threshold. This helps ensure
    that the robot lifts its feet off the ground and takes steps. The reward is computed as the sum of
    the time for which the feet are in the air.

    If the commands are small (i.e. the agent is not supposed to take a step), then the reward is zero.

    yaw_gate: if False (default, unchanged behaviour), the reward is zeroed whenever the commanded
    linear velocity magnitude |(vx,vy)| <= 0.1, regardless of the commanded yaw rate -- so a pure
    turn-in-place command (vx=vy=0, wz large) always gets zero reward here even if the robot steps
    properly. If True, the gate instead opens when EITHER |(vx,vy)| > 0.1 OR |wz| > 0.1, so turn-in-
    place commands can also earn this reward (2026-09-17, exp06 J0-1).
    """
    # extract the used quantities (to enable type-hinting)
    contact_sensor: ContactSensor = env.scene.sensors[sensor_cfg.name]
    # compute the reward
    first_contact = contact_sensor.compute_first_contact(env.step_dt)[:, sensor_cfg.body_ids]
    last_air_time = contact_sensor.data.last_air_time[:, sensor_cfg.body_ids]
    # negative reward for small steps
    air_time = (last_air_time - threshold_min) * first_contact
    # no reward for large steps
    air_time = torch.clamp(air_time, max=threshold_max - threshold_min)
    reward = torch.sum(air_time, dim=1)
    # no reward for zero command
    command = env.command_manager.get_command(command_name)
    if yaw_gate:
        reward *= (torch.norm(command[:, :2], dim=1) > 0.1) | (command[:, 2].abs() > 0.1)
    else:
        reward *= torch.norm(command[:, :2], dim=1) > 0.1
    return reward


def feet_air_time_positive_biped(env, command_name: str, threshold_min: float, threshold_max: float,
                                 sensor_cfg: SceneEntityCfg, yaw_gate: bool = False) -> torch.Tensor:
    """Reward long steps taken by the feet for bipeds.

    This function rewards the agent for taking steps up to a specified threshold and also keep one foot at
    a time in the air.

    If the commands are small (i.e. the agent is not supposed to take a step), then the reward is zero.

    yaw_gate: see feet_air_time's docstring -- same semantics (2026-09-17, exp06 J0-1).
    """
    contact_sensor: ContactSensor = env.scene.sensors[sensor_cfg.name]
    # compute the reward
    air_time = contact_sensor.data.current_air_time[:, sensor_cfg.body_ids]
    contact_time = contact_sensor.data.current_contact_time[:, sensor_cfg.body_ids]
    in_contact = contact_time > 0.0
    in_mode_time = torch.where(in_contact, contact_time, air_time)
    single_stance = torch.sum(in_contact.int(), dim=1) == 1
    reward = torch.min(torch.where(single_stance.unsqueeze(-1), in_mode_time, 0.0), dim=1)[0]
    reward = torch.clamp(reward, max=threshold_max)
    # no reward for small steps
    reward *= reward > threshold_min
    # no reward for zero command
    command = env.command_manager.get_command(command_name)
    if yaw_gate:
        reward *= (torch.norm(command[:, :2], dim=1) > 0.1) | (command[:, 2].abs() > 0.1)
    else:
        reward *= torch.norm(command[:, :2], dim=1) > 0.1
    return reward


def feet_slide(env, sensor_cfg: SceneEntityCfg, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    """Penalize feet sliding.

    This function penalizes the agent for sliding its feet on the ground. The reward is computed as the
    norm of the linear velocity of the feet multiplied by a binary contact sensor. This ensures that the
    agent is penalized only when the feet are in contact with the ground.
    """
    # Penalize feet sliding
    contact_sensor: ContactSensor = env.scene.sensors[sensor_cfg.name]
    contacts = contact_sensor.data.net_forces_w_history[:, :, sensor_cfg.body_ids, :].norm(dim=-1).max(dim=1)[0] > 1.0
    asset = env.scene[asset_cfg.name]

    body_vel = asset.data.body_lin_vel_w[:, asset_cfg.body_ids, :2]
    reward = torch.sum(body_vel.norm(dim=-1) * contacts, dim=1)
    return reward
