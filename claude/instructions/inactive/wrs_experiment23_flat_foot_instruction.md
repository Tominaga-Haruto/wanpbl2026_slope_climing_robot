# WRS 実験23: 軸足をべったり着けたままにする罰を足して X22 から再開（X23a・X23b）＋動画スクリプト

作成 2026-09-30 16:40。**新しい CLI チャットに「CLI に渡すもの」と「追記するコード」を貼る。**
実際に回ったのは 14:00 版の X22（X21a/b から action_rate −0.1・joint_acc −2.5e-7、参照の振り足は 2.0 のまま）で、約 4000 iter まで。
14:50 版の X22（参照 0.5・動画スクリプト）は使われなかったので、動画スクリプトはこの実験23で作る。

## 本人の所見（X22、4000 iter）
1. 振り足を出す前に、軸足がかかとを上げてつま先立ちになる（右足を上げる → 左足べったり → 左のかかとが上がる → 右足を前へ）。
   胴が上に動いて見えたのはこれ。動画が速く見えたのは Isaac Sim が重かっただけの可能性。
2. 真後ろから見て、足裏の外側だけが床に着いている（がに股）。足を着く横幅は良い。

## 見立て（推定）
- 1: 振り足の高さの罰（swing_clearance）は足首の点の**床からの高さ**で測っている。軸足でつま先立ちすると体ごと上がるので、
  膝を曲げて足を上げるより安く高さが稼げる。まっすぐ寄りの姿勢では特にそう。
- 2: 足首に横（ロール）の関節が無い。4番目で脚を内側へ閉じて足の間隔を狭めると、足裏も同じ角度だけ傾いて外側が接地する。
  胴を軸足の側へ傾けない限り、「狭い間隔」と「足裏が平ら」は同時には成り立たない。
- どちらも「床に着いている足裏の傾き」（前後＝つま先立ち、左右＝外側の接地）を罰すれば1つの項で押さえられる。
  代わりに、足の間隔が少し広がるか、胴が左右に揺れる（ペンギン歩き）歩き方になる可能性がある。

## 変更（コードに追記。2本とも同じ）
- `feet_flat`（−10）: 接地している足について、足の座標で見た重力の向きと、既定姿勢で平らに立ったときの向きの差の²。
  ≒ 傾きの角度² [rad²]。20°のつま先立ちで 1 step あたり約 −1.2、10°の外側の接地で約 −0.3。
- 14:00 版 X22 の上書き（action_rate −0.1・joint_acc −2.5e-7）を cfg に入れた（起動行の上書きは要らない）。
- X23a（GaitFlat-v0）は X22a から、X23b（GaitFlatH-v0）は X22b から再開。観測 44 のまま。1000 iter 追加。
判定は +300 iter: 軸足のかかとが上がらない・足裏が平ら（真後ろから）で、前へ歩き続けていれば当たり。
立往生したら feet_flat を −5 にして同じ親からやり直す。外側の接地が残るなら −20。
終わったらこのファイルを `../inactive/` へ移す。

## CLI に渡すもの

```
# 依頼: 実験23。足裏の傾きの罰を追記し、基準の向きを測り、X22 から再開する学習コマンドを渡し、そのあと動画スクリプトを作る

## このプロンプトの前提
- 新しいチャット。このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。
- 長時間の学習をバックグラウンドで回さない。本番の学習はユーザーが別々の PowerShell で前景実行する。
- 既存のクラス・関数の中身は変えない（stand_env_cfg.py の末尾への追記と、下で指示する定数の書き換えだけ）。
  新しく作ってよいファイルは tools\runs\x23_video.py だけ。何も削除しない。pip しない。git の commit・push をしない。
  動いている学習を止めない。
- stand_env_cfg.py は references\...\config\skyentific_poclegs\ と my_robot_code\ のハードリンク。**Edit ツールを使わない**。
  先に stand_env_cfg.py.bak_20260930_x23 と __init__.py.bak_20260930_x23 を取り、python で open(path, "r+") で読み、
  seek(0)・write・truncate で書き換える。書いたあと両パスの inode（os.stat().st_ino）が同じか確かめる。
- 推測で直さない。API 名が違う（例: math_utils.quat_apply_inverse が無ければ quat_rotate_inverse）ときは Isaac Lab のソースを見て
  同じ意味の名前に直すのはよい（報告に書く）。意味が変わる修正が要るなら止まって報告。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\（run フォルダ）
- 学習・再生は train.py / play.py を直接呼ぶ。起動行の形（_preload_h5py_and_run.py 経由、conda activate、
  OMNI_KIT_ACCEPT_EULA、agent.policy.noise_std_type=log）は tools\logs\run_X18h_bold_from_c.txt の先頭と同じ（resume の例でもある）。
- stand_env_cfg.py の末尾は X21 節（GaitRef / GaitRefH、_feet_in_contact、FEET_ORDERED、FEET_BODIES_ORDERED、_play）まで。
  無ければ止まって報告。
- 親: run フォルダ名が *_X22a_smooth_upright（GaitRef-v0 で学習）・*_X22b_smooth_hpose（GaitRefH-v0）の、一番新しいもの。
  観測 44 次元（最後の2つが 0.7 s 周期の時計）。制御 50 Hz。GPU は RTX 3090 Ti が1枚。

## S1 追記と基準の向き
1. 末尾に「追記するコード」をそのまま追記。__init__.py に4つ（形は GaitRef-v0 と同じ、rsl_rl の entry point も同じ）:
   Skyentific-Poclegs-GaitFlat-v0 / GaitFlat-Play-v0 → SkyentificPoclegsGaitFlatEnvCfg / _PLAY、
   Skyentific-Poclegs-GaitFlatH-v0 / GaitFlatH-Play-v0 → SkyentificPoclegsGaitFlatHEnvCfg / _PLAY。
2. GaitFlat-Play-v0 と GaitFlatH-Play-v0 で、それぞれ 16 env・行動 0・押しなし、リセット直後の最初の 1 step で、
   ll_ffe・lr_ffe の足の座標で見た重力の向き（quat_apply_inverse(body_quat_w, [0,0,−1])）の 16 env の中央値を求め、
   小数 4 桁で FOOT_FLAT_GREF（GaitFlat）・FOOT_FLAT_GREF_H（GaitFlatH）に書き込む。
   確かめる: 胴の傾きがほぼ 0（projected_gravity の xy が 0.02 以下）、両足が接地、左右の足で向きが左右対称に近いこと、
   GaitFlat と GaitFlatH の値の差（どちらも足裏が平らなら小さいはず）。値を報告。
3. 書き込んだあと同じ条件で feet_flat の値が 0.001 以下になることを確かめる。

## S2 スモーク（各 64 env・5 iter、親から resume）
- TEST_X23a（GaitFlat-v0、親 X22a）・TEST_X23b（GaitFlatH-v0、親 X22b）。上書きは不要（値は cfg に入っている）。
- 確かめて表に: checkpoint を読めた行、iter が親の続き、観測 44、env.yaml の feet_flat −10・action_rate_l2 −0.1・
  joint_acc_l2 −2.5e-07・ref_joint_pos 2.0・gait_contact 2.0、ログに feet_flat の項目、NaN なし。TEST_ は消さない。
- **合格したら、ここで学習コマンドを先に出す**: 別々の PowerShell、train.py を直接、親の最新 checkpoint から resume、seed 1、
  num_envs 4096、max_iterations 1000（追加分）、save_interval 100、noise_std_type=log、entropy_coef 0.005、--device cuda:0。
  run名 X23a_flat_upright / X23b_flat_hpose。先頭に nvidia-smi の1行と「1本目の 1〜2 iter 後に空きを見て2本目」。
  実行フォルダ付き・プレースホルダ無し・改行なしの1行版。そのあと S3 に進む。

## S3 動画スクリプト tools\runs\x23_video.py（学習と並行でよい。1 env だけ使う）
play.py を手本に新規に書く（play.py は変えない）:
- 引数: --task（Play の方）、--run（run フォルダ名、部分一致可）、--checkpoint（model_XXXX.pt）、--mode stand_walk|random、
  --vx（既定 0.3）、--seconds（既定 12）、--seed（既定 0）、--headless、--video。
- num_envs 1、カメラは env 0 のロボットを追う（viewer.env_index = 0）。押し・外乱なし。リセットは最初の1回だけ
  （時計がエピソードの経過時間で進むため。転んだらそこで終了）。
- 速度指令は毎 step スクリプトが直接書く（自動の再抽選と heading 制御は止める）:
  stand_walk は最初の 2 s が 0、そのあと vx・vy 0・wz 0。random は 3 s ごとに vx −0.2〜0.6・vy ±0.1・wz ±0.3 から --seed で抽選。
- 上書きしない保存: run フォルダ\videos\x23\<checkpoint>_<mode>_vx<vx>_seed<seed>_<YYYYMMDD_HHMMSS>.mp4 と同名の .csv。
- csv に毎 step: 時刻、指令、胴の位置と速度・yaw 角速度、両足の接地、両足首の点の x/z、両足の傾き（前後・左右、deg。
  上の基準の向きからの差を、胴の yaw で回した座標で前後・左右に分ける）、10 関節の角度、行動。
- 要約を表示: 胴の z の振れ幅（p95−p5、mm）、1 秒あたりの歩数、指令ありの区間の平均の前後・左右の速度と yaw 角速度、
  両足同時に浮いた時間の割合、**接地中の足の前後の傾き（つま先立ち）と左右の傾き（外側の接地）の p50・p95 [deg]**、転倒したか。
- 動作確認: 親 X22a・X22b の最新 checkpoint で stand_walk（vx 0.3）を各1回、--video 付きで撮り、要約の表を出す（X23 の比較の基準）。

## 報告（これで止まる。短く）
1. 冒頭3行: 基準の向きの値、S2 の合否、S3 の要約で X22a・X22b のつま先立ち・外側の接地・胴の z の振れ幅がいくつだったか。
2. S1・S2・S3 の表、直した API 名、変えたファイル。
3. 学習コマンド（S2 の直後に出したものを再掲）。
4. 動画コマンド（x23_video.py、実行フォルダ付き・1行版）: X23a / X23b の stand_walk（vx 0.3、例 model_「親+300」.pt）と
   random（seed 0・1・2）、画面で見る用（--video・--headless なし）1本。checkpoint・seed・vx を変えるだけで何度でも撮れる形。
   mp4 と csv ができるフォルダの絶対パス。
5. 学習中に見る値: Episode_Reward/feet_flat は 0 に近づく、track_lin_vel_xy_exp・gait_contact は親から大きく下がらない、
   mean_episode_length が下がらない。track_lin_vel_xy_exp が親の半分以下に落ち続けたら立往生の兆し。
```

## 追記するコード

```python

# =====================================================================================================
# X23 (2026-09-30 16:40): X22a/X22b (X21 resumed with action_rate -0.1, joint_acc -2.5e-7) walk at ~4000 iter,
# but (user's replay) 1) the stance foot rises onto its toe before the other foot swings forward (the body
# goes up -> looks like bouncing), 2) seen from behind, feet land on the outer edge of the sole.
# Likely: swing_clearance counts world z of the swing foot, and standing on the toe lifts the whole body,
# so it is the cheapest clearance; the edge contact is geometry - there is no ankle roll joint, so a leg
# closed with HAA (narrow stance) tilts the sole by the same angle unless the torso leans with it.
# Fix: penalize the tilt (pitch and roll) of a foot while it is on the ground. The flat reference is the
# gravity direction in each foot frame measured at the default pose on flat ground (exp23 step S1).
# =====================================================================================================
import isaaclab.utils.math as math_utils  # noqa: E402

# exp23 S1 writes these (gravity [0, 0, -1] seen in the ll_ffe / lr_ffe body frame, feet flat at the default pose).
FOOT_FLAT_GREF = ((0.0, 0.0, -1.0), (0.0, 0.0, -1.0))
FOOT_FLAT_GREF_H = ((0.0, 0.0, -1.0), (0.0, 0.0, -1.0))


def feet_flat_in_contact(env, sensor_cfg: SceneEntityCfg, asset_cfg: SceneEntityCfg, gref) -> torch.Tensor:
    """Sum over feet on the ground of |g_foot - g_flat|^2 (~ tilt angle^2 in rad^2, pitch and roll together)."""
    asset = env.scene[asset_cfg.name]
    quat = asset.data.body_quat_w[:, asset_cfg.body_ids]  # (N, 2, 4) left, right
    n = quat.shape[0]
    g_w = torch.tensor([0.0, 0.0, -1.0], device=quat.device, dtype=quat.dtype).expand(n * 2, 3)
    g_f = math_utils.quat_apply_inverse(quat.reshape(-1, 4), g_w).reshape(n, 2, 3)
    ref = torch.tensor(gref, device=quat.device, dtype=quat.dtype).unsqueeze(0)
    err = torch.sum((g_f - ref) ** 2, dim=-1)
    contact = _feet_in_contact(env, sensor_cfg).float()
    return torch.sum(err * contact, dim=1)


def _x23(cfg, gref):
    r = cfg.rewards
    r.action_rate_l2.weight = -0.1      # exp22 values, now in the cfg
    r.joint_acc_l2.weight = -2.5e-7
    r.feet_flat = RewTerm(
        func=feet_flat_in_contact, weight=-10.0,
        params={"sensor_cfg": FEET_ORDERED, "asset_cfg": FEET_BODIES_ORDERED, "gref": gref},
    )


@configclass
class SkyentificPoclegsGaitFlatEnvCfg(SkyentificPoclegsGaitRefEnvCfg):
    """X23a: X22a + flat stance foot (upright pose)."""

    def __post_init__(self):
        super().__post_init__()
        _x23(self, FOOT_FLAT_GREF)


@configclass
class SkyentificPoclegsGaitFlatHEnvCfg(SkyentificPoclegsGaitRefHEnvCfg):
    """X23b: X22b + flat stance foot (H pose)."""

    def __post_init__(self):
        super().__post_init__()
        _x23(self, FOOT_FLAT_GREF_H)


@configclass
class SkyentificPoclegsGaitFlatEnvCfg_PLAY(SkyentificPoclegsGaitFlatEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)


@configclass
class SkyentificPoclegsGaitFlatHEnvCfg_PLAY(SkyentificPoclegsGaitFlatHEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)
```
