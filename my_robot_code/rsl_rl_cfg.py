# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlPpoActorCriticCfg, RslRlPpoAlgorithmCfg

from isaaclab.utils import configclass



@configclass
class SkyentificPoclegsRoughPPORunnerCfg(RslRlOnPolicyRunnerCfg):
    num_steps_per_env = 24
    max_iterations = 30000
    save_interval = 200
    experiment_name = "skyentific_poclegs_rough"
    empirical_normalization = False
    policy = RslRlPpoActorCriticCfg(
        init_noise_std=1.0,
        actor_hidden_dims=[512, 256, 128],
        critic_hidden_dims=[512, 256, 128],
        activation="elu",
    )
    algorithm = RslRlPpoAlgorithmCfg(
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.2,
        entropy_coef=0.005,
        num_learning_epochs=5,
        num_mini_batches=4,
        learning_rate=1.0e-3,
        schedule="adaptive",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.01,
        max_grad_norm=1.0,
    )


@configclass
class SkyentificPoclegsFlatPPORunnerCfg(SkyentificPoclegsRoughPPORunnerCfg):
    def __post_init__(self):
        super().__post_init__()

        self.max_iterations = 15000
        self.experiment_name = "skyentific_poclegs_flat"
        self.policy.actor_hidden_dims = [128, 128, 128]
        self.policy.critic_hidden_dims = [128, 128, 128]


# X26b (2026-10-01): mirror-symmetry loss on top of the runner GaitFwd-v0 / GaitCadence-v0 use.
# CLI: replace SkyentificPoclegsRoughPPORunnerCfg below with that runner class if it differs, and fix the
# import path of x26_mirror to where stand_env_cfg.py actually lives (report both).
from isaaclab_rl.rsl_rl import RslRlSymmetryCfg  # noqa: E402

from .stand_env_cfg import X26_MIRROR_LOSS_COEFF, x26_mirror  # noqa: E402


@configclass
class SkyentificPoclegsMirrorPPORunnerCfg(SkyentificPoclegsRoughPPORunnerCfg):
    def __post_init__(self):
        if hasattr(super(), "__post_init__"):
            super().__post_init__()
        self.algorithm.symmetry_cfg = RslRlSymmetryCfg(
            use_data_augmentation=False, use_mirror_loss=True,
            mirror_loss_coeff=X26_MIRROR_LOSS_COEFF, data_augmentation_func=x26_mirror,
        )
