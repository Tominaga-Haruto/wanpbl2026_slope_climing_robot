
# WRS機 Claude Code の新チャットに貼る文（2026-09-17 夜）

> 使い方: WRS機で Claude Code の新しいチャットを開き、下のコードブロックを1つ貼る。
> 前提: WRS 側が commit `6c65826` でリポジトリの README.md / project_handbook.md / docs/experiments/exp06_turn_in_place.md / chats/2026-09-17_exp05_exp06.md を整備済み。

```
# 新チャットの開始: 引き継ぎの確認と、実験07（その場旋回ができない理由の診断。学習はしない）

## 0. 最初に読む（この順。読んだら要点を 5 行で書く）
1. D:\\Tominaga\\slope-climbing-robot\\README.md
2. D:\\Tominaga\\slope-climbing-robot\\project_handbook.md
3. D:\\Tominaga\\slope-climbing-robot\\docs\\experiments\\exp06_turn_in_place.md
4. D:\\Tominaga\\slope-climbing-robot\\chats\\2026-09-17_exp05_exp06.md
読むだけで、ほかの報告書の全文は必要になったときだけ開く。

## 1. 掟（前のチャットから変わらない）
- 共用PC。D:\\Tominaga\\ の外に書かない。システム設定を変えない。開始時に nvidia-smi で他人の計算プロセスがあれば何も起動せず報告して止まる。GPU の使用はユーザー了承済み。
- 起動は tools\\runs\\_launch.ps1 / _eval.ps1 / _play.ps1（conda activate 込み。python.exe 直叩きは h5py の DLL 競合で落ちる）。
- noise_std_type=log。学習ログの error_vel は正規化値（生値×500/エピソード長）で読む。平地は sub_terrains の proportion 上書き。
- 再開は --resume --load_run --checkpoint をトップレベル引数で（agent.resume は効かない）。起動行は実際の run の params から写し、テスト run の params\\env.yaml / agent.yaml を元の run と丸ごと diff してから本番。
- Edit でハードリンクが切れる。編集後は5組のリンク数と SHA256 を確認する。
- 破壊的操作は .bak を取ってから。push しない（ユーザーが行う）。削除しない。pip / conda で入れない。
- 推測で直さない。想定外は止まって報告。規則と違う推奨をするときは、規則の結論と違える理由を並べる。

## 2. トークン節約のための作法（ユーザーの要望）
- 待ち時間の監視は短い間隔で何度もコマンドを打たない。1回の待機コマンドで 5〜10 分待つ（例: Start-Sleep -Seconds 600 のあとにログの末尾だけ見る）。
- ログは全文を表示しない。Select-String や末尾 30 行に絞る。
- 報告書はファイルに書き、チャットには「冒頭3行＋判定の表＋未実施」だけを出す（ユーザーはそれを Cowork に貼る）。

## 3. 背景（1段落）
その場旋回（S6 / S9: 前進 0 で ±0.5 rad/s）がどの方策でもできない。実験06 で足上げ報酬の判定（yaw_gate）と、その場旋回の指令 20% を入れても、7 チェックポイントすべて不合格（最大 0.12、学習が進むほど 0 へ）。回ろうとすると損をするのか、物理的に回れないのかがまだ分からない。そのための診断（T0-3）と足裏の評価（P6-1）は、評価スクリプトが Kit 起動直後に毎回ハングして一度も取れていない。今回は学習をせず、この2つを取る。

## 実験07

### K0 状態の確認（GPU なし）
- git log -12 --format=\"%h %ad %s\" --date=iso、git status --short、origin/main との差のコミット数。
- ハードリンク5組のリンク数と SHA256。

### K1 ハングの原因（最初に。GPU を使うのは env 16、単独実行、各 10 分まで）
- t0_3_s6_diag.py と p6_1_footpitch.py を、毎回完走する p6_2_basevel_dropout.py とファイル全体で diff する。対象: 先頭の import とその順番（AppLauncher より前か後か。pxr / UsdGeom / isaaclab.sensors / matplotlib など）、argparse の引数、AppLauncher に渡す引数（enable_cameras・headless・device・kit_args）、_eval.ps1 からの起動行。行番号つきで一覧にする。
- 切り分け: p6_2_basevel_dropout.py をコピーして tools\\k1_bisect.py を作り、env を作ったらすぐ閉じるだけにする。そこに差分を1つずつ足して env 16 で起動し、どれを足すとハングするかを特定する。1回ごとに起動時刻・止まった場所・結果を表にする。10 分進まなければ止める（リトライしない）。
- 原因が分かったら、t0_3_s6_diag.py と p6_1_footpitch.py を .bak を取ってから最小限だけ直し、diff を載せる。分からなければ、診断の中身を p6_2_basevel_dropout.py の骨組みに移した新しいスクリプトで K2 / K4 を行う（どちらにしたかを書く）。

### K2 その場旋回で何が起きているか（64 env、ハングしたら 16 env）
チェックポイント: H_eff13p5@2999、J_turn_scratch@1000（S9 0.12 だったもの。名前は docs で確認）、J_turn_scratch@2999。
シナリオ: S6 (0, 0, +0.5)、S9 (0, 0, −0.5)、S3 (0, 0, 0)、S1 (0.5, 0, 0)。
- 胴体: yaw rate の平均、|(vx, vy)| の平均、転倒率
- 足: 左右の接地率、1歩の滞空時間、10 s あたりの歩数
- HR（股のひねり）: 関節角の平均・範囲・|値| の p95（左右）、computed torque の p95 と飽和率
- 立脚足の滑り: 接地している足リンクの world の yaw 角速度の平均と p95、水平速度の平均
- 接地: 立脚中の足ごとの接触点の数と、接触点の x 方向・y 方向の広がり [mm]（足リンク座標で）
- 報酬: 項ごとの 1 step 平均（weight 込み）を S6 と S1 と S3 で並べる

### K3 足が出せる yaw 方向のトルク（H_eff13p5@2999、S3 で方策を動かしたまま、32 env）
- 2 s 立たせたあと、胴体に world の z 軸まわりの外力トルクを 0 から 1 N·m/s で 10 s かけて 10 N·m まで上げる。
- 記録: 胴体の yaw 角速度が 0.2 rad/s を超えたときのトルク、立脚足の yaw 角速度が 0.2 rad/s を超えたとき（足が滑り出した）のトルク、転倒した時刻。env ごとの中央値と範囲。
- 参考として、胴体の z 軸まわりの慣性モーメント（全身、base 座標）と、HR の effort_limit・stiffness を併記する。
- 外力の加え方（使った API と行番号）を書く。cfg は変えず、スクリプト内だけで行う。

### K4 足裏（P6-1、K1 でハングが解消したときだけ）
前の指示の P6-1 の 1〜3（FFE を何 rad 足すと足裏の pitch が 0 か、S3 と S1 の立脚中の足裏 pitch と FFE 角、補正した姿勢で action 0 で 2 s 立てるか）。方策は H_eff13p5@2999。

## 【停止点7】K0〜K3（K4 は解消したときだけ）が終わったら報告して止まる
- 報告書は tools\\logs\\REPORT_exp07_stop7.md。チャットには冒頭3行・判定の表・未実施だけを出す。
- 冒頭3行: ハングの原因（または未特定）、その場旋回で立脚足が滑っているか・HR を使っているか、報酬の内訳で何が効いているか
- 表: K1 の切り分け表、K2 の表（3 チェックポイント × 4 シナリオ）、K3 の表、K4 の結果
- commit のハッシュ（push しない）

## やらないこと
- 学習の起動、報酬・指令・地形・アクチュエータ・機体の cfg の変更
- push、削除、pip / conda でのインストール
推測で直さない。想定外は止まって報告。
```
