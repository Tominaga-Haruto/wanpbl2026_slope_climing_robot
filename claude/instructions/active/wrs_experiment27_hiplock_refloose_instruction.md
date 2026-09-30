# WRS 実験27: がに股と内股の理由を切り分ける診断 ＋ X26c から resume する 2 本（X27a 5番目をほぼ固定・X27b 参照の振り足を緩める）

作成 2026-10-01 07:00。**本人が X26a・X26c の学習を止めてから、新しい CLI チャットに「CLI に渡すもの」を貼る。**
**「CLI に渡すもの」の4つ連続のバッククォートの中を丸ごと1回で貼る**（追記するコードも中に入っている。リポジトリの `my_robot_code/stand_env_cfg.py` 末尾にも同じものを追記済み）。

## X26 の結果（model_4000、stand_walk vx 0.3 seed 0、t 2.5〜12 s、本人が添付した CSV を解析）

| 項目 | X26a_hipquiet（4・5番目の罰 −5） | X26c_hipnarrow（＋5番目 ±8°） |
|---|---|---|
| CSV | `model_4000_stand_walk_vx0.3_seed0_20261001_055355.csv` | `model_4000_stand_walk_vx0.3_seed0_20261001_054122.csv` |
| 着地 / 同じ足の連続 | 43 / 1 | 42 / **0** |
| 前へ（胴の座標、指令 0.3） | 0.40 m/s | 0.32 m/s |
| **yaw** | **平均 +1.05 rad/s、10 s で約 570°回った＝その場で円を描いて旋回** | 平均 −0.05 rad/s、10 s で向きが約 25°右へずれた |
| 横の速度の平均 | −0.07 m/s | **+0.08 m/s（左へ流れる）** |
| 5番目（左 / 右）平均 | −10 / +6°（右は立脚で +9、振り足で −3。+25 の端に 12%） | **−8.0 / −8.0°（下限の端に 100% 張り付き、行動 −1.5 で押し付け）** |
| 4番目（左 / 右）平均 | +7.4 / +6.6°（歩行中ずっと開く） | +1.6 / +2.2°（立脚 −0.6 / +0.5、振り足 +2.6 / +4.3） |
| 立っているとき（t < 2 s）の4番目 | −4.5 / −4.4° | −6.0 / −2.6° |
| 足首の間隔 | 0.38 m | 0.35 m |
| 両足接地 / 転倒 | 53% / なし | 27% / なし |
| 膝の速さ p99 | 379 / 514°/s | 513 / 511°/s |

- 本人の目視: a・c ともがに股。a は5番目が外に開き、x 方向の指令だけなのに旋回。c はそこまでがに股ではなく、まっすぐ寄りに歩く。
- X26a の旋回の仕組み: 右の5番目が立脚中に +9°（つま先を外へ）＝足が床に着いたまま骨盤を左へ回し、振り足で −3°へ戻す。1 歩ごとに胴を左へ回す「ラチェット」。
  速度追従の報酬は**胴の座標**で測るので、円を描いても前へ 0.4 m/s 歩いていれば満額に近い。旋回を咎めるのは track_ang_vel_z_exp（重み 0.5）だけで、hip_quiet −5 に比べて安すぎた。
- X26c の5番目: 罰を掛けても、可動域を ±8°にしても、内（−）へ押し付け続ける＝内に向けて得をする理由がある。

## 形からの計算（ノートPC、`onshape_export/myrobot_dummy/robot_sim.urdf` の順運動学、立ち姿勢、胴の座標）

- 4番目の軸は胴の中心から左 +5.5 cm・右 −9.5 cm（中心 −2 cm）だが、3番目のモーターがその外 11 cm にあり、**4番目 0°で足首の間隔は 32.6 cm**（脚の長さ約 0.30 m に対して）。重心の横位置は両足首のちょうど真ん中（ずれ 0.1 cm）。
- 片足の真上に重心を載せるには、立脚の4番目を約 −30°閉じる必要がある（足首が胴の中心の下に来る）。足首に左右の関節が無いので足裏も 30°傾く。実機は −8.5〜−11°で足が当たり、シムの下限も −8°。
  **＝このロボットは片足で静かに釣り合えない。歩き方は「横に倒れかけては反対の足で受ける」しかない**（0.45 s の時計で初めて交互に歩けた理由、推定）。
- 4番目を両脚 +5°開くと間隔は 37.8 cm（+5 cm）、+10°で 42.8 cm。−8°で 24.1 cm。
- 5番目を両脚 −8°（つま先を内）にすると、足首が**前へ 1.2 cm**（−25°なら 3.7 cm）、内へ 0.1 cm（−25°で 0.9 cm）動く。足首は5番目の軸の 9 cm 外にあるので、ひねると前後に動く。

## 見立て（推定、実験27の診断で確かめる）

1. **がに股の大部分は形**（4番目 0°でも足首の間隔 33 cm）。報酬では消えない。報酬で減らせるのは「振り足で 4番目を +3〜4°開く分（着地を外へ置いて横の倒れを受ける）」と、X26a のように歩行中ずっと開く分。
2. **5番目の内向きは、前後の足の位置を変える抜け道**。3・2・1番目は参照の振り足（重み 2.0、exp(−2×誤差)）に縛られていて、足を前後に置き直すのが高い。5番目をひねると足首が前後に動く（−8°で 1.2 cm）。
   参照を緩めれば 5番目を使わなくなるはず（X27b）。逆に5番目を固定しても歩けるなら、5番目は無くてもよい（X27a）。
3. **実機の5番目は不感帯 4.5〜6.5°**（D9-6）。±8°の中の細かい使い方は実機に移らない。5番目をほぼ固定して歩ける方策の方が実機向き。
4. X26c の横流れ（左へ 0.08 m/s）と向きのずれ（右へ）は、体（重心は左右の真ん中）ではなく方策の左右差。yaw の重みを上げて抑える。

## 2 本（どちらも X26c の最新から resume、1500 iter、観測 44・時計 0.45 s のまま）

| run | 変えたこと | 確かめること |
|---|---|---|
| **X27a_hrlock**（GaitHrLock-v0） | X26c ＋ 5番目の可動域 ±8 → **±2°**、track_ang_vel_z_exp 0.5 → **1.5** | 5番目なしで同じように歩けるか。歩ければ実機では5番目をほぼ固定でよい |
| **X27b_refloose**（GaitHipNarrow-v0 ＋ 起動行の上書き） | X26c ＋ ref_joint_pos 2.0 → **0.5**、track_ang_vel_z_exp 0.5 → **1.5** | 3・2・1番目が自由になると、5番目の押し付けと振り足の開きが減るか（見立て 2） |

- 判定（x27_video.py の要約、stand_walk vx 0.3 と random seed 0〜2、+300 と +1000 iter）:
  同じ足の連続 ≤1・前へ 0.25 m/s 以上・転倒なし・膝 p99 550°/s 以下（歩き方を崩していない）、
  **10 s の向きのずれ ≤10°・横の速度の平均の絶対値 ≤0.03 m/s**（X26c は 25°・0.08）、random で yaw の追従が X26c より悪くない、
  X27b は5番目が ±8°の端（1°以内）にいる時間 20% 以下・5番目の行動の平均の絶対値 1.0 以下、
  **4番目の「振り足の平均 − 立脚の平均」が左右とも 2°以下、4番目の平均の絶対値 3°以下**（がに股の報酬で減らせる分）。本人の目視でがに股が減ったか。
- 起きうること: X27a が転ぶ・横に流れる → 5番目は実際に役に立っていた（前後の足の位置か横の釣り合い）。X27b が参照から離れて歩き方が崩れる（二段の振り足・右右左左に戻る）→ 0.5 は緩めすぎ、1.0 で。
- 終わったらこのファイルを `../inactive/` へ移す。

## CLI に渡すもの

````
# 依頼: 実験27。X26c の最新で「なぜ5番目を内に押し付けるか・なぜ4番目を開くか」を再生だけで切り分ける診断をし、X26c から resume する 2 本（X27a 5番目 ±2°、X27b 参照の振り足を緩める）の学習コマンドを渡す。動画スクリプト x27 を作る

## このプロンプトの前提
- 新しいチャット。このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。
- 長時間の学習をバックグラウンドで回さない。本番の学習・再生・動画はユーザーが別々の PowerShell で前景実行する。
  診断（S0）の再生は 1 env・headless・1 回 12 s 程度なので CLI が自分で回してよい。
- 既存のクラス・関数の中身は変えない（stand_env_cfg.py の末尾への追記、__init__.py への登録だけ）。
  新しく作ってよいファイルは tools\runs\x27_video.py と tools\logs\x27_diag_*.txt だけ（x26_video.py はコピー元で、変えない）。何も削除しない。pip しない。
  git の commit・push をしない。動いている学習を止めない（X26a・X26c が動いていたら止まって報告）。
- stand_env_cfg.py は references\...\config\skyentific_poclegs\ と my_robot_code\ のハードリンク。**Edit ツールを使わない**。
  先に stand_env_cfg.py.bak_20261001_x27・__init__.py.bak_20261001_x27 を取り、python で open(path, "r+") で読み、seek(0)・write・truncate で書き換える。
  書いたあと、ハードリンクの両パスの inode（os.stat().st_ino）が同じか確かめる。
- 推測で直さない。API 名・呼び出し形の違いは Isaac Lab のソースを見て同じ意味に直してよい（報告に書く）。意味が変わる修正が要るなら止まって報告。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\（run フォルダ）
- 学習・再生は train.py / play.py を直接呼ぶ。起動行の形（_preload_h5py_and_run.py 経由、conda activate、OMNI_KIT_ACCEPT_EULA、
  agent.policy.noise_std_type=log、entropy_coef の上書きの有無）は X26c を起動した行と同じ（tools\logs\ の run_X26c で始まるファイルの先頭。無ければ run_X25b）。
- stand_env_cfg.py の末尾は X26c 節（X26_HR_LIMITS_DEG、SkyentificPoclegsGaitHipNarrowEnvCfg とその _PLAY）まで。無ければ止まって報告。
- 親: run フォルダ名が *_X26c_hipnarrow の一番新しいものの、一番新しい model_*.pt（4000 以上のはず）。比較用に *_X26a_hipquiet の最新も使う。
  観測 44 次元、時計 0.45 s、制御 50 Hz、行動は「既定姿勢 ＋ 0.5 × 行動」[rad]。GPU は RTX 3090 Ti が1枚。
- 関節の符号: 5番目（HR）の + はつま先が外、4番目（HAA）の − は脚を閉じる・+ は開く。左右とも同じ角度で鏡写し。

## S1 動画スクリプト tools\runs\x27_video.py（先に作る。S0 の診断で使う）
x26_video.py をコピーして、次だけ変える・足す（視点・引数・csv の列・保存先の形はそのまま。保存先は videos\x27\）:
- 引数 --hr-limit-deg A（既定なし）: 与えたら、env を作る前に env_cfg.events.set_joint_limits.params["limits_deg"] の ".*_HR" を (−A, +A) に差し替える。
  引数 --haa-limit-deg LO HI（既定なし）: 同じく ".*_HAA" を (LO, HI) に。どちらもファイル名に _hr2 / _haa-8_30 のように残す。
- 要約に追加:
  - 向きのずれ: t 2.5 s から終わりまで yaw 角速度を積分した角度 [deg] と、そのあいだの世界座標の移動を最初の向きに対して前・横に分けた距離 [m]。
  - 4番目の「立脚中の平均」と「振り足中の平均」（左右別。立脚＝その足だけ接地、振り足＝その足が浮いてもう一方が接地）。
  - 5番目の行動の平均（左右別、端に押し付けているかの目安）と、可動域の端から 1°以内の時間の割合（端は実際に使った可動域で）。
  - **報酬の内訳**: t 2.5〜12 s の各報酬項の合計（重み・dt を掛けた後）。env.unwrapped.reward_manager の get_active_iterable_terms(0) か _step_reward
    （Isaac Lab のソースで確かめて、使った方を報告）。項の名前順に 1 行ずつ。
- 動作確認は S0 を兼ねる。

## S0 診断（学習しない。X26c の最新で。1 env・headless・vx 0.3 と random、各 12 s）
結果を tools\logs\x27_diag_20261001.txt にも保存し、報告の表にする。
1. **5番目を固定すると何が悪くなるか**: GaitHipNarrow-Play-v0、X26c の最新、--period 0.45 で
   (a) そのまま、(b) --hr-limit-deg 0.5、(c) --hr-limit-deg 25（端を外すと −8°を越えてどこまで内へ行くか）。
   それぞれ stand_walk（seed 0）と random（seed 0・1・2）。
   表: 転倒の有無、前への速度、同じ足の連続、向きのずれ、横の流れ、4番目の立脚／振り足の平均、5番目の平均と行動の平均、膝 p99、
   **報酬の内訳で (a) との差が大きい項 上位 5 つ**（どの報酬を守るために5番目を内に向けているかの手がかり）。
2. **4番目の振り足の開きは何のためか**: 同じく (d) --haa-limit-deg -8 3（振り足で 3°より開けない）を stand_walk（seed 0）と random（seed 0）。
   表は 1. と同じ。転ぶ・横に流れるなら、振り足の開きは横の倒れを受けるのに要っている。
3. **X26a の旋回の値段**: GaitHipQuiet-Play-v0、X26a の最新、stand_walk（seed 0）で報酬の内訳と向きのずれ。
   track_ang_vel_z_exp がいくら失われ、hip_quiet がいくらかを並べる（「旋回の罰が安すぎた」の確認）。
4. 形の確認（1 回だけ）: 既定姿勢で、両脚の5番目を 0・−8・−25°にしたときの足首（ll_ffe・lr_ffe の原点）の胴の座標の前後・横の位置と、
   4番目を 0・+5・−8°にしたときの足首の間隔を、シムの順運動学（関節角を書いて sim を 1 回 forward）で表に。
   ノートPC の URDF の計算では、5番目 −8°で足首が前へ 1.2 cm・−25°で 3.7 cm、4番目 0°で間隔 32.6 cm・+5°で 37.8 cm・−8°で 24.1 cm。合っているか。

## S2 追記と登録
1. stand_env_cfg.py の末尾に「追記するコード」をそのまま追記。
2. __init__.py に2つ（形は GaitHipNarrow-v0 と同じ、rsl_rl も同じ）:
   Skyentific-Poclegs-GaitHrLock-v0 / GaitHrLock-Play-v0 → SkyentificPoclegsGaitHrLockEnvCfg / _PLAY。
3. 確認（表で）: GaitHrLock の env.yaml 相当で HR の可動域 −2〜+2、HAA −8〜+30、track_ang_vel_z_exp 1.5、hip_quiet −5.0、ref_joint_pos 2.0、period 0.45。
   X27b の起動行の上書き env.rewards.ref_joint_pos.weight=0.5 env.rewards.track_ang_vel_z_exp.weight=1.5 が GaitHipNarrow-v0 で効くこと（スモークの env.yaml で見る）。

## S3 スモーク（各 64 env・5 iter、どちらも親 X26c の最新から resume）
- TEST_X27a: GaitHrLock-v0、上書きなし。 TEST_X27b: GaitHipNarrow-v0 ＋ env.rewards.ref_joint_pos.weight=0.5 env.rewards.track_ang_vel_z_exp.weight=1.5。
- 確かめて表に: checkpoint を読めた行と iter が親の続き、観測 44、env.yaml の上の値、NaN なし。TEST_ は消さない。
- **合格したら、ここで学習コマンドを先に出す**: 別々の PowerShell、train.py を直接、seed 1、num_envs 4096、agent.save_interval=100、
  noise_std_type=log、--device cuda:0、どちらも親 X26c の最新 checkpoint から resume、max_iterations 1500（追加分）、entropy_coef は X26c の起動行と同じ。
  - X27a_hrlock: GaitHrLock-v0。 X27b_refloose: GaitHipNarrow-v0 ＋ 上の 2 つの上書き、--run_name X27b_refloose。
  - 先頭に nvidia-smi の1行と「1本目の 1〜2 iter 後に空きを見て2本目」。実行フォルダ付き・プレースホルダ無し・改行なしの1行版。
  - 所要時間の見積もり（2本並べたときの iter/s から）を1行で。

## 報告（これで止まる。短く）
1. 冒頭3行: S0 で5番目を固定したとき何が起きたか（転倒・流れ・報酬の差の上位）、4番目の振り足を 3°までにしたとき何が起きたか、S3 の合否。
2. S0・S2・S3 の表、直した API 名・呼び出し形、変えたファイル。
3. 学習コマンド（S3 の直後に出したものを再掲）。
4. **動画コマンドと再生コマンドを分けて出す。**
   - 動画コマンド（x27_video.py、--headless、mp4 と csv を保存、--views side,front,back,top,diag、--cam-dist 2.0）:
     X27a（GaitHrLock-Play-v0）と X27b（GaitHipNarrow-Play-v0、run X27b_refloose）、どちらも --period 0.45、例 model_「親+300」.pt。
     stand_walk（vx 0.3）と random（seed 0・1・2）。checkpoint・seed・vx・--views を変えるだけで何度でも撮れる形。
     mp4 と csv ができるフォルダの絶対パスと、視点ごとのファイル名の例。
   - 再生コマンド（play.py、画面で見るだけ、--video なし・--headless なし、録画しない）: X27a・X27b それぞれ1本。checkpoint を差し替えるだけで見る対象を変えられる形。
   - どちらも実行フォルダ付き・プレースホルダ無し・改行なしの1行版。
5. 学習中に見る値: mean_episode_length が下がらない、Episode_Reward/track_ang_vel_z_exp が上がる、track_lin_vel_xy_exp が親から大きく下がらない、
   Episode_Reward/same_foot_touchdown が 0 付近のまま。X27b は Episode_Reward/ref_joint_pos が下がりすぎない（歩き方が崩れていないか）。

## 追記するコード（stand_env_cfg.py の末尾）

```python


# =====================================================================================================
# X27 (2026-10-01 07:00): X26 at model_4000 (stand_walk vx 0.3, seed 0, t 2.5..12 s).
#   X26a GaitHipQuiet: walks L-R-L-R but SPINS in place (+1.05 rad/s, ~570 deg in 10 s). The right 5th turns
#     the pelvis in stance (+9 deg) and resets in swing (-3): a yaw ratchet. Tracking is in the body frame, so
#     walking in a circle at 0.4 m/s is still paid; only track_ang_vel_z_exp (0.5) objects, far below hip_quiet -5.
#     4th open +7 deg the whole time (ankles 0.38 m apart).
#   X26c GaitHipNarrow: L-R-L-R, 0 repeats, vx 0.32, no fall. BOTH 5th joints on the -8 deg limit 100 % of the
#     time, action -1.5 (still pushing in). Drifts left 0.08 m/s and ~25 deg of heading in 10 s. 4th: stance
#     ~0, swing +3..+4 deg.
# URDF FK (upright stand pose): ankles are 32.6 cm apart at HAA 0 (the HFE motor sits 11 cm outside the HAA
# axis); CoM is laterally centred between the ankles. Putting the CoM over one ankle would need HAA ~ -30 deg
# (the sole tilts with it, no ankle roll), so the gait must be fall-and-catch. HR -8 deg (toes in) moves both
# ankles 1.2 cm forward (-25: 3.7 cm): a way to re-place the feet fore-aft while HFE/KFE/FFE are held by the
# reference swing (weight 2.0). The real 5th has a 4.5..6.5 deg dead band, so fine HR use will not transfer.
#   X27a GaitHrLock : X26c + 5th limited to +-2 deg + yaw tracking 0.5 -> 1.5 (resume X26c).
#   X27b (launch-line overrides on GaitHipNarrow-v0): ref_joint_pos 2.0 -> 0.5, yaw tracking 0.5 -> 1.5.
# =====================================================================================================
X27_HR_LOCK_DEG = (-2.0, 2.0)
X27_YAW_TRACK_WEIGHT = 1.5


@configclass
class SkyentificPoclegsGaitHrLockEnvCfg(SkyentificPoclegsGaitHipNarrowEnvCfg):
    """X27a: X26c + 5th joint (HR) limited to +-2 deg + stronger yaw tracking (resume X26c)."""

    def __post_init__(self):
        super().__post_init__()
        limits = dict(self.events.set_joint_limits.params["limits_deg"])
        limits[".*_HR"] = X27_HR_LOCK_DEG
        self.events.set_joint_limits.params["limits_deg"] = limits
        self.rewards.track_ang_vel_z_exp.weight = X27_YAW_TRACK_WEIGHT


@configclass
class SkyentificPoclegsGaitHrLockEnvCfg_PLAY(SkyentificPoclegsGaitHrLockEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        _play(self)
```
````
