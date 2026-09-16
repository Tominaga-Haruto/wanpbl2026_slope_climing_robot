# P1-1 自作 ROUGH_TERRAINS_CFG のパラメータとレベル 0 の実寸

出典: `my_robot_code/rough_env_cfg.py:35-77`（`ROUGH_TERRAINS_CFG`）。
難易度の式は `isaaclab/terrains/terrain_generator.py:260-262`、各地形の補間は
`height_field/hf_terrains.py` / `trimesh/mesh_terrains.py`。

## 全体パラメータ

| 項目 | 値 | 行 |
|---|---|---|
| size | (8.0, 8.0) m | rough_env_cfg.py:36 |
| border_width | 20.0 m | :37 |
| num_rows（＝地形レベル数） | 10 | :38 |
| num_cols | 20 | :39 |
| horizontal_scale | 0.1 m | :40 |
| vertical_scale | 0.005 m | :41 |
| slope_threshold | 0.75 | :42 |
| difficulty_range | (0.0, 1.0)（既定値、上書きなし） | terrain_generator_cfg.py:115 |
| max_init_terrain_level | 0 | rough_env_cfg.py:312 |

難易度: `difficulty = (sub_row + U(0,1)) / num_rows`、`difficulty_range` が (0,1) なので
そのまま。**行 0（レベル 0）は difficulty ∈ [0.0, 0.1)**。行 9 が最難で [0.9, 1.0)。

列の割り当ては proportion を正規化した累積で決まる（`terrain_generator.py:238-247`）。
proportion 合計はちょうど 1.0 なので、20 列の内訳は下表の「列数」のとおり。
`max_init_terrain_level=0` なので全 env が行 0 に置かれ、`terrain_types = arange(N) // (N/20)` で
20 列に均等配分される。つまり **レベル 0 での遭遇確率＝列数/20**。

## レベル 0（difficulty 0.0〜0.1）での実寸

| sub_terrain | proportion | 列数 /20 | 遭遇率 | 難易度で変わる量 | レベル 0 での実寸 | 最難（レベル 9）での実寸 |
|---|---|---|---|---|---|---|
| `flat` | 0.30 | 6 | 30 % | なし | 完全な平面 0 cm | 0 cm |
| `hf_pyramid_slope` | 0.10 | 2 | 10 % | `slope = 0.0 + d × 0.4` | 勾配 0〜4 %（0〜2.3°）、頂点高さ `slope × size/2` ＝ **0〜16 cm**（水平 4 m で） | 勾配 36〜40 %、頂点 144〜160 cm |
| `hf_pyramid_slope_inv` | 0.10 | 2 | 10 % | 同上（符号反転＝すり鉢） | 深さ **0〜16 cm** | 深さ 144〜160 cm |
| `pyramid_stairs` | 0.05 | 1 | 5 % | `step_height = 0.0 + d × 0.1` | 段差 **0〜1.0 cm**、踏面 30 cm | 段差 9〜10 cm |
| `pyramid_stairs_inv` | 0.05 | 1 | 5 % | 同上（下り） | 段差 **0〜1.0 cm** | 段差 9〜10 cm |
| `wave_terrain` | 0.20 | 4 | 20 % | `amplitude = 0.0 + d × 0.2`、振幅は `0.5 × amplitude` | 全振幅 **0〜2.0 cm**（±0〜1.0 cm）、波 4 本／8 m ＝ 波長 2 m | 全振幅 18〜20 cm |
| `random_rough` | 0.20 | 4 | 20 % | **difficulty を無視**（hf_terrains.py:30 に明記） | `noise_range=(0.0,0.06)`, `noise_step=0.02`, `vertical_scale=0.005` → 高さの候補は `arange(0,16,4)×0.005` ＝ **{0, 2, 4, 6} cm をセル（10 cm 角）ごとに一様抽選**。レベルに関係なく常にこれ | 同左（変わらない） |

## ここから言えること（訂正2 の裏づけ）

- レベル 0 でも **env の 20 % は 6 cm までのランダム凹凸**の上に置かれる。`random_uniform_terrain` は
  difficulty を使わないので、**カリキュラムを下げても上げてもこのタイルだけは常に最大荒さ**。
  ロボットの初期 base 高さが 0.3758 m なので、6 cm は股関節高さの約 16 %。10 cm 角のセルごとに
  独立抽選なので、足裏スケール（後述の支持多角形）で見ると段差として効く。
- レベル 0 で「本当に平ら」なのは `flat` の 30 % だけ。`wave`（20 %、±1 cm）と合わせても
  実質的に平坦なのは 50 % 程度。
- 逆に `max_init_terrain_level` を **上げる**と初期地形は難しくなる（`None` なら全レベルから一様抽選、
  `terrain_importer.py:340-347`）。レベル 0 が最易なので、立ち往生対策として「上げる」のは逆効果。
  実験01 の報告でこれを次の候補に挙げたのは誤りで、ユーザーの訂正2 が正しい。
- 平地化が効いた理由の候補としては「random_rough の 6 cm を消したこと」が最有力になる。
  地形カリキュラムが 0 から動かないこと自体は、レベル 0 が最易である以上、悪化要因ではない。
