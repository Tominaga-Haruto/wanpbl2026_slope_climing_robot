# Skyentific PocLegs ひな形コード 体系解説（坂登坂ロボット）

対象ファイル（ALIEN: `~/projects/slope-climbing-robot/references/BipedalRobotSim/skyentific_poclegs/skyentific_poclegs/`）
- `assets/skyentific_poclegs.py` … ロボット定義（ArticulationCfg）
- `tasks/locomotion/velocity/config/skyentific_poclegs/rough_env_cfg.py` … 環境設定
- `tasks/locomotion/velocity/mdp/curriculums.py` … カリキュラム関数（自作ロジック）

区分: ライブラリ由来 / 自作 / 定型文（枠は決まっていて数値だけ差し込む）

---

## A. ロボット側コンフィグ（skyentific_poclegs.py）

`ArticulationCfg`（ライブラリ）に spawn / init_state / actuators を詰める箱。

### A-1 spawn
- `usd_path`：どのUSDを読むか。**唯一「機体そのもの」を決める行**。現状 `myrobot_dummy` → 本物か要確認（自作・要確認）。
- `activate_contact_sensors=True`：接触センサ有効化。足接地・胴体接地(転倒)検知に必須（定型・重要）。
- `rigid_props`：disable_gravity=False、damping=0、max速度=1000（安全弁）、max_depenetration_velocity=1.0（めり込み押し戻し上限）。定型。
- `articulation_props`：enabled_self_collisions=True（脚同士衝突を計算）、solver反復4/0。定型。

### A-2 init_state
- `pos=(0,0,0.449)`：スポーン高さ[m]。見本脚長基準。実寸と違うとめり込み/浮き（自作・要調整）。
- `joint_pos`：初期角[rad]。HR=0, HAA=-0.1745, HFE=-0.1745, KFE=0.3491, FFE=-0.1745＝軽く膝を曲げた待機姿勢。joint_deviation罰の基準でもある（自作・調整候補）。

### A-3 actuators（DelayedPDActuatorCfg, ライブラリ）4グループ
パラメータ意味：effort_limit=最大トルク／velocity_limit=最大角速度／stiffness=Pゲイン(硬さ)／damping=Dゲイン(制動)／armature=実効ロータ慣性(×81=減速比9²)／friction=関節摩擦／min-max_delay=指令遅延ランダム化(sim-to-real)。
- hr(.*HR)：股回転。effort24, stiff10。
- haa(.*HAA)：股横開き。effort30, stiff15。
- kfe(.*HFE,.*KFE)：股前後+膝。effort30, stiff15, armature大。
- ffe(.*FFE)：足首。effort20, stiff10。
- 自作で合わせるべき：effort/velocity/armature（実モーターAK10/AK80諸元）。stiffness/dampingは制御チューニング。
- `soft_joint_pos_limit_factor=0.95`：可動域95%にソフト限界。dof_pos_limits罰と連動。定型。

---

## B. Observations（方策が見る）rough_env_cfg.py / SkyentificObservationsCfg
全ObsTermはライブラリ、自作は関節の切り分けだけ。各項にUnoiseでセンサ誤差模擬。
- base_lin_vel(3)：胴体並進速度。
- base_ang_vel(3)：胴体角速度。
- projected_gravity(3)：重力を胴体座標で＝傾き情報。坂で重要。
- velocity_commands：指令速度。
- hip_pos(.*HR) / kfe_pos(.*HAA,.*HFE,.*KFE) / ffe_pos(.*FFE)：全関節の現在角（相対）。
- joint_vel：全関節角速度。
- actions：直前の指令。
- height_scan：地形高さスキャン → **__post_init__でNone＝無効（ブラインド歩行）**。将来復活で地形先読み可（大きめ変更）。
- __post_init__: enable_corruption=True（ノイズ適用）、concatenate_terms=True（連結）。

## C. Actions
親クラス（ライブラリ）が定義。関節目標角10個を出力→A-3のPD制御がトルク化。通常いじらない。

---

## D. Rewards（報酬）rough_env_cfg.py / SkyentificRewardsCfg
正=やってほしい/負=やめてほしい。l2=二乗罰、exp=近いほど1の山型。

タスク（プラス）
- D-1 track_lin_vel_xy_exp(+1.0, lib)：指令並進速度への一致。主目的。坂=登れ。
- D-2 track_ang_vel_z_exp(+0.5, lib)：指令旋回への一致。

ペナルティ（マイナス）
- D-3 lin_vel_z_l2(-2.0, lib)：上下速度罰。跳ね/沈み抑制。強め。
- D-4 ang_vel_xy_l2(-0.05, lib)：ロール/ピッチ回転罰。ぐらつき。
- D-5 joint_torques_l2(-1e-5, lib)：トルク罰。省エネ。弱。
- D-6 action_rate_l2(-0.01, lib)：指令急変化罰。滑らかさ。
- D-7 feet_air_time(+2.0, 自作)：足の滞空が0.2〜0.5秒窓でプラス。すり足/棒立ち防止。坂調整候補（強める）。
- D-8 feet_slide(-0.25, 自作)：接地中の足横滑り罰。坂で効く。
- D-9 undesired_contacts(-1.0, lib)：もも/股(.*hfe,.*haa)接地罰。這うの禁止。
- D-10 joint_deviation_hip(-0.1, lib)：股(.*HR,.*HAA)の初期姿勢ズレ罰。まっすぐ歩く。
- D-11 joint_deviation_knee(-0.01, lib)：膝(.*KFE)ズレ罰。弱。
- D-12 flat_orientation_l2（クラス0.0→__post_init__で-0.5, lib）：胴体傾き罰。**坂の最重要調整点＝前傾を許すなら__post_init__の-0.5を緩める**。
- D-13 dof_pos_limits（クラス0.0→__post_init__で-1.0, lib）：関節限界接近罰。

坂で触るのは主にD-12(前傾許可)・D-7(足上げ)・D-8(滑り)。

---

## E. Terminations（終了条件）SkyentificTerminationsCfg（両方lib）
- E-1 time_out(time_out=True)：規定ステップ到達で終了。失敗でなく完走扱い（価値ブートストラップ上、転倒と区別）。episode長が伸び time_out比率↑＝学習前進。
- E-2 base_contact(illegal_contact, body=base, 閾値1.0)：胴体接地=転倒の失敗終了。初期は全部これ（即転倒）。坂で胴体擦るなら閾値/対象body見直しも。

## F. Events（sim-to-realドメインrandomization）SkyentificEventCfg（全lib、範囲だけ設定）
mode: startup=起動1回 / reset=毎リセット / interval=定期。
- F-1 physics_material(startup)：摩擦0.2〜1.25・反発0〜0.1。坂の滑りに直結。
- F-2 scale_all_link_masses(startup)：各リンク質量0.9〜1.1倍。
- F-3 add_base_mass(startup)：胴体±1kg。
- F-4 scale_all_joint_armature(startup)：1.0〜1.05倍。
- F-5 scale_all_joint_friction(startup)：0.9〜1.1倍。
- F-6 base_external_force_torque(reset)：範囲0＝実質無効（枠のみ）。
- F-7 reset_base(reset)：胴体位置±0.5m・yaw全周・速度randomize。
- F-8 reset_robot_joints(reset)：関節角0.5〜1.5倍。
- F-9 push_robot(interval 10〜15s)：横から速度パルス。頑健性。カリキュラムで増強。

## G. Commands
親クラス（lib）がbase_velocity（前後左右・旋回の目標速度）を定義。D-1/D-2・B velocity_commands・H command_velが参照。範囲変更は親上書き。通常触らない。

---

## H. Curriculum（進むほど難化）SkyentificCurriculumCfg
ロジック本体はcurriculums.py（自作・定型）、数値はenv_cfg側paramsで渡す。
- H-1 terrain_levels(terrain_levels_vel)：十分歩けたら地形1段難化/歩けなければ易化。坂特化で最も頼る。
- H-2 push_force_levels(modify_push_force)：starting_step=1500*24以降、200iter毎に転倒少なければ小突き1.5倍。上限max_velocity=[3.0,3.0]。
- H-3 command_vel(modify_command_velocity)：starting_step=5000*24以降、速度追従報酬が高ければ指令レンジを±0.5拡大。上限[-1.5,3.0]。
- curriculums.py本体は「距離測定」「転倒数vs時間切れ数で増減判定」の実装。get_term修正以外は触らない。調整数字(starting_step等)はenv_cfg側params。

## I. Terrain（訓練地形）ROUGH_TERRAINS_CFG（TerrainGeneratorCfg, lib）
8m×8mタイルをnum_rows×num_colsで並べ、H-1が行方向を難易度に使う。sub_terrains比率：
- flat 0.3
- hf_pyramid_slope 0.1 / _inv 0.1（登り/下り坂, slope_range=(0.0,0.4)）← 坂特化ならここ主役
- pyramid_stairs 0.05 / _inv 0.05
- wave_terrain 0.2
- random_rough 0.2
坂特化：坂proportion↑・slope_range上限↑・階段/波↓。急にすると学習停止→H-1の自動難易度に任せてじわじわ。

## J. __post_init__ と PLAY
__post_init__（自作の上書き集約点・実効値はここで決まる）:
- scene.terrain=ROUGH_TERRAINS_CFG（地面摩擦1.0・見た目）。
- scene.robot=自作機に差し替え。
- scene.height_scanner=None & obs.height_scan=None（ブラインド化）。
- rewards.flat_orientation_l2.weight=-0.5（D-12実効・坂調整はここ）。
- rewards.dof_pos_limits.weight=-1.0（D-13実効）。
- **重要：報酬の実効値はクラス定義でなくここで上書き。いじるならここを見る。**
PLAY（_PLAY, 再生専用, play.pyが使用）：env50・地形5×5・ノイズOFF・押しOFF。学習では不使用。基本触らない。

---

## 坂登坂の優先順位
1. 土台：A-1 usd_path本物化 / A-2 pos実寸化。
2. 本丸：I Terrainの坂比率/slope_range → J の flat_orientation_l2=-0.5緩める(D-12) → D-7 feet_air_time強める。一度に1つ、.bak+diff。
3. 仕上げ：F-1摩擦・E-2転倒判定・B height_scan復活はsim-to-real/精度詰めの段。
