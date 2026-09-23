# WRS 実験12: friction DR で今夜10時間の学習2本（前景実行用のコマンドを作らせる）

作成 2026-09-23。WRS機の CLI の**新しいチャット**に、下のコードブロックをそのまま貼る。
選定理由は `../../chats/2026-09-23_今夜の学習選定とCLI運用.md`。終わったらこのファイルを `../inactive/` へ移す。

```
# 依頼: 今夜の学習2本の準備（学習は起動しない。最後にコマンドを渡して止まる）

## このプロンプトの前提
- このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。必要な情報はすべてここに書いた。
- 長時間の学習・評価をバックグラウンドで回さない。やってよいのは、ファイルの確認、数分以内のスモークテスト
  （64 env／20 iter）、短い評価だけ。本番の学習はユーザーが別々の PowerShell で前景実行する。
- cfg ファイル（my_robot_code\*.py、references\ 以下）は書き換えない。条件は起動行の Hydra 上書きで作る。
  my_robot_code\*.py は IsaacLab 側とハードリンクなので、移動・置換しない。
- 何も削除しない。pip で何も入れない。git の commit・push はしない。
- 推測で直さない。上書きが効かない・値が違う・落ちる、は止まって報告。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\<run名>
- 前景学習 tools\runs\_train_foreground.ps1（noise_std_type 未指定で止まる、別の train.py があると止まる）
- 再生 tools\runs\_play.ps1 -Run <run> -Ckpt <model_N.pt> [-Terrain flat|rough]
- 過去の起動行は tools\logs\run_<RunName>.txt の先頭にある

## 今夜の2本（どちらも「親の起動行そのまま＋friction DR だけ」。変える変数は1つ）
変更点は1つだけ:
  env.events.scale_all_joint_friction_model.params.friction_distribution_params=[1.0,4.0]
（既定は (0.9, 1.1)、mode=startup、operation=scale。実機の不感帯が シムの friction の 1.7〜3.1 倍あったため）

| run名 | 親 run | 親 checkpoint | 親の設定 |
|---|---|---|---|
| X12a_fricDR_H2999 | H_eff13p5（名前が H_eff13p5 の元の run。_extend_20000 ではない） | model_2999.pt | 平地、HFE/FFE effort 13.5、第一回実機候補 |
| X12b_fricDR_Lw1_4000 | 2026-09-17_21-18-22_L_angstd_w1 | model_4000.pt | H_eff13p5 から派生。その場旋回に合格（S6 +0.268 / S9 -0.353 rad/s、転倒0） |

どちらも:
- 親 run の起動行（tools\logs\run_*.txt）と params\env.yaml・params\agent.yaml から、報酬・指令分布・地形・
  アクチュエータ（effort 13.5 を含む）・観測・seed・num_envs・noise_std_type を**そのまま**引き継ぐ。
  親と違ってよいのは run名、再開元、max_iterations、save_interval、friction_distribution_params だけ。
- 再開の仕方は、その親 run（または B_direct_wz_turn_H20000）を作ったときと同じ方法を使う（--resume 系の引数か
  load_run/checkpoint の上書き。実際に使われた形を起動行から写す）。
- max_iterations は追加 10000（朝にユーザーが Ctrl+C で止める前提）。save_interval は 200。
- 2本を同時に前景で回す。

## P0 評価スクリプトの退避（数分）
以前の棚卸しで作った坂評価スクリプトが一時フォルダにある:
  C:\Users\WRS\AppData\Local\Temp\claude\C--Users-WRS\0b32fd46-1a58-461d-b39f-d2299383924f\scratchpad\inv
残っていれば slope_eval.py、run_eval.ps1、run_queue.ps1、agg.py、tbsum.py、tbtable.py、cfgdump.py、cfgdiff.py を
D:\Tominaga\slope-climbing-robot\tools\eval_slope\ にコピーし、中のパスがコピー先で動くように直す（元は消さない）。
残っていなければ「無かった」と書くだけでよい。

## P1 friction の上書きが本当に効くか（ここで止まる可能性がある）
1. H_eff13p5@2999 を 64 env・平地で env を作り、上の上書きを [3.0,3.0] にして、
   robot の関節 friction のテンソル実効値（10関節）を読む。cfg 値（hr/haa/kfe 0.37、hfe/ffe 0.22）の 3 倍に
   なっているか。[1.0,4.0] のときは 1.0〜4.0 倍の範囲に散っているか。
2. 同じ方策で、[1.0,1.0] と [3.0,3.0] の2条件、指令 (0,0,0) で 10 s 立たせ、関節ごとの
   「目標角 − 実関節角」の定常差 p95 [deg] を出す（Isaac Lab の joint_pos_target と joint_pos）。
   目安: シムの不感帯は friction/stiffness なので、1.0 倍で HR 約 2.1°、FFE 約 1.3°。3.0 倍でおよそ 3 倍。
   - 数値が目安と大きく違っても、3.0 倍で 1.0 倍より明確に大きくなっていれば「効いている」とし、実際の値を報告する。
   - 1.0 倍と 3.0 倍で差が無い → DR 上書きが効いていない。代わりに
     env.scene.robot.actuators.<hr|haa|hfe|kfe|ffe>.friction の上書きで同じことを試す。
     それが効くなら、今夜は DR の代わりに固定 2.5 倍（hr/haa/kfe 0.925、hfe/ffe 0.55）で2本を作り、そう明記する。
     どちらも効かなければ止まって報告（学習コマンドは出さない）。

## P2 スクリプトの最小修正（必要なときだけ。.bak_20260923_<内容> を取ってから）
- _train_foreground.ps1 は別の train.py があると止まる。2本同時に前景で回せるよう、
  既定の挙動は変えずに -AllowParallel スイッチを足す（指定したときだけ二重起動チェックを飛ばす）。
- _play.ps1 に -FrictionScale <float>（既定 1.0＝今と同じ）を足す。指定時は P1 で効いた方の上書きで
  friction をその倍率に固定して再生する。
- どちらも diff を報告に貼る。

## P3 スモークテスト（2本とも、1本ずつ）
- 本番と同じ起動行で num_envs 64、max_iterations 20、run名は TEST_X12a / TEST_X12b。
- 確認: 親 checkpoint を読み込めた（ログの行を貼る）、iteration 番号が親の続きから始まる、
  params\env.yaml に friction_distribution_params [1.0, 4.0] が入っている、effort_limit（HFE/FFE 13.5）、
  観測 42・行動 10、報酬の重みと指令分布が親と同じ（cfgdiff で親との差分が上記の許可項目だけ）。
- 20 iter の所要時間から、2本並走時の 1 iter の秒数と、10 時間で届く iteration を見積もる。
- TEST_ run は消さない。

## 報告（これで止まる）
1. 冒頭3行: P1 の判定（効いた／固定値に切替／効かない）、スモークの合否、10 時間で届く iteration の見積り。
2. P1 の表（10関節 × 1.0倍／3.0倍 の friction 実効値と定常差 p95）。
3. 親との設定差分の表（2本ぶん。許可項目以外に差が無いこと）。
4. **ユーザーが前景で打つ学習コマンド 2本**（PowerShell 1つにつき1本。実行フォルダ付き、プレースホルダ無し、
   複数行版と改行なしの1行版）。
5. **再生コマンド**（checkpoint 名だけ差し替えれば別の点を見られる形。例は model_6000.pt で書く）:
   X12a・X12b それぞれ、friction 1.0 倍と 3.0 倍の2通り。
6. **朝の評価コマンド**（ユーザーが前景で打つ）: いつもの measure_crab.py の S1〜S9 を、friction 1.0 倍と 3.0 倍で、
   1000 iter ごとの checkpoint に掛ける1本のスクリプト呼び出し。比較用に親（H_eff13p5@2999、L_angstd_w1@4000）も同条件で含める。
7. P0・P2 でやったこと（コピー先、.bak、diff）。
```

## 朝に見ること（このチャット側のメモ）

- X12a・X12b の各点を、friction 1.0 倍と 3.0 倍の S1〜S9 で親と比べる。**3.0 倍で親より良く、1.0 倍で親と同等以上**なら、その点が床上デプロイ候補の置き換え候補。
- X12b は S6/S9（その場旋回）が保たれているかを必ず見る。L_angstd_w1 は 4498 で旋回が崩れた前例がある。
- 同時に実験11（H_eff13p5@2999 の friction スイープ、評価のみ）の結果があれば、X12a と並べて判断する。
