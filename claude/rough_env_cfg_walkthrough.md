# `rough_env_cfg.py` 完全解説 ── ファイルを上から順に

このファイル1枚に、報酬・終了・地形・観測・イベント・カリキュラムの**設定値**が全部入っている。
コードの**登場順どおり**に注釈をつける。実ファイルを横に開いて対応させながら読むと早い。

全体の骨格（先に地図）:
1. import 群（ライブラリの部品を持ってくる）
2. `ROUGH_TERRAINS_CFG` … 地形の定義
3. `SkyentificObservationsCfg` … 観測（方策が見るもの）
4. `SkyentificEventCfg` … イベント（リセット・外乱・ランダム化）
5. `SkyentificRewardsCfg` … 報酬
6. `SkyentificCurriculumCfg` … カリキュラム
7. `SkyentificTerminationsCfg` … 終了条件
8. `SkyentificPoclegsRoughEnvCfg` … **全部を束ねる本体＋`__post_init__`（実効値の最終上書き）**
9. `SkyentificPoclegsRoughEnvCfg_PLAY` … 再生専用（学習では不使用）

区分の読み方: **`@configclass` と `*Cfg`/`*Term` はライブラリの器**。ユーザーが書くのは**その器に詰める中身（クラス名・数値・対象）**。器＝定型、中身の数値＝自作の編集面。

---

## 1. import 群（1〜35行あたり）

```python
import math
import isaaclab.sim as sim_utils
from isaaclab.utils import configclass
from isaaclab_tasks.manager_based.locomotion.velocity.velocity_env_cfg import LocomotionVelocityRoughEnvCfg
import skyentific_poclegs.tasks.locomotion.velocity.mdp as skyentific_mdp   # ← 自作mdp
import isaaclab_tasks.manager_based.locomotion.velocity.mdp as mdp          # ← ライブラリmdp
import isaaclab.terrains as terrain_gen
...
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import EventTermCfg  as EventTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import CurriculumTermCfg as CurrTerm
...
from skyentific_poclegs.assets.skyentific_poclegs import SKYENTIFIC_POCLEGS_CFG  # ← 機体定義を持ってくる
```

読み解きポイント:
- **すべてライブラリの部品の輸入**。ここは触らない。
- 重要なのは2つの `mdp`。**`mdp.` はライブラリ関数、`skyentific_mdp.` は自作パッケージ経由**（前の解説どおり）。この使い分けが本文全体で効く。
- `LocomotionVelocityRoughEnvCfg` が**親クラス（ライブラリ）**。本体クラスはこれを継承し、書いていない部分（Actions・Commands・Scene骨格）は親から受け継ぐ。
- `DoneTerm / ObsTerm / EventTerm / RewTerm / CurrTerm` は「1項目」を作る器。名前が違うだけで**構造は全部同じ**（`func` / `params` / 重みやフラグ）。
- 末尾の `SKYENTIFIC_POCLEGS_CFG` が**機体本体**（別ファイル `assets/skyentific_poclegs.py` 由来）。`__post_init__` でシーンに差し込まれる。

---

## 2. `ROUGH_TERRAINS_CFG` ── 地形の定義【ライブラリの器・中身は自作の数値】

```python
ROUGH_TERRAINS_CFG = TerrainGeneratorCfg(
    size=(8.0, 8.0),            # 1タイルの大きさ[m]
    border_width=20.0,
    num_rows=10, num_cols=20,   # タイルを 10行×20列 並べる
    horizontal_scale=0.1, vertical_scale=0.005, slope_threshold=0.75,
    use_cache=False,
    sub_terrains={ ... },       # ← ★ここが調整対象：タイルの種類と混合比
)
```

- `TerrainGeneratorCfg` はライブラリ。**行(row)方向が「難易度レベル」**になっていて、カリキュラム `terrain_levels` が上手く歩けた機体を上の行（難）へ、失敗を下の行（易）へ動かす。`max_init_terrain_level=0`（後述`__post_init__`）で全機体が最易から開始。
- `sub_terrains` の各タイル（すべてライブラリの `*TerrainCfg`）:

```python
"flat":               MeshPlaneTerrainCfg(proportion=0.3),                                   # 平地
"hf_pyramid_slope":   HfPyramidSlopedTerrainCfg(proportion=0.1, slope_range=(0.0,0.4), ...), # 登り坂 ★
"hf_pyramid_slope_inv":HfInvertedPyramidSlopedTerrainCfg(proportion=0.1, slope_range=(0.0,0.4)),# 下り坂 ★
"pyramid_stairs":     MeshPyramidStairsTerrainCfg(proportion=0.05, step_height_range=(0.0,0.1)),# 階段
"pyramid_stairs_inv": ...(proportion=0.05),
"wave_terrain":       HfWaveTerrainCfg(proportion=0.2, amplitude_range=(0.0,0.2)),            # 波
"random_rough":       HfRandomUniformTerrainCfg(proportion=0.2, noise_range=(0.0,0.06)),      # ゴツゴツ
```

**いじる場所は2つだけ:**
- `proportion` … 各タイルの出現割合（相対比。内部で正規化）。**坂特化なら slope 系を上げ、stairs/wave を下げる**。
- `slope_range` … 坂の勾配範囲。`(0.0, 0.4)` ≒ 0〜22度。**上限を上げると急坂が混じる**。

注意: 一気に難しくすると学習が止まる。上限を大きく上げるより、`terrain_levels` カリキュラムに任せて自動でじわじわ上げるのが定石。

---

## 3. `SkyentificObservationsCfg` ── 方策が見る情報【器はライブラリ・関節の切り分けだけ自作】

```python
@configclass
class SkyentificObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        base_lin_vel       = ObsTerm(func=mdp.base_lin_vel, noise=Unoise(-0.1,0.1))   # 胴体並進速度
        base_ang_vel       = ObsTerm(func=mdp.base_ang_vel, noise=Unoise(-0.2,0.2))   # 胴体角速度
        projected_gravity  = ObsTerm(func=mdp.projected_gravity, noise=Unoise(-0.05,0.05)) # 傾き（坂で重要）
        velocity_commands  = ObsTerm(func=mdp.generated_commands, params={"command_name":"base_velocity"}) # 指令速度
        hip_pos = ObsTerm(func=mdp.joint_pos_rel, params={"asset_cfg":SceneEntityCfg("robot", joint_names=[".*HR"])})
        kfe_pos = ObsTerm(..., joint_names=[".*HAA",".*HFE",".*KFE"])
        ffe_pos = ObsTerm(..., joint_names=[".*FFE"])
        joint_vel = ObsTerm(func=mdp.joint_vel_rel, noise=Unoise(-1.5,1.5))           # 全関節角速度
        actions   = ObsTerm(func=mdp.last_action)                                     # 直前の指令
        height_scan = ObsTerm(func=mdp.height_scan, ...)                              # 地形高さ（後で無効化）

        def __post_init__(self):
            self.enable_corruption = True    # ノイズを実際に適用
            self.concatenate_terms = True    # 全部を1本のベクトルに連結
```

- **全 ObsTerm がライブラリ関数**（`mdp.〜`）。自作は「どの関節をひとまとめに観測させるか」の切り分け（`hip_pos`/`kfe_pos`/`ffe_pos`）だけ。
- `noise=Unoise(...)` は**センサ誤差の模擬**（sim-to-real 用）。実機センサのノイズを想定して観測を汚す。
- **`height_scan` は定義されているが、末尾 `__post_init__` で `None` にされ無効**（＝地形を先読みしない「ブラインド歩行」）。将来これを復活させると地形の起伏を方策に見せられるが、height_scanner センサも要復活で影響大。
- 触るとき: 通常は触らない。観測を増減すると**NN の入力次元が変わり、既存チェックポイントと非互換**になる（学習やり直し）。慎重に。

---

## 4. `SkyentificEventCfg` ── リセット・外乱・ドメインランダム化【全ライブラリ関数・範囲だけ設定】

`mode` が3種類:`startup`（起動時1回）/`reset`（毎エピソードリセット）/`interval`（定期）。

```python
# startup（sim-to-real のための機体個体差ランダム化）
physics_material         = EventTerm(mode="startup", func=mdp.randomize_rigid_body_material,
    params={... "static_friction_range":(0.2,1.25), "dynamic_friction_range":(0.2,1.25), "restitution_range":(0.0,0.1)}) # 摩擦（坂で直結）
scale_all_link_masses    = EventTerm(mode="startup", ... mass ×0.9〜1.1)
add_base_mass            = EventTerm(mode="startup", ... 胴体 ±1kg)
scale_all_joint_armature = EventTerm(mode="startup", ... ×1.0〜1.05)
scale_all_joint_friction = EventTerm(mode="startup", ... ×0.9〜1.1)

# reset（毎エピソード最初にやること）
base_external_force_torque = EventTerm(mode="reset", ... force_range=(0,0))  # 範囲0＝実質無効（枠だけ）
reset_base   = EventTerm(mode="reset", func=mdp.reset_root_state_uniform, ... 位置±0.5m・yaw全周・速度randomize)
reset_robot_joints = EventTerm(mode="reset", func=mdp.reset_joints_by_scale, ... 関節角×0.5〜1.5)

# interval（学習中に定期的に）
push_robot = EventTerm(mode="interval", interval_range_s=(10,15), ... 横から速度パルス)  # 頑健性。カリキュラムで増強
```

- 全部ライブラリ関数。**ユーザーが書くのは範囲（min,max）だけ**。
- 坂で効くのは `physics_material` の摩擦。滑って登れないならここと `feet_slide` 罰を見る。
- `push_robot` は「歩行中に横から突っつく」外乱。転倒に強い方策を作る。強さはカリキュラム `push_force_levels` が自動で上げる。
- `reset_base` の `yaw:(-3.14,3.14)` は毎回ランダムな向きでスポーン＝どの向きの指令にも対応させるため。

---

## 5. `SkyentificRewardsCfg` ── 報酬【ここが一番いじる】

各項目 = `RewTerm(func=何を測る, weight=符号と強さ, params=対象)`。総報酬は毎ステップの**全項目の合計**。

```python
# -- task（プラス＝やってほしい）
track_lin_vel_xy_exp = RewTerm(func=mdp.track_lin_vel_xy_exp, weight=1.0,  params={"command_name":"base_velocity","std":math.sqrt(0.25)})  # 指令並進速度に一致＝主目的（坂=登れ）
track_ang_vel_z_exp  = RewTerm(func=mdp.track_ang_vel_z_exp,  weight=0.5,  ...)  # 指令旋回に一致

# -- penalties（マイナス＝やめてほしい）
lin_vel_z_l2      = RewTerm(func=mdp.lin_vel_z_l2,      weight=-2.0)    # 上下動（跳ね/沈み）罰。強め
ang_vel_xy_l2     = RewTerm(func=mdp.ang_vel_xy_l2,     weight=-0.05)   # ロール/ピッチのぐらつき罰
joint_torques_l2  = RewTerm(func=mdp.joint_torques_l2,  weight=-1.0e-5) # トルク罰＝省エネ。極弱
action_rate_l2    = RewTerm(func=mdp.action_rate_l2,    weight=-0.01)   # 指令の急変化罰＝滑らかさ
feet_air_time     = RewTerm(func=skyentific_mdp.feet_air_time, weight=2.0,   # ★自作：足の滞空0.2〜0.5秒でプラス（すり足防止）
    params={"sensor_cfg":SceneEntityCfg("contact_forces", body_names=".*ffe"), "command_name":"base_velocity",
            "threshold_min":0.2, "threshold_max":0.5})
feet_slide        = RewTerm(func=skyentific_mdp.feet_slide, weight=-0.25,     # ★自作：接地中の足の横滑り罰（坂で効く）
    params={"sensor_cfg":SceneEntityCfg("contact_forces", body_names=".*ffe"), "asset_cfg":SceneEntityCfg("robot", body_names=".*ffe")})
undesired_contacts= RewTerm(func=mdp.undesired_contacts, weight=-1.0,   # もも/股(.*hfe,.*haa)接地罰＝這うの禁止
    params={"sensor_cfg":SceneEntityCfg("contact_forces", body_names=[".*hfe",".*haa"]), "threshold":1.0})
joint_deviation_hip = RewTerm(func=mdp.joint_deviation_l1, weight=-0.1,  params={... joint_names=[".*HR",".*HAA"]}) # 股が初期姿勢からズレる罰＝まっすぐ歩く
joint_deviation_knee= RewTerm(func=mdp.joint_deviation_l1, weight=-0.01, params={... joint_names=[".*KFE"]})        # 膝ズレ罰。弱

# -- optional penalties（クラスでは0.0だが __post_init__ で実効値に上書きされる！）
flat_orientation_l2 = RewTerm(func=mdp.flat_orientation_l2, weight=0.0)  # → 実効 -0.5（胴体傾き罰）★坂の最重要
dof_pos_limits      = RewTerm(func=mdp.joint_pos_limits,    weight=0.0)  # → 実効 -1.0（関節限界接近罰）
```

読み解きと編集:
- **符号**: `+`=増やしたい行動、`−`=減らしたい行動。**大きさは他項目との相対**。
- **`exp`**（`track_*_exp`）=指令に近いほど1に近づく山型報酬。**`l2`**=ズレの二乗罰（大きくズレるほど急に痛い）。報酬の型はほぼこの2つ。
- **自作は `feet_air_time` と `feet_slide` の2つだけ**（`skyentific_mdp.`）。式は `mdp/rewards.py` にある。窓 `threshold_min/max` のような数値は params で渡すので、**式を変えず数値だけ変えるならここ（rough_env_cfg）で完結**。
- **最大の罠**: 最後の2項目 `flat_orientation_l2` と `dof_pos_limits` は**クラス本体で `weight=0.0`（一見無効）だが、`__post_init__` で −0.5 / −1.0 に上書きされる**（後述8）。実効値を変えるなら `__post_init__` を触る。
- 坂で触る主役: **`flat_orientation_l2`（前傾を許すなら緩める）→ `feet_air_time`（足上げ強化）→ `feet_slide`（滑り対策）**。一度に1つ、.bak+diff。

---

## 6. `SkyentificCurriculumCfg` ── 進むほど難化【ロジックは自作・数値はここ】

```python
terrain_levels    = CurrTerm(func=skyentific_mdp.terrain_levels_vel)   # 歩けたら地形1段難化/失敗で易化
push_force_levels = CurrTerm(func=skyentific_mdp.modify_push_force,
    params={"term_name":"push_robot", "max_velocity":[3.0,3.0], "interval":200*24, "starting_step":1500*24})
command_vel       = CurrTerm(func=skyentific_mdp.modify_command_velocity,
    params={"term_name":"track_lin_vel_xy_exp", "max_velocity":[-1.5,3.0], "interval":200*24, "starting_step":5000*24})
```

- 3つとも `skyentific_mdp.`（自作パッケージ経由）。**判定式は `mdp/curriculums.py`**、**発動時期・上限はここの params**。
- `terrain_levels_vel` … 地形難易度の自動調整（坂特化で最も頼る）。中身は Isaac Lab 標準関数のコピペ。
- `modify_push_force` … `starting_step`(1500iter×24) 以降、`interval`(200iter×24) ごとに、転倒が少なければ横突きを1.5倍、多ければ0.2減。上限 `max_velocity`。
- `modify_command_velocity` … 5000iter 以降、速度追従が十分なら指令レンジを±0.5拡大。上限 `[-1.5,3.0]`。
- 触り方: **params の数字（starting_step / interval / max_velocity）だけ**を触る。式（curriculums.py）は原則触らない。
- 注意: `1500*24` の `24` は「1 iter = 24 環境ステップ」（`num_steps_per_env=24`、rsl_rl_cfg.py 由来）。だから `starting_step` は「iter数 × 24」で書かれている。

---

## 7. `SkyentificTerminationsCfg` ── 終了条件【両方ライブラリ】

```python
time_out     = DoneTerm(func=mdp.time_out, time_out=True)   # 規定ステップ到達＝完走（失敗ではない）
base_contact = DoneTerm(func=mdp.illegal_contact,           # 胴体(base)が地面に1N以上＝転倒の失敗終了
    params={"sensor_cfg":SceneEntityCfg("contact_forces", body_names="base"), "threshold":1.0})
```

- `time_out=True` は**特殊フラグ**。「時間切れ＝成功で打ち切り」を意味し、価値計算上、転倒(失敗)と区別される。**触らない。**
- `base_contact` は胴体接地だけを転倒とみなす → 脚で支える中途半端な前のめりは拾えない。**追加候補が `bad_orientation`**（傾きで切る。存在確認してから足す）。
- 終了は報酬より破壊力大。厳しすぎると何も学べない、甘すぎると倒れたまま報酬を稼ぐ抜け道ができる。追加は1つずつ、64env/20iter でログ確認。

---

## 8. `SkyentificPoclegsRoughEnvCfg` ── 本体＋`__post_init__`（★実効値の最終確定点）

```python
@configclass
class SkyentificPoclegsRoughEnvCfg(LocomotionVelocityRoughEnvCfg):   # ← 親はライブラリ
    observations = SkyentificObservationsCfg()   # 上で定義した各クラスを差し込む
    rewards      = SkyentificRewardsCfg()
    terminations = SkyentificTerminationsCfg()
    events       = SkyentificEventCfg()
    curriculum   = SkyentificCurriculumCfg()
    viewer = ViewerCfg(eye=(3.5,3.5,0.5), origin_type="env", env_index=1, asset_name="robot")  # カメラ（表示用）

    def __post_init__(self):
        super().__post_init__()                  # ← まず親の初期化（Actions/Commands/Sceneの土台）
        # 地面（地形＋摩擦＋見た目）を差し替え
        self.scene.terrain = TerrainImporterCfg(
            terrain_type="generator", terrain_generator=ROUGH_TERRAINS_CFG,
            max_init_terrain_level=0,             # 全機体を最易レベルから開始
            physics_material=RigidBodyMaterialCfg(static_friction=1.0, dynamic_friction=1.0),  # ← 地面の摩擦
            visual_material=MdlFileCfg(...))      # 見た目のタイル模様（学習に無関係）
        # 機体を自作機に差し替え
        self.scene.robot = SKYENTIFIC_POCLEGS_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
        self.scene.height_scanner = None          # 高さスキャナ無効（ブラインド化）
        # ★報酬の実効値を上書き（ここが本当の値）
        self.rewards.flat_orientation_l2.weight = -0.5   # 胴体傾き罰（坂＝前傾許すならここを緩める）
        self.rewards.dof_pos_limits.weight      = -1.0   # 関節限界接近罰
        self.observations.policy.height_scan = None       # 観測からも高さスキャンを外す
```

ここが**このファイルで一番重要**:
- `@configclass` と親 `LocomotionVelocityRoughEnvCfg` はライブラリ。**書いていない Actions（関節目標角10個を出す）・Commands（目標速度を生成）・Scene の骨組みは親から継承**。
- クラス直下の代入（`rewards = ...`）で、上で作った自作の各設定クラスを束ねる。
- **`__post_init__` は「親の初期化が終わった後に走る最終上書き」**。実効値はここで決まる。つまり:
  - **地形・摩擦・機体・ブラインド化・報酬の −0.5/−1.0 は全部ここ**。
  - クラス本体で `weight=0.0` と書いてあっても、ここで上書きされていれば**そちらが本当の値**。「実効値を知りたい／変えたいときは必ず `__post_init__` を見る」。
- 坂調整で最初に触るのはここの `flat_orientation_l2.weight`。

---

## 9. `SkyentificPoclegsRoughEnvCfg_PLAY` ── 再生専用【学習では不使用・基本触らない】

```python
class SkyentificPoclegsRoughEnvCfg_PLAY(SkyentificPoclegsRoughEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50               # 少数だけ表示
        self.scene.terrain.terrain_generator.num_rows = 5
        self.scene.terrain.terrain_generator.num_cols = 5
        self.observations.policy.enable_corruption = False  # ノイズOFF
        self.events.push_robot = None                        # 押しOFF
```

- `play.py`（学習済み方策の再生・可視化）が使う設定。学習した方策を「見る」ときだけ。
- 環境数を50に減らし、地形を小さくし、ノイズと外乱を切る＝**きれいな条件で観察するため**。
- 学習の挙動には無関係。**基本触らない。**

---

## まとめ ── このファイルで何を触るか

| 目的 | 触るセクション | 場所 |
|---|---|---|
| 坂の比率・急さ | 2. `ROUGH_TERRAINS_CFG` | proportion / slope_range |
| 前傾を許す | 8. `__post_init__` | `flat_orientation_l2.weight = -0.5` を緩める |
| 足上げ強化・滑り対策 | 5. Rewards | `feet_air_time` / `feet_slide` の weight・params |
| 転倒判定を厳しく | 7. Terminations | `bad_orientation` 追加 |
| 地面の摩擦 | 8. `__post_init__` | `TerrainImporterCfg(...friction...)` |
| 外乱の範囲 | 4. Events | 各 range |
| カリキュラム時期 | 6. Curriculum | params の starting_step / interval |

**鉄則: 実効値は `__post_init__` を見る。編集は一度に1つ、`.bak`+`diff`、64env/20iter で通してから本番。**
（各関数の中身は `isaaclab_edit_guide.md`、ファイル間の位置関係は `project_structure_map.md` を参照）
