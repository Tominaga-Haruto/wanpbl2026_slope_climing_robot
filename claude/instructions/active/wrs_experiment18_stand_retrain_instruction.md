# WRS 実験18: 立った開始・ほぼまっすぐの既定姿勢・報酬の修正で、ゼロから 3000 iter（準備とスモークまで）

作成 2026-09-25。理由はノートPCチャットの判断（シムの歩行が「膝を曲げたまま 5 Hz のすり足」で、実機の安全制限に掛かる歩き方そのもの。開始は毎回空中から落として速度付き）。
終わったらこのファイルを `../inactive/` へ移す。コードの正本は `my_robot_code/stand_env_cfg.py`（下に全文を埋め込んだ）。

```
# 依頼: 新しいタスク（立った開始の学習）を追加し、立たせる確認とスモークテストをして、学習コマンドを渡して止まる

## このプロンプトの前提
- このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。
- 長時間の学習をバックグラウンドで回さない。やってよいのは、ファイルの追加、下の S1〜S3（各数分）だけ。
  本番の学習はユーザーが別の PowerShell で前景実行する。
- 今回は例外として「新しいファイルの追加」と「タスク登録（gym.register）の追記」をしてよい。
  既存の cfg（rough_env_cfg.py、skyentific_poclegs.py、rewards.py、curriculums.py、rsl_rl_cfg.py）の中身は変えない。
  追記するファイルは先に .bak_20260925_x18 を取る。何も削除しない。pip で何も入れない。git の commit・push はしない。
- 推測で直さない。import が通らない・API 名が違う（例: joint_pos_limits、write_joint_position_limit_to_sim、
  base_height_l2、reset_joints_by_offset）のときは、Isaac Lab のソースを見て**同じ意味の**名前に直すのはよい。
  直した箇所は報告に全部書く。意味が変わる修正が要るなら止まって報告。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\（run名）
- 前景学習 tools\runs\_train_foreground.ps1、再生 tools\runs\_play.ps1、過去の起動行は tools\logs\run_*.txt の先頭
- 比較の親: run 2026-09-17_00-08-51_H_eff13p5（model_2999.pt）。seed・num_envs・noise_std_type・学習率など
  エージェント側の設定はこの run の params\agent.yaml と同じにする。

## S0 追加
1. rough_env_cfg.py の実体がある場所（references\...\skyentific_poclegs\tasks\locomotion\velocity\ 以下。
   my_robot_code\ とハードリンク）を探す。同じフォルダに stand_env_cfg.py を下の全文で作る。
   my_robot_code\stand_env_cfg.py にも同じ内容を置く（ハードリンクにできるならハードリンク、無理ならコピーと報告）。
2. 既存の rough タスクを gym.register しているファイル（__init__.py）に、同じ形で2つ追記する:
   - id "Skyentific-Poclegs-Stand-v0"  env_cfg_entry_point = stand_env_cfg:SkyentificPoclegsStandEnvCfg
   - id "Skyentific-Poclegs-Stand-Play-v0"  env_cfg_entry_point = stand_env_cfg:SkyentificPoclegsStandEnvCfg_PLAY
   - rsl_rl_cfg_entry_point は rough タスクと同じもの（ログの experiment_name も同じでよい）。
3. `from .rough_env_cfg import ...` が通らなければ、実際のモジュールパスに直す。

## S1 行動 0 で平らな床に立たせる（小さなスクリプトを tools\runs\x18_stand_check.py に作ってよい）
- Stand-Play-v0、num_envs 16、行動は常に 0（＝PD の目標が既定姿勢）。押し・ノイズなし。
- (a) 高さを測る: init_state.pos の z を 0.45 に上書きして 3 s 回す。落ちて止まった後の胴の z の中央値を
  H0 とする。INIT_Z = H0 + 0.003、BASE_HEIGHT_TARGET = H0（mm 単位で丸める）を stand_env_cfg.py に書き込む
  （ハードリンク先も同じになることを確認）。
- (b) 確かめる: 書き込んだ INIT_Z のまま 5 s 回し、次を報告する:
  最初の 0.2 s で胴が落ちた距離（5 mm 以下が合格）、5 s 後に立っている env の数、胴の pitch・roll の最大、
  両足（.*ffe）の接触の有無、関節角が既定姿勢から何度ずれたか（関節ごとの最大）。
- (c) 前か後ろに倒れる（|pitch| > 10°）env が半分を超えたら: 両脚の FFE の既定値に δ、HFE の既定値に −δ を
  足して（δ は 1°刻み、±5°まで）立つ δ を探す。前に倒れるなら重心が前なので、足首を後ろへ倒す向きを試す。
  見つかったら STAND_JOINT_POS をそう書き換えて (a)(b) をやり直し、δ を報告。±5°で立たなければ止まって報告。
- 並べて報告: 既定姿勢の関節角（度）、H0、倒れた向き。

## S2 設定が効いているか（S3 の env.yaml と実テンソルで）
- 関節の位置制限（soft limit を含む）の実テンソルを1 env 分、度で表に貼る。
  期待値: HR ±25、HAA −6〜30、HFE ±60、LL_KFE −14.3〜100、LR_KFE −9.2〜100、FFE ±45
  （soft は係数 0.95 で少し内側になる）。効いていなければ止まって報告。
- effort_limit: ffe 10、hfe 8、kfe 20、haa 12、hr 6。terrain が plane。reset 時の胴の速度が 0。
- 報酬の項目と重みの一覧（env.yaml から）。

## S3 スモークテスト
- Stand-v0 で num_envs 64、max_iterations 20、run名 TEST_X18。落ちずに 20 iter 回ること、
  報酬の各項目がログに出ること（joint_vel_l2、joint_acc_l2、base_height_l2、feet_air_time_biped を含む）。
- TEST_X18 は消さない。

## 報告（これで止まる）
1. 冒頭3行: S1 の合否（立ったか、δ）、S2・S3 の合否、このまま進めてよいか。
2. S1 の数値、S2 の表、直した API 名。
3. **ユーザーが前景で打つ学習コマンド**: Stand-v0、num_envs 4096、max_iterations 3000、save_interval 100、
   run名 X18_stand_v1、ゼロから（再開しない）。実行フォルダ付き・プレースホルダ無し・複数行版と改行なしの1行版。
4. **再生コマンド**（Stand-Play-v0、checkpoint 名だけ差し替えれば別の点を見られる形。例は model_1500.pt）。
5. **評価コマンド**（学習後にユーザーが打つ。数分）: Stand-Play-v0 の 1 env を、止まって立った開始から
   vx 0.3 で 10 s 回し、次を出す: 転倒の有無、実際の vx、歩行周期 [Hz]（HFE の FFT でよい）、
   KFE の平均（度）、関節ごとの角速度 p99 [°/s] とトルク p99 [N·m]、下から1番目（FFE）が 5.2 N·m を超える時間の割合、
   KFE が 200°/s を超える時間の割合、HAA の最小（度）。tools\dump_golden.py が使えるならそれを流用してよい。
   H_eff13p5@2999 の値（周期 5.1 Hz、KFE 平均 33°、KFE 角速度 p99 421〜467°/s、FFE トルク p99 11〜12 N·m、HAA −15°）と並べる形で。
```

## 埋め込むコード（stand_env_cfg.py の全文）

```python
# X18 (2026-09-25): "stand-start" retrain config.
# New task only. Subclasses SkyentificPoclegsRoughEnvCfg and overrides in __post_init__,
# so the existing rough task (and every past run) is unchanged.
#
# What changes vs H_eff13p5 (reasons: claude/reports/2026-09-25_*):
#   1. default pose = physically near-straight leg (knee 8 deg), with the CAD zero-pose asymmetry
#      (URDF FK: LL HFE +2.9 / KFE -12.3 / FFE +9.4, LR -0.9 / -7.2 / +8.1 deg = physically straight)
#   2. joint limits (URDF has +-180 deg everywhere): knee cannot hyperextend, HAA cannot close the feet
#   3. start on a flat plane, feet on the floor, zero initial velocity, joints +-3 deg
#   4. rewards against the 5 Hz shuffle gait: single-stance time, joint vel/acc/torque, knee pose,
#      base height, orientation
#   5. effort limits near the real transmitter's abort currents, friction / gain DR
import copy
import math

import torch

from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils import configclass

import isaaclab_tasks.manager_based.locomotion.velocity.mdp as mdp

# CLI: fix this import to the real module path if needed (same package as rough_env_cfg.py).
from .rough_env_cfg import SkyentificPoclegsRoughEnvCfg

D = math.radians

# physical pose: knee bent 8 deg, HFE -4, FFE -4 (thigh and shank symmetric -> torso upright, foot flat).
# sim angle = physical angle from straight + CAD offset. HFE+KFE+FFE = 0 on both legs (foot parallel to torso).
STAND_JOINT_POS = {
    "LL_HR": 0.0, "LR_HR": 0.0,
    "LL_HAA": 0.0, "LR_HAA": 0.0,
    "LL_HFE": D(-1.1), "LR_HFE": D(-4.9),
    "LL_KFE": D(-4.3), "LR_KFE": D(0.8),
    "LL_FFE": D(5.4), "LR_FFE": D(4.1),
}

# measured by the zero-action stand check (step S1 of exp18): settled base z + 0.003 m.
INIT_Z = 0.38
# measured by the same check: settled base z.
BASE_HEIGHT_TARGET = 0.37

# sim joint limits [deg]. KFE lower = physically straight - 2 deg. HAA lower -6 (real feet touch at -8.5..-11).
JOINT_LIMITS_DEG = {
    ".*_HR": (-25.0, 25.0),
    ".*_HAA": (-6.0, 30.0),
    ".*_HFE": (-60.0, 60.0),
    "LL_KFE": (-14.3, 100.0),
    "LR_KFE": (-9.2, 100.0),
    ".*_FFE": (-45.0, 45.0),
}

# N*m. current = torque / c_p (AK80-9 0.523, AK10-9 1.258): FFE 19 A, HFE 15 A, KFE 16 A, HAA 9.5 A, HR 4.8 A
EFFORT_LIMITS = {"ffe": 10.0, "hfe": 8.0, "kfe": 20.0, "haa": 12.0, "hr": 6.0}


def set_joint_limits_deg(env, env_ids, asset_cfg: SceneEntityCfg, limits_deg: dict):
    """Startup event: overwrite joint position limits (and hence soft limits) for the given joints."""
    asset = env.scene[asset_cfg.name]
    limits = asset.data.joint_pos_limits.clone()
    for expr, (lo, hi) in limits_deg.items():
        ids, _ = asset.find_joints(expr)
        limits[:, ids, 0] = math.radians(lo)
        limits[:, ids, 1] = math.radians(hi)
    asset.write_joint_position_limit_to_sim(limits, warn_limit_violation=False)


@configclass
class SkyentificPoclegsStandEnvCfg(SkyentificPoclegsRoughEnvCfg):
    def __post_init__(self):
        super().__post_init__()

        # ---- robot: default pose, spawn height, effort limits
        robot = copy.deepcopy(self.scene.robot)
        robot.init_state.pos = (0.0, 0.0, INIT_Z)
        robot.init_state.joint_pos = dict(STAND_JOINT_POS)
        for name, eff in EFFORT_LIMITS.items():
            robot.actuators[name].effort_limit = eff
        self.scene.robot = robot

        # ---- flat plane only
        self.scene.terrain.terrain_type = "plane"
        self.scene.terrain.terrain_generator = None
        self.curriculum.terrain_levels = None
        self.curriculum.push_force_levels = None  # keep pushes at +-0.5 m/s

        # ---- commands (deployment range) + standing envs
        self.commands.base_velocity.ranges.lin_vel_x = (-0.3, 0.6)
        self.commands.base_velocity.ranges.lin_vel_y = (-0.2, 0.2)
        self.commands.base_velocity.ranges.ang_vel_z = (-0.6, 0.6)
        self.commands.base_velocity.rel_standing_envs = 0.15

        # ---- events: calm start, joint limits, DR
        self.events.reset_base.params["velocity_range"] = {
            "x": (0.0, 0.0), "y": (0.0, 0.0), "z": (0.0, 0.0),
            "roll": (0.0, 0.0), "pitch": (0.0, 0.0), "yaw": (0.0, 0.0),
        }
        self.events.reset_robot_joints = EventTerm(
            func=mdp.reset_joints_by_offset,
            mode="reset",
            params={"position_range": (-0.05, 0.05), "velocity_range": (0.0, 0.0)},
        )
        self.events.set_joint_limits = EventTerm(
            func=set_joint_limits_deg,
            mode="startup",
            params={"asset_cfg": SceneEntityCfg("robot"), "limits_deg": JOINT_LIMITS_DEG},
        )
        self.events.scale_all_joint_friction_model.params["friction_distribution_params"] = (1.0, 3.0)
        self.events.randomize_actuator_gains.params["stiffness_distribution_params"] = (0.8, 1.2)
        self.events.randomize_actuator_gains.params["damping_distribution_params"] = (0.8, 1.2)

        # ---- rewards
        r = self.rewards
        r.flat_orientation_l2.weight = -2.0
        r.joint_torques_l2.weight = -1.0e-4
        r.action_rate_l2.weight = -0.02
        r.feet_air_time.params["threshold_min"] = 0.25  # swings shorter than 0.25 s are penalized
        r.feet_air_time.params["threshold_max"] = 0.5
        r.feet_air_time_biped.weight = 0.5
        r.feet_air_time_biped.params["threshold_min"] = 0.2
        r.feet_air_time_biped.params["threshold_max"] = 0.4
        r.joint_deviation_knee.weight = -0.1
        r.undesired_contacts.params["sensor_cfg"] = SceneEntityCfg(
            "contact_forces", body_names=[".*hfe", ".*haa", ".*kfe"]
        )
        r.joint_vel_l2 = RewTerm(func=mdp.joint_vel_l2, weight=-1.0e-3)
        r.joint_acc_l2 = RewTerm(func=mdp.joint_acc_l2, weight=-2.5e-7)
        r.base_height_l2 = RewTerm(
            func=mdp.base_height_l2, weight=-30.0, params={"target_height": BASE_HEIGHT_TARGET}
        )

        # ---- terminations
        self.terminations.bad_orientation.params["limit_angle"] = 0.8


@configclass
class SkyentificPoclegsStandEnvCfg_PLAY(SkyentificPoclegsStandEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
        self.events.base_external_force_torque = None
        self.events.push_robot = None
```
