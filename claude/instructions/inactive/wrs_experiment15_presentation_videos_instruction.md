# WRS 実験15: 発表用のシム動画（平地・坂・でこぼこ・旋回）と、足りなければ今日の学習の準備

作成 2026-09-24。発表（2026-09-25）用。sim-to-real は発表では扱わない前提。
主役は B_direct_wz_turn_H20000@25000（H 系列を累計 25000 iter、坂 10°で転倒 0、その場旋回あり）。
根拠は `../../reports/2026-09-23_学習H以降の棚卸し.md`。終わったらこのファイルを `../inactive/` へ移す。

```
# 依頼: 発表用のシミュレーション動画を撮る。撮れない場面があれば、今日の学習の準備までして止まる

## このプロンプトの前提
- このプロンプトだけで完結している。AGENTS.md、claude\ 以下の文書、過去の報告書、メモリは読みに行かない
  （自動で読み込まれたものは無視してよい）。必要な情報はすべてここに書いた。
- やってよいこと: ファイルの確認、16 env・長さ 500〜750 step の動画撮影（1本数分）、64 env・20 s の短い評価、
  64 env／20 iter のスモークテスト。本番の学習は起動しない（ユーザーが前景の PowerShell で回す）。
- cfg ファイル（my_robot_code\*.py、references\ 以下）は書き換えない。地形・指令は起動行の Hydra 上書きで作る。
  my_robot_code\*.py は IsaacLab 側とハードリンクなので、移動・置換しない。
- スクリプトを直すのは、_play.ps1 が Hydra の追加引数を渡せない場合だけ。そのときは
  .bak_20260924_extra を取り、既定の挙動を変えない引数追加（例 -Extra に文字列配列を渡すと play.py の末尾に足す）に
  とどめ、diff を報告に貼る。
- 何も削除しない。pip で何も入れない。git の commit・push はしない。推測で直さない（効かない・落ちるは止まって報告）。

## 環境（固定）
- 作業フォルダ D:\Tominaga\slope-climbing-robot、Isaac Lab D:\Tominaga\IsaacLab、python D:\Tominaga\envs\isaac_env\python.exe
- run の保存先 D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\<run名>
- 再生 tools\runs\_play.ps1 -Run <run> -Ckpt <model_N.pt> [-Terrain flat|rough] [-NumEnvs N] [-Video] [-VideoLength N]
  （conda activate 込み。python.exe 直叩きは h5py の DLL 競合で落ちる）
- 前景学習 tools\runs\_train_foreground.ps1。過去の起動行は tools\logs\run_<RunName>.txt の先頭。
- 坂の評価の既存設定: tools\eval_slope\（30 m の逆ピラミッド、中心線 10°、指令 (0.5,0,0)、64 env、20 s）。
- 地形の sub_terrains 名: flat / hf_pyramid_slope / hf_pyramid_slope_inv / pyramid_stairs / pyramid_stairs_inv /
  wave_terrain / random_rough。HfPyramidSloped の slope_range は「高さ÷水平」の比（10° = 0.176、15° = 0.268）。
  random_rough の noise_range は高さ [m]。平地は sub_terrains の proportion 上書きで作ってきた（その形を写す）。

## 対象
| 役 | run | checkpoint |
|---|---|---|
| 主役 | B_direct_wz_turn_H20000（フォルダ名の実名を確認） | model_25000.pt（無ければ実在する最も近い保存点） |
| 予備（主役が坂・でこぼこで倒れる場面だけ） | 同 run | model_23000.pt と model_27000.pt（実在名を確認） |
| 予備2（同上） | P2_gainDR_seed2 | model_4000.pt |
| 参考（平地だけ） | 2026-09-17_00-08-51_H_eff13p5 | model_2999.pt |

## P0 確認（撮る前に）
1. 上の run フォルダの実名と checkpoint の実在（Test-Path）。
2. B の params\env.yaml から: 地形の設定（sub_terrains・curriculum）、指令の term のクラス名と、
   vx・vy・wz を固定するための実際のキー名（B は (vx,vy,wz) を直接指定する専用の command term を使っている）、
   heading_command の有無。これで下の各場面の上書き行を組む。
3. _play.ps1 の引数一覧（Hydra の追加引数を渡せるか、動画の出力先フォルダ）。

## P1 動画（主役で5本。すべて 16 env、--headless --video、長さ 750 step、指令は固定で再サンプルしない）
各場面、地形は「その sub_terrain だけ proportion 1.0、ほかは 0」にする。
| 名前 | 地形 | 指令 (vx, vy, wz) |
|---|---|---|
| V1_flat | flat | (0.5, 0, 0) |
| V2_slope10 | hf_pyramid_slope_inv、slope_range [0.176, 0.176]（tools\eval_slope の設定が使えるならそちらを優先して、その旨書く） | (0.5, 0, 0) |
| V3_rough | random_rough、noise_range を [0.02,0.02]・[0.04,0.04]・[0.06,0.06] の3段 | (0.4, 0, 0) |
| V4_turn | flat | (0, 0, +0.5) |
| V5_walkturn | flat | (0.3, 0, +0.4) |
- V2 は 15°（[0.268, 0.268]）も1本撮る（V2_slope15）。撮れれば発表のおまけ、倒れても問題ない。
- 撮った動画は run フォルダの videos\ から tools\videos_presentation_20260924\ へ
  <run短縮名>_<ckpt>_<場面名>.mp4 の名前でコピーする（元は消さない）。
- 動画ごとに、同じ上書きで 64 env・20 s（または 750 step）の短い評価を1回だけ回し、
  転倒率・前進距離の平均・yaw 速度の平均を取る（既存の measure_crab.py か tools\eval_slope の仕組みを使う。
  新しい評価スクリプトを書くのは最小限にし、書いたらパスを報告）。
- 主役が V2 か V3 で転倒率 20% 超なら、その場面だけ予備・予備2でも撮って評価する。
- 参考として H_eff13p5@2999 の V1_flat を1本撮る。

## P2 学習の準備（P1 で「坂 10° か でこぼこ 0.04 m のどちらかで、主役も予備も転倒率 20% 超」のときだけ）
- run名 X15_demo_terrain_B25000。親 B_direct_wz_turn_H20000@model_25000.pt。再開の仕方は B を作ったときの起動行から写す。
- 親から変えるのは地形だけ: rough の generator、curriculum 有効、proportion を
  flat 0.2 / hf_pyramid_slope 0.15 / hf_pyramid_slope_inv 0.25 / random_rough 0.25 / wave_terrain 0.15 /
  pyramid_stairs 0 / pyramid_stairs_inv 0、slope_range [0.0, 0.27]、random_rough noise_range [0.0, 0.06]。
  指令の割合（旋回を含む）・報酬・アクチュエータ・観測・noise_std_type は親のまま。
  追加 6000 iter、save_interval 200。
- スモーク（64 env／20 iter、run名 TEST_X15）: 親 checkpoint の読込行、iteration が親の続きから始まること、
  params\env.yaml の地形が上の値になっていること、親との yaml 差分が「run名・再開元・max_iterations・
  save_interval・地形」だけであることを貼る。1つでも余計な差分があれば学習コマンドを出さずに止まる。

## 報告（これで止まる）
1. 冒頭3行: 撮れた場面／撮れなかった場面、発表に使える動画のフォルダ、学習が要るか。
2. 表: 場面 × run@ckpt × 転倒率・前進距離・yaw 速度・動画ファイル名。
3. ユーザーが自分で撮り直すための再生コマンド（場面ごと、PowerShell の1行、実行フォルダを明示、
   run名・checkpoint を実名で埋める、山括弧なし）。checkpoint を差し替えるだけで別の点を撮れる形にする。
4. P2 をやった場合: ユーザーが別の PowerShell で前景実行する学習コマンド（1行版つき）、
   学習後に撮り直すための再生コマンド（model_ 番号を差し替える形）、止め方（Ctrl+C、保存点は残る）。
```
