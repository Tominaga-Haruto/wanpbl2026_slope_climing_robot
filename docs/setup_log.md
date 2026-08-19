# Slope-Climbing-Robot Setup Log

## 2026-07-17 環境確認 & Skyentific poclegs 動作確認

### 環境
- OS: Ubuntu 22.04.5 LTS (Kernel 6.8.0-134-generic)
- CPU: Intel i7-14700KF (20 cores / 40 threads)
- GPU: NVIDIA RTX 4070 12GB (Driver 580.159.03)
- RAM: 64GB
- venv: `~/projects/slope-climbing-robot/isaac_env` (Python 3.11)
- Isaac Sim: 5.1.0 (pip版, isaac_env内)
- Isaac Lab: 0.54.2 (v2.3系, ソースインストール @ `~/projects/slope-climbing-robot/IsaacLab`)
- torch: 2.7.0+cu128, CUDA 12.8
- ISAAC_LAB_PATH: `/home/wanpbl2026/projects/slope-climbing-robot/IsaacLab` (未永続化)

### ディレクトリ構造

~/projects/slope-climbing-robot/
├── IsaacLab/                        # 本体（v2.3系）
├── isaac_env/                       # venv
├── references/
│   └── BipedalRobotSim/             # Skyentific参考実装
│       └── skyentific_poclegs/      # 外部extension（pip editable install済）
└── docs/
└── setup_log.md

### トラブル1: ディスク100%満杯（解決済）
- **症状**: `/` 使用率100%、`No space left on device` で全操作失敗
- **原因**: Slack (deb版) が `/dev/shm` shared memory と netlink socket で
  permission denied エラーを毎ミリ秒吐き、`/var/log/syslog` が840GBに肥大化
- **対処**:
  1. `pkill -f slack`
  2. `sudo truncate -s 0 /var/log/syslog`
  3. `sudo systemctl restart rsyslog`
- **結果**: 空き 0 → 839GB回復
- **未対処 (TODO)**: Slack本体は残っている。起動するとまた暴走する。
  - 対策案: Snap版に置換 (`sudo apt remove slack-desktop && sudo snap install slack`)、
    または deb版アンインストールしてブラウザで運用

### トラブル2: pip 消失（解決済）
- 症状: venv内で `No module named pip`
- 原因: 前回の venv 作成時にディスクフルで壊れた可能性
- 対処: `python -m ensurepip --upgrade`（pip 24.0 復活）

### トラブル3: skyentific_poclegs setup.py が古い（解決済）
- 症状: `python -m pip install -e .` すると torch が 2.7.0+cu128 → 2.5.1+cu124 に
  ダウングレードされる
- 原因: setup.py の `INSTALL_REQUIRES` に `torch==2.5.1` の pin (Isaac Sim 4.5 時代の設定)
- 対処:
  1. `cp setup.py setup.py.original` でバックアップ
  2. `INSTALL_REQUIRES = []` に書き換え（依存は Isaac Lab/Sim 側が持つので不要）
  3. `python -m pip install --upgrade "torch==2.7.0" "torchvision==0.22.0" "torchaudio==2.7.0" --index-url https://download.pytorch.org/whl/cu128` で torch復旧
  4. `python -m pip install -e . --no-deps` で再インストール（`--no-deps` が重要）

### トラブル4: Skyentific タスクが Gymnasium に登録されない（解決済）
- 症状: `gymnasium.error.NameNotFound: Environment 'Velocity-Rough-Skyentific-Poclegs' doesn't exist`
- 原因: Isaac Lab の train.py は起動時に `isaaclab_tasks` しか import しないので、
  外部extension の skyentific_poclegs の `gym.register` が実行されない
- 対処: `IsaacLab/scripts/reinforcement_learning/rsl_rl/train.py` の99行目
  `import isaaclab_tasks` の直後に `import skyentific_poclegs  # noqa: F401` を追加
- バックアップ: `train.py.original` として同ディレクトリに保存
- 命令: `sed -i '99a import skyentific_poclegs  # noqa: F401' scripts/reinforcement_learning/rsl_rl/train.py`

### 動作確認結果（成功）



## Python環境
- 種別: venv（uv製）※condaではない
- パス: ~/projects/slope-climbing-robot/isaac_env
- 有効化: source ~/projects/slope-climbing-robot/isaac_env/bin/activate
- エイリアス: `isaac`（~/.bashrc に登録）
- 注意: 再起動後は自動で有効化されない




2026-07-22 タスク登録問題 解決
結論: skyentific_poclegs のタスク登録は正常。問題は確認方法だった。
pxr（Isaac Sim本体）は AppLauncher 起動後でないと import できない。素の -c 実行では ModuleNotFoundError: No module named 'pxr' になる。
タスク登録は Sim起動後の import で実行される → list_envs.py に出ないのは、同スクリプトが skyentific_poclegs を import しないため（パッケージの不具合ではない）。
確認方法: AppLauncher(headless=True) 起動 → import skyentific_poclegs → gym.registry を見る。
登録済みタスク: Velocity-Rough-Skyentific-Poclegs-v0 / -Play-v0



2026-08-16
このvenvではpipではなく必ずpython -m pipを使う。pip単体だとシステム側/usr/bin/pipを見てしまい失敗する（onshape-to-robot初回インストールがuv-buildエラーで落ちた。pip 24→26.2.1に更新＋python -m pipで解決）
pxr（USD）を使うスクリプトは冒頭にSimulationApp起動が必要。ワンライナー不可。from isaacsim import SimulationApp → simulation_app = SimulationApp({"headless": True}) の後でないとfrom pxr import ...できない
USDのjoint/link一覧を出すスクリプト作成済み: ~/projects/slope-climbing-robot/tools/dump_usd_joints.py（引数にusdパス。自作ロボットUSDにも流用可）
Onshape APIキーの取得場所はdev-portalではなく、cad.onshape.com右上アイコン→My account→左メニュー Developer→API keys（dev-portalはOAuth専用になっている）




## 2026-08-18 URDF化・USD化フェーズ

### 環境(変更なし)
Ubuntu 22.04.5 / RTX 4070 12GB / i7-14700KF / ドライバ 580.159.03 / CUDA 13.0
Isaac Sim 5.1(pip版) / Isaac Lab(ソース) / Python 3.11.15 / venv isaac_env

### 引き継ぎ書の誤りを訂正
- 「dump_usd_joints.py 作成済み・tools/ に配置」→ 実際には tools/ フォルダごと存在しなかった。未作成。次回必要なら作る。
- 「config.json の dynamics で質量手動指定できる」→ onshape-to-robot 1.8.2 に該当機能なし。robot_builder.py を確認。config が読むのは no_dynamics(bool)のみ。

### onshape-to-robot 書き出し結果(成功)
- config.json: no_dynamics: true で質量エラー(KeyError:'mass')を回避。
- 結果: link 11 / joint 10 / 全 revolute / fixed 0。目標構成に一致。
- joint命名も LL_HR..LL_FFE / LR_* が正しく出力。見本の正規表現流用可。
- モーター242部品フォルダでも merge_stls:"all" で自動的に1リンクに統合された。
  → 円柱差し替え・サブアセンブリ化は不要だった(円柱2種は作成済みだが未使用)。

### 非ASCII問題(USD変換の地雷)
- 中国語STL名(下行星架/驱动板)がUSDパスで潰れ同名衝突する警告が出た。
- 対処: 下行星架→gear, 驱动板→board にリネーム。URDF参照と assets/merged/ 実ファイルの両方。
- robot_sim.urdf.bak をバックアップ済み。

### USD変換(成功)
- IsaacLab/scripts/tools/convert_urdf.py で変換。
- 出力: onshape_export/myrobot/usd/robot.usd(生成確認済み)。
- 注意: この robot.usd は雑な仮質量(全link 0.5kg / 慣性0.001)。構造確認用。学習前に正確値へ要入れ替え。

### TeamViewer制約(新規・重要)
- リモートセッションでGPU描画(Vulkan)デバイス列挙不可 → yourdfpy表示もIsaac Sim GUIも起動不可。
- GPUコンピュート(学習・convert_urdf変換本体)はリモートでも動作する。
- 3D形状目視は本体ディスプレイで直接ログインが必要。

### 生成ファイル対応(onshape_export/myrobot/)
- robot.urdf         : 原本。STL参照は package://。質量0(no_dynamics)。
- robot_view.urdf    : yourdfpy確認用。相対パス化。色NaNエラーで表示不可。
- robot_view_nomat.urdf : material除去版。本体でyourdfpy表示する用。
- robot_sim.urdf     : 学習仮版。相対パス化+仮質量0.5kg+非ASCIIをgear/board化。USD変換元。
- robot_sim.urdf.bak : 非ASCII置換前のバックアップ。
- usd/robot.usd      : 上記から変換。仮質量。構造確認用。

### 未確認事項(次回の最優先)
- 脚の3D形状が正しいか未目視(私が木構造で LR_HR/LL_HR の並びに疑問を出したが、
  URDFの数値だけでは正否判定できず。CAD上のdof割り当ては本人確認済みで正しいとの由)。
  → 本体で yourdfpy robot_view_nomat.urdf を開いて目視確認する。


## 2026-08-18 追記
- NVIDIAドライバ: unattended-upgradeで 580.159.03→580.173 に更新されミスマッチ発生。再起動で解消。
- robot_view_nomat.urdf の中国語STL参照(下行星架/驱动板)を gear/board にリネーム。.bakあり。MISSINGなし確認済み。
- 本体でyourdfpy目視完了: 胴体からV字2本脚・左右分離・ねじれなし。構造は正常。前チャットのLR_HR/LL_HR構造破綻疑いは杞憂と決着。
- 次回(TeamViewerで可): 正確な質量入れ(各link=モーター+脚パーツ合算)→ArticulationCfg登録→学習。
EOF



# setup_log.md 追記（2026-08-19）

> 既存の `docs/setup_log.md` の末尾に以下を追記する。

---

## 2026-08-19：質量入れ・link改名・タスク登録・学習起動まで到達

### 環境
- ドライバ **580.173.02**（前回の 580.173 と同一系。nvidia-smi で確認）。CUDA 13.0、RTX 4070 12GB、Isaac Sim 5.1 / Isaac Lab（ソース）、Python 3.11.15（isaac_env）で変更なし。
- TeamViewerセッションで headless 学習が正常完走することを確認。**GUI描画（--headless無し）は `omni.kit.renderer.init` 付近で落ちる**（2回試行、2回とも）。GPUコンピュートは動くが描画列挙は不可、というルール2の制約を再確認。

### 作業内容
1. **仮質量→実質量へ入れ替え**。各URDF link＝「モーター＋脚パーツ」の合算。モーター公式値（AK10-9=0.96 / AK80-9=0.485 kg）＋Onshape質量特性で取得した脚パーツ質量。3Dプリント想定で概算方針。慣性は概算（モーターlink=0.003、足=0.001、対角）。
   - 割り当て：base=1.73 / lr_hr=ll_hr=1.30 / lr_haa=ll_haa=1.02 / lr_hfe=ll_hfe=1.32 / lr_kfe=ll_kfe=1.00 / lr_ffe=ll_ffe=0.61（合計約12.2kg）。
   - スクリプト `onshape_export/myrobot/set_mass.py`。`.bak2` 取得＋diff確認。
2. **link（body）名を見本命名規則へ改名**。joint名は一致していたが body名がモーター型番のままで、見本 env_cfg の `body_names="base"/".*ffe"/".*hfe"/".*haa"` に当たらず学習起動でエラー（`ValueError: ... base: []`）。
   - `ak10_9_kv60_v3_0`→`base`、以下 `lr_hr/ll_hr/lr_haa/ll_haa/lr_hfe/ll_hfe/lr_kfe/ll_kfe/lr_ffe/ll_ffe`（**小文字**、見本regexが小文字のため）。
   - スクリプト `onshape_export/myrobot/rename_links.py`（link name と joint parent/child を書換、mesh filename は不変、実行後 MISSING 0 確認）。`.bak4` 取得。
3. **USD再変換 → 見本アセットへコピー**。`convert_urdf.py` で `onshape_export/myrobot/usd/` を更新後、`references/BipedalRobotSim/.../assets/robots/myrobot/` に `robot.usd` と `configuration/` をコピー（学習が参照するのはこちら側）。
4. **タスク登録（置き換え方式）**。`skyentific_poclegs.py` の `usd_path` を `robots/myrobot/robot.usd` へ変更（`.bak`＋diff）。env_cfg は無改変（命名一致のため）。
5. **学習起動確認**。`--num_envs 64 --max_iterations 20 --headless` で20iter完走。joint 10 / observation 42 / action 10 認識。初期方策のため全エピソード `base_contact` 終了・episode長17〜19ステップ（即転倒、初期としては正常）。

### 新規作成ツール
- `tools/dump_usd_mass.py`（USD内の各link質量・慣性を一覧表示。SimulationApp起動→pxr読み出し）。ルール3の「tools/ 未作成」宿題を解消。今回の質量検算自体はスキップして先へ進んだ。

### バックアップ・記録
- `robot_sim.urdf` のbak：`.bak`（非ASCII前）/`.bak2`（質量前）/`.bak3`,`.bak4`（改名前）。
- `skyentific_poclegs.py`（アセット）の `.bak`。train.py の `.original`、play.py の `.bak`。

### 学習 run フォルダ
- 今回のテスト run（20iter）：`logs/rsl_rl/skyentific_poclegs_rough/2026-08-18_20-13-38`（およびその後の再起動ぶん）。テスト目的なので評価対象外。
- **宿題**：本番学習を回したら run フォルダ（名前・iter数・評価）を対応表としてここに追記していく。

### 次の予定
- num_envs 4096 で本格学習（1500〜3000 iter）。
- 歩けない場合は init_state.pos（見本値0.449）の見直し、報酬・カリキュラム設計（flat_orientation_l2 緩和 / feet_air_time 強化 など）。坂登坂は現タスク（rough terrain）から別途設計が必要。
