# WRS 実験24: 振り足の途中で床を突く二段の歩きを直す 2 本（X24a 無難・X24b 革新）＋動画スクリプト x24

作成 2026-09-30 20:40。**新しい CLI チャットに「CLI に渡すもの」と「追記するコード」を貼る。**
前提: 実験23（X23a_flat_upright / X23b_flat_hpose、1000 iter 追加）が終わった。本人の再生（X23a model_4200、stand_walk vx 0.3）の CSV
`model_4200_stand_walk_vx0.3_seed0_20260930_200500.csv` を解析した結果が下。

## X23a@4200 の所見（本人の目視 ＋ CSV、t 2.5〜12 s）
- 本人: 二段の動きの種類が変わった。前（X22）は「右足を上げる → 左のつま先を上げる → 右足を前へ」。
  今は「右足を左足と前後同じくらいに着く → 右足を前へ」、つまり右・右・左・左の順。
- CSV: 前へは歩けている（指令 0.3 に前後 0.275 m/s、転倒なし、両足同時に浮く 0%）。胴の z の振れ 21 mm。
  足裏は X22（外側 10°前後）より平ら: 接地中の外側の傾き p50 左 7.5°・右 5.7°、つま先の傾き p50 左 2.6°・右 −0.4°（p95 6.3° / 9.9°）。
- **片足が 0.7 s に 2 回着地している**（着地の間隔 0.20 s と 0.50 s の繰り返し）。振り足の時間帯（約 0.33 s）の中で、
  0.10 s 浮く → 0.06〜0.08 s 着く → 0.12 s 浮く。
- 着く瞬間の振り足は、股の前後 −25〜−28°・膝 +35〜+40°・足首 −14°で、参照の振り足の頂点（既定 + (−A, +2A, −A)、A 0.35 rad = 20°）とほぼ同じ。
  その姿勢で足首の点の高さは 84 mm（立っている足 81 mm）＝**参照どおりに振ると床に着いてしまう**。方策は時計より早く頂点の姿勢に行き、
  床を突いてからもう一度上げて下ろしている（推定。胴のロール、足の前後位置は CSV に無いので未確認）。
- **軸足の股の開閉（下から4番目）が、毎歩シムの下限 −16°に張り付いている。** 実機は −8.5〜−11°で両足が触れ、送信器の `--safe-clamp` は −8°。
  このままでは実機で横の釣り合いの取り方が変わる。左右の胴の速度は ±0.2〜0.3 m/s で揺れ、yaw 角速度の標準偏差 0.14 rad/s。

## 本人の追加（20:20）
「少しがに股。joint_deviation_hip の重みは上げていい。下から4・5番目はあまり動く必要がない」→ 2 本とも、
`joint_deviation_hip`（既定姿勢からの |角度| の和）を X21 で外した 4番目を戻して 5番目＋4番目、重み −0.1 → −0.5（H の元の対象、5 倍）。
代わりに起きうること: 4番目 0°では足首の間隔が約 33 cm（URDF）なので、足を着く横幅が広がり、胴が左右に揺れる歩き方になりうる。
X23a では軸足の4番目が −16°（約 0.28 rad）なので、この罰は 1 step あたり約 −0.14（速度追従の最大 2.0 に対して小さめ）。

## 2 本（どちらもまっすぐ寄りの姿勢、観測 44 のまま、送信器の準備はそのまま使える）
| run | 親 | 変えたこと | ねらい |
|---|---|---|---|
| **X24a_notap**（GaitNoTap-v0、無難） | X23a の最新 | 参照の振り足の高さ A 0.35→0.42 rad、振り足の時間帯の真ん中（活性 >0.3）で床に着いている足 1 本につき −2.0（`swing_tap`）、**`joint_deviation_hip` を 5番目だけ −0.1 → 5番目＋4番目 −0.5** | 床を突くのをやめて 1 歩 1 回にする。がに股を減らす。それ以外は X23a のまま |
| **X24b_fwd**（GaitFwd-v0、革新） | **ゼロから** | X24a の3つ ＋ 参照の振り足に**前後の運び**（左 股 −B cos φ・右 +B cos φ、足首は逆で足裏平行、B = 0.625 × vx rad、上限 0.35）、振り足の高さを**軸足の足首からの差**で測る（3 cm × 活性、つま先立ちで稼げない）、**4番目の可動域 −8〜+30°**（実機の足の干渉と送信器の clamp に合わせる） | 参照が真上に上げ下げするだけで前へ運ぶ成分が無い（X21 からの見立て）ことを直し、実機で使えない −16°の横の釣り合いを最初から学ばせない |

判定（stand_walk vx 0.3 と random seed 0〜2、x24_video.py の要約）:
- **1 周期（0.7 s）あたりの着地が片足 1.0 回**、途中の床突き（振り足の時間帯の着地）がほぼ 0、前へ 0.25 m/s 以上、転倒なし → 当たり。
- 両方で、4番目・5番目の既定からのずれが X23a より小さい（がに股が減った、本人の目視も）。
- 追加で X24b は 4番目の最小が −8°に張り付いていないか、左右の揺れが X23a より小さいか。
- X24a は +300 iter（resume なので早い）、X24b は 1200 iter（X21 がゼロから歩いたのが約 1200）で最初の判定。
- X24a が当たりでも、4番目 −16°の張り付きが残るなら実機ではそのまま使えない（`--safe-clamp` −8°で横の釣り合いが変わる）。実機の本命は X24b。
- 立往生（X24b が 1200 で歩かない）なら、X24b の前後の運びを残したまま X23a から resume する版（X24c）を次に出す。
終わったらこのファイルを `../inactive/` へ移す。

## CLI に渡すもの

```
# 依頼: 実験24。2 本の学習（X24a は X23a から resume、X24b はゼロから）を準備して学習コマンドを渡し、そのあと動画スクリプト x24 を作る

## このプロンプトの前提
- 新しいチャット。このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。
- 長時間の学習をバックグラウンドで回さない。本番の学習はユーザーが別々の PowerShell で前景実行する。
- 既存のクラス・関数の中身は変えない（stand_env_cfg.py の末尾への追記と __init__.py への登録だけ）。
  新しく作ってよいファイルは tools\runs\x24_video.py だけ（x23_video.py はコピー元で、変えない）。何も削除しない。pip しない。
  git の commit・push をしない。動いている学習を止めない（止める必要があれば止まって報告）。
- stand_env_cfg.py は references\...\config\skyentific_poclegs\ と my_robot_code\ のハードリンク。**Edit ツールを使わない**。
  先に stand_env_cfg.py.bak_20260930_x24 と __init__.py.bak_20260930_x24 を取り、python で open(path, "r+") で読み、
  seek(0)・write・truncate で書き換える。書いたあと両パスの inode（os.stat().st_ino）が同じか確かめる。
- 推測で直さない。API 名の違いは Isaac Lab のソースを見て同じ意味の名前に直してよい（報告に書く）。意味が変わる修正が要るなら止まって報告。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\（run フォルダ）
- 学習・再生は train.py / play.py を直接呼ぶ。起動行の形（_preload_h5py_and_run.py 経由、conda activate、OMNI_KIT_ACCEPT_EULA、
  agent.policy.noise_std_type=log）は X23a を起動した行と同じ（tools\logs\ に run_X23a で始まるファイルがあればその先頭、
  無ければ run_X18h_bold_from_c.txt の先頭）。
- stand_env_cfg.py の末尾は X23 節（GaitFlat / GaitFlatH、feet_flat_in_contact、_x23、FOOT_FLAT_GREF に S1 で測った値）まで。
  そこで使っている名前 _swing_activation、_feet_in_contact、_is_moving、REF_SWING_SHAPE、X21_SAGITTAL_JOINTS、GAIT_PERIOD_S、
  FEET_ORDERED、FEET_BODIES_ORDERED、_play、math が定義済みか確かめる。無ければ止まって報告。
- 親（X24a）: run フォルダ名が *_X23a_flat_upright の一番新しいものの、一番新しい model_*.pt。観測 44 次元。制御 50 Hz。
  GPU は RTX 3090 Ti が1枚。X23 の学習がまだ動いていたら止まって報告。

## S1 追記と登録
1. 末尾に「追記するコード」をそのまま追記。__init__.py に4つ（形は GaitFlat-v0 と同じ、rsl_rl の entry point も同じ）:
   Skyentific-Poclegs-GaitNoTap-v0 / GaitNoTap-Play-v0 → SkyentificPoclegsGaitNoTapEnvCfg / _PLAY、
   Skyentific-Poclegs-GaitFwd-v0 / GaitFwd-Play-v0 → SkyentificPoclegsGaitFwdEnvCfg / _PLAY。
2. 16 env・押しなしの短い確認（学習しない、数秒）で次を表に:
   - GaitNoTap-Play: ref_joint_pos の amp 0.42、swing_tap の重み −2.0、joint_deviation_hip の重み −0.5 と対象の関節名（左右の HR・HAA の 4 つ）。
   - GaitFwd-Play: ref_joint_pos の func が ref_joint_pos_tracking_fwd、swing_clearance の func が swing_clearance_rel_deficit、
     4番目（.*_HAA）の可動域がシム上で −8〜+30°（asset の joint_pos_limits を度で）。
   - GaitFwd の参照の符号: 指令 vx 0.3 固定・1 env で、時刻 t（sin(2πt/0.7) が 0→1→0→−1）ごとの参照の股の前後（LL_HFE・LR_HFE の
     q_ref − 既定）を 0.05 s 刻みで表にする。右（LR）は sin > 0 の間に +0.19 → −0.19 rad、左（LL）は sin < 0 の間に +0.19 → −0.19 rad
     と動けば正しい（+ = 足首が後ろ）。違ったら止まって報告。

## S2 スモーク（各 64 env・5 iter）
- TEST_X24a（GaitNoTap-v0、親 X23a から resume）・TEST_X24b（GaitFwd-v0、ゼロから）。上書きは不要。
- 確かめて表に: X24a は checkpoint を読めた行と iter が親の続き、X24b は iter 0 から。観測 44。env.yaml に swing_tap −2.0・joint_deviation_hip −0.5（対象 .*HR と .*HAA）・feet_flat −10・
  action_rate_l2 −0.1・joint_acc_l2 −2.5e-07・ref_joint_pos 2.0 と amp 0.42、X24b は fwd_gain 0.625・target_dz 0.03・HAA の −8。
  ログに swing_tap の項目、NaN なし。TEST_ は消さない。
- **合格したら、ここで学習コマンドを先に出す**: 別々の PowerShell、train.py を直接、seed 1、num_envs 4096、save_interval 100、
  noise_std_type=log、--device cuda:0。
  - X24a_notap: GaitNoTap-v0、親 X23a の最新 checkpoint から resume、max_iterations 1000（追加分）、entropy_coef 0.005。
  - X24b_fwd: GaitFwd-v0、ゼロから、max_iterations 3000、entropy_coef は X21a をゼロから起動した行と同じ
    （tools\logs\ に run_X21a で始まるファイルがあればその値、無ければ上書きしない＝既定）。
  - 先頭に nvidia-smi の1行と「1本目の 1〜2 iter 後に空きを見て2本目」。実行フォルダ付き・プレースホルダ無し・改行なしの1行版。
  そのあと S3 に進む。

## S3 動画スクリプト tools\runs\x24_video.py（学習と並行でよい。1 env だけ使う）
x23_video.py をコピーして、次を足す（引数・保存先の形・リセットは最初の1回だけ・最初の 2 s は指令 0、はそのまま。保存先は videos\x24\）:
- csv の列を追加: 胴のロール・ピッチ [deg]、両足首の点の位置を胴の yaw で回した座標の前後・左右 [m]（胴の位置からの差）、
  その step の時計 sin(2πt/0.7)。
- 要約を追加:
  - 1 周期（0.7 s）あたりの着地回数（左右別。1.0 が正常、X23a@4200 は 2.0）。
  - 4番目・5番目の |既定からの角度| の平均 [deg]（左右別。がに股の目安）。
  - 途中の床突き: 振り足の時間帯（左は sin < −0.37、右は sin > +0.37）に着地した回数の 1 周期あたり。
  - 歩幅: 着地した瞬間の、その足の前後位置 − もう一方の足の前後位置 の中央値 [m]。
  - 下から4番目（HAA）の、接地中の p5 と最小 [deg]（左右別）、−15.5°以下 または −7.5°以下にいた時間の割合。
  - 胴のロールの振れ幅（p95−p5）[deg]、左右の速度の標準偏差 [m/s]。
- 動作確認: X23a の最新 checkpoint（GaitFlat-Play-v0）で stand_walk（vx 0.3）を1回、--video 付きで撮り、要約の表を出す（X24 の比較の基準）。

## 報告（これで止まる。短く）
1. 冒頭3行: S1 の符号の確認、S2 の合否、X23a 最新の着地回数・途中の床突き・歩幅・4番目の p5。
2. S1・S2・S3 の表、直した API 名、変えたファイル。
3. 学習コマンド（S2 の直後に出したものを再掲）。
4. 動画コマンド（x24_video.py、実行フォルダ付き・1行版）: X24a（GaitNoTap-Play-v0、例 model_「親+300」.pt）と
   X24b（GaitFwd-Play-v0、例 model_1200.pt）の stand_walk（vx 0.3）と random（seed 0・1・2）、画面で見る用（--video・--headless なし）1本。
   checkpoint・seed・vx を変えるだけで何度でも撮れる形。mp4 と csv ができるフォルダの絶対パス。
5. 学習中に見る値: Episode_Reward/swing_tap は 0 に近づく、track_lin_vel_xy_exp・gait_contact は X24a で親から大きく下がらない、
   mean_episode_length が下がらない。X24b は 500 iter までに track_lin_vel_xy_exp が上がり始めなければ立往生の兆し。
```

## 追記するコード

```python


# =====================================================================================================
# X24 (2026-09-30 20:30): X23a (model_4200, user's replay + csv) walks forward (vx 0.275 for 0.3), feet
# flatter than X22 (outer edge p50 7.5 / 5.7 deg, toe p50 2.6 / -0.4 deg), but every swing is split in two:
# each foot touches down 2x per 0.7 s cycle (touchdown intervals 0.20 / 0.50 s). In the csv the swing leg
# reaches the reference peak pose early (HFE -25..-28, KFE +35..+40, FFE -14 deg ~= default + (-A, +2A, -A))
# and at that pose the foot is ON the floor (ankle z 84 mm vs 81 mm in stance): the reference gives no
# clearance in the real posture, so the foot taps at mid-swing and lifts again ("R, R, L, L").
# Also: the stance leg's HAA sits on the sim limit -16 deg in every step (the real feet touch at
# -8.5..-11 deg and the transmitter clamps at -8), lateral body speed swings +-0.2..0.3 m/s.
#   X24a GaitNoTap (safe)       : resume X23a. Reference amplitude 0.35 -> 0.42, a penalty for the
#                                 scheduled swing foot touching the floor in the middle of its window, and
#                                 joint_deviation_hip on HR + HAA at -0.5 (was HR only, -0.1).
#   X24b GaitFwd   (innovative) : from scratch, upright pose. Reference swing that also carries the foot
#                                 from back to front (HFE +-B cos(phase), FFE compensates, B from the vx
#                                 command), clearance measured against the stance foot (no tiptoe trick),
#                                 the same tap penalty and hip deviation, HAA limited to -8 deg like the real robot.
# =====================================================================================================
X24_REF_SWING_AMP_RAD = 0.42
X24_TAP_MIN_ACT = 0.3           # swing activation above which a touching swing foot counts as a tap
X24_FWD_GAIN = 0.625            # rad per (m/s): half stride vx*T/4 over a ~0.28 m leg
X24_FWD_MAX = 0.35
X24_REL_CLEARANCE_M = 0.03      # swing ankle above stance ankle at full swing activation
X24_HAA_LIMITS_DEG = (-8.0, 30.0)
X24_HIP_DEV_WEIGHT = -0.5         # joint_deviation_hip (L1 of HR and HAA from default), was -0.1 on HR only


def swing_foot_tap(env, period: float, command_name: str, sensor_cfg: SceneEntityCfg, min_act: float) -> torch.Tensor:
    """Number of feet (0..2) touching the floor while the clock says they are in mid-swing."""
    act = _swing_activation(env, period, command_name)  # zero when not moving
    contact = _feet_in_contact(env, sensor_cfg).float()
    return torch.sum((act > min_act).float() * contact, dim=1)


def swing_clearance_rel_deficit(env, period: float, command_name: str, asset_cfg: SceneEntityCfg,
                                target_dz: float) -> torch.Tensor:
    """Sum over feet of max(0, target_dz * activation - (z_this - z_other)) [m]. Standing on the toe of the
    stance foot raises both ankles, so it no longer buys clearance."""
    act = _swing_activation(env, period, command_name)
    z = env.scene[asset_cfg.name].data.body_pos_w[:, asset_cfg.body_ids, 2]  # (N, 2) left, right
    dz = z - z.flip(dims=[1])
    return torch.clamp(target_dz * act - dz, min=0.0).sum(dim=1)


def ref_joint_pos_tracking_fwd(env, period: float, command_name: str, asset_cfg: SceneEntityCfg,
                               amp: float, fwd_gain: float, fwd_max: float) -> torch.Tensor:
    """X21 reference (lift: HFE -A, KFE +2A, FFE -A times swing activation) plus a fore-aft sweep:
    left HFE -B cos(ph), right HFE +B cos(ph), FFE the opposite (sole stays parallel), B = gain * vx.
    +HFE moves the ankle back: the left leg (swings while sin < 0) goes back -> front over pi..2pi and
    front -> back while it stands; the right leg the same half a cycle later."""
    asset = env.scene[asset_cfg.name]
    ids = asset_cfg.joint_ids
    q = asset.data.joint_pos[:, ids]
    q0 = asset.data.default_joint_pos[:, ids]
    act = _swing_activation(env, period, command_name)
    shape = torch.tensor(REF_SWING_SHAPE, device=q.device, dtype=q.dtype)
    lift = torch.cat([act[:, 0:1] * shape, act[:, 1:2] * shape], dim=1) * amp
    t = env.episode_length_buf.float() * env.step_dt
    c = torch.cos(2.0 * math.pi * t / period)
    vx = env.command_manager.get_command(command_name)[:, 0]
    b = torch.clamp(vx * fwd_gain, -fwd_max, fwd_max) * _is_moving(env, command_name).float()
    hl = -b * c
    hr = b * c
    zero = torch.zeros_like(hl)
    fwd = torch.stack([hl, zero, -hl, hr, zero, -hr], dim=1)
    err = torch.norm(q - (q0 + lift + fwd), dim=1)
    return torch.exp(-2.0 * err) - 0.2 * torch.clamp(err, 0.0, 0.5)


def _x24_common(cfg):
    cfg.rewards.ref_joint_pos.params["amp"] = X24_REF_SWING_AMP_RAD
    # user (2026-09-30 20:20): slightly bow-legged; HAA and HR (4th and 5th from the bottom) need not move much.
    # Back to H's joint set (HR + HAA, X21 had dropped HAA) and 5x the weight.
    cfg.rewards.joint_deviation_hip.weight = X24_HIP_DEV_WEIGHT
    cfg.rewards.joint_deviation_hip.params["asset_cfg"] = SceneEntityCfg("robot", joint_names=[".*HR", ".*HAA"])
    cfg.rewards.swing_tap = RewTerm(
        func=swing_foot_tap, weight=-2.0,
        params={"period": GAIT_PERIOD_S, "command_name": "base_velocity", "sensor_cfg": FEET_ORDERED,
                "min_act": X24_TAP_MIN_ACT},
    )


@configclass
class SkyentificPoclegsGaitNoTapEnvCfg(SkyentificPoclegsGaitFlatEnvCfg):
    """X24a: X23a + higher reference swing + mid-swing tap penalty (resume X23a)."""

    def __post_init__(self):
        super().__post_init__()
        _x24_common(self)


@configclass
class SkyentificPoclegsGaitFwdEnvCfg(SkyentificPoclegsGaitFlatEnvCfg):
    """X24b: fore-aft reference swing, clearance against the stance foot, tap penalty, HAA >= -8 deg."""

    def __post_init__(self):
        super().__post_init__()
        _x24_common(self)
        r = self.rewards
        r.ref_joint_pos.func = ref_joint_pos_tracking_fwd
        r.ref_joint_pos.params = {
            "period": GAIT_PERIOD_S, "command_name": "base_velocity", "asset_cfg": X21_SAGITTAL_JOINTS,
            "amp": X24_REF_SWING_AMP_RAD, "fwd_gain": X24_FWD_GAIN, "fwd_max": X24_FWD_MAX,
        }
        r.swing_clearance.func = swing_clearance_rel_deficit
        r.swing_clearance.params = {
            "period": GAIT_PERIOD_S, "command_name": "base_velocity", "asset_cfg": FEET_BODIES_ORDERED,
            "target_dz": X24_REL_CLEARANCE_M,
        }
        limits = dict(self.events.set_joint_limits.params["limits_deg"])
        limits[".*_HAA"] = X24_HAA_LIMITS_DEG
        self.events.set_joint_limits.params["limits_deg"] = limits


@configclass
class SkyentificPoclegsGaitNoTapEnvCfg_PLAY(SkyentificPoclegsGaitNoTapEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)


@configclass
class SkyentificPoclegsGaitFwdEnvCfg_PLAY(SkyentificPoclegsGaitFwdEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)
```
