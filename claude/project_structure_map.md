# プロジェクト構成マップ ── どこに何があり、どこをいじるか

坂登坂ロボットの学習コードを「構造として」把握するための地図。
2階層で見る:**(1) プロジェクト全体**（CAD〜学習の大枠）と **(2) RL パッケージ内部**（日々いじる本体）。
末尾に「やりたいこと → いじるファイル」早見表。

---

## 1. プロジェクト全体（`~/projects/slope-climbing-robot/`）

```
slope-climbing-robot/                     ← 親Gitリポジトリのルート（ブランチ master）
├── IsaacLab/                 【ライブラリ｜原則触らない】Isaac Lab 本体。学習コマンドはここから実行
│                                train.py / play.py にだけ import を1行追記済み（他は不可侵）
├── isaac_env/                【環境｜触らない】Python venv。.gitignore 除外
├── my_robot_code/            ★★【自作の実体・Git管理・編集対象】自作コードはすべてここに集約
│   ├── rough_env_cfg.py           ← 報酬・終了・地形・観測・イベント・カリキュラム（最重要）
│   ├── skyentific_poclegs.py      ← 機体定義（usd_path / init_state / actuators）
│   ├── curriculums.py             ← カリキュラムのロジック関数
│   ├── rewards.py                 ← 自作報酬の式（feet_air_time / feet_slide）※2026-08-20 分離
│   └── rsl_rl_cfg.py              ← PPOハイパラ（max_iterations / NN / lr / gamma）※2026-08-20 分離
├── references/BipedalRobotSim/ 【別リポジトリ｜.gitignore除外】Skyentific 参考実装の clone
│   └── …/skyentific_poclegs/      ← 実際に学習が読むRLパッケージ。上の5ファイルは
│                                     my_robot_code/ を指す symlink（=編集は my_robot_code 側で即反映）
├── onshape_export/           【CADパイプライン】URDF/USD の生成物と変換スクリプト
│   ├── .env                       ← ★Onshape APIキー。絶対にコミット/貼り付けしない
│   ├── myrobot/                   ← 本命（旧方式・質量後付け）
│   └── myrobot_dummy/             ← ★ダミーモーター版（現行の本線。usd_path はここを向く）
├── docs/                     【記録】setup_log.md など作業ログ
└── tools/                    【未整備｜宿題】USD質量検算ツール等（現状フォルダごと無い）
```

### この階層で覚える3点
- **編集する自作コードは `my_robot_code/` の5ファイル。** references 側は symlink なので、`my_robot_code/` を書けば学習に即反映（コピー往復不要）。日々の坂登坂調整はほぼ `rough_env_cfg.py` に集約。
- **`IsaacLab/` はライブラリ。触らない。** 例外は `train.py` / `play.py` の import 1行（追記済み・バックアップあり）。
- **学習コマンドを打つ場所は `IsaacLab/` の中**（`./isaaclab.sh -p scripts/.../train.py ...`）。編集する場所（my_robot_code）と実行する場所（IsaacLab）が別、というのが最初の混乱ポイント。

---

## 2. RL パッケージ内部（`references/BipedalRobotSim/skyentific_poclegs/skyentific_poclegs/`）

ここが「学習タスクの本体」。日々の調整はほぼこの中で完結する。全体像:

```
skyentific_poclegs/                        ← Pythonパッケージのルート
├── __init__.py                【定型｜触らない】パッケージ宣言
│
├── assets/                     ── 機体（ロボットそのもの）の定義
│   ├── __init__.py             【定型】USD等のパスの基準(ISAAC_ASSET_DIR)を作るだけ
│   └── skyentific_poclegs.py   ★【編集対象】機体定義 ArticulationCfg
│                                   ・usd_path       … どのUSD(機体)を読むか
│                                   ・init_state     … スポーン高さ・初期関節角
│                                   ・actuators      … モーターの上限トルク/速度/PDゲイン
│
└── tasks/locomotion/velocity/  ── 学習タスク（環境）の定義
    ├── __init__.py             【定型】説明文だけ
    │
    ├── mdp/                     ── 報酬・カリキュラムの「関数（式）」置き場
    │   ├── __init__.py          【定型】ライブラリ関数＋自作(rewards,curriculums)を束ねる
    │   ├── rewards.py           ★【編集対象(式)】自作報酬 feet_air_time / feet_slide の実装
    │   └── curriculums.py       ★【編集対象(式)】自作カリキュラム
    │                                terrain_levels_vel / modify_push_force / modify_command_velocity
    │
    └── config/                  ── 「この機体×このタスク」の具体設定
        ├── __init__.py          【定型】説明文だけ（空に近い）
        └── skyentific_poclegs/
            ├── __init__.py      ★【登録】gym.register でタスクIDを定義（★まだ symlink 未分離＝Git未追跡）
            │                        \"Velocity-Rough-Skyentific-Poclegs-v0\" ←学習コマンドの--taskで指定する名前
            ├── rough_env_cfg.py ★★★【最重要・編集対象】環境設定の中枢。
            │                        報酬/終了/地形/観測/イベント/カリキュラムの「設定値」が全部ここ
            └── agents/
                ├── __init__.py  【定型】
                └── rsl_rl_cfg.py ★【編集対象(学習側)】PPOハイパラ
                                     max_iterations / NN層サイズ / learning_rate / gamma 等
```

### 2階層の分業（ここが体系の肝）
- **`mdp/*.py`（rewards.py, curriculums.py）＝「式・ロジック」**。「滑りをどう測るか」「地形をいつ難化するか」という**計算の中身**。
- **`config/.../rough_env_cfg.py`＝「その式に渡す数値・対象・重み」**。「滑り罰を −0.25 で、対象は足先」という**設定**。
- **`assets/skyentific_poclegs.py`＝「機体そのもの」**。報酬とは別物だが、報酬の正規表現(`.*FFE`等)がこの機体の関節名と一致していないと落ちる。
- **`agents/rsl_rl_cfg.py`＝「学習アルゴリズム側」**。環境（報酬・地形）ではなく、PPO の回し方（反復数・NN・学習率）。

**原則: まず rough_env_cfg.py の「数値」で足りるか考える → 足りないときだけ mdp/ の「式」に降りる。**

---

## 3. どのファイルが Git 管理下か（重要な落とし穴）

`.gitignore` で `references/` は**丸ごと除外**。追跡されているのは `my_robot_code/` のみ。
references 内の各ファイルは、my_robot_code へ symlink されているものだけが実質 Git 管理下になる。

| ファイル | Git追跡 | 理由 |
|---|---|---|
| `rough_env_cfg.py` | ○ | my_robot_code の実体を symlink |
| `skyentific_poclegs.py` | ○ | 同上 |
| `curriculums.py` | ○ | 同上 |
| `rewards.py` | ○ | my_robot_code の実体を symlink（**2026-08-20 分離**） |
| `agents/rsl_rl_cfg.py` | ○ | 同上（**2026-08-20 分離**） |
| `config/.../__init__.py`（登録） | **✗** | references 内の実体のまま。symlink 未分離 |

**意味:** 2026-08-20 に `rewards.py`（自作報酬の式）と `rsl_rl_cfg.py`（PPOハイパラ）を他3ファイルと同じ手当て（実体を my_robot_code へ移動＋元位置に絶対パス symlink、`.bak_symlink` 取得）で分離し、Git 追跡下に入れた。これで報酬の式・PPO設定を編集すると学習に効き、かつ `git commit` で履歴に残る。**残る未追跡は `config/.../__init__.py`（タスク登録）のみ。** タスクIDや gym.register を版管理したくなったら、同じ手当てをする。

---

## 4. 「やりたいこと → いじるファイル」早見表

| やりたいこと | 開くファイル | どのクラス/場所 | Git |
|---|---|---|---|
| 報酬の強さを変える/符号を変える | `rough_env_cfg.py` | `SkyentificRewardsCfg` と末尾 `__post_init__` | ○ |
| 報酬項目を追加/削除する | `rough_env_cfg.py` | `SkyentificRewardsCfg` | ○ |
| **前傾を許す（坂）** | `rough_env_cfg.py` | `__post_init__` の `flat_orientation_l2.weight = -0.5` | ○ |
| 終了条件を変える/追加する | `rough_env_cfg.py` | `SkyentificTerminationsCfg` | ○ |
| **坂の比率・急さを変える** | `rough_env_cfg.py` | 上部 `ROUGH_TERRAINS_CFG` の proportion / slope_range | ○ |
| 地面の摩擦を変える | `rough_env_cfg.py` | `__post_init__` の `TerrainImporterCfg(...friction...)` | ○ |
| 観測項目を足す/減らす | `rough_env_cfg.py` | `SkyentificObservationsCfg` | ○ |
| 外乱・ドメインランダム化の範囲 | `rough_env_cfg.py` | `SkyentificEventCfg` | ○ |
| カリキュラムの発動時期/上限 | `rough_env_cfg.py` | `SkyentificCurriculumCfg` の params | ○ |
| カリキュラムの判定式そのもの | `curriculums.py` | 各関数本体 | ○ |
| 自作報酬の計算式そのもの | `rewards.py` | `feet_air_time` / `feet_slide` | ○ |
| 機体・初期姿勢・スポーン高さ | `skyentific_poclegs.py` | `init_state` | ○ |
| モーターの上限トルク/PDゲイン | `skyentific_poclegs.py` | `actuators` | ○ |
| どのUSD(機体)を使うか | `skyentific_poclegs.py` | `usd_path` | ○ |
| 学習の反復数/NN/学習率 | `agents/rsl_rl_cfg.py` | `SkyentificPoclegsRoughPPORunnerCfg` | ○ |
| タスクID・登録 | `config/.../__init__.py` | `gym.register(...)` | ✗ |

**結論:** 坂登坂の調整（報酬・終了・地形・カリキュラム数値）は **`rough_env_cfg.py` の1ファイルにほぼ全部集約**されている。ここを起点にし、式を変えたいときだけ `curriculums.py` / `rewards.py` に、機体側は `skyentific_poclegs.py` に、学習の回し方は `rsl_rl_cfg.py` に降りる、という地図で動けば迷わない。**これら5ファイルは全て Git 追跡下**（未追跡は登録用 `__init__.py` のみ）。

（各項目の中身の読み方・書き換え方は `isaaclab_edit_guide.md` を参照）
