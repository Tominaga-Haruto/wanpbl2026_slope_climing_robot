# WRS 実験13: friction DR で今夜の学習2本（前景実行用のコマンドを作らせる／地形を必ず確認する版）

作成 2026-09-23。実験12（`instructions/inactive/` に移動済み）は、検証手順を削った依頼文で実行した結果、
地形が平地から変わってしまい学習が無駄になった。今回は「地形が親と同じか」を起動前に必ず確認する。
run名は X12a/X12b から X13a/X13b に変えて衝突を避ける。
選定理由は `../../chats/2026-09-23_今夜の学習選定とCLI運用.md`。終わったらこのファイルを `../inactive/` へ移す。

```
# 依頼: 今夜の学習2本の準備（学習は起動しない。最後にコマンドを渡して止まる）

## このプロンプトの前提
- このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。必要な情報はすべてここに書いた。
- 長時間の学習・評価をバックグラウンドで回さない。やってよいのは、ファイルの確認と、下記の
  スモークテスト（64 env／20 iter、数分）だけ。本番の学習はユーザーが別々の PowerShell で前景実行する。
  学習を実際に起動しない・裏で監視し続けない・このチャットのキャッシュが切れた後に何かを評価しない。
- cfg ファイル（my_robot_code\*.py、references\ 以下）は書き換えない。条件は起動行の Hydra 上書きで作る。
  my_robot_code\*.py は IsaacLab 側とハードリンクなので、移動・置換しない。スクリプトの改造もしない
  （前回、並列実行用にスクリプトを直そうとして時間を使いすぎた。今回は2本を別々の PowerShell ウィンドウで
  手で順に起動する前提でよい。二重起動チェックで2本目が止まるなら、そこで止めて報告する）。
- 何も削除しない。pip で何も入れない。git の commit・push はしない。
- 推測で直さない。上書きが効かない・値が違う・落ちる、は止まって報告。
- **地形（terrain）は今回変えてはいけない唯一の値。** 親が平地なら、生成される起動行・env.yaml も平地の
  ままであることを、下のスモークテストで実際の yaml を読んで確認する。「変えていないはず」という申告では
  なく、親の env.yaml の terrain 項目の値と、今回生成した env.yaml の terrain 項目の値を、両方そのまま
  報告に貼ること。

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
| X13a_fricDR_H2999 | H_eff13p5（名前が H_eff13p5 の元の run。_extend_20000 ではない） | model_2999.pt | 平地、HFE/FFE effort 13.5、第一回実機候補 |
| X13b_fricDR_Lw1_4000 | 2026-09-17_21-18-22_L_angstd_w1 | model_4000.pt | H_eff13p5 から派生。その場旋回に合格（S6 +0.268 / S9 -0.353 rad/s、転倒0） |

どちらも:
- 親 run の起動行（tools\logs\run_*.txt）と params\env.yaml・params\agent.yaml から、報酬・指令分布・**地形**・
  アクチュエータ（effort 13.5 を含む）・観測・seed・num_envs・noise_std_type を**そのまま**引き継ぐ。
  親と違ってよいのは run名、再開元、max_iterations、save_interval、friction_distribution_params だけ。
  それ以外のキーが1つでも変わったら、理由が分かっても止めて報告する（黙って直さない）。
- 再開の仕方は、その親 run（または B_direct_wz_turn_H20000）を作ったときと同じ方法を使う（--resume 系の引数か
  load_run/checkpoint の上書き。実際に使われた形を起動行から写す）。
- max_iterations は追加 10000（ユーザーが今夜24時ごろ Ctrl+C で止める前提。それより早く止めても構わない）。
  save_interval は 200。
- 2本は別々の PowerShell ウィンドウで、ユーザーが手で順に起動する（同時押しでなくてよい）。

## P1 friction の上書きが効くかの最小確認（数分。ここで止まる可能性がある）
1. H_eff13p5@2999 を 64 env・平地で env を作り、上の上書きを [3.0,3.0] にして、
   robot の関節 friction のテンソル実効値を1関節分でよいので読む。cfg 値（hr/haa/kfe 0.37、hfe/ffe 0.22）の
   3 倍になっていれば「効いている」でよい（10関節全部・定常差の計測までは今回は不要）。
2. 効いていなければ、env.scene.robot.actuators.<hr|haa|hfe|kfe|ffe>.friction の上書きで同じことを試す。
   それが効くなら、今夜は DR の代わりに固定 2.5 倍（hr/haa/kfe 0.925、hfe/ffe 0.55）で2本を作り、そう明記する。
   どちらも効かなければ止まって報告（学習コマンドは出さない）。

## P2 スモークテスト（2本とも、1本ずつ。必須。ここを省略しない）
- 本番と同じ起動行で num_envs 64、max_iterations 20、run名は TEST_X13a / TEST_X13b。
- 確認して報告に貼る:
  - 親 checkpoint を読み込めた（ログの行）。iteration 番号が親の続きから始まる。
  - **params\env.yaml の terrain 項目：親の値と今回の値を並べて貼る（一致必須）。**
  - params\env.yaml に friction_distribution_params [1.0, 4.0]（または P1 で切り替えた固定値）が入っている。
  - effort_limit（HFE/FFE 13.5）、観測・行動の次元数、報酬の重みと指令分布。
  - cfgdiff 相当（yaml の diff でよい）で、親との差分が「run名・再開元・max_iterations・save_interval・
    friction_distribution_params」以外に無いこと。terrain を含め1つでも余計な差分があれば、学習コマンドを
    出さずに止めて報告する。
- TEST_ run は消さない。

## 報告（これで止まる）
1. 冒頭3行: P1 の判定（効いた／固定値に切替／効かない）、スモークの合否（terrain 一致を含む）、
   このまま進めてよいか。
2. **地形の確認結果**（親 env.yaml の terrain 値 と 今回の env.yaml の terrain 値を2本ぶん並べる）。
3. 親との設定差分の表（2本ぶん。許可項目以外に差が無いこと。terrain を明示的に含める）。
4. **ユーザーが前景で打つ学習コマンド 2本**（PowerShell 1つにつき1本。実行フォルダ付き、プレースホルダ無し、
   複数行版と改行なしの1行版）。
5. **再生コマンド**（checkpoint 名だけ差し替えれば別の点を見られる形。例は model_6000.pt で書く）:
   X13a・X13b それぞれ。
6. 何か上書きを変えた・スクリプトの二重起動チェックで止まった等があれば、その事実。
```
