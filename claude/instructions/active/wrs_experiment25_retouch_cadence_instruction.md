# WRS 実験25: 同じ足の連続着地を止める 2 本（X25a 本人案・X25b 周期を短く）＋動画スクリプト x25

作成 2026-09-30 23:15。**本人が X24a・X24b の学習を止めてから、新しい CLI チャットに「CLI に渡すもの」と「追記するコード」を貼る。**
前提: 実験24 の 2 本が終わった／打ち切った。本人の再生 2 本（stand_walk vx 0.3、seed 0）を解析した結果が下。
- `model_5800_stand_walk_vx0.3_seed0_20260930_223802.csv`（X24a_notap、X23a から resume、最新）
- `model_1200_stand_walk_vx0.3_seed0_20260930_225334.csv`（X24b_fwd、ゼロから 1200 iter。本人判断で打ち切り）

## X24a@5800・X24b@1200 の所見（CSV、t 2.5〜12 s）
- **両方とも右右左左のまま、形まで同じ。** 着地 54 回のうち同じ足の連続が 27 回＝片足が 1 周期（0.7 s）に 2.0 回着地。
  振り足: 0.10〜0.14 s 浮く → **時計の頂点（|sin| ≈ 1）で、軸足の横（前後の差 0±3 cm）に** 約 0.05 s 着く → 0.12〜0.14 s 浮く →
  時間帯の終わりに 10〜16 cm 前へ着く。
- 途中の着地の瞬間、胴は振り足の側へ横に動いている（+0.07〜0.14 m/s、4 例中 3 例）。足首の横位置は胴から +0.16 / −0.15〜−0.19 m（間隔 32〜35 cm）。
- 振り足の高さは足りている（浮いている間の足首 p95 100〜112 mm、立っている足 77〜84 mm）。**高さの問題ではない。**
- 前へ 0.28（a）/ 0.31（b）m/s、転倒なし、両足同時に浮く 0%、両足接地 26 / 32%。左右の速度の標準偏差 0.14 / 0.13、yaw 0.19 / 0.19 rad/s。
- X24a: 右の5番目（HR）が **+25°（可動域の端）に張り付いたまま**、右の4番目 p5 −16°（下限）。実機には使えない。
  X24b: 4番目 p5 −2°前後、5番目 +4〜8°。関節の速さ p99 は膝 415〜465°/s、股の前後 220〜285°/s、足首 285〜315°/s。
- **見立て（推定）: 途中の着地は横に倒れかけたのを受け止める一歩。** 軸足が胴から約 16 cm 外にあるので、0.7 s の時計が求める約 0.3 s の片足立ちが持たず、
  約 0.13 s で振り足を着いて支えている。`swing_tap` −2 は 1 回あたり約 −0.15（報酬は重み × 0.02 s）で、倒れるより安い。
  ゼロからの X24b でも 1200 iter で同じ形になった＝X23a の癖ではなく、共通の報酬と体の形から来ている。

## 2 本（どちらも X24b の上、まっすぐ寄りの姿勢、観測 44 次元のまま）
| run | 親 | 変えたこと | ねらい |
|---|---|---|---|
| **X25a_retouch**（GaitRetouch-v0、本人案） | X24b_fwd の最新から resume、1500 iter | **同じ足が 2 回続けて着地したら 1 回 −0.5**（重み −25 × 0.02 s、0.04 s 以上浮いた着地だけ数える、時計と無関係） | 本人案をそのまま確かめる。時刻をずらして逃げられない |
| **X25b_cadence**（GaitCadence-v0、革新） | **ゼロから**、3000 iter | X25a ＋ **時計の周期 0.7 → 0.45 s**（観測と時計を使う報酬すべて）、前後の運びの係数 0.625 → 0.40、片足の空中時間の報酬 0.10〜0.25 s | 体が持つ片足立ち（約 0.13 s）に近い振り足の時間帯（約 0.21 s）にして、受け止める一歩を要らなくする |

- X25a で起きうること: 横の釣り合いが原因なら、罰だけでは「すり足」「その場で止まる」「転ぶ」に逃げる。それ自体が見立ての確認になる。
- X25b で起きうること: 関節が速くなる（膝 p99 が 500°/s を超えないか見る。送信器の速度中止は `--wide-limits` で 900°/s）。
  **当たりなら送信器の時計を 0.45 s に変える必要がある**（`transmitter_x21_clock_pose_instruction.md` は 0.7 s 前提）。

判定（stand_walk vx 0.3 と random seed 0〜2、x25_video.py の要約）:
- **同じ足の連続着地が 1 周期あたりほぼ 0**、1 周期あたりの着地が片足 1.0 回、前へ 0.25 m/s 以上、転倒なし → 当たり。
- 4番目の p5 が −8°に張り付いていない、5番目のずれが小さい、関節の速さ p99 が膝 500°/s 以下。
- X25a は +300 iter、X25b は 1200 iter で最初に見る。
終わったらこのファイルを `../inactive/` へ移す。

## CLI に渡すもの

```
# 依頼: 実験25。2 本の学習（X25a は X24b から resume、X25b はゼロから）を準備して学習コマンドを渡し、そのあと動画スクリプト x25 を作る

## このプロンプトの前提
- 新しいチャット。このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。
- 長時間の学習をバックグラウンドで回さない。本番の学習はユーザーが別々の PowerShell で前景実行する。
- 既存のクラス・関数の中身は変えない（stand_env_cfg.py の末尾への追記と __init__.py への登録だけ）。
  新しく作ってよいファイルは tools\runs\x25_video.py だけ（x24_video.py はコピー元で、変えない）。何も削除しない。pip しない。
  git の commit・push をしない。動いている学習を止めない（X24a・X24b が動いていたら止まって報告）。
- stand_env_cfg.py は references\...\config\skyentific_poclegs\ と my_robot_code\ のハードリンク。**Edit ツールを使わない**。
  先に stand_env_cfg.py.bak_20260930_x25 と __init__.py.bak_20260930_x25 を取り、python で open(path, "r+") で読み、
  seek(0)・write・truncate で書き換える。書いたあと両パスの inode（os.stat().st_ino）が同じか確かめる。
- 推測で直さない。API 名の違いは Isaac Lab のソースを見て同じ意味の名前に直してよい（報告に書く）。意味が変わる修正が要るなら止まって報告。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\（run フォルダ）
- 学習・再生は train.py / play.py を直接呼ぶ。起動行の形（_preload_h5py_and_run.py 経由、conda activate、OMNI_KIT_ACCEPT_EULA、
  agent.policy.noise_std_type=log）は X24b を起動した行と同じ（tools\logs\ に run_X24b で始まるファイルがあればその先頭、
  無ければ run_X23a で始まるもの）。
- stand_env_cfg.py の末尾は X24 節（GaitNoTap / GaitFwd、swing_foot_tap、ref_joint_pos_tracking_fwd、_x24_common）まで。
  そこで使っている名前 SkyentificPoclegsGaitFwdEnvCfg、_is_moving、FEET_ORDERED、RewTerm、_play が定義済みか、
  GaitFwd の rewards に ref_joint_pos（params に fwd_gain）・feet_single_air_time・swing_clearance・gait_contact・swing_tap があり、
  observations.policy に gait_phase があるか確かめる。無ければ止まって報告。
- 親（X25a）: run フォルダ名が *_X24b_fwd の一番新しいものの、一番新しい model_*.pt。観測 44 次元。制御 50 Hz。GPU は RTX 3090 Ti が1枚。

## S1 追記と登録
1. 末尾に「追記するコード」をそのまま追記。__init__.py に4つ（形は GaitFwd-v0 と同じ、rsl_rl の entry point も同じ）:
   Skyentific-Poclegs-GaitRetouch-v0 / GaitRetouch-Play-v0 → SkyentificPoclegsGaitRetouchEnvCfg / _PLAY、
   Skyentific-Poclegs-GaitCadence-v0 / GaitCadence-Play-v0 → SkyentificPoclegsGaitCadenceEnvCfg / _PLAY。
2. 16 env・押しなしの短い確認（学習しない）で次を表に:
   - GaitRetouch-Play: same_foot_touchdown の重み −25.0・min_air 0.04。時計を使う項（gait_contact・swing_clearance・ref_joint_pos・swing_tap）
     と観測 gait_phase の period がすべて 0.7。
   - GaitCadence-Play: 上の period がすべて 0.45、ref_joint_pos の fwd_gain 0.40、feet_single_air_time の threshold_min 0.10・max 0.25、
     same_foot_touchdown −25.0、4番目の可動域 −8〜+30°。
   - same_foot_touchdown の動作: GaitRetouch-Play の 1 env を、指令 vx 0.3 固定・**親 X24b の最新 checkpoint の方策で** 10 s 回し、
     各 step の左右の接地と same_foot_touchdown の生の値（重みを掛ける前、0 か 1）を記録。
     「同じ足が 2 回続けて着地した step」を接地の列から数えた回数と、生の値が 1 だった回数が一致すれば合格（X24b@1200 では 10 s でおよそ 25〜30 回のはず）。
     合わなければ止まって報告。

## S2 スモーク（各 64 env・5 iter）
- TEST_X25a（GaitRetouch-v0、親 X24b から resume）・TEST_X25b（GaitCadence-v0、ゼロから）。上書きは不要。
- 確かめて表に: X25a は checkpoint を読めた行と iter が親の続き、X25b は iter 0 から。観測 44。
  env.yaml に same_foot_touchdown −25.0、swing_tap −2.0、joint_deviation_hip −0.5、feet_flat −10、ref_joint_pos 2.0・amp 0.42、
  X25a は period 0.7・fwd_gain 0.625、X25b は period 0.45・fwd_gain 0.40・feet_single_air_time 0.10〜0.25。
  ログに Episode_Reward/same_foot_touchdown の項目、NaN なし。TEST_ は消さない。
- **合格したら、ここで学習コマンドを先に出す**: 別々の PowerShell、train.py を直接、seed 1、num_envs 4096、save_interval 100、
  noise_std_type=log、--device cuda:0。
  - X25a_retouch: GaitRetouch-v0、親 X24b の最新 checkpoint から resume、max_iterations 1500（追加分）、entropy_coef 0.005。
  - X25b_cadence: GaitCadence-v0、ゼロから、max_iterations 3000、entropy_coef は X24b を起動した行と同じ（上書きしていなければ上書きしない）。
  - 先頭に nvidia-smi の1行と「1本目の 1〜2 iter 後に空きを見て2本目」。実行フォルダ付き・プレースホルダ無し・改行なしの1行版。
  そのあと S3 に進む。

## S3 動画スクリプト tools\runs\x25_video.py（学習と並行でよい。1 env だけ使う）
x24_video.py をコピーして、次だけ変える・足す（引数・保存先の形・リセットは最初の1回だけ・最初の 2 s は指令 0 はそのまま。保存先は videos\x25\）:
- 引数 --period（既定 0.7）。csv の clock_sin と、要約の「1 周期あたり」・振り足の時間帯の判定はこの周期で計算する。
  GaitCadence のときは 0.45 を渡す（task 名に Cadence が入っていれば既定を 0.45 にしてもよい）。
- 要約を追加:
  - 同じ足の連続着地の回数（0.04 s 以上浮いた着地の列で、直前の着地と同じ足）と、その 1 周期あたり。
  - 横に着く一歩: 着地した瞬間の前後の差（その足 − もう一方の足）が 5 cm 未満だった着地の割合。
  - 関節の速さの p99 [deg/s]（10 関節、csv の角度の差分 ÷ 0.02）。
  - 胴から足首までの横の距離の中央値 [m]（左右別）。
- 動作確認: X24b の最新 checkpoint（GaitFwd-Play-v0、--period 0.7）で stand_walk（vx 0.3）を1回撮り、要約の表を出す
  （同じ足の連続は 1 周期あたり約 1.0 のはず。X25 の比較の基準）。

## 報告（これで止まる。短く）
1. 冒頭3行: S1 の same_foot_touchdown の一致、S2 の合否、X24b 最新の同じ足の連続・横に着く一歩の割合・膝の速さ p99。
2. S1・S2・S3 の表、直した API 名、変えたファイル。
3. 学習コマンド（S2 の直後に出したものを再掲）。
4. 動画コマンド（x25_video.py、実行フォルダ付き・1行版）: X25a（GaitRetouch-Play-v0、--period 0.7、例 model_「親+300」.pt）と
   X25b（GaitCadence-Play-v0、--period 0.45、例 model_1200.pt）の stand_walk（vx 0.3）と random（seed 0・1・2）、画面で見る用（--video・--headless なし）1本。
   checkpoint・seed・vx を変えるだけで何度でも撮れる形。mp4 と csv ができるフォルダの絶対パス。
5. 学習中に見る値: Episode_Reward/same_foot_touchdown が 0 に近づく、mean_episode_length が下がらない、track_lin_vel_xy_exp が
   X25a で親から大きく下がらない（下がって戻らなければ「罰だけでは無理」の兆し）。X25b は 500 iter までに track_lin_vel_xy_exp が上がり始めなければ立往生の兆し。
```

## 追記するコード

リポジトリの `my_robot_code/stand_env_cfg.py` 末尾にも同じものを追記済み。

```python

# =====================================================================================================
# X25 (2026-09-30 23:10): X24a@5800 (resumed X23a) and X24b@1200 (from scratch, fore-aft reference, HAA >= -8)
# both still land every foot twice per 0.7 s cycle ("L, L, R, R", 27 same-foot repeats in 54 touchdowns,
# stand_walk vx 0.3, t 2.5..12 s). The pattern is identical in both: lift 0.10..0.14 s -> touch at the clock
# peak (|sin| ~ 1) BESIDE the stance foot (fore-aft offset ~ 0 +- 3 cm) for ~0.05 s -> lift 0.12..0.14 s ->
# land 10..16 cm ahead at the end of the window. At the mid touch the body is moving sideways toward the swing
# side (+0.07..0.14 m/s in 3 of 4 cases), feet are 32..35 cm apart (ankle_lat +0.16 / -0.15..-0.19 m).
# Reading: the tap is a lateral catch step. With the stance ankle ~16 cm outside the body the robot cannot stay
# on one foot for the ~0.3 s swing window of a 0.7 s clock; ~0.13 s is what it holds. swing_tap (-2, i.e.
# ~ -0.15 per tap) is far cheaper than falling. Swing clearance itself is fine (ankle 25..30 mm above stance).
#   X25a GaitRetouch (user's idea)  : X24b + a penalty on the same foot landing twice in a row (-0.5 per event,
#                                     counted on landings after >= 0.04 s in the air). Resume the latest X24b.
#   X25b GaitCadence (innovative)  : X25a + clock period 0.7 -> 0.45 s (swing window ~0.21 s, close to the
#                                     ~0.13 s single support the robot holds), fore-aft gain rescaled to the
#                                     shorter stride, single-stance air-time reward window 0.10..0.25 s.
#                                     From scratch (the clock in the observation changes speed).
# =====================================================================================================
X25_RETOUCH_WEIGHT = -25.0       # x step_dt 0.02 -> -0.5 per same-foot re-landing
X25_RETOUCH_MIN_AIR_S = 0.04     # landings after a shorter lift (contact flicker) are not counted
X25_PERIOD_S = 0.45
X25_FWD_GAIN = 0.40              # vx * T / 4 over a ~0.28 m leg at T = 0.45 (X24: 0.625 at T = 0.7)
X25_AIR_MIN_S = 0.10
X25_AIR_MAX_S = 0.25


def same_foot_touchdown(env, command_name: str, sensor_cfg: SceneEntityCfg, min_air: float) -> torch.Tensor:
    """1 when a foot lands and the previous landing (after >= min_air s in the air) was the same foot.
    The last landing foot is kept on the env (-1 = none) and cleared at the start of every episode."""
    cs = env.scene.sensors[sensor_cfg.name]
    first = cs.compute_first_contact(env.step_dt)[:, sensor_cfg.body_ids] > 0          # (N, 2) left, right
    td = first & (cs.data.last_air_time[:, sensor_cfg.body_ids] > min_air)
    last = getattr(env, "_x25_last_td_foot", None)
    if last is None or last.shape[0] != td.shape[0]:
        last = torch.full((td.shape[0],), -1, dtype=torch.long, device=td.device)
    last = torch.where(env.episode_length_buf <= 1, torch.full_like(last, -1), last)
    left, right = td[:, 0], td[:, 1]
    pen = (left & ~right & (last == 0)) | (right & ~left & (last == 1))
    last = torch.where(left & ~right, torch.zeros_like(last), last)
    last = torch.where(right & ~left, torch.ones_like(last), last)
    last = torch.where(left & right, torch.full_like(last, -1), last)
    env._x25_last_td_foot = last
    return pen.float() * _is_moving(env, command_name).float()


def _x25_retouch(cfg):
    cfg.rewards.same_foot_touchdown = RewTerm(
        func=same_foot_touchdown, weight=X25_RETOUCH_WEIGHT,
        params={"command_name": "base_velocity", "sensor_cfg": FEET_ORDERED, "min_air": X25_RETOUCH_MIN_AIR_S},
    )


@configclass
class SkyentificPoclegsGaitRetouchEnvCfg(SkyentificPoclegsGaitFwdEnvCfg):
    """X25a: X24b + same-foot re-landing penalty (resume X24b)."""

    def __post_init__(self):
        super().__post_init__()
        _x25_retouch(self)


@configclass
class SkyentificPoclegsGaitCadenceEnvCfg(SkyentificPoclegsGaitRetouchEnvCfg):
    """X25b: X25a with a 0.45 s clock (observation and every clock-driven reward), from scratch."""

    def __post_init__(self):
        super().__post_init__()
        self.observations.policy.gait_phase.params["period"] = X25_PERIOD_S
        for term in self.rewards.__dict__.values():
            if isinstance(term, RewTerm) and isinstance(term.params, dict) and "period" in term.params:
                term.params["period"] = X25_PERIOD_S
        self.rewards.ref_joint_pos.params["fwd_gain"] = X25_FWD_GAIN
        self.rewards.feet_single_air_time.params["threshold_min"] = X25_AIR_MIN_S
        self.rewards.feet_single_air_time.params["threshold_max"] = X25_AIR_MAX_S


@configclass
class SkyentificPoclegsGaitRetouchEnvCfg_PLAY(SkyentificPoclegsGaitRetouchEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)


@configclass
class SkyentificPoclegsGaitCadenceEnvCfg_PLAY(SkyentificPoclegsGaitCadenceEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)
```
