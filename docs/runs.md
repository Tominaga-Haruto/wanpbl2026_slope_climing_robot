# run フォルダ対応表

場所: `D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\`
（このフォルダは `.gitignore` の `logs/` で追跡外。実体はローカルにしかない）

チェックポイントは `save_interval = 200` なので 0, 200, 400, ... と最終 iter のもの。

## 2026-09-16

| run フォルダ | 設定 | iter | 結果の一言 | 評価済み |
|---|---|---|---|---|
| `2026-09-16_03-14-52` | 前チャットのテスト | 20 | 評価対象外 | — |
| `2026-09-16_05-08-07_TEST_A` | 64 env の疎通テスト（A 設定） | 20 | 評価対象外 | 19（スクリプト検証用） |
| `2026-09-16_05-11-41_TEST_B` | 64 env の疎通テスト（B 設定） | 20 | 評価対象外 | — |
| **`2026-09-16_05-14-59_A_base0821`** | 08-21 設定そのまま。rough 地形 | 3000 | **立ち往生。3000 iter 通して一歩も動かない。terrain_levels は 0 のまま** | 1000 / 1600 / 2400 / 2999 |
| **`2026-09-16_05-15-41_B_combined`** | 平地 ＋ feet_air_time_biped w0.25 ＋ track std 0.35 | 3000 | **基準となる歩行。全判定通過（2999）。旋回だけ未獲得** | 1000 / 1600 / 2400 / 2999 |
| `2026-09-16_05-32-13_B_combined_s2` | B と同じ seed 2 | 30 で停止 | スループット基準を満たさず停止。評価対象外 | — |
| **`2026-09-16_08-49-55_C_noflat`** | 報酬/std だけ B、地形は rough | 3000 | **立ち往生。2999 で後退だけ獲得（-0.217）。旋回は 1600 で +0.172 だが転倒率 90.6%** | 1000 / 1600 / 2400 / 2999 |
| **`2026-09-16_08-50-17_C_flatonly`** | 平地だけ変更、報酬/std は 08-21 | 3000 | **1600 までは前進で立ち往生、2400 で完全に歩き出す。平地だけで十分だと分かった決め手** | 1000 / 1600 / 2400 / 2999 |
| **`2026-09-16_13-40-10_E_yawcmd`** | B ＋ `rel_heading_envs=0.5` | 2000 | **旋回は未解決（S6 +0.063、指令 0.5 の 1/8）。前後左右は B より速く収束** | 1000 / 1600 / 1999 |
| **`2026-09-16_13-40-37_F_BtoRough`** | B@2999 から resume、地形だけ rough に戻す | +1500（通算 4498） | **terrain_levels 0.98 → 4.69。平地歩行も保持。ただし円を描いて歩く（S1 yaw +0.324）** | +401 / +1001 / +1499 |

## 起動行の記録

すべて `--task Velocity-Rough-Skyentific-Poclegs-v0 --num_envs 4096 --headless`、
`env.commands.base_velocity.debug_vis=false agent.policy.noise_std_type=log` が共通。

平地化は「`terrain_type=plane` が使えない」ため **sub_terrains の proportion を flat=1.0 / 他 0.0**
にする方式（`docs/reference/eval_protocol.md` 参照）。以下これを `<FLAT>` と書く:

```
env.scene.terrain.terrain_generator.sub_terrains.flat.proportion=1.0
env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.proportion=0.0
env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=0.0
env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs.proportion=0.0
env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs_inv.proportion=0.0
env.scene.terrain.terrain_generator.sub_terrains.wave_terrain.proportion=0.0
env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=0.0
env.curriculum.terrain_levels=null
```

報酬まわりを `<REW>` と書く:

```
env.rewards.feet_air_time.weight=0.0
env.rewards.feet_air_time_biped.weight=0.25
env.rewards.track_lin_vel_xy_exp.params.std=0.35
```

| ラン | 追加した引数 |
|---|---|
| A_base0821 | （共通のみ）`--max_iterations 3000 --seed 1` |
| B_combined | `--max_iterations 3000 --seed 1` ＋ `<FLAT>` ＋ `<REW>` |
| C_noflat | `--max_iterations 3000 --seed 1` ＋ `<REW>`（`<FLAT>` なし） |
| C_flatonly | `--max_iterations 3000 --seed 1` ＋ `<FLAT>`（`<REW>` なし） |
| E_yawcmd | `--max_iterations 2000 --seed 1` ＋ `<FLAT>` ＋ `<REW>` ＋ `env.commands.base_velocity.rel_heading_envs=0.5` |
| F_BtoRough | `--max_iterations 1500 --seed 1 --resume --load_run 2026-09-16_05-15-41_B_combined --checkpoint model_2999.pt` ＋ `<REW>`（`<FLAT>` なし） |

起動は `tools\runs\_launch.ps1 -RunName <名前> -ExtraArgs @(...)`。

**`--max_iterations` は「追加 iter 数」**（`rsl_rl/runners/on_policy_runner.py:76-78` の
`total_it = start_it + num_learning_iterations`）。resume したときは通算ではないので注意。
