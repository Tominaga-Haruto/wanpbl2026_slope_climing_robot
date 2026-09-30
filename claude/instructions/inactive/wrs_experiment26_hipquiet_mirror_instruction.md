> 実行済み（2026-10-01）。結果と後継は `../active/wrs_experiment27_hiplock_refloose_instruction.md`。
> **最新は末尾の追記（02:45）: X26b（鏡映）は取りやめ、X26c（5番目 ±8°）に差し替え。2本とも X25b@2100 から 10000 iter。**

# WRS 実験26: X25b の右の5番目（内股）を直す 2 本（X26a 4/5番目の罰・X26b 左右対称の損失）＋多視点の動画スクリプト x26

作成 2026-10-01 02:40。**本人が X25a・X25b の学習を止めてから、新しい CLI チャットに「CLI に渡すもの」を貼る。**
**「CLI に渡すもの」の4つ連続のバッククォートの中を丸ごと1回で貼る**（コード A・B も中に入っている）。コード（リポジトリの `my_robot_code/stand_env_cfg.py` と `my_robot_code/rsl_rl_cfg.py` の末尾にも同じものを追記済み）。

## X25a・X25b の所見
- **X25a_retouch（本人の目視、CSV なし）: 外れ。** 同じ足の連続着地の罰を、**もう一方の足でちょんと着く**ことで避けた
  （右を出す → 左でちょん → 左を出す → 右でちょん）。1 周期に 4 回着く形のまま。がに股で足幅が大きい。打ち切り。
- **X25b_cadence（時計 0.45 s、ゼロから）: 当たり。** 本人「2000 iter でかなりいい。足を擦っていない、ほぼ完璧。少し内股なのだけ気になる。1200 と 2000 はほぼ同じ」。
  CSV `model_1200_stand_walk_vx0.3_seed0_20261001_015825.csv`（t 2.5〜12 s）:

| 項目 | X25b@1200 |
|---|---|
| 着地 / 同じ足の連続 | 42 回 / **0 回**（片足 1 周期 1.0 回、LRLR…） |
| 前後の速度（指令 0.3） | 0.324 m/s、転倒なし、両足同時に浮く 0% |
| 両足接地 / 片足の空中時間 | 16% / 左 0.20・右 0.18 s |
| **右の5番目** | **−25.0°（可動域の端、つま先が内向き）に歩いている間 100% 張り付き**。行動 −0.9 で押し付けている。立っている間は −6° |
| 左の5番目 | −2°（p5 −3.3、p95 −0.7） |
| 4番目（左 / 右） | 平均 +4.3 / +3.6°（開く向き）、p95 +9.8 / +6.6° |
| 足首の横（胴から） | 左 +0.166・右 −0.195 m、間隔 0.36 m（立っているとき 0.34 m） |
| 膝の速さ p99 | 左 501・右 539°/s |
| 左右の速度の標準偏差 / yaw | 0.20 m/s / 0.11 rad/s |

- **本人の「少し内股」は右の5番目の −25°張り付き**（5番目の + はつま先が外）。片側だけの癖。
  今の `joint_deviation_hip`（4/5番目の L1、−0.5）は 25°でも 1 秒あたり約 −0.2 で、癖を止めるには安すぎる。
- 本人の方針（2026-10-01）: **まっすぐ歩くときは直立姿勢から4・5番目はほとんど動かさなくていい。**

## 2 本（どちらも X25b の最新から resume、観測 44・時計 0.45 s のまま）
| run | 変えたこと | ねらい |
|---|---|---|
| **X26a_hipquiet**（GaitHipQuiet-v0、無難） | X25b ＋ **4・5番目の既定からのずれ（L1）に −5**、yaw の指令が小さい（\|wz\| < 0.15）ときだけ | まっすぐ歩くときの4・5番目を止める。旋回では5番目を使ってよい |
| **X26b_mirror**（GaitMirror-v0、革新） | X26a と同じ環境 ＋ **RSL-RL の左右対称の損失**（左右の脚を入れ替え、時計を半周期ずらした観測に、入れ替えた行動を出させる。係数 0.5） | 片側だけの癖そのものを消す。罰の値付けに頼らない |

- 起きうること: X26a は5番目が内に寄せられなくなって yaw が流れる（まっすぐ歩けない）かもしれない。それなら右の5番目は曲がるのを打ち消していた＝体の左右差が原因。X26b は対称になるが、いったん歩き方が崩れてから戻る可能性。
- 判定（x26_video.py の要約、stand_walk vx 0.3 と random seed 0〜2）: **5番目が ±25°に張り付いていない（端から 1°以内の時間 0%）・5番目の平均が左右とも ±8°以内**、4番目の平均 ±4°以内、
  同じ足の連続 ほぼ 0・前へ 0.25 m/s 以上・転倒なし（X25b を崩していない）、膝 p99 550°/s 以下、random で yaw の追従が X25b から大きく落ちない。+300 iter で最初に見る。
- 終わったらこのファイルを `../inactive/` へ移す。

## CLI に渡すもの

````
# 依頼: 実験26。X25b から resume する 2 本（X26a 4/5番目の罰、X26b 左右対称の損失）を準備して学習コマンドを渡し、そのあと多視点の動画スクリプト x26 を作る

## このプロンプトの前提
- 新しいチャット。このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。
- 長時間の学習をバックグラウンドで回さない。本番の学習・再生・動画はユーザーが別々の PowerShell で前景実行する。
- 既存のクラス・関数の中身は変えない（stand_env_cfg.py と rsl_rl の agent cfg ファイルの末尾への追記、__init__.py への登録だけ）。
  新しく作ってよいファイルは tools\runs\x26_video.py だけ（x25_video.py はコピー元で、変えない）。何も削除しない。pip しない。
  git の commit・push をしない。動いている学習を止めない（X25a・X25b が動いていたら止まって報告）。
- stand_env_cfg.py は references\...\config\skyentific_poclegs\ と my_robot_code\ のハードリンク。**Edit ツールを使わない**。
  先に stand_env_cfg.py.bak_20261001_x26・__init__.py.bak_20261001_x26・（agent cfg ファイル名）.bak_20261001_x26 を取り、
  python で open(path, "r+") で読み、seek(0)・write・truncate で書き換える。書いたあと、ハードリンクの両パスの inode（os.stat().st_ino）が同じか確かめる
  （agent cfg ファイルもハードリンクなら同じ扱い）。
- 推測で直さない。API 名・呼び出し形の違いは Isaac Lab / rsl_rl のソースを見て同じ意味に直してよい（報告に書く）。意味が変わる修正が要るなら止まって報告。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\（run フォルダ）
- 学習・再生は train.py / play.py を直接呼ぶ。起動行の形（_preload_h5py_and_run.py 経由、conda activate、OMNI_KIT_ACCEPT_EULA、
  agent.policy.noise_std_type=log、entropy_coef の上書きの有無）は X25b を起動した行と同じ（tools\logs\ の run_X25b で始まるファイルの先頭）。
- stand_env_cfg.py の末尾は X25 節（same_foot_touchdown、SkyentificPoclegsGaitCadenceEnvCfg とその _PLAY）まで。
  SkyentificPoclegsGaitCadenceEnvCfg・_play・RewTerm・SceneEntityCfg・configclass・torch が定義済み／import 済みか確かめる。無ければ止まって報告。
- 親: run フォルダ名が *_X25b_cadence の一番新しいものの、一番新しい model_*.pt（2000 以上のはず）。観測 44 次元。制御 50 Hz。GPU は RTX 3090 Ti が1枚。

## S1 追記と登録
1. stand_env_cfg.py の末尾に「追記するコード A」をそのまま追記。
2. GaitCadence-v0 の rsl_rl_cfg_entry_point が指すクラスとファイルを確かめ、そのファイルの末尾に「追記するコード B」を追記。
   B の親クラス名がそのクラスと違えば親を差し替え、stand_env_cfg の import パスも実際の場所に合わせる。
   isaaclab_rl に RslRlSymmetryCfg が無い、または入っている rsl_rl の PPO に symmetry（mirror loss）が無ければ、**B は入れずに止まって報告**（A と X26a だけ進めてよい）。
3. __init__.py に4つ（形は GaitCadence-v0 と同じ）:
   Skyentific-Poclegs-GaitHipQuiet-v0 / GaitHipQuiet-Play-v0 → SkyentificPoclegsGaitHipQuietEnvCfg / _PLAY（rsl_rl は GaitCadence-v0 と同じ）、
   Skyentific-Poclegs-GaitMirror-v0 / GaitMirror-Play-v0 → 同じ SkyentificPoclegsGaitHipQuietEnvCfg / _PLAY、rsl_rl は B の SkyentificPoclegsMirrorPPORunnerCfg。
4. 16 env・押しなしの短い確認（学習しない）で次を表に:
   - GaitHipQuiet-Play: hip_quiet の重み −5.0・wz_max 0.15・対象関節が LL_HR・LR_HR・LL_HAA・LR_HAA の4つ。時計の period がすべて 0.45。same_foot_touchdown −25 が残っている。
   - hip_quiet の動作: 1 env を指令 vx 0.3・wz 0 固定で、**親 X25b の最新 checkpoint の方策で** 5 s 回し、生の値（重みを掛ける前）と
     |LR_HR|＋|LL_HR|＋|LR_HAA|＋|LL_HAA|（rad、関節角から自分で計算）が一致するか（X25b なら右の5番目が約 0.44 rad なので、合計およそ 0.5〜0.6 のはず）。
     指令を wz 0.3 にすると生の値が 0 になるか。
   - 鏡映（B を入れた場合）: 観測 policy の各項の名前と次元、action の関節の並び（action term の joint 名）が scene["robot"].joint_names と同じ順か。
     x26_mirror の表に無い項があれば止まって報告（critic の group があればそれも）。
     親 X25b の方策で 1 env を 3 s 回した観測 o について、m(m(o)) == o（2 回鏡映で元に戻る）、
     指令 vy・wz と重力の y の符号が反転していること、gait_phase の sin・cos が反転していることを表に。

## S2 スモーク（各 64 env・5 iter）
- TEST_X26a（GaitHipQuiet-v0）・TEST_X26b（GaitMirror-v0）とも親 X25b から resume。上書きは不要。
- 確かめて表に: checkpoint を読めた行と iter が親の続き。観測 44。env.yaml に hip_quiet −5.0、same_foot_touchdown −25.0、period 0.45、fwd_gain 0.40、
  joint_deviation_hip −0.5。TEST_X26b の agent.yaml に symmetry_cfg（use_mirror_loss true、mirror_loss_coeff 0.5）。
  ログに Episode_Reward/hip_quiet、X26b は mirror（symmetry）損失の値が出ている。NaN なし。TEST_ は消さない。
- **合格したら、ここで学習コマンドを先に出す**: 別々の PowerShell、train.py を直接、seed 1、num_envs 4096、save_interval 100、
  noise_std_type=log、--device cuda:0、どちらも親 X25b の最新 checkpoint から resume、max_iterations 1000（追加分）、entropy_coef は X25b の起動行と同じ。
  - X26a_hipquiet: GaitHipQuiet-v0。 X26b_mirror: GaitMirror-v0。
  - 先頭に nvidia-smi の1行と「1本目の 1〜2 iter 後に空きを見て2本目」。実行フォルダ付き・プレースホルダ無し・改行なしの1行版。
  そのあと S3 に進む。

## S3 動画スクリプト tools\runs\x26_video.py（学習と並行でよい。1 env だけ使う）
x25_video.py をコピーして、次だけ変える・足す（引数・csv の列・要約・保存先の形はそのまま。保存先は videos\x26\）:
- **視点を増やす。いまの視点は近すぎる。** 引数 --views（既定 "side,front,back,top,diag"）と --cam-dist（既定 2.0 m）。
  side は左真横、front は正面、back は真後ろ、top は真上、diag は斜め前 45°・少し上から。カメラは胴の水平位置を追い、胴の yaw では回さない
  （ロボットが曲がれば見え方も変わってよい）。高さは胴の高さ＋0.3 m、top だけ cam-dist の真上。
- **1 回の起動で視点ごとに別々の mp4 を作る。** 同じ checkpoint・seed・指令で、視点ごとに最初から回し直す（視点ごとのリセットはよい。最初の 2 s は指令 0 もそのまま）。
  csv と要約は最初の視点の回だけ。各視点の終わりの胴の xy が最初の回と何 cm ずれたかを要約に1行（再現性の確認）。
  1 回の起動で複数のカメラを同時に撮れるなら（Camera センサーなど）それでもよい。どちらにしたか報告。
- 要約に追加: 4・5番目それぞれの平均・p5・p95（左右別）と、可動域の端から 1°以内にいた時間の割合（5番目は ±25°、4番目は −8°/+30°）。
  胴から足首までの横の距離の中央値（左右別）と足の間隔。random のときは yaw の指令と実際の yaw の差の平均絶対値。
- 動作確認: X25b の最新 checkpoint（GaitCadence-Play-v0、--period 0.45）で stand_walk（vx 0.3）を --views side,diag で1回撮り、要約の表を出す
  （右の5番目が −25°の端に張り付いている割合がほぼ 100% のはず。X26 の比較の基準）。

## 報告（これで止まる。短く）
1. 冒頭3行: S1 の hip_quiet の一致と鏡映の確認、S2 の合否、X25b 最新の 5番目の張り付きの割合と4番目の平均。
2. S1・S2・S3 の表、直した API 名・呼び出し形、変えたファイル。
3. 学習コマンド（S2 の直後に出したものを再掲）。
4. **動画コマンドと再生コマンドを分けて出す。**
   - 動画コマンド（x26_video.py、--headless、mp4 と csv を保存）: X26a（GaitHipQuiet-Play-v0）と X26b（GaitMirror-Play-v0）、どちらも --period 0.45、
     例 model_「親+300」.pt。stand_walk（vx 0.3）と random（seed 0・1・2）。checkpoint・seed・vx・--views を変えるだけで何度でも撮れる形。
     mp4 と csv ができるフォルダの絶対パスと、視点ごとのファイル名の例。
   - 再生コマンド（play.py、画面で見るだけ、--video なし・--headless なし、録画しない）: X26a・X26b それぞれ1本。checkpoint を差し替えるだけで見る対象を変えられる形。
   - どちらも実行フォルダ付き・プレースホルダ無し・改行なしの1行版。
5. 学習中に見る値: Episode_Reward/hip_quiet が 0 に近づく、mean_episode_length が下がらない、track_lin_vel_xy_exp・track_ang_vel_z_exp が親から大きく下がらない、
   Episode_Reward/same_foot_touchdown が 0 付近のまま。X26b は mirror 損失が下がる。

## 追記するコード A（stand_env_cfg.py の末尾）

```python
# =====================================================================================================
# X26 (2026-10-01 02:30): X25b GaitCadence (0.45 s clock, from scratch) is the first policy that walks
# L-R-L-R: user's replay of model_1200 (stand_walk vx 0.3, seed 0, t 2.5..12 s): 42 touchdowns, 0 same-foot
# repeats (1.0 landing per foot per cycle), vx 0.324, no fall, no flight, double support 16 %, air time
# 0.18..0.20 s. The user saw no foot scuffing, only "slightly pigeon-toed"; model_2000 looks the same.
# CSV: the RIGHT 5th joint (LR_HR) sits at -25 deg (the sim limit, toe pointing IN) 100 % of the walking time,
# stance and swing alike, action -0.9 (pushing into the limit); the left 5th stays at -2 deg. Standing
# (command 0, t < 2 s) it is -6 deg and jumps to -25 when walking starts. 4th (HAA) opens +4 / +3.6 deg on
# average, ankles 0.166 / -0.195 m from the body (width 0.36 m vs 0.34 m standing). Knee p99 501 / 539 deg/s.
# joint_deviation_hip (L1 of HR + HAA, -0.5) costs only ~0.2 per second at 25 deg, far below what the policy
# gains from its one-sided trick. User (2026-10-01): walking straight, the 4th and 5th need hardly move.
# X25a GaitRetouch (same-foot penalty on top of X24b, 0.7 s clock) dodged the penalty by tapping with the
# OTHER foot (R step, L tap, L step, R tap) and walked wide-legged: dropped (user's replay, no csv analysed).
#   X26a GaitHipQuiet (safe)       : resume X25b. + L1 of HR and HAA from default, -5, only while the yaw
#                                     command is small (|wz| < 0.15), so turning still may use the 5th.
#   X26b GaitMirror   (innovative) : the same env + RSL-RL mirror-symmetry loss (left <-> right swap, clock
#                                     shifted by half a period), resume X25b. Targets the one-sided habit
#                                     itself instead of only pricing it.
# =====================================================================================================
X26_HIP_QUIET_WEIGHT = -5.0
X26_WZ_STRAIGHT = 0.15
X26_MIRROR_LOSS_COEFF = 0.5
HIP_ROT_ABD_JOINTS = SceneEntityCfg("robot", joint_names=[".*HR", ".*HAA"])


def hip_quiet_straight(env, command_name: str, asset_cfg: SceneEntityCfg, wz_max: float) -> torch.Tensor:
    """Sum over the 4th and 5th joints of |q - default| [rad], only while |yaw command| < wz_max."""
    asset = env.scene[asset_cfg.name]
    ids = asset_cfg.joint_ids
    dev = torch.abs(asset.data.joint_pos[:, ids] - asset.data.default_joint_pos[:, ids]).sum(dim=1)
    wz = env.command_manager.get_command(command_name)[:, 2].abs()
    return dev * (wz < wz_max).float()


@configclass
class SkyentificPoclegsGaitHipQuietEnvCfg(SkyentificPoclegsGaitCadenceEnvCfg):
    """X26a/X26b: X25b + 4th/5th kept near default while walking straight (resume X25b)."""

    def __post_init__(self):
        super().__post_init__()
        self.rewards.hip_quiet = RewTerm(
            func=hip_quiet_straight, weight=X26_HIP_QUIET_WEIGHT,
            params={"command_name": "base_velocity", "asset_cfg": HIP_ROT_ABD_JOINTS, "wz_max": X26_WZ_STRAIGHT},
        )


@configclass
class SkyentificPoclegsGaitHipQuietEnvCfg_PLAY(SkyentificPoclegsGaitHipQuietEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)


# ---- mirror symmetry (X26b). Joint convention (reference/robot_model_conventions.md section 2): the same
# angle on LL_x and LR_x is the mirror image for every joint, so mirroring a joint vector is a pure L<->R swap.
# Base frame x forward, y left, z up: mirror in the x-z plane.
_X26_VEC_SIGNS = {
    "base_lin_vel": [1.0, -1.0, 1.0],
    "base_ang_vel": [-1.0, 1.0, -1.0],
    "projected_gravity": [1.0, -1.0, 1.0],
    "velocity_commands": [1.0, -1.0, -1.0],
    "gait_phase": [-1.0, -1.0],  # sin, cos of phase + pi: left swing window <-> right swing window
}
_X26_JOINT_TERMS = ("joint_pos", "joint_vel", "actions")


def _x26_joint_perm(env) -> list:
    names = list(env.scene["robot"].joint_names)  # CLI: must equal the action order (check, report)
    perm = []
    for n in names:
        partner = n.replace("LL_", "LR_") if n.startswith("LL_") else n.replace("LR_", "LL_")
        perm.append(names.index(partner))
    return perm


def _x26_obs_map(env, group: str, device):
    cache = getattr(env, "_x26_obs_maps", None)
    if cache is None:
        cache = {}
        env._x26_obs_maps = cache
    if group not in cache:
        om = env.observation_manager
        perm = _x26_joint_perm(env)
        idx, sign, off = [], [], 0
        for name, dims in zip(om.active_terms[group], om.group_obs_term_dim[group]):
            d = int(dims[-1]) if len(dims) else 1
            if name in _X26_VEC_SIGNS and len(_X26_VEC_SIGNS[name]) == d:
                idx += [off + i for i in range(d)]
                sign += _X26_VEC_SIGNS[name]
            elif name in _X26_JOINT_TERMS and d == len(perm):
                idx += [off + p for p in perm]
                sign += [1.0] * d
            else:
                raise RuntimeError(f"x26 mirror: no rule for obs term '{name}' (dim {d}) in group '{group}'")
            off += d
        cache[group] = (torch.tensor(idx, device=device, dtype=torch.long),
                        torch.tensor(sign, device=device, dtype=torch.float32))
    return cache[group]


def x26_mirror(env, obs=None, actions=None, obs_type: str = "policy"):
    """RSL-RL data_augmentation_func: returns [original; mirrored] stacked on dim 0 (None stays None).
    CLI: adapt only the calling convention to the installed rsl_rl (e.g. TensorDict obs), not the maps."""
    obs_out = act_out = None
    if obs is not None:
        group = "policy" if obs_type in ("policy", None) else obs_type
        idx, sign = _x26_obs_map(env, group, obs.device)
        obs_out = torch.cat([obs, obs[:, idx] * sign], dim=0)
    if actions is not None:
        perm = torch.tensor(_x26_joint_perm(env), device=actions.device, dtype=torch.long)
        act_out = torch.cat([actions, actions[:, perm]], dim=0)
    return obs_out, act_out
```

## 追記するコード B（GaitCadence-v0 の rsl_rl entry point のクラスがあるファイルの末尾）

```python
# X26b (2026-10-01): mirror-symmetry loss on top of the runner GaitFwd-v0 / GaitCadence-v0 use.
# CLI: replace SkyentificPoclegsRoughPPORunnerCfg below with that runner class if it differs, and fix the
# import path of x26_mirror to where stand_env_cfg.py actually lives (report both).
from isaaclab_rl.rsl_rl import RslRlSymmetryCfg  # noqa: E402

from .stand_env_cfg import X26_MIRROR_LOSS_COEFF, x26_mirror  # noqa: E402


@configclass
class SkyentificPoclegsMirrorPPORunnerCfg(SkyentificPoclegsRoughPPORunnerCfg):
    def __post_init__(self):
        if hasattr(super(), "__post_init__"):
            super().__post_init__()
        self.algorithm.symmetry_cfg = RslRlSymmetryCfg(
            use_data_augmentation=False, use_mirror_loss=True,
            mirror_loss_coeff=X26_MIRROR_LOSS_COEFF, data_augmentation_func=x26_mirror,
        )
```
````



## 追記（2026-10-01 02:45）CLI の報告と返答

- CLI の報告: X26a の S1・S2 合格、x26_video.py も動いた。**X25b@2100 は5番目が左右とも −24.7°（端から 1° 以内 97%）**＝@1200 の「右だけ」から両側に広がっていた。4番目 平均 左 +2.3・右 +0.1°、足の間隔 0.325 m、同じ足の連続 1/45、vx 0.299、膝 p99 約 553°/s。観測は hip_pos(2)・kfe_pos(6)・ffe_pos(2) に分かれていて鏡映の表に無く、X26b は S1 で停止。rsl_rl は 4.x（TensorDict）で x26_mirror を合わせた、agent の import は `..stand_env_cfg`。__init__.py は references 側だけ。
- 判断: 左右対称の内股なので鏡映では直らない → **X26b 取りやめ**（登録・コードは残す）。代わりに **X26c_hipnarrow（GaitHipNarrow-v0、X26a ＋ 5番目の可動域 ±8°）**。親は 2 本とも X25b model_2100、本人が寝る間に **10000 iter**、save_interval 200。

CLI への返答（同じ CLI チャットに貼る）:

````
判断です。これで進めて、学習コマンドを出したら止まってください。ユーザーはこのあと寝るので、2本とも長く回します。

## 1. X26b（鏡映）はやめる
- 左右とも −25° で対称なので、鏡映の損失では直りません。hip_pos・kfe_pos・ffe_pos の規則は足さない。
- GaitMirror-v0 の登録と x26_mirror・SkyentificPoclegsMirrorPPORunnerCfg は、消さずにそのまま残してください（使わない）。

## 2. 代わりに X26c_hipnarrow を1本（5番目の可動域を ±8° にする）
罰で値付けするのではなく、可動域の端で物理的に止めます。4番目と同じ扱いです。
stand_env_cfg.py の末尾に、次をそのまま追記してください（前と同じく r+ で書き、inode を確認）。

```python


# X26c (2026-10-01 02:40): X25b@2100 has BOTH 5th joints on -25 deg (toes in, 97 % of the time; at model_1200
# only the right one was). Symmetric, so the mirror loss (X26b) cannot fix it -> dropped. Instead limit the 5th
# to +-8 deg like HAA (limit instead of price), on top of X26a's hip_quiet.
X26_HR_LIMITS_DEG = (-8.0, 8.0)


@configclass
class SkyentificPoclegsGaitHipNarrowEnvCfg(SkyentificPoclegsGaitHipQuietEnvCfg):
    """X26c: X26a + 5th joint (HR) limited to +-8 deg (resume X25b)."""

    def __post_init__(self):
        super().__post_init__()
        limits = dict(self.events.set_joint_limits.params["limits_deg"])
        limits[".*_HR"] = X26_HR_LIMITS_DEG
        self.events.set_joint_limits.params["limits_deg"] = limits


@configclass
class SkyentificPoclegsGaitHipNarrowEnvCfg_PLAY(SkyentificPoclegsGaitHipNarrowEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)
```

- __init__.py に Skyentific-Poclegs-GaitHipNarrow-v0 / GaitHipNarrow-Play-v0 → SkyentificPoclegsGaitHipNarrowEnvCfg / _PLAY を登録（rsl_rl は GaitCadence-v0 と同じ。鏡映の runner ではない）。
- 確認（表で）: env.yaml の HR の可動域が −8〜+8、4番目は −8〜+30 のまま、hip_quiet −5.0 がある。
  親 X25b@2100 の方策で 1 env を vx 0.3 で 5 s 回し、左右の5番目が ±8° の中に収まっている。
- スモーク TEST_X26c（64 env・5 iter、親 X25b model_2100 から resume）: 親の続きの iter、観測 44、NaN なし。

## 3. 親はどちらも X25b の model_2100
- 本人は「2000 は 1200 とほぼ同じで良い」と言っています。罰が重くて最初に崩れても、長く回すので戻るのを待ちます。

## 4. 学習コマンド（寝ている間に回す。10000 iter）
- X26a_hipquiet: GaitHipQuiet-v0、--max_iterations 10000、X25b model_2100 から resume。いま出したコマンドの max_iterations と save_interval だけ変える。
- X26c_hipnarrow: GaitHipNarrow-v0、同じ形で --run_name X26c_hipnarrow、--max_iterations 10000。
- どちらも agent.save_interval=200。別々の PowerShell。先頭に nvidia-smi、「1本目の 1〜2 iter 後に空きを見て2本目」。1行版で。
- 所要時間の見積もり（1本だけのときと、2本並べたときの iter/s から）を1行で。朝までに終わらなければ、途中の checkpoint で見るのでそのままでよい。

## 5. 動画コマンドと再生コマンド
- X26c 用も、X26a と同じ形で出す（--task Skyentific-Poclegs-GaitHipNarrow-Play-v0 --run X26c_hipnarrow）。例の checkpoint は model_4000.pt。
- 判定に使う要約はいまのまま（5番目・4番目の平均と端に張り付いた割合、同じ足の連続、前への速度、膝 p99）。
  X26c は5番目が ±8° の端（端から 1° 以内）に張り付いていないかも見る。

報告は短く: 冒頭3行（X26c の確認・スモークの合否、2本の学習コマンドを出したこと）、表、コマンド。
````
