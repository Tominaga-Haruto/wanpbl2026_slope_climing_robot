# WRS 実験18: 立った開始・ほぼまっすぐの既定姿勢・報酬の修正で、ゼロから 3000 iter（準備とスモークまで）

作成 2026-09-25。**S0〜S2 は実行済み。続きは末尾の「続き（S1 の判断のあと）」の prompt を渡す。**理由はノートPCチャットの判断（シムの歩行が「膝を曲げたまま 5 Hz のすり足」で、実機の安全制限に掛かる歩き方そのもの。開始は毎回空中から落として速度付き）。
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

## 続き（S1 の判断のあと）— これを CLI に渡す

```
# 依頼の続き: 実験18 の S1 の判断と、S3（スモークテスト）・学習コマンド

## 前提（前回と同じ）
このプロンプトだけで完結。AGENTS.md・claude\ 以下・メモリは読まない。学習をバックグラウンドで回さない。
何も削除しない。pip しない。git commit・push しない。既存 cfg の中身は変えない。

## 判断
- 「行動 0 で立つこと」は前提から外す。足首の PD（2 本 × 10 N·m/rad）は、胴の倒れようとする剛性
  （m·g·h ≒ 10 kg × 9.8 × 約 0.3 m ≒ 30 N·m/rad）より弱いので、行動 0 ではどの δ でも立てないのが物理的に正しい。
  方策が足首を動かして釣り合いを取る前提で進める。足首の stiffness は変えない（実機の Kp と対応しているため）。
- 倒れる向きが δ=+1 と +2 の間で切り替わったので、δ=+1.5 を既定姿勢に入れる。

## やること
1. stand_env_cfg.py（ハードリンクなので1か所でよい）を次のとおり変える。.bak_20260925_x18b を取ってから。
   - STAND_JOINT_POS の HFE と FFE（度）: LL_HFE −2.6、LR_HFE −6.4、LL_FFE +6.9、LR_FFE +5.6（KFE・HR・HAA はそのまま）
   - INIT_Z = 0.377、BASE_HEIGHT_TARGET = 0.372
   - reset_robot_joints の下（scale_all_joint_friction_model の行の直前）に、胴の重心の DR を足す:
       self.events.randomize_base_com = EventTerm(
           func=mdp.randomize_rigid_body_com,
           mode="startup",
           params={
               "asset_cfg": SceneEntityCfg("robot", body_names="base"),
               "com_range": {"x": (-0.02, 0.03), "y": (-0.01, 0.01), "z": (-0.01, 0.01)},
           },
       )
     （randomize_rigid_body_com が無い・引数名が違うときは、Isaac Lab のソースの同じ意味の関数に合わせる。無ければこの項だけ外して報告。）
2. S1 の確認だけやり直す（行動 0、16 env、INIT_Z 0.377）: 最初の 0.2 s の沈み（mm）、両足が床に着いているか、
   倒れ始めるまでの時間と向き。合否は「沈み 3 mm 以下かつ足が床に着いている」だけ（立ち続けることは問わない）。
   沈みが 3 mm を超えるなら INIT_Z を 1 mm ずつ下げ、床にめり込んで跳ねる（胴の z が上に動く）手前の値にする。
3. S3 スモークテスト: Stand-v0、num_envs 64、max_iterations 20、run名 TEST_X18b。落ちずに回ること、
   報酬の各項目がログに出ること（joint_vel_l2、joint_acc_l2、base_height_l2、feet_air_time_biped を含む）、
   env.yaml の報酬の重み一覧、randomize_base_com が入っていること。
4. 学習コマンドは _train_foreground.ps1 を使わず、train.py を直接呼ぶ起動行にする（スクリプトは直さない）。
   task Skyentific-Poclegs-Stand-v0、num_envs 4096、max_iterations 3000、save_interval 100、run名 X18_stand_v1、
   ゼロから（resume しない）、headless、seed と noise_std_type などエージェント側は H_eff13p5 の params\agent.yaml と同じ。
   起動前に nvidia-smi で空きメモリを見る1行も付ける（今 GUI と別プロセスで約 13.9 GB 使用中）。

## 報告（これで止まる）
1. 冒頭3行: S1 やり直しの合否と INIT_Z、S3 の合否、進めてよいか。
2. S3 の報酬の重み一覧、変えたもの。
3. 学習コマンド（実行フォルダ付き・プレースホルダ無し・複数行版と改行なしの1行版）。
4. 再生コマンド（Stand-Play-v0、checkpoint 名だけ差し替える形、例 model_1500.pt）。
5. 評価コマンド（前回の依頼の「評価コマンド」の内容そのまま）。
```

## 結果と本番（2026-09-25 05:00）

- S1 やり直し合格（INIT_Z 0.377、沈み最大 2.96 mm、16/16 両足接地）、S3 合格（`2026-09-25_04-40-56_TEST_X18b`）。評価スクリプト `tools\runs\x18_eval.py`。
- WRS の Stand-v0 の env.yaml では track_ang_vel_z_exp が 1.0 / std 0.35（ノートPCの rough_env_cfg.py の 0.5 / 0.5 と違う。WRS 側が正）。
- 本番は2本を並走（別々の PowerShell）。GPU は1本 約 7.4 GB、先に他の isaacsim GUI を閉じる。
  - **X18_stand_v1**: 設定そのまま。
  - **X18_stand_v2_soft**: 保険。罰を緩めた版（Hydra 上書き）: joint_vel_l2 −5e-4、joint_acc_l2 −1.25e-7、joint_torques_l2 −5e-5、base_height_l2 −10、flat_orientation_l2 −1.0、feet_air_time の threshold_min 0.2。v1 が罰の重さで歩かなくなった場合の受け皿。
- 目安: 2本並走で 3000 iter 約 3〜3.5 時間。1500 iter（約 1.5〜2 時間）で一度再生して見る。

## X18c（2026-09-25 07:30）: v1@1500・v2_soft@1300 とも立往生 → 報酬と4番目の可動域を直して 1000 iter 再開

見立て（未検証）: ①速度追従の幅 std 0.5 が緩く、vx 0.3 で止まっていても追従報酬の約 7 割がもらえる、②4番目 −6°までだと足が約 25 cm 離れていて片足に体重を移しにくい（H は −15°で歩いていた）、③長い歩幅を見つける前に短い歩幅が罰される、④振り出しに要る膝の曲げを膝・高さの罰が邪魔する。

CLI に渡すもの:

```
# 依頼: 実験18 の続き X18c。新しいタスクを1つ追加し、スモークして、再開の学習コマンドを渡して止まる

## 前提
このプロンプトだけで完結。AGENTS.md・claude\ 以下・メモリは読まない。学習をバックグラウンドで回さない。
何も削除しない。pip しない。git commit・push しない。既存のクラスの中身は変えない（追記だけ）。
追記するファイルは先に .bak_20260925_x18c を取る。

## やること
1. stand_env_cfg.py（references 側と my_robot_code がハードリンク）の末尾に、下のコードをそのまま追記する。
2. __init__.py に2つ追記（形は Stand-v0 と同じ、rsl_rl 側も同じ）:
   - "Skyentific-Poclegs-StandWalk-v0" → stand_env_cfg:SkyentificPoclegsStandWalkEnvCfg
   - "Skyentific-Poclegs-StandWalk-Play-v0" → stand_env_cfg:SkyentificPoclegsStandWalkEnvCfg_PLAY
3. スモーク: StandWalk-v0、num_envs 64、max_iterations 5、run名 TEST_X18c、X18_stand_v2_soft の最新
   checkpoint（model_1300.pt。無ければあるうちの最大）から resume。確認して報告:
   checkpoint を読めた行、env.yaml の track_lin_vel_xy_exp（weight 2.0、std 0.25）、feet_air_time の
   threshold_min 0.15、feet_air_time_biped 1.0、joint_deviation_knee −0.02、base_height_l2 −10、
   HAA の位置制限の実テンソル（−10〜30°）。
4. 本番の学習コマンド（前回の X18_stand_v2_soft の起動行と同じ形、train.py を直接）:
   task StandWalk-v0、num_envs 4096、resume（--resume と --load_run に X18_stand_v2_soft の run フォルダ名、
   --checkpoint に 3 の checkpoint）、max_iterations 1000、save_interval 100、run名 X18c_walk、
   agent.policy.noise_std_type=log、報酬の Hydra 上書きは付けない（新クラスに入っている）。
5. 再生コマンド（StandWalk-Play-v0、-Filter *_X18c_walk、checkpoint 差し替え式）と、
   評価コマンド（x18_eval.py を --task で StandWalk-Play-v0 にできるならそうする。できなければ、
   x18_eval.py を .bak を取ってから --task 引数を足す。既定は今のまま）。

## 報告（これで止まる）
冒頭3行（スモークの合否、resume した checkpoint、進めてよいか）、確認した値、学習・再生・評価のコマンド
（実行フォルダ付き・プレースホルダ無し・1行版）。

## 追記するコード
```

```python
# X18c (2026-09-25 07:30): v1@1500 and v2_soft@1300 both stood still ("立往生").
# Likely reasons (not verified): (1) track_lin_vel std 0.5 pays ~70% of the tracking reward for standing
# still at vx 0.3; (2) HAA >= -6 deg keeps the feet ~25 cm apart, so shifting the weight onto one foot is
# hard; (3) short steps are penalized before long ones can be found; (4) knee/height penalties punish
# the knee bend a swing needs. Registered as a separate task; the classes above are unchanged.
@configclass
class SkyentificPoclegsStandWalkEnvCfg(SkyentificPoclegsStandEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        r = self.rewards
        r.track_lin_vel_xy_exp.weight = 2.0
        r.track_lin_vel_xy_exp.params["std"] = 0.25
        r.feet_air_time.params["threshold_min"] = 0.15
        r.feet_air_time_biped.weight = 1.0
        r.joint_deviation_knee.weight = -0.02
        r.base_height_l2.weight = -10.0
        r.flat_orientation_l2.weight = -1.0
        r.joint_vel_l2.weight = -5.0e-4
        r.joint_acc_l2.weight = -1.25e-7
        r.joint_torques_l2.weight = -5.0e-5
        limits = dict(JOINT_LIMITS_DEG)
        limits[".*_HAA"] = (-10.0, 30.0)
        self.events.set_joint_limits.params["limits_deg"] = limits


@configclass
class SkyentificPoclegsStandWalkEnvCfg_PLAY(SkyentificPoclegsStandWalkEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
        self.events.base_external_force_torque = None
        self.events.push_robot = None
```

- 07:36 X18c スモーク合格（`2026-09-25_07-34-17_TEST_X18c`）。再開元 `2026-09-25_05-18-51_X18_stand_v2_soft\model_1300.pt`、本番 run名 X18c_walk、checkpoint は model_1400〜2299。1304 iter 時点は vx 0.00（立往生のまま）、4番目は下限 −10°いっぱい。`x18_eval.py` に `--task` 追加済み。
- 07:50 X18d: StandWalk-v0 をゼロから（resume なし）1500 iter、run名 X18d_walk_scratch、2枚目の GPU（`--device cuda:1`）。X18c が「立った方策」から抜けられなかった場合の受け皿。

## X18e / X18f（2026-09-25 08:50）: X18c@2000・X18d@400 とも立往生（体は指令の方へ傾ける）→ 2本

見立て（未検証）: 静かな開始にしたので「踏み出さないと倒れる」経験がなくなった（H は落下と速度付きの開始で踏み出しを覚えた）。加えて 4番目の下限と、トルク上限が一歩を難しくしている可能性。
- **X18e**（ゼロから、1500 iter）: StandWalk の姿勢・報酬のまま、4番目 −16°・トルク上限を H と同じに戻し、開始に胴の速度 ±0.3・関節 ±0.1 rad、押しを 5〜8 s ごと、短い一歩の罰を弱める。
- **X18f**（H_eff13p5@2999 から再開、1000 iter）: H の姿勢・開始はそのまま（もう歩ける方策）、すり足への罰と膝・4番目（−10°）・5番目の可動域だけ足す。

CLI に渡すもの:

```
# 依頼: 実験18 の続き X18e / X18f。タスクを2つ追加し、スモークして、学習コマンド2本を渡して止まる

## 前提
このプロンプトだけで完結。AGENTS.md・claude\ 以下・メモリは読まない。学習をバックグラウンドで回さない。
何も削除しない。pip しない。git commit・push しない。既存のクラスの中身は変えない（追記だけ）。
追記するファイルは先に .bak_20260925_x18ef を取る。

## やること
1. stand_env_cfg.py（ハードリンク）の末尾に下のコードをそのまま追記。
2. __init__.py に4つ追記（形は StandWalk-v0 と同じ）:
   - "Skyentific-Poclegs-StandWalk2-v0" / "-StandWalk2-Play-v0" → SkyentificPoclegsStandWalkV2EnvCfg / _PLAY
   - "Skyentific-Poclegs-HShape-v0" / "-HShape-Play-v0" → SkyentificPoclegsHShapeEnvCfg / _PLAY
3. X18f の起動行は、H_eff13p5 の元の起動行（tools\logs\run_*H_eff13p5*.txt の先頭）の Hydra 上書きを
   そのまま引き継ぐ（task だけ HShape-v0 に替える）。ただし上書きのうち、HShape のクラスで決めた項目
   （terrain、報酬の重み、reset の範囲、friction の DR、指令の範囲）と重なるものは付けない。重なった項目は報告に書く。
4. スモーク（各 64 env・5 iter）:
   - TEST_X18e: StandWalk2-v0 ゼロから。env.yaml で HAA 制限 −16〜30（実テンソル）、effort ffe/hfe 13.5・他 53、
     reset の胴の速度 ±0.3、joint offset ±0.1、push 5〜8 s、feet_air_time threshold_min 0.1、biped threshold_min 0.0。
   - TEST_X18f: HShape-v0 を 2026-09-17_00-08-51_H_eff13p5 の model_2999.pt から resume。checkpoint を読めた行、
     既定姿勢が H と同じ（HFE −10・KFE +20・FFE −10）、HAA 制限 −10〜30・KFE 下限 L −14.3 / R −9.2（実テンソル）、
     joint_vel_l2・joint_acc_l2・feet_air_time_biped 1.0 が入っていること、terrain が plane。
     さらに 1 env を StandWalk と同じ評価（x18_eval.py --task HShape-Play-v0、vx 0.3、10 s）で、
     再開直後に歩いている（実際の vx > 0.1）ことを確かめる。
5. 学習コマンド2本（別々の PowerShell、train.py を直接、seed 1、noise_std_type=log、save_interval 100）:
   - X18e_walk2_scratch: StandWalk2-v0、4096 env、1500 iter、ゼロから、--device cuda:0
   - X18f_hshape: HShape-v0、4096 env、1000 iter、--resume --load_run 2026-09-17_00-08-51_H_eff13p5 --checkpoint model_2999.pt、--device cuda:1
   GPU が1枚しか見えない（nvidia-smi -L が1行）なら、両方 cuda:0 で書き、その旨を書く。
6. 再生・評価コマンドを2本ぶん（checkpoint 差し替え式）。

## 報告（これで止まる）
冒頭3行（スモーク2本の合否、X18f の再開直後の vx、進めてよいか）、確認した値、コマンド（実行フォルダ付き・1行版）。

## 追記するコード
```

```python
# X18e / X18f (2026-09-25 08:50): X18c (resume, 2000 it) and X18d (scratch, 400 it) still stood still,
# leaning toward the command. Suspected: the calm start removed every reason to step (H learned its
# stepping from being dropped with random velocities), and the HAA/effort limits may make a step hard.

# X18e: StandWalk from scratch, with the H-era physics back (HAA -15, H efforts) and a disturbed start.
@configclass
class SkyentificPoclegsStandWalkV2EnvCfg(SkyentificPoclegsStandWalkEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        for name, eff in {"ffe": 13.5, "hfe": 13.5, "kfe": 53.0, "haa": 53.0, "hr": 53.0}.items():
            self.scene.robot.actuators[name].effort_limit = eff
        limits = dict(JOINT_LIMITS_DEG)
        limits[".*_HAA"] = (-16.0, 30.0)
        self.events.set_joint_limits.params["limits_deg"] = limits
        self.events.reset_base.params["velocity_range"] = {
            "x": (-0.3, 0.3), "y": (-0.3, 0.3), "z": (0.0, 0.0),
            "roll": (-0.3, 0.3), "pitch": (-0.3, 0.3), "yaw": (-0.3, 0.3),
        }
        self.events.reset_robot_joints.params["position_range"] = (-0.1, 0.1)
        self.events.push_robot.interval_range_s = (5.0, 8.0)
        r = self.rewards
        r.feet_air_time.params["threshold_min"] = 0.1
        r.feet_air_time_biped.params["threshold_min"] = 0.0


@configclass
class SkyentificPoclegsStandWalkV2EnvCfg_PLAY(SkyentificPoclegsStandWalkV2EnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
        self.events.base_external_force_torque = None
        self.events.push_robot = None


# X18f: keep H_eff13p5's pose/start (it already walks) and resume it from model_2999.pt, adding only
# the anti-shuffle rewards and the knee/HAA/HR limits. Default pose and observations are H's, so the
# checkpoint loads as is.
H_JOINT_LIMITS_DEG = {
    ".*_HR": (-25.0, 25.0),
    ".*_HAA": (-10.0, 30.0),
    ".*_HFE": (-60.0, 60.0),
    "LL_KFE": (-14.3, 100.0),
    "LR_KFE": (-9.2, 100.0),
    ".*_FFE": (-45.0, 45.0),
}


@configclass
class SkyentificPoclegsHShapeEnvCfg(SkyentificPoclegsRoughEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        robot = copy.deepcopy(self.scene.robot)
        for name in ("ffe", "hfe"):
            robot.actuators[name].effort_limit = 13.5  # same as H_eff13p5
        self.scene.robot = robot
        self.scene.terrain.terrain_type = "plane"
        self.scene.terrain.terrain_generator = None
        self.curriculum.terrain_levels = None
        self.curriculum.push_force_levels = None
        self.commands.base_velocity.ranges.lin_vel_x = (-0.3, 0.6)
        self.commands.base_velocity.ranges.lin_vel_y = (-0.2, 0.2)
        self.commands.base_velocity.ranges.ang_vel_z = (-0.6, 0.6)
        self.events.reset_base.params["velocity_range"] = {
            "x": (-0.2, 0.2), "y": (-0.2, 0.2), "z": (0.0, 0.0),
            "roll": (-0.2, 0.2), "pitch": (-0.2, 0.2), "yaw": (-0.2, 0.2),
        }
        self.events.reset_robot_joints.params["position_range"] = (0.8, 1.2)
        self.events.set_joint_limits = EventTerm(
            func=set_joint_limits_deg,
            mode="startup",
            params={"asset_cfg": SceneEntityCfg("robot"), "limits_deg": H_JOINT_LIMITS_DEG},
        )
        self.events.scale_all_joint_friction_model.params["friction_distribution_params"] = (1.0, 3.0)
        r = self.rewards
        r.action_rate_l2.weight = -0.02
        r.flat_orientation_l2.weight = -1.0
        r.joint_torques_l2.weight = -5.0e-5
        r.feet_air_time.params["threshold_min"] = 0.25
        r.feet_air_time_biped.weight = 1.0
        r.feet_air_time_biped.params["threshold_min"] = 0.2
        r.feet_air_time_biped.params["threshold_max"] = 0.4
        r.joint_deviation_knee.weight = -0.05
        r.joint_vel_l2 = RewTerm(func=mdp.joint_vel_l2, weight=-5.0e-4)
        r.joint_acc_l2 = RewTerm(func=mdp.joint_acc_l2, weight=-1.25e-7)


@configclass
class SkyentificPoclegsHShapeEnvCfg_PLAY(SkyentificPoclegsHShapeEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
        self.events.base_external_force_torque = None
        self.events.push_robot = None
```

## X18g / X18h（2026-09-25 09:00）: 報酬を大胆に（X18e / X18f は取り下げ）

本人: 揺さぶる開始は「押さないと動かない」と同じで本質的でない、重みをもっと大胆に。→ 立っていると損をする報酬に:
速度追従 重み 5・幅 0.25、速度誤差の L1 罰 −3（指令から遠くても勾配がある）、指令中に両足を 0.3 s 以上着けたままの罰 −2、
一歩の報酬 feet_air_time 5（閾値 0.05〜0.4 s）・片足支持 3、止まれの指令なし（vx 0.15〜0.6）、正則化は H 並みに戻す、
トルク上限は H と同じ、4番目 −16°、エントロピー ×2。立ち姿勢・可動域（膝）・静かな開始は StandWalk のまま。観測は変えない。
- **X18g**: StandBold-v0 をゼロから 1500 iter（cuda:0）
- **X18h**: StandBold-v0 を X18c_walk の最新 checkpoint（まっすぐ立てて、指令の方へ傾く方策）から 1000 iter（cuda:1）

CLI に渡すもの:

```
# 依頼: 実験18 の続き X18g / X18h（X18e / X18f はやらない）。タスクを追加し、スモークして、学習コマンド2本を渡して止まる

## 前提
このプロンプトだけで完結。AGENTS.md・claude\ 以下・メモリは読まない。学習をバックグラウンドで回さない。
何も削除しない。pip しない。git commit・push しない。既存のクラスの中身は変えない（追記だけ）。
追記するファイルは先に .bak_20260925_x18gh を取る。前回の X18e/X18f のコードを追記済みなら、そのままでよい（使わない）。

## やること
1. stand_env_cfg.py（ハードリンク）の末尾に下のコードをそのまま追記。
2. __init__.py に2つ追記: "Skyentific-Poclegs-StandBold-v0" / "-StandBold-Play-v0" → SkyentificPoclegsStandBoldEnvCfg / _PLAY
3. エントロピー係数: H_eff13p5 の params\agent.yaml の algorithm.entropy_coef の値を読み、その2倍を
   Hydra（agent.algorithm.entropy_coef=値）で両方の起動行に付ける。値を報告。
4. スモーク（各 64 env・5 iter）:
   - TEST_X18g: StandBold-v0 ゼロから。env.yaml で次を確認して表に: track_lin_vel_xy_exp 5.0 / std 0.25、
     lin_vel_error_l1 −3、double_support −2（min_time 0.3）、feet_air_time 5.0（0.05〜0.4）、feet_air_time_biped 3.0（0.1〜0.4）、
     指令 vx 0.15〜0.6・rel_standing_envs 0、effort ffe/hfe 13.5・他 53、HAA 制限 −16〜30（実テンソル）。
     ログに lin_vel_error_l1 と double_support の項が出ること。
   - TEST_X18h: StandBold-v0 を X18c_walk の run フォルダの最新 checkpoint から resume。読めた行と checkpoint 名。
5. 学習コマンド2本（別々の PowerShell、train.py を直接、seed 1、noise_std_type=log、save_interval 100、エントロピー ×2）:
   - X18g_bold_scratch: StandBold-v0、4096 env、1500 iter、ゼロから、--device cuda:0
   - X18h_bold_from_c: StandBold-v0、4096 env、1000 iter、--resume --load_run（X18c_walk の run フォルダ名）--checkpoint（その最新）、--device cuda:1
   nvidia-smi -L が1行なら両方 cuda:0 で書き、その旨を書く。
6. 再生・評価コマンドを2本ぶん（StandBold-Play-v0、checkpoint 差し替え式）。

## 報告（これで止まる）
冒頭3行（スモーク2本の合否、エントロピーの値、進めてよいか）、確認した値の表、コマンド（実行フォルダ付き・1行版）。

## 追記するコード
```

```python
# X18g / X18h (2026-09-25 09:00): bold reward change instead of disturbed starts (X18e/X18f withdrawn).
# Standing must stop paying: big tracking weight, a linear velocity-error penalty that has a gradient
# even far from the command, a penalty for keeping both feet down while a velocity is commanded, big
# stepping rewards, no zero commands, H-level regularization only, H efforts and HAA -16.
def lin_vel_error_l1(env, command_name: str, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    asset = env.scene[asset_cfg.name]
    cmd = env.command_manager.get_command(command_name)
    return torch.sum(torch.abs(cmd[:, :2] - asset.data.root_lin_vel_b[:, :2]), dim=1)


def double_support_while_moving(env, command_name: str, sensor_cfg: SceneEntityCfg, min_time: float) -> torch.Tensor:
    contact_sensor = env.scene.sensors[sensor_cfg.name]
    contact_time = contact_sensor.data.current_contact_time[:, sensor_cfg.body_ids]
    both_down_long = torch.all(contact_time > min_time, dim=1)
    moving = torch.norm(env.command_manager.get_command(command_name)[:, :2], dim=1) > 0.1
    return (both_down_long & moving).float()


@configclass
class SkyentificPoclegsStandBoldEnvCfg(SkyentificPoclegsStandWalkEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        # physics that allowed H to walk
        for name, eff in {"ffe": 13.5, "hfe": 13.5, "kfe": 53.0, "haa": 53.0, "hr": 53.0}.items():
            self.scene.robot.actuators[name].effort_limit = eff
        limits = dict(JOINT_LIMITS_DEG)
        limits[".*_HAA"] = (-16.0, 30.0)
        self.events.set_joint_limits.params["limits_deg"] = limits
        # always a forward command, never "stand"
        self.commands.base_velocity.ranges.lin_vel_x = (0.15, 0.6)
        self.commands.base_velocity.ranges.lin_vel_y = (-0.1, 0.1)
        self.commands.base_velocity.ranges.ang_vel_z = (-0.3, 0.3)
        self.commands.base_velocity.rel_standing_envs = 0.0
        r = self.rewards
        # drive
        r.track_lin_vel_xy_exp.weight = 5.0
        r.track_lin_vel_xy_exp.params["std"] = 0.25
        r.lin_vel_error_l1 = RewTerm(func=lin_vel_error_l1, weight=-3.0, params={"command_name": "base_velocity"})
        r.double_support = RewTerm(
            func=double_support_while_moving, weight=-2.0,
            params={"command_name": "base_velocity",
                    "sensor_cfg": SceneEntityCfg("contact_forces", body_names=".*ffe"), "min_time": 0.3},
        )
        r.feet_air_time.weight = 5.0
        r.feet_air_time.params["threshold_min"] = 0.05
        r.feet_air_time.params["threshold_max"] = 0.4
        r.feet_air_time_biped.weight = 3.0
        r.feet_air_time_biped.params["threshold_min"] = 0.1
        r.feet_air_time_biped.params["threshold_max"] = 0.4
        # regularization back to H level (shape the gait later, after it walks)
        r.flat_orientation_l2.weight = -0.5
        r.base_height_l2.weight = -2.0
        r.joint_deviation_knee.weight = -0.01
        r.joint_torques_l2.weight = -1.0e-5
        r.action_rate_l2.weight = -0.01
        r.joint_vel_l2.weight = -1.0e-4
        r.joint_acc_l2.weight = -2.5e-8


@configclass
class SkyentificPoclegsStandBoldEnvCfg_PLAY(SkyentificPoclegsStandBoldEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
        self.events.base_external_force_torque = None
        self.events.push_robot = None
```
