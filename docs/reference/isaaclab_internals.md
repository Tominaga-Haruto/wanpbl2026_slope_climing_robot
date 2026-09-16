# P1-3 Isaac Lab 2.3.2 での確認（grep 結果）

## 1. metrics の式（訂正1 の裏づけ）

`isaaclab/envs/mdp/commands/velocity_command.py:114-124`

```python
def _update_metrics(self):
    # time for which the command was executed
    max_command_time = self.cfg.resampling_time_range[1]
    max_command_step = max_command_time / self._env.step_dt
    # logs data
    self.metrics["error_vel_xy"] += (
        torch.norm(self.vel_command_b[:, :2] - self.robot.data.root_lin_vel_b[:, :2], dim=-1) / max_command_step
    )
    self.metrics["error_vel_yaw"] += (
        torch.abs(self.vel_command_b[:, 2] - self.robot.data.root_ang_vel_b[:, 2]) / max_command_step
    )
```

- `resampling_time_range = (10.0, 10.0)`（親 `velocity_env_cfg.py:96`）、`step_dt = 0.02` なので
  **`max_command_step = 500`**。
- 毎ステップ「誤差 / 500」を足し込み、エピソード終了時に記録する。したがって
  **記録値 = 平均誤差 × エピソード長ステップ数 / 500**。
- 逆算: **正規化値（＝1 ステップ平均誤差） = 生値 × 500 / `Train/mean_episode_length`**。
  ユーザーの訂正1 のとおり。20 s 完走（1000 ステップ）なら生値は平均誤差の 2 倍になる。
- なお `root_lin_vel_b` は COM 速度をフル姿勢の base フレームに落とした値、
  `root_ang_vel_b` も同じく base フレーム（world の z 軸まわりではない）。

## 2. `rel_heading_envs` の意味

`isaaclab/envs/mdp/commands/commands_cfg.py:55-60`

```
rel_heading_envs: float = 1.0
"""The sampled probability of environments where the robots follow the heading-based angular velocity
command (the others follow the sampled angular velocity command). Defaults to 1.0.

This parameter is only used if :attr:`heading_command` is True.
"""
```

使われ方（`velocity_command.py:136-141, 149-163`）:

```python
if self.cfg.heading_command:
    self.heading_target[env_ids] = r.uniform_(*self.cfg.ranges.heading)
    self.is_heading_env[env_ids] = r.uniform_(0.0, 1.0) <= self.cfg.rel_heading_envs
...
def _update_command(self):
    if self.cfg.heading_command:
        env_ids = self.is_heading_env.nonzero(...).flatten()
        heading_error = wrap_to_pi(self.heading_target[env_ids] - self.robot.data.heading_w[env_ids])
        self.vel_command_b[env_ids, 2] = clip(self.cfg.heading_control_stiffness * heading_error, ...)
```

- **`heading_command=True` のときだけ効く。** 本タスクは親から `heading_command=True` /
  `rel_heading_envs=1.0` を継承しているので、**現状は全 env が heading 追従**であり、
  `ranges.ang_vel_z=(-1.0, 1.0)` でサンプルした旋回速度指令は `_update_command` で毎ステップ
  上書きされて捨てられている。
- `rel_heading_envs=0.5` にすると、**半分の env だけ heading 制御になり、残り半分は
  サンプルした旋回速度指令がそのまま生き残る**。E_yawcmd の意図どおりに機能する。
- 旋回追従（S6）が全ランで弱いのは、そもそも「旋回速度を直接指令された経験」がほぼ無いため、
  という説明が成り立つ。

## 3. yaw フレーム版の報酬関数の有無と引数

`isaaclab_tasks/manager_based/locomotion/velocity/mdp/rewards.py`

| 関数 | 行 | 引数 | 使う速度 |
|---|---|---|---|
| `track_lin_vel_xy_yaw_frame_exp` | 88-90 | `(env, std, command_name, asset_cfg=SceneEntityCfg("robot"))` | 重力方向に揃えた（yaw だけの）フレームでの水平速度 |
| `track_ang_vel_z_world_exp` | 103-105 | `(env, command_name, std, asset_cfg=SceneEntityCfg("robot"))` | `root_ang_vel_w[:, 2]`（world の z 軸まわり） |

- **どちらも存在する。** 引数名も現行の `track_lin_vel_xy_exp` / `track_ang_vel_z_exp` と同じ並びで、
  `params` の書き換えなしに `func` だけ差し替えられる（`std` / `command_name` はキーワード指定のため）。
- Isaac Lab 同梱の G1・H1 はこの 2 つを使っている（`config/g1/rough_env_cfg.py:25-30`）。
  本タスクは `isaaclab.envs.mdp.rewards` 側の非 yaw フレーム版を使っている
  （`my_robot_code/rough_env_cfg.py:213-218`）。

## 4. `random_uniform_terrain` が difficulty を無視すること（訂正2 の裏づけ）

`isaaclab/terrains/height_field/hf_terrains.py:22-30`

```
def random_uniform_terrain(difficulty: float, cfg: hf_terrains_cfg.HfRandomUniformTerrainCfg) -> np.ndarray:
    ...
        The :obj:`difficulty` parameter is ignored for this terrain.
```

`max_init_terrain_level` の扱い（`isaaclab/terrains/terrain_importer.py:340-347`）:

```python
if self.cfg.max_init_terrain_level is None:
    max_init_level = num_rows - 1
else:
    max_init_level = min(self.cfg.max_init_terrain_level, num_rows - 1)
self.terrain_levels = torch.randint(0, max_init_level + 1, (num_envs,), device=self.device)
```

- `None` は「全レベル（0〜9）から一様抽選」。数値を上げるほど初期地形は難しくなる。
  **レベル 0 が最易**なので、立ち往生対策として上げるのは逆効果。訂正2 のとおり。
