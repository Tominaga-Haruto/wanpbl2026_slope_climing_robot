# 指示書 実験04: デプロイ候補（G_real_peak）の頑健性チェック ＋ ONNX 検証 ＋ 保険の学習（WRS機）

> 作成 2026-09-16 深夜。実験03 の最終報告（`tools\\logs\\REPORT_exp03_final.md`、要点は `training_runs.md` と `next_chat_briefing.md` §1）を受けて。
> **実験03 と同じ WRS チャットに続けて貼ってよい。** 新しいチャットにする場合は、`wrs_training_operator_instruction.md` → 実験03 の指示書の「更新」節 → 下のコードブロックの順に貼る。
> 設計の考え方: デプロイ候補は上限が実機 MIT 上限と一致する G_real_peak。実機とのずれ（Kt 未決で実トルクが約 0.7 倍の可能性、Kp・Kd 換算誤差、遅延の揺れ、暫定の friction）を**まず評価だけ**で確かめ、並行して保険の学習（観測から base_lin_vel を外す H_nolinvel と、スイープ結果で選ぶ1本）を回す。

```
# 指示: 実験04 デプロイ候補の頑健性チェック ＋ ONNX 検証 ＋ 保険の学習

実験03 の報告ありがとう。h5py の原因特定と measure_crab.py の評価バグの発見は大きい。
最初に貼った指示書（wrs_training_operator_instruction.md）の掟・作法と、実験03 の指示の「更新」はすべて有効。起動は必ず conda activate 込みの _launch.ps1 / _eval.ps1 / _play.ps1 で行う。
ユーザーは今夜〜明朝、この GPU を占有することを了承済み。開始時に nvidia-smi で他人の計算プロセスがあれば、何も起動せず報告して止まる。

## 方針（Cowork 側の判断）
- デプロイ候補は G_real_peak とする。理由: effort の上限 18 N·m が実機 AK80-9 の MIT トルク上限と同じなので、シムと実機の上限が一致する。G_real_rated は 9 N·m の天井に張り付く歩き方を覚えているが、実機のモーターは 18 まで出すので、足首の挙動がシムとずれる。
- ただし実機は次の点がシムとずれる可能性がある。これを「評価だけ」で先に確かめる:
  - トルク定数（Kt）が未確定。指令トルク÷電流 0.59 N·m/A に対し、データシートは 0.855。物理的に出るトルクが指令の約 0.7 倍かもしれない（AK80-9 の実質上限が 12〜13.5 N·m 程度になる）
  - 実効 Kp は指令の 0.538 倍（換算して指令するが誤差は残る）、実効 Kd も約 0.55 倍（未確定）
  - 通信遅延は中央値 10 ms、一度だけ 80 ms の揺れ
  - AK10-9 の friction・armature は未実測の暫定値
- 候補のチェックポイントは G_real_peak の 2400 と 2999（2999 は S1 のカニ歩き判定を境界でわずかに外れたため）。

## 報告書の直し（最初に 5 分で）
- REPORT_exp03_final.md の S1 トルク表で「max / avg」の順が逆に見える（例: FFE の RMS が max 5.53 < avg 7.04）。どちらがどちらか確認して直す。
- S3 の表で、G 系列の KFE / FFE の行に RMS ではなく computed max が入っている。S3 の全関節の RMS・p95・max・computed max・飽和率を3本分そろえて出し直す。
- G_real_rated@1000 の評価が、measure_crab.py 修正後に再実行されているか確認して1行書く。

## P1 評価だけの頑健性スイープ（学習コードは変えない。GPU は 64 env × 1本ずつ）
measure_crab.py に、評価時だけ env cfg を上書きする引数を足す（例 --override \"scene.robot.actuators.ffe.effort_limit=13.5\"。複数可。上書き後の実効値を actuators のテンソルから読み直して .md の冒頭に書く）。シナリオは S1 / S3 / S7 / S8 だけでよい（時間短縮）。
対象: G_real_peak の model_2400.pt と model_2999.pt。条件（1条件ずつ、他は学習時と同じ）:
1. 基準（上書きなし）
2. AK80-9（hfe・ffe）の effort_limit 13.5
3. AK80-9 の effort_limit 12.0
4. AK80-9 の effort_limit 9.0
5. AK10-9（hr・haa・kfe）の effort_limit 36.0
6. 全グループの stiffness × 0.7
7. 全グループの stiffness × 1.3
8. 全グループの damping × 0.5
9. 全グループの damping × 2.0
10. 遅延を固定 4 step（min_delay = max_delay = 4）
11. 遅延を固定 8 step（バッファの上限で入らなければ入る最大値で。値を報告）
12. 全グループの friction × 2
13. base の質量 +1 kg（add_base_mass を固定値で）
14. 地面の摩擦 0.5（static / dynamic とも）
15. 観測ノイズ ON（学習時と同じノイズ）
16. 吊り下ろし: 既定のスポーン高さ ＋ 0.05 m、S3（指令 0）で開始して、最初の 2 s の転倒率と、着地後 10 s の転倒率・base の水平ドリフト [m]
条件ごとに1行: S1 の v_x・|v_y|・yaw rate・静止率・転倒率、S3 の転倒率、S7 / S8 の yaw rate と小旋回判定、FFE と KFE の飽和率。
不合格の定義: S1 転倒率 > 5%、S1 静止率 > 5%、S1 v_x < 0.35、S3 転倒率 > 5%、小旋回不合格、のどれか。

## P2 ONNX の書き出しと検証（pip で何も入れない）
1. _play.ps1（headless・動画なし）で G_real_peak の 2400 と 2999 を書き出し、exported\\policy.onnx と policy.pt のサイズ・時刻。書き出し先が run フォルダの exported\\ で上書きになるなら、書き出すたびに exported_2400\\ / exported_2999\\ のようにコピーして分ける。
2. 観測の正規化（empirical normalization）が ONNX に含まれているかを rsl_rl のエクスポートのコードで確認。
3. onnx 1.22.0 の onnx.reference.ReferenceEvaluator で ONNX を実行し、torch の方策（play.py が使うのと同じ推論経路）と、ランダムな観測 200 個・評価中の実観測 200 個で出力を比べる。最大絶対誤差を報告（1e-4 以下なら合格）。スクリプトは tools\\verify_onnx.py（新規）。
4. obs_contract.md に G_real_peak 用の節を追記（観測の並び・scale・clip、行動の scale・offset、既定関節角、指令の設定が B と同じか違うか）。

## P3 形状の診断（学習 cfg は変えない）
1. 既定姿勢（init_state.joint_pos）で、左右それぞれの足裏の平面の傾き（地面に対する pitch と roll [deg]）と、足の衝突形状の最下点の x 範囲（base 座標）。実験03 で t=0 に片足 0 点・もう片足 6 点しか接地していなかった理由を数値で示す。
2. P1-4 の「左右の y が一律 4 cm ずれる」の出どころ: base 座標での LL_HR / LR_HR 関節原点の位置、左右の股の間隔の中点の y、全身 COM の (x, y, z)。base 原点が左右の中心から横にずれているのか、脚の形状自体が非対称なのかを区別する。
3. USD の足（ll_ffe / lr_ffe）の衝突形状の近似の種類と頂点数。

## P4 保険の学習（P1 の結果で2本目を選ぶ。2本並走、4096 env、seed 1、3000 iter、一から）
共通: G_real_peak とまったく同じ起動行（アクチュエータ・報酬・平地・rel_heading_envs 0.5・noise_std_type=log）。
- 1本目（必ず）H_nolinvel: 共通 ＋ 方策の観測から base_lin_vel を外す（env.observations.policy.base_lin_vel=null などの上書きで。効かなければ rough_env_cfg.py を .bak_nolinvel を取ってから直し、既定の挙動が変わらないように「上書きで外せる形」にする）。観測の合計次元が 39 になることを params\\env.yaml と起動ログで確認。理由: 実機の base_lin_vel は T265 の VIO 頼みで、脚ロボットの着地の衝撃で外れやすい。外しても歩けるなら、実機のセンサ要件が軽くなる。
- 2本目（P1 で決める）:
  - 条件 2〜4（AK80-9 の effort を下げる）のどれかで不合格 → H_eff13p5: 共通 ＋ hfe / ffe の effort_limit を 13.5 に上書き
  - それ以外で、条件 6〜11（ゲイン・遅延）のどれかで不合格 → H_gainDR: 共通 ＋ アクチュエータのゲインのランダム化（mdp.randomize_actuator_gains、stiffness と damping を ×0.7〜1.3、mode reset）。イベント項を rough_env_cfg.py に「既定は無効（範囲 1.0〜1.0）」で .bak_gaindr を取ってから足し、起動行の上書きで範囲を入れる
  - 全条件で合格 → G_real_peak_s2: 共通で --seed 2（再現性の確認）
- 64 env / 20 iter で2本とも通してから本番。params\\env.yaml で上書きの反映確認。コード変更があれば diff → ハードリンク5組のハッシュとリンク数 → commit（push しない）。
- iter 1000 / 2000 / 2999 で measure_crab.py（S1〜S9、トルク指標込み）。H_nolinvel の評価は観測 39 次元で動くことを確認。
- P1〜P3 と P4 の GPU の重なり: P4 の学習を起動したあとなら、P1 の残りや P3 は 64 env 以下・VRAM 空き 4 GB 以上で並行してよい。env 構築が 10 分以上進まないときは止めて、env 数を下げてやり直す（実験03 のハングの教訓）。

## 【停止点1】P1〜P3 が終わり、P4 を起動したら、報告を1回（学習は回したまま）
- 冒頭3行: 候補（2400 / 2999）の頑健性の結論、ONNX 検証の合否、P4 の2本目に何を選んだかと理由
- P1 の表（候補2つ × 16条件）
- P2 の結果（最大絶対誤差、正規化の有無、書き出し先）
- P3 の結果
- 報告書の直し3点
- P4 の起動時刻と終了見込み時刻

## 【停止点2】P4 の2本の 2999 の評価が終わったら報告して止まる
- 冒頭: 2本それぞれ「カニ歩き・立ち往生・転倒・トルク・小旋回」の判定1行
- 評価の表（G_real_peak@2999 と並べる。S1〜S9、FFE / KFE のトルク指標）
- 正規化 error_vel_xy / error_vel_yaw（500 / 1000 / 2000 / 2999）
- H_nolinvel は、P1 の条件 1・3・10・15 を 2999 でも回す（観測から速度を外したことで頑健性が変わるか）
- 所見3行以内、次の候補1〜2個

## やらないこと
- G_real_peak / G_real_rated の run フォルダとチェックポイントを変更しない（exported のコピー以外）
- 報酬・指令レンジ・地形・stiffness / damping の既定値は変えない（P4 の上書きは起動行で）
- pip / conda で入れる・消す・更新するを一切しない
- Isaac Lab 本体、isaacsim、extscache のファイルを変更しない
- push はしない（ユーザーが行う）。何も削除しない
```
