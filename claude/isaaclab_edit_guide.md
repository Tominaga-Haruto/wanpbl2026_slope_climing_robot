# Isaac Lab 環境コードを「いじれる」ための解説

対象: `rough_env_cfg.py` を中心に、報酬・地形・終了条件を自分で編集できるようになるための実践解説。
既存の `template_code_reference.md`（どこに何があるかの地図）を前提に、**「なぜそう書くのか / どう書き換えるのか / それはライブラリか自作か定型か」**を掘り下げる。

---

## 0. まず全体像 ── このコードは「設定の箱」であって「処理」ではない

一番大事な感覚: **`rough_env_cfg.py` は実行コードではなく、設定（Config）の集まり。**
IsaacLab は **Manager-based RL 環境**という作りで、学習ループ本体（物理を進める・観測を集める・報酬を足す・終了判定する・リセットする）は**ライブラリ側の `ManagerBasedRLEnv` が持っている**。ユーザーが書くのは「そのループに何を食わせるか」の設定だけ。

登録の入口を見ると分かる（`config/skyentific_poclegs/__init__.py`）:

```python
gym.register(
    id="Velocity-Rough-Skyentific-Poclegs-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",      # ← 実行するのはライブラリの汎用エンジン
    kwargs={"env_cfg_entry_point": rough_env_cfg.SkyentificPoclegsRoughEnvCfg},  # ← 設計図だけ渡す
)
```

`entry_point` がライブラリの汎用エンジン、`env_cfg_entry_point` が**あなたの設計図**。
つまり編集作業とは「エンジンは触らず、設計図の数値と項目を差し替える」こと。だから壊しにくいし、逆に**設計図の項目名・body名がエンジンの期待と1文字でも違うと起動時に落ちる**（`base: []` エラーの正体）。

### エンジンが中に持つ5つの Manager（これがキーワード）
`ManagerBasedRLEnv` は起動時に設計図を読んで、5つの担当（Manager）を組み立てる。編集対象はこの5つに1対1で対応する:

| Manager | 役割 | 設計図クラス（この repo） | ライブラリ/自作 |
|---|---|---|---|
| ObservationManager | 方策が見る情報 | `SkyentificObservationsCfg` | 枠は定型、中身の関節切り分けだけ自作 |
| ActionManager | 方策が出す指令 | （親クラスから継承） | ライブラリ |
| RewardManager | 報酬の合計 | `SkyentificRewardsCfg` | 主にライブラリ関数＋自作2つ |
| TerminationManager | いつ終わるか | `SkyentificTerminationsCfg` | ライブラリ関数 |
| EventManager | リセット/外乱/ランダム化 | `SkyentificEventCfg` | ライブラリ関数、範囲だけ設定 |
| （+ CurriculumManager） | 進むほど難化 | `SkyentificCurriculumCfg` | 自作ロジック |

**編集とは、この各クラスの中の「Term（項目）」を足す・消す・数値を変える、の3操作に尽きる。**

---

## 1. 「Term」の解剖 ── すべての項目は同じ形をしている

報酬も終了も観測も、中身は全部 **Term** という同じ部品で書かれている。形は共通:

```python
名前 = ○○Term(func=関数, weight=重み or 特殊フラグ, params={対象や閾値})
```

- **`func`（関数）= 「何を測るか」**。ここが `mdp.〜` ならライブラリ、`skyentific_mdp.〜` なら自作の可能性（後述1-3）。
- **`weight`（重み）= 「符号＝やってほしい(+)/やめてほしい(−)」と「強さ」**。報酬だけが持つ。
- **`params`（引数）= 「どの body / どの関節 / しきい値いくつ」**。関数に渡す材料。

例（報酬の1項目）:
```python
feet_slide = RewTerm(
    func=skyentific_mdp.feet_slide,        # 何を測る: 接地中の足の横滑り量
    weight=-0.25,                          # 符号−=罰、強さ0.25
    params={                               # 材料:
        "sensor_cfg": SceneEntityCfg("contact_forces", body_names=".*ffe"),  # 足先の接触センサ
        "asset_cfg":  SceneEntityCfg("robot", body_names=".*ffe"),           # 足先リンクの速度
    },
)
```

こうした3要素の意味が読めれば、**どの項目も同じ読み方で読める**。以降の報酬・終了・地形は全部この応用。

### 1-3. func が「ライブラリか自作か」を見分ける確実な方法
ファイル冒頭の import を見る:

```python
import isaaclab_tasks.manager_based.locomotion.velocity.mdp as mdp          # ← ライブラリ(歩行タスク標準)
import skyentific_poclegs.tasks.locomotion.velocity.mdp as skyentific_mdp   # ← 自作パッケージ
```

- `func=mdp.〜` → **100%ライブラリ**（Isaac Lab 標準関数）。中身は書き換えない。
- `func=skyentific_mdp.〜` → **自作パッケージ経由**。ただし自作パッケージの中身は:
  ```python
  # mdp/__init__.py
  from isaaclab.envs.mdp import *      # ライブラリ関数を丸ごと取り込み
  from .curriculums import *           # 自作
  from .rewards import *               # 自作
  ```
  なので `skyentific_mdp.〜` でも**中身は「自作 or ライブラリの再輸出」の両方あり得る**。実際に自作なのは `rewards.py`（`feet_air_time`, `feet_slide`）と `curriculums.py`（`terrain_levels_vel`, `modify_push_force`, `modify_command_velocity`）**の5つだけ**。それ以外はライブラリ。

**見分け方の結論:** `mdp.` はライブラリ確定。`skyentific_mdp.` なら `rewards.py` / `curriculums.py` を grep して、その名前が定義されていれば自作、無ければライブラリの再輸出。

---

## 2. 報酬（Rewards）── ここが一番いじる場所

`SkyentificRewardsCfg` は Term を並べただけのクラス。**足し算で総報酬が決まる**（各 Term の値 × weight を毎ステップ合計）。

### 2-1. weight の符号と大きさの読み方
- `+` = 増やしたい行動（速度追従など）。`−` = 減らしたい行動（傾き、滑り、無駄トルク）。
- 大きさは**他の項目との相対**。`track_lin_vel_xy_exp`(+1.0) が主目的で、罰はそれを邪魔しすぎない範囲に置く。`joint_torques_l2`(−1e-5) が極端に小さいのは「省エネは弱く効かせたい」から。
- `exp`（例 `track_lin_vel_xy_exp`）= 指令に近いほど1に近づく山型。`l2`（例 `lin_vel_z_l2`）= ズレの二乗罰（大きくズレるほど急に痛い）。この2つが報酬関数の型のほぼ全部。

### 2-2. 「クラス定義の weight」と「実効 weight」が違う罠（最重要）
クラス本体ではこう書いてある:
```python
flat_orientation_l2 = RewTerm(func=mdp.flat_orientation_l2, weight=0.0)   # 一見ゼロ=無効
dof_pos_limits      = RewTerm(func=mdp.joint_pos_limits,   weight=0.0)
```
ところが**ファイル末尾の `__post_init__` で上書きされている**:
```python
def __post_init__(self):
    super().__post_init__()
    ...
    self.rewards.flat_orientation_l2.weight = -0.5   # ← 実際はこっちが効く
    self.rewards.dof_pos_limits.weight = -1.0
```
`__post_init__` は「親クラスの初期化が終わった**後**に走る最終上書き」。**実効値を知りたい・変えたいときは必ず `__post_init__` を見る。** クラス本体の `weight=0.0` だけ見て「無効」と誤読すると事故る。坂で最重要の**胴体傾き罰 `flat_orientation_l2` の実効値 −0.5 はここにある**。前傾を許したいならこの −0.5 を −0.2 などに緩める（0 で完全に傾き自由）。

### 2-3. params の `SceneEntityCfg` と正規表現 ── 「どの部品に効かせるか」
`SceneEntityCfg(\"robot\", joint_names=[\".*KFE\"])` は「robot の中で、名前が KFE で終わる関節すべて」を選ぶフィルタ。`.*` は正規表現の「任意の文字列」。だから:
- `\".*KFE\"` → `LL_KFE`, `LR_KFE`（左右の膝）
- `\".*ffe\"` → `ll_ffe`, `lr_ffe`（左右の足先リンク。**body名は小文字、joint名は大文字**という命名規則に注意）
- `[\".*hfe\", \".*haa\"]` → もも・股リンク（`undesired_contacts` が「這うな」と罰する対象）

**なぜ正規表現なのか:** 左右2本ぶんをまとめて1行で指定できるから。ここが env_cfg とロボット定義（body/joint名）の**契約**になっていて、名前が合わないと `ValueError: ... base: []` で起動失敗する。だから**リンク名を変えるときは env_cfg 側の正規表現が当たるか必ず確認**（`grep body_names rough_env_cfg.py`）。

### 2-4. 報酬をいじる3つの操作（コピペ用パターン）

**(A) 強さ・符号を変える** ── 一番安全。数値1つ。
```python
feet_air_time = RewTerm(func=skyentific_mdp.feet_air_time, weight=4.0, ...)  # 2.0→4.0 で足上げを強調
```
坂用途で頻出: `flat_orientation_l2` を緩める（`__post_init__` の −0.5→−0.2）、`feet_air_time` を強める（+2.0→+3.0）。

**(B) 項目を追加する** ── 新しい罰/報酬を1つ増やす。
ライブラリ関数を使うのが安全。まず**その関数が存在するか確認**してから足す（バージョンで有無が変わる）:
```
python -c "import isaaclab_tasks.manager_based.locomotion.velocity.mdp as mdp; print([x for x in dir(mdp) if 'vel' in x])"
```
存在を確認できたら Term を1行足す。**追加も一度に1つ、.bak+diff、64env/20iter で通してから本番**。

**(C) 項目を消す/無効化する** ── `weight=0.0` にする（`__post_init__` で上書きされていないか要確認）か、行をコメントアウト。

### 2-5. 自作報酬 `rewards.py` の中身（改造したくなったとき）
`feet_air_time` と `feet_slide` はライブラリに無い/微調整版なので自作ファイルにある。ロジックは:
- `feet_air_time`: 足が「0.2〜0.5秒」宙に浮いた着地の瞬間だけプラス。窓 `threshold_min/max` は params で渡している → **窓を変えたいだけなら関数は触らず params を変える**。関数本体を変えるのは報酬の式そのものを変えたいとき（例: 単脚支持ボーナスを足す `feet_air_time_positive_biped` に差し替える等）。
- `feet_slide`: 接地中(接触力>1N)の足先の水平速度ノルムを罰。坂での踏ん張り（滑り防止）に効く。

**原則: 数値・対象は env_cfg の params で、式そのものは rewards.py で。** まず params で足りないか考える。

---

## 3. 終了条件（Terminations）── 「いつエピソードを切るか」

```python
class SkyentificTerminationsCfg:
    time_out     = DoneTerm(func=mdp.time_out, time_out=True)
    base_contact = DoneTerm(func=mdp.illegal_contact,
        params={"sensor_cfg": SceneEntityCfg("contact_forces", body_names="base"), "threshold": 1.0})
```
両方ライブラリ関数。ここも Term の形は報酬と同じ（weight が無いだけ）。

- **`time_out`（`time_out=True` フラグが特殊）**: 規定ステップ到達で終了。これは**失敗ではなく「無事に完走」扱い**。RL の価値計算上、転倒(=失敗)と時間切れ(=成功)を区別する必要があり、この `time_out=True` フラグがその印。**触らない。**
- **`base_contact`**: 胴体(`base`)が地面に threshold=1N 以上でぶつかったら失敗終了＝転倒判定。学習初期はほぼ全部これ（即コケる）。

### 3-1. 「膝で支える中途半端な転倒が消えない」問題への追加
`base_contact` は胴体が地面に着かないと反応しない。脚で支えたまま前のめり…は拾えない。対策は**傾きで切る `bad_orientation` を足す**:
```python
# まず存在確認（見本は古いAPIで落ちた前例あり）
python -c "import isaaclab.envs.mdp as mdp; print(hasattr(mdp,'bad_orientation'))"
```
True なら Term を追加:
```python
    bad_orientation = DoneTerm(
        func=mdp.bad_orientation,
        params={"limit_angle": 1.0},   # 約57度傾いたら終了。まず甘めから
    )
```
`limit_angle` を下げるほど早めに切る。**坂では常に傾いているので、坂特化時はこの角度としきい値の相性に注意**（坂の前傾を転倒と誤判定しない値にする）。

### 3-2. 終了条件を触るときの考え方
終了は報酬より**破壊力が大きい**。切る条件を厳しくすると「立つ前に全部切られて何も学べない」になり得る。逆に甘いと「倒れたまま報酬を稼ぐ」抜け道ができる。だから**追加は1つずつ、64env/20iter で episode 長のログ（`Episode_Termination/*` の内訳）を見てから本番**。初期は base_contact で episode 長 17〜19 ステップが正常、学習が進むと time_out 比率が上がって episode が伸びる、が健全サイン。

---

## 4. 地形（Terrain）── 坂特化の本丸

地形はファイル上部の `ROUGH_TERRAINS_CFG`（`TerrainGeneratorCfg`、ライブラリ）で定義。**8m×8mのタイルを num_rows×num_cols 並べ、行方向を難易度段階に使う**（カリキュラムが行を上下させる）。

```python
ROUGH_TERRAINS_CFG = TerrainGeneratorCfg(
    size=(8.0, 8.0), num_rows=10, num_cols=20,
    sub_terrains={                       # ← タイルの「種類と混合比率」
        "flat":              MeshPlaneTerrainCfg(proportion=0.3),
        "hf_pyramid_slope":  HfPyramidSlopedTerrainCfg(proportion=0.1, slope_range=(0.0,0.4), ...),  # 登り坂
        "hf_pyramid_slope_inv": HfInvertedPyramidSlopedTerrainCfg(proportion=0.1, slope_range=(0.0,0.4), ...),  # 下り坂
        "pyramid_stairs":    ...(proportion=0.05),   # 階段
        "pyramid_stairs_inv":...(proportion=0.05),
        "wave_terrain":      ...(proportion=0.2),    # 波
        "random_rough":      ...(proportion=0.2),    # ゴツゴツ
    },
)
```

### 4-1. いじる場所は2つだけ
- **`proportion`（混合比率）**: 各タイルの出現割合。合計が内部で正規化されるので**相対比**で考える。坂を主役にするなら slope 系を上げ、階段・波を下げる。
- **`slope_range`（坂の急さの範囲）**: `(0.0, 0.4)` は「勾配0〜0.4（≒0〜22度）の範囲でランダム生成」。上限を上げると急坂が混じる。

坂特化の実務: `hf_pyramid_slope` / `_inv` の proportion を上げ（例 0.1→0.3）、`slope_range` の上限を少しずつ上げ（0.4→0.5）、`stairs`/`wave` を下げる。**ただし急に難しくすると学習が止まる。** 上限を一気に上げるより、**カリキュラム（`terrain_levels`）の自動難易度調整に任せてじわじわ上げる**のが定石。

### 4-2. 地面そのものの摩擦は別の場所
坂の「滑る/滑らない」は2箇所で決まる:
- 地面側の摩擦 = `__post_init__` の `TerrainImporterCfg(... static_friction=1.0, dynamic_friction=1.0 ...)`。
- ロボット足裏側の摩擦 = Event の `physics_material`（0.2〜1.25 でランダム化、sim-to-real用）。
坂で滑って登れないときは、まずこの摩擦設定と `feet_slide` 罰を確認する。

---

## 5. カリキュラム（Curriculum）── 「進むほど難しく」の自動調整

`SkyentificCurriculumCfg` の3項目。**ロジック本体は `curriculums.py`（自作）、調整数値は env_cfg 側の params で渡す**、という分業。

```python
class SkyentificCurriculumCfg:
    terrain_levels   = CurrTerm(func=skyentific_mdp.terrain_levels_vel)          # 歩けたら地形1段難化
    push_force_levels= CurrTerm(func=skyentific_mdp.modify_push_force,
        params={"max_velocity":[3.0,3.0], "interval":200*24, "starting_step":1500*24})
    command_vel      = CurrTerm(func=skyentific_mdp.modify_command_velocity,
        params={"max_velocity":[-1.5,3.0], "interval":200*24, "starting_step":5000*24})
```

- **`terrain_levels_vel`**: 「指令速度で歩かせたとき、タイル半分(4m)以上進めたら地形を1段難しく、進めなければ易しく」。中身は**Isaac Lab 標準関数のコピペ**（自作ファイルにあるが式はライブラリ標準）。坂特化で最も頼る。
- **`modify_push_force`（本当の自作ロジック）**: `starting_step`(=1500iter×24) 以降、`interval` ごとに「転倒数 < 時間切れ数×2 なら横突きを1.5倍、転倒が多ければ0.2減」。頑健性を鍛える。数値だけ params で調整。
- **`modify_command_velocity`（自作）**: 速度追従報酬が十分高ければ指令速度レンジを±0.5拡大。上限 `[-1.5, 3.0]`。

**触り方:** 挙動の調整は**env_cfg 側の params の数字だけ**（`starting_step`, `interval`, `max_velocity`）。`curriculums.py` の関数本体は原則触らない（過去に触ったのは Isaac Lab 5.1 のAPI変更対応 `get_term` 修正のみ）。ここは「憶測でAPIを直さない」ルールの震源地。

---

## 6. ロボット定義側（skyentific_poclegs.py）── 報酬とは別ファイルだが連動する

`ArticulationCfg`（ライブラリ）に spawn / init_state / actuators を詰めた箱。報酬をいじる文脈で関係するのは:
- **`init_state.joint_pos`（初期姿勢）**: `joint_deviation_hip/knee` 罰の**基準点**。この初期角からのズレを罰しているので、初期姿勢を変えると「まっすぐ」の定義が変わる。
- **`actuators` の `effort_limit`/`velocity_limit`**: 出せるトルク上限。坂で力不足なら報酬をいじる前にここが実モーター(AK10/AK80)諸元と合っているか確認。`stiffness`/`damping` は PD 制御のゲイン（硬さ・制動）で、歩容の質に直結。
- **`usd_path`**: どの機体を読むか。報酬設計以前の「土台」。現在 `myrobot_dummy` を向いている。

**要点:** 報酬の `SceneEntityCfg(... joint_names=[\".*HR\"])` などの正規表現は、このファイルの joint/body 名と**必ず一致していないと落ちる**。報酬側の対象を変えるときはロボット側の名前を grep で確認してから。

---

## 7. 親クラスから継承しているもの（画面に見えないが効いている）

`SkyentificPoclegsRoughEnvCfg(LocomotionVelocityRoughEnvCfg)` の**親がライブラリ**。この repo で**書いていない**が効いているもの:
- **Actions**（関節目標角10個を出力 → PD制御でトルク化）。通常いじらない。
- **Commands**（`base_velocity` = 前後左右・旋回の目標速度をランダム生成）。報酬 `track_lin_vel_xy_exp` やカリキュラム `command_vel` がこれを参照。範囲を変えるなら親を上書き。
- **Scene の一部**（`contact_forces` 接触センサ、`height_scanner` 高さスキャナ）。

**継承と上書きの関係:** 子クラスは `rewards`/`terminations`/`events`/`curriculum`/`observations` を**丸ごと自作クラスに差し替え**、`scene`/`actions`/`commands` は**親のものを継承して `__post_init__` で部分的に微調整**（地形を差し替え、ロボットを差し替え、height_scanner を None に）。だから「見えないのに効く」項目は親クラス側にある。

---

## 8. ライブラリ / 自作 / 定型 早見表（この repo の実際）

| 区分 | 具体的に何 | 触り方 |
|---|---|---|
| **ライブラリ（触らない）** | `ManagerBasedRLEnv` 本体、`mdp.〜` の全関数、`TerrainGeneratorCfg`・各 `*TerrainCfg`、`DoneTerm/RewTerm/ObsTerm/EventTerm/CurrTerm`、親 `LocomotionVelocityRoughEnvCfg` | 呼ぶだけ。中身は読むが編集しない |
| **定型（枠は決まり数値だけ差す）** | 報酬/終了/観測/イベントの各 Term の並べ方、`SceneEntityCfg(...)` の書式、`__post_init__` の上書きパターン、`curriculums.py` の関数骨格 | 数値・対象・weight を差し替える |
| **自作（式そのもの）** | `rewards.py` の `feet_air_time`/`feet_slide`、`curriculums.py` の `modify_push_force`/`modify_command_velocity`（`terrain_levels_vel` は標準のコピペ） | 式を変えたいときだけ関数本体を編集 |
| **自作（設定値）** | `rough_env_cfg.py` の各 weight・proportion・slope_range・params、`__post_init__` の −0.5/−1.0、`skyentific_poclegs.py` の usd_path/init_state/actuators | ここが日常の編集対象 |

**覚え方:** `mdp.` で始まる関数と `*Cfg`/`*Term` クラスはライブラリ。`SkyentificXxxCfg` クラスの中の**数字と対象**が自作の編集面。式を変えたいときだけ `rewards.py`/`curriculums.py` に降りる。

---

## 9. 編集の作法（毎回これを守ると事故らない）

1. **一度に1つだけ変える**（報酬1項目 or 地形比率 or 終了1つ）。同時に複数変えると、良くなった/悪くなった原因が切り分けられない。
2. **`.bak` を取ってから編集 → `diff` で差分を目視**。
3. **64env / 20iter の小回しで通す**（ロード・joint・observation・action が通り、`Episode_Termination` の内訳とepisode長が想定通りか確認）→ 良さそうなら本番 4096env。
4. **実効値は `__post_init__` を見る**（クラス本体の weight を信じない）。
5. **新しい関数を足す前に存在確認**（`python -c \"...hasattr(mdp,'名前')\"`）。バージョンで有無が変わる。
6. **報酬の対象を変えたら body/joint 名の正規表現が当たるか grep 確認**（`base: []` 予防）。

### 坂登坂の優先順位（結論）
1. 土台: `usd_path` が本物か / `init_state.pos` が実寸か。
2. 本丸: 地形の坂 `proportion`↑・`slope_range` 上限↑ → `__post_init__` の `flat_orientation_l2 = -0.5` を緩めて前傾許可 → `feet_air_time` を強める。**一度に1つ、.bak+diff。**
3. 仕上げ: 摩擦・転倒判定(`bad_orientation`)・`height_scan` 復活（sim-to-real / 精度詰め）。

**iter を増やすだけでは改善しない**（3000→9000 で転倒率が微悪化した実績）。報酬・地形・カリキュラムの**設計**で解く。
