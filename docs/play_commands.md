# 再生（play）コマンド集

学習した方策を目で見るためのコマンド。全部そのまま PowerShell に貼れる。

## 大事な前提（ここを外すと動かない）

1. **`agent.policy.noise_std_type=log` が必須。** 学習を log で回したので、外すと分布パラメータの
   名前が食い違ってチェックポイントの読み込みで落ちる。`_play.ps1` は自動で付ける。
2. **`--checkpoint` はファイルのフルパス。** `play.py:127-130` が `retrieve_file_path` に渡す作りなので、
   `--load_run` と組み合わせる形ではない（`train.py` の `--checkpoint` は逆に「名前」なので注意）。
3. **作業ディレクトリは `D:\Tominaga\IsaacLab`。** ログのルートが CWD 相対で解決される。
4. **環境変数 `OMNI_KIT_ACCEPT_EULA=YES` が必要。** 無いと EULA プロンプトの入力待ちで
   `Unable to bootstrap inner kit kernel: EOF when reading a line` で落ちる。`_play.ps1` は自動で設定する。
5. **地形を方策の学習条件に合わせる。** 平地で学習した方策を rough で再生すると当然こける。下表参照。

## ラッパー: `tools\runs\_play.ps1`

```
_play.ps1 -Run <run フォルダ名> [-Ckpt model_XXXX.pt] [-Terrain flat|rough] [-NumEnvs 16] [-Video]
```

- `-Terrain flat`（既定）: 全面平地。`sub_terrains` の proportion を flat=1.0 にする方式。
- `-Terrain rough` : 08-21 の混合地形（flat 0.3 / 坂 0.2 / 階段 0.1 / 波 0.2 / ランダム凹凸 0.2）。
- `-Video` : GUI を出さずに動画だけ録る。出力は run フォルダ配下の `videos\play\`。
  GUI が `omni.kit.renderer.init` で落ちる環境（TeamViewer 経由など）向け。
  **※ まだ一度も動作確認していない。初回は試行になる。**
- GUI ありのときは `--real-time` が付くので実時間で再生される。

---

## おすすめの見どころ

### 1. いま一番の見もの: rough を登れるようになった方策

```powershell
D:\Tominaga\slope-climbing-robot\tools\runs\_play.ps1 -Run 2026-09-16_13-40-37_F_BtoRough -Ckpt model_4498.pt -Terrain rough
```

平地で歩けるようにした B を rough に移して +1500 iter 回したもの。地形レベルが 0.98 → 4.69 まで上がった。

### 2. 同じ方策を平地で見ると「円を描いて歩く」のが分かる

```powershell
D:\Tominaga\slope-climbing-robot\tools\runs\_play.ps1 -Run 2026-09-16_13-40-37_F_BtoRough -Ckpt model_4498.pt
```

前進指令に対して yaw rate が +0.324 rad/s 出ており、10 s で約 186° 回る。

### 3. いちばんきれいに真っ直ぐ歩くやつ（平地）

```powershell
D:\Tominaga\slope-climbing-robot\tools\runs\_play.ps1 -Run 2026-09-16_05-15-41_B_combined -Ckpt model_2999.pt
```

### 4. 立ち往生の実物（3000 iter 回して一歩も動かない）

```powershell
D:\Tominaga\slope-climbing-robot\tools\runs\_play.ps1 -Run 2026-09-16_05-14-59_A_base0821 -Ckpt model_2999.pt -Terrain rough
```

### 5. 「後退はできるが前進は固まる」途中段階

```powershell
D:\Tominaga\slope-climbing-robot\tools\runs\_play.ps1 -Run 2026-09-16_08-50-17_C_flatonly -Ckpt model_1600.pt
```

同じランの `model_2999.pt` にすると前進もできるようになっている（iter 2400 で獲得）。

---

## 全ランの一覧と、そのランに合う地形

| run フォルダ | 中身 | 合う地形 | おすすめ ckpt |
|---|---|---|---|
| `2026-09-16_05-14-59_A_base0821` | 08-21 設定そのまま。立ち往生 | `rough` | `model_2999.pt` |
| `2026-09-16_05-15-41_B_combined` | 平地＋dense足上げ＋std0.35。基準となる歩行 | `flat` | `model_2999.pt` |
| `2026-09-16_08-49-55_C_noflat` | 報酬/std だけ変更、地形は rough。立ち往生 | `rough` | `model_2999.pt` |
| `2026-09-16_08-50-17_C_flatonly` | 平地だけ変更。2400 で歩き出す | `flat` | `model_2999.pt` / `model_1600.pt` |
| `2026-09-16_13-40-10_E_yawcmd` | B ＋ rel_heading_envs=0.5。旋回は未解決 | `flat` | `model_1999.pt` |
| `2026-09-16_13-40-37_F_BtoRough` | B@2999 から rough へ移行。地形レベル 4.69 | `rough`（平地でも可） | `model_4498.pt` |
| `2026-09-16_05-32-13_B_combined_s2` | 30 iter で停止。評価対象外 | — | — |
| `2026-09-16_05-08-07_TEST_A` / `..._05-11-41_TEST_B` | 64 env 20 iter のテスト | — | — |

run フォルダの場所: `D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\`

チェックポイントは `save_interval = 200` なので 0, 200, 400, ... と最終 iter のものがある。
F_BtoRough は 2999 から再開したので 3000, 3200, ..., 4400, 4498。

---

## ラッパーを使わずに直に打つ場合（1行）

```powershell
cd D:\Tominaga\IsaacLab; $env:OMNI_KIT_ACCEPT_EULA="YES"; D:\Tominaga\envs\isaac_env\python.exe scripts\reinforcement_learning\rsl_rl\play.py --task Velocity-Rough-Skyentific-Poclegs-Play-v0 --num_envs 16 --checkpoint D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\2026-09-16_05-15-41_B_combined\model_2999.pt --real-time agent.policy.noise_std_type=log env.scene.terrain.terrain_generator.sub_terrains.flat.proportion=1.0 env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs_inv.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.wave_terrain.proportion=0.0 env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=0.0 env.curriculum.terrain_levels=null
```

rough で見たいときは `env.scene.terrain...` から `env.curriculum.terrain_levels=null` までを全部消すだけ。

---

## 数値で見たいとき（GUI 不要）

```powershell
D:\Tominaga\slope-climbing-robot\tools\runs\_eval.ps1 -Run 2026-09-16_13-40-37_F_BtoRough -Ckpt model_4498.pt -NumEnvs 64
```

`tools\logs\eval_<run>_<iter>.md` と `.csv` が出る。中身は `docs\reference\eval_protocol.md` を参照。
