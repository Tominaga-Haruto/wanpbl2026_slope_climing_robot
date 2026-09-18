# 2026-09-15 再エクスポート指示書を WRS機向けに作り直し

## やったこと

- ユーザーから、Alienware 前提の `urdf_reexport_instruction.md` を WRS機（Windows 11）で実行できるよう直してほしいと依頼。WRS機の Claude Code に指示を出せるとのことだったが、このセッションからは WRS機のセッションが見えなかった（ListAgents で到達可能なエージェント 0）ため、**貼り付け用の指示書**として作成。
- クラウド側で事前確認:
  - GitHub（`Tominaga-Haruto/wanpbl2026_slope_climing_robot`）の追跡ファイルと `.gitignore`、08-21 版 `skyentific_poclegs.py`
  - Skyentific `BipedalRobotSim` の `ISAAC_ASSET_DIR` の位置
  - PyPI の onshape-to-robot 1.8.3 のソース（根の選び方・config キー・依存・`.env` 読み込み・mesh パス生成）
  - Isaac Lab `b4c3210247` の `convert_urdf.py` 引数
- `claude/wrs_urdf_reexport_instruction.md` を新規作成。README を更新。
- ユーザーに「自分がやること」を整理して伝えた（指示書を貼る／API キーと `.env`／先頭インスタンスの目視／停止点の報告をこのチャットに貼る）。
- **停止点A の報告を受けて Step 4 へ進む許可を出した**（下記）。

## 停止点A（WRS機からの報告の要点）

- 機体 `DESKTOP-MACG22A` / Windows 11 Education / RTX 3090 Ti。git は 08-21、`?? references/` のみ。ハードリンク5組健在。C: 43.6GB / D: 534GB。config.json・usd_path は想定どおり。
- **cmd に conda が無く PowerShell からのみ使える。** conda の Avast 回避は `CONDA_SSL_VERIFY`、pip は `PIP_CERT`。
- onshape_env（Python 3.11.16 / onshape-to-robot 1.8.3）作成成功。isaac_env の tensordict 0.7.0 に影響なし。
- 根の選び方の4パターン全て `assembly.py` に存在＝事前確認どおり。
- `.env`: 最初「`.env` フォルダの中にファイル」→ 修正、中身が3行形式でない → ユーザーが修正。3行一致を確認（中身は見ていない）。
- ユーザーが Onshape で先頭が `Part 1 <6>` であることを目視確認済み（ユーザー本人もこのチャットで明言）。
- WRS機に `wrs_pc_environment.md` が無いと報告 → これはプロジェクト文書でWRS機のディスクには無いのが正常。
- `D:\\Tominaga` → `D:\\pbl2026` のリネーム案はスキップ。


## 停止点B（WRS機からの報告の要点）

- 再エクスポート成功。ログ `Found 1 root nodes: - Part 1 <6>`。
- 木構造 5/5（base → HR→HAA→HFE→KFE→FFE を左右）、根 2.91813 kg、link 11 / joint 10（revolute 10 / fixed 0）、合計 10.105775 kg、非対角慣性は全11リンクで非ゼロ、左右対の質量一致（KFE のみ差 1e-6）。
- limit は全関節 ±π / effort 10 / velocity 10（Mate に limit 無し）。
- mesh パスは `package://assets\\merged\\...`（22/22 がバックスラッシュ）＝事前予想どおり。MISSING 0。
- **気になる点:** ゼロ姿勢の FK で左右の Y 座標のズレが足先ほど大きい（HR/HAA は 1mm 未満、KFE 約1.15cm、FFE 約0.8cm）。X は対称。
- **判断:** 木構造の修正は成功と判定。Y のズレは「リンク長など構造の差」か「CAD 上の組み付け角度（＝各関節のゼロ点）が左右で少し違うだけ」かで意味が変わる。KFE→FFE でズレが減っているので後者の可能性が高い。**姿勢に依存しない比較（隣り合う関節原点間の距離、軸の向き）を追加で出させ、並行して Step 6–7 に進めた。** 後者なら構造は正しいが、ゼロ点が左右で数度ずれていると `init_state.joint_pos` 基準の既定姿勢が左右非対称になり、過去のカニ歩き（横流れ）と同種の偏りの原因になりうるので、角度差を数字で出させる。


## Step 6–7 と停止点C（WRS機からの報告の要点）

- Step 6: 木構造から改名。part_1→base、part_1_2〜6→lr_hr/haa/hfe/kfe/ffe、part_1_7〜11→ll_*。Step 7: 22件 `package://` 除去・`/` 統一、MISSING 0。
- 左右差の追加診断:
  - 関節間距離 HR→HAA 75.0 / HAA→HFE 112.5 / HFE→KFE 158.2727 / KFE→FFE 152.5 mm で**左右完全一致**。base→HR のみ 151.0 vs 129.0 mm（base 原点が左右の中央にないためと WRS 側は解釈）。
  - **左右の鏡映はワールド X 軸方向**（＝CAD 上ロボットの左右が X）。軸ずれ 0.5〜0.7°。
  - 関節フレームの「ゼロ点の向き」の残差が 176〜180°。WRS 側は「ミラーコピーで Mate 座標系が反転した」と解釈。
- 停止点C: limit は全関節 ±π / effort 10 / velocity 10。Isaac Lab 2.3.2 の実装調査: **effort は explicit actuator なので URDF 値は効かない／velocity は `velocity_limit_sim` 未指定のため URDF 値 10 rad/s が物理側の上限として効く／lower・upper は効く。**

## 停止点C でのこちらの判断

- **形（リンク長）は左右完全一致 → 構造は正しい。**
- **180° の残差はフレームの取り方の問題である可能性が高く、それ自体は実害の証拠にならない。** 鏡映すると右手系が左手系になるため、比べ方次第で 180° が出る。実害の有無は「同じ符号の関節角を入れて、左右の足先位置が鏡映になるか」を FK で直接確かめる方が確実 → それを指示。
- **★新しい懸念: ロボットの左右がワールド X だと、base の +X（Isaac Lab の「前」）がロボットの横方向になっている可能性がある。** Isaac Lab の速度指令 `lin_vel_x` は base 座標の +X を前として扱うので、そうなら「前進指令＝横歩き」を学習する。過去のカニ歩きとの関係は未検証（旧 URDF は根が別部品で base フレームも別物だった）。**USD 変換の前に、base 座標で「左右の股が並ぶ方向」「足先の向き（膝の曲がる方向）」「上下」を確認させる。**
- Step 8 の決定（推奨として提示、ユーザー判断）: URDF の velocity を 08-21 版 actuator の値（HR 23 / HAA 15 / HFE・KFE 20 / FFE 23 rad/s）に、effort も同じく actuator 値（24 / 30 / 30 / 20）に揃える（effort は効かないが混乱防止）。lower/upper は今回 ±π のまま（可動域はゼロ点と前方向の確認後に決める）。なお 08-21 の旧 URDF も velocity 10 だったので、過去の学習も 10 rad/s 上限で回っていた。


## 前方向・左右符号の確認結果（WRS機、B/C に進まず停止）

- base 座標: **X＝左右、Y＝前後、Z＝上下**（左右 HR 間ベクトル [0.150, -0.0005, 0.0006]、胴体→足首 [-0.019, 0.109, -0.298]、足リンク bbox 最長が Y）。**+X は前ではない。**
- init_state.joint_pos（左右同符号）で左右足首が 223 mm 非対称。
- +0.3 rad 鏡映テスト: HR/HAA/HFE/KFE は**左右逆符号で**鏡映（残差 8〜10 mm）、同符号では 46〜184 mm ずれ。FFE は符号で結果が変わらない。

## こちらの分析（このチャット）

- **旧 URDF（GitHub の 08-21 版 robot_sim.urdf）をクラウド側で FK 計算したら、旧版も左右の HR が base の X 方向に 0.15 m 並んでいた＝旧版も +X が横。** onshape-to-robot の base フレームは CAD のワールド軸と同じ向きなので当然。**→ Alienware での過去の学習は全部「Isaac Lab の前進指令＝機体の横方向」で回っていた可能性が高い。カニ歩き（横歩き）の有力な説明。** ただし旧版は根も壊れていたので、切り分けは新 URDF での学習で確認する（仮説扱い）。
- FFE が「符号によらず同じ」なのは、足首リンクの**原点＝足首関節そのもの**の位置で比べたから（関節を回しても原点は動かない）。テストの作りの問題で、足の重心など原点以外の点で測り直す必要がある。
- 直し方の方針（ユーザーに提示）:
  - 前方向: **URDF の base フレームを Z 軸まわりに回す後処理スクリプト**（base の inertial/visual/collision の origin と、base から出る2本の joint の origin に回転を掛ける）。Onshape 側でアセンブリの向きを変えるより確実で、FK で検証できる。Isaac Lab の init_state.rot では base フレームの意味は変わらないので不可。
  - 左右符号: **片脚の関節軸を URDF で反転**（same sign = mirror にする）。08-21 版コードと Skyentific の同符号の初期姿勢をそのまま使える。どちらの脚を反転するかは「初期姿勢で膝が前・足裏が水平」になる方で決める。
  - あわせて初期姿勢での足裏の最下点から、スポーン高さ 0.449 m が合っているかを計算させる。
- ここまで URDF の修正と検証だけ行い、USD 変換の前に止めて報告させる。


## 軸反転の案L/案R評価（WRS機、両案とも不採用で停止）

- 前方向の判定: 足首→足裏の重心 Y が -0.001、bbox 中心 Y が -0.02 → 「前＝-Y」と判定し base を +90° 回転（FK 誤差 0、LL_HR が +Y＝左で命名と整合）。**ただし根拠は 1〜2 cm の差で弱い。**膝リンク重心は逆の +Y 側。
- COM で測り直すと 5 関節とも同符号では鏡映にならず（42〜223 mm）、逆符号で 9〜11 mm。
- init_state.joint_pos での評価:
  - 案L（LL 反転）: 鏡映 8.8 mm ✓ / 膝が後ろ ✗ / 足裏 roll 7.2〜7.4°・pitch 6.8〜7.0° ✗ / 必要高さ 0.406 m
  - 案R（LR 反転）: 鏡映 11.4 mm ✗ / 膝が前 ✓ / 足裏 roll 8.0〜8.1°・pitch 5.8〜6.0° ✗ / 必要高さ 0.370 m
- 現在の robot_sim.urdf は base 回転のみ適用、軸反転は未適用。

## こちらの分析

- 鏡映 8.8 mm と 11.4 mm の差は CAD 誤差（8〜10 mm）の範囲内で、10 mm の線引きに意味はない。
- **足裏の傾きは両案とも合成すると約 10°（√(7.3²+6.9²)≈10.0、√(8.05²+5.9²)≈10.0）＝ HAA の初期値 -0.1745 rad（10°）そのもの。** 足首にロール関節が無いので HAA を 10° 開けば足裏も 10° 傾くのは設計上当然で、異常ではない。
- **問題はその 10° の回転軸が前後方向から約 40〜45° 斜めになっていること（roll と pitch に半々に分かれている）。** 考えられる原因: CAD のゼロ姿勢で HR（股の回転）が 40〜45° ほど回っていて、脚全体が斜めを向いている。すると爪先も斜めを向くので、足裏の bbox 中心の Y 差が 2 cm と小さかったことも説明がつく。
- **→ 本質は「CAD のゼロ姿勢が『脚まっすぐ・爪先前・足裏水平』になっていない」こと。** Skyentific の初期値はゼロ＝その中立姿勢を前提にしている。手順書 B7 の「CAD の関節ゼロ点はバラバラ」がここで効いてきた。
- 直し方の候補: URDF の各関節 origin に「中立姿勢までのオフセット回転」を掛けて、q=0 が中立姿勢になるようにする（子リンクの中身は変えない）。実機の原点合わせも「中立姿勢＝0」で揃えられる利点がある。
- 進め方: どの案も適用せず、ゼロ姿勢の診断（各関節軸の向き、脚の曲がり、爪先の向き）と **3 方向からの絵（PNG）** を出させ、ユーザーが目で前後・膝の向きを確認してから決める。ユーザーに「設計上の膝の曲がる向き（人間型か鳥型か）」を質問。


## ゼロ姿勢の診断と絵（WRS機）→ 真因の特定

- 関節軸（base +90° 回転後）: HR≈±Z、HAA≈±X、HFE/KFE/FFE≈±Y で、**どれも 1° 以内でまっすぐ**。**→ 「HR が 45° 回っている」というこちらの仮説は外れ。** 絵でもゼロ姿勢の脚はほぼまっすぐ下に伸びている。
- WRS 側の「膝角度 150°」は、HFE 関節の原点が股から横に張り出した位置にあるため、原点どうしを結ぶと斜めになるだけの見かけの値。「足裏の長手が Y・法線 42°」も絵と合わない（絵では足は X 方向に約 0.17 m、Y 方向に約 0.09 m で X が長い）。この2つの数値診断は信用しない。
- **軸の向きの一覧（ゼロ姿勢・回転後）:**
  - LR: HR +Z / HAA -X / HFE +Y / **KFE -Y** / FFE +Y
  - LL: HR +Z / HAA -X / HFE -Y / **KFE +Y** / FFE -Y
- **真因は2つ重なっていた:**
  1. **左右:** ピッチ軸（HFE/KFE/FFE）が左右で逆向き、ロール軸（HAA）とヨー軸（HR）が左右で同じ向き。同じ符号で鏡写しにするには、ピッチは左右同じ向き・ロールとヨーは左右逆向きでないといけないので、全部逆になっている（案L でも案R でも「鏡写し」自体は直る理由）。
  2. **脚の中:** 1本の脚の中で **KFE だけ HFE・FFE と逆向き**。Skyentific の初期値（HFE -10° / KFE +20° / FFE -10°）は3つのピッチ軸が同じ向きのとき「膝を曲げて足裏水平」になる値。逆向きだと全部同じ方向に足されて、太もも +10°・すね +30°・足 +40° と前に振り上げた姿勢になる。案L の絵で足が前に大きく出て傾いていたのはこれ。**案L/案R（片脚まるごと反転）ではこちらが直らないので、両案とも基準を満たさなかった。**
- **ユーザーの回答: 膝は人間と同じ向きに曲がる設計。**
- 直し方の方針: 最終的な軸の向きを「両脚とも HFE/KFE/FFE = +Y」「HAA と HR は左右で逆向き」に揃える（＝LL の HR・HAA・HFE・FFE と LR の KFE を反転）。右手の法則で、+Y 軸まわりのとき HFE 負→脚が前、KFE 正→足が後ろ（人間の膝）、FFE 負→爪先が上で、Skyentific の値で足裏が水平になる。HAA -10° で足が内側に寄るか外側に開くかは HAA の左右どちらを +X にするかで変わるので、両方の絵を出させてユーザーが選ぶ。
- 前方向（+X が爪先か）は、足の形が ankle から +X に 0.10 m・-X に 0.07 m で弱く +X。最終姿勢の絵で「人間がしゃがんだ形で +X を向いているか」をユーザーが目で確認し、逆なら base をさらに 180° 回して軸の割り当てをやり直す。


## 軸反転の最終2案（WRS機）とユーザーの決定

- 案OUT（LL_HR, LR_HAA, LL_HFE, LR_KFE, LL_FFE を反転）/ 案IN（LL_HR, LL_HAA, LL_HFE, LR_KFE, LL_FFE を反転）。どちらも軸は目標どおり（HFE/KFE/FFE = +Y 両脚）。
- init_state.joint_pos での FK: 鏡映ズレ 10〜11 mm、膝は両脚とも HFE-FFE 線より 35〜42 mm 前、足裏 pitch ±0.5〜0.7°・roll ±10.0°（HAA の分）、足の間隔 OUT 423 mm / IN 222 mm（HAA 0 相当で約 325 mm）、必要な base 高さ OUT 0.357 m / IN 0.388 m。**分析どおり直った。**
- **ユーザー確定: 爪先は +X。HAA は外にも内にも開かないのが理想（足裏が平らなので、開くと足裏の縁で立つことになる）。**
- **決定:**
  - 初期姿勢の HAA を 0 にする（`my_robot_code/skyentific_poclegs.py` の LL_HAA / LR_HAA を -0.1745 → 0.0）。Skyentific の -0.1745 は見本機体の値で、この機体には合わない。
  - HAA=0 なら OUT/IN で姿勢は同じなので、案の選択は「符号の約束」だけの問題になる。**約束を「HAA も HR も、正の角度＝外向き（HAA は足が外へ開く、HR は爪先が外を向く）」に統一**。最終的な軸: LR_HR -Z / LL_HR +Z / LR_HAA -X / LL_HAA +X / 両脚の HFE・KFE・FFE +Y。
  - スポーン高さは HAA=0 の姿勢で計算し直して `init_state.pos` の z に反映（足裏最下点 + 数 mm の余裕）。
  - limit は前回決めた値（velocity 23/15/20/20/23、effort 24/30/30/30/20、lower/upper ±π）。
  - その後 USD 変換 → 配置 → 64 env / 20 iter テスト。コードの変更はハードリンクを切らない書き方で行い、リンク数とハッシュを確認。commit はまだしない。
- メモ（後回し）: base 原点が胴体メッシュの前面付近（脚より約 9 cm 前、左右中心から約 2 cm ずれ）にある。学習は動くが、速度の観測は原点の位置で測られるので、いずれ胴体中心や IMU 位置に原点を移すか検討。


## USD 変換でブロック（WRS機）

- EULA 未承認 → `OMNI_KIT_ACCEPT_EULA=Y` で解消。
- 次に `Can't find extension ... isaacsim.asset.importer.urdf = 2.4.31`（手元は 2.4.30 のみ）＋拡張レジストリ3つとも接続失敗 → `ModuleNotFoundError: isaacsim.asset`。**exit code は 0 なのに USD は未生成**（終了コードで成否を判断しない）。
- クラウド側で確認: Isaac Lab `b4c3210247` の `urdf_converter.py` は Isaac Sim 5.1 以上で `isaacsim.asset.importer.urdf-2.4.31` を有効化する（コメント: 固定ジョイントを既定でマージする挙動を保つための後方互換の pin）。レジストリから取りに行く設計で、Avast の SSL 検査で失敗したと考えられる。
- 判断: この機体の URDF は fixed joint 0 個なので、pin の理由（固定ジョイントのマージ）は影響しない。進め方は (1) Kit 側に証明書の環境変数を渡して1回だけ再試行 → (2) だめなら自分専用 clone `D:\\Tominaga\\IsaacLab` の `urdf_converter.py` の pin を 2.4.30 に**一時的に**変えて変換し、終わったら元に戻す（`.bak_pin` から復元、ハッシュ確認）。変換後に USD の中身（関節数・名前・軸・limit・質量合計）を Isaac Sim 経由で検算。IsaacLab 本体の編集なのでユーザー了承のうえで。


## USD 変換ブロックの続き

- 証明書の環境変数（SSL_CERT_FILE / CURL_CA_BUNDLE / REQUESTS_CA_BUNDLE）を足しても Kit の拡張レジストリには接続できず。**Kit のレジストリ通信は Python の証明書設定が効かない。**
- pin を 2.4.30 に一時変更 → `ImportConfig` に `set_merge_fixed_ignore_inertia` が無いという AttributeError。**2.4.31 固定は挙動だけでなく API の差もある。** urdf_converter.py は復元済み（ハッシュ一致、git clean）。
- 次の方針（ユーザーに提示）:
  1. **ディスク上に 2.4.31 が既にないか読み取りで探す**（同じ Windows ユーザー WRS の他の Isaac 環境が過去に取得している可能性。Kit の拡張キャッシュは環境内の extscache やユーザーの AppData 配下）。見つかれば、自分の環境の拡張の検索先に追加するか、自分の環境側へコピーして使う（他人のファイルは読むだけ）。
  2. 無ければ、**Isaac Lab を書き換えずに** `tools\\convert_urdf_local.py` を書く: `UrdfConverter` を継承して、2.4.31 を有効化する部分と 2.4.30 に無いメソッド呼び出しだけを飛ばす。fixed joint 0 個なので飛ばしても意味は変わらない。変換後 `verify_usd.py` で中身を URDF と突き合わせる。


- ユーザーから「あとで戻すなら Avast の設定を変えてもよい」と提案。回答: 根本解決としては有効だが、共用PCのセキュリティ設定で他の利用者にも効くので TA さんの了承を取ってから。変えるなら全体の停止ではなく、Web シールドの HTTPS スキャンの除外に Kit の拡張レジストリのドメインだけを足す形が最小。GUI 操作なのでユーザー本人が TeamViewer で行う（WRS の Claude Code には触らせない）。まずは設定変更不要の手順（ディスク上の 2.4.31 探索 → 自前スクリプト）を先に試し、両方ダメなときの第3候補とする。


- ユーザー: TA さんの許可は取得済み。**順番を「1. ディスク上の 2.4.31 探索 → 見つからなければユーザーが Avast の GUI で設定 → 変換 → 設定を戻す → それでもダメなら自前スクリプト」に変更。** WRS 側には探索と、Kit ログからレジストリの URL（ドメイン）を抜き出すところまでをやらせ、Avast 操作の前で止めさせる。Avast はまず URL 例外、効かなければ変換の数分間だけ「HTTPS スキャン」をオフ → 変換後すぐ戻す。


## USD 変換の解決とテスト起動（WRS機、総合報告）

- ディスク上の Kit キャッシュ `C:\\Users\\WRS\\AppData\\Local\\ov\\data\\exts\\v2\\` に `isaacsim.asset.importer.urdf-2.4.31+107.3.3.wx64.r.cp311` があった（他ユーザーの過去利用）。自分の環境の extscache にコピー → 依存の `omni.kit.pip_archive-5df61bf515266ea2` も同じ場所からコピー → **変換成功**。Isaac Lab 無変更、Avast も触らずに済んだ。
- `verify_usd.py`: 関節 10・全 revolute・fixed 0、質量 10.105775 kg、driveMaxForce = effort、maxJointVelocity = velocity（deg/s 換算）、±180°。食い違いなし。
- テスト起動: `arrow_x.usd`（速度指令の矢印、S3）取得が 300 s タイムアウト → Hydra オーバーライド `env.commands.base_velocity.debug_vis=false` で回避 → **20/20 完走**。1.5〜2.3 s/iter、VRAM 約 7.4 GB、iter19 の終了理由 bad_orientation 99.5% / base_contact 1.2% / time_out 0%、episode 長 21.2 → 38.1。
- 最終軸（確認済み）: LR_HR -Z / LL_HR +Z、LR_HAA -X / LL_HAA +X、HFE/KFE/FFE +Y。HR +0.2 rad で爪先外向き ±11.5°、HAA +0.2 rad で足が外へ ±57 mm。
- `skyentific_poclegs.py`: pos z 0.449 → 0.375776、LL_HAA / LR_HAA -0.1745 → 0.0。ハードリンク維持（リンク数 2、ハッシュ一致）。HAA=0 で鏡映 10.9 mm、膝前 35〜42 mm、足裏 ≈0°。
- git status: M my_robot_code/skyentific_poclegs.py、M onshape_export/myrobot_dummy/robot_sim.urdf、未追跡（バックアップ群、robot.urdf、robot_sim_IN/OUT.urdf、references/、tools/）。秘密・生成物は出ていない。

## 次の一手（ユーザーに提示）

1. **後処理を1本のスクリプトにまとめる**（`tools/postprocess_urdf.py`: robot.urdf → リンク改名 → mesh パス整形 → base +90° → 5関節の軸反転 → limit → robot_sim.urdf）。今の robot_sim.urdf と完全一致することを確認。次に再エクスポートしたとき手作業の再発見を防ぐため。
2. **commit と push**: 対象は robot_sim.urdf / robot.urdf（生の出力の記録）/ skyentific_poclegs.py / tools の .py（検算・後処理）。バックアップ・IN/OUT 案・PNG・ログは入れない。push はユーザーが PAT を入力。push 後に `git log origin/main` の日付を確認（08-21 で止まっていた件の再発防止）。ハードリンクのハッシュ確認。
3. その後 `wrs_training_strategy.md` §1 の棚卸し（08-21 版コードの grep）から学習へ。


## commit / push 完了

- `6ede75b`（再エクスポート・軸修正・limit・初期姿勢・検算スクリプト）を push。ユーザーの push 出力 `b50a6ee..6ede75b main -> main` と origin/main の最新が一致。**08-21 で止まっていた GitHub がようやく更新された。**
- WRS の Claude Code の Bash からは `git fetch` が証明書で失敗（push はユーザーの PowerShell で成功）。
- 後処理スクリプト `tools/postprocess_urdf.py` が作られ robot_sim.urdf と一致したかは報告に明記がなかった → 次回確認。
- Onshape API キーは作業完了につき Revoke をユーザーに推奨。
- 次: `wrs_training_strategy.md` §1 の棚卸し（読むだけ）を WRS 側に依頼する文をユーザーに提示。


## 閉じる前のまとめ（2026-09-16）

- 後処理スクリプト `postprocess_urdf.py` は robot.urdf から再実行して robot_sim.urdf と差分0（自己チェック PASS）。
- 08-21 版コードの棚卸し完了 → `wrs_training_strategy.md` §1 に反映。要点: noise_std_type 無し、clip_actions 無し、指令は Isaac Lab 既定（全方向・heading 全周）、bad_orientation 1.3 rad あり（0.8 は Alienware 9月版）、command_vel は昇格のみ、HFE と KFE が同じアクチュエータグループ、ゲインのランダム化無し、randomize_actuator_gains と DCMotorCfg は Isaac Lab に存在。
- **ユーザーの方針: 「X 軸が横」問題でカニ歩きが解決するかもしれないので、このチャットを閉じ、学習戦略と実行のための新しいチャットを Cowork 側・WRS 側の両方で始める。** 了承。
- 書き換え・新規作成した文書:
  - `project_handbook.md`: 全面改訂（A0 現在地、A1 に座標・符号の検証／状況説明の依頼、A2〜A6 を WRS機本線に、B1〜B3 を新パイプライン、B2 に問題2・3、B4 を 08-21 版の現状値に、B6 に WRS機のトラブル、B7 limit・質量、B8・B9・B11・B12 更新）
  - `handover.md`: 全面改訂
  - `wrs_training_strategy.md`: 棚卸し結果（§1）、9月変更の仕分けを改訂（前提に「横向きの機体」）、段階0（最小変更で横向き仮説を確認）を追加
  - `next_chat_briefing.md`: 次の Cowork チャット（学習戦略と実行）への指示書
  - `wrs_training_operator_instruction.md`（新規）: WRS機の Claude Code の新チャットに最初に貼る指示書
  - `README.md`: 現在の状況・一覧・索引
- 決まっていないこと（新チャットで決める）: 段階0 の設計（地形・iter・「カニ歩きが消えた」の判定基準）、9月変更をどれから戻すか、アクチュエータの実機寄せの順番。

## 決めたこと・分かったこと

- **onshape-to-robot 1.8.3 は実装上「インスタンス一覧の先頭＝根」**: `process_mates()` が最初に `make_body(rootAssembly.instances[0])`、merge で小さい body id を残し、`build_trees()` が id 順に根を選ぶ。ログに `Found N root nodes:` が出る。WRS機の実物でも確認済み。
- GitHub には `onshape_export/myrobot_dummy/config.json`・旧 `robot_sim.urdf`（08-21、旧木構造、limit は ±π/10/10）・`rename_links_dummy.py`・`set_limits_dummy.py` がある。
- 08-21 版 `skyentific_poclegs.py` の `usd_path` は既に `robots/myrobot_dummy/robot.usd` → 今回は編集不要。
- **Windows 固有の落とし穴:** mesh パスが `\\` 区切りになる見込み（Step 7 で `/` に統一）。`requests` には `REQUESTS_CA_BUNDLE`。cp932 対策に `PYTHONUTF8=1`。
- onshape-to-robot は `isaac_env` に入れず別環境 `onshape_env`。
- リンク改名は joint 名から機械的に。XML 属性で書き換える。
- **指示書の `cmd /c \"conda activate ...\"（Step 9 / 10）は WRS機では動かない → PowerShell に読み替えるよう WRS側に伝えた。** Step 4 は conda 不要（exe フルパス）なので cmd でも可。
- **`D:\\Tominaga` はリネームしない方がよい**（conda 環境・editable インストール・ハードリンクが絶対パスに依存）。変えるなら環境の作り直し扱い。
- 共用PCなので、API キーは使用後 Revoke を勧める。
- 08-21 版 actuators は HFE を KFE と同じグループにしており、モーター割り当て（HFE=AK80-9）と合っていない（今回は報告のみ）。

## 手を動かした場所

- `claude/robot_model_conventions.md`（新規。座標・関節符号・初期姿勢・limit の正本）
- `claude/project_handbook.md` / `claude/handover.md` / `claude/next_chat_briefing.md`（全面改訂）、`claude/wrs_training_strategy.md`（改訂）、`claude/wrs_training_operator_instruction.md`（新規）

- `claude/wrs_urdf_reexport_instruction.md`（新規）
- `claude/README.md`（現在の状況・アクティブ指示書の表・索引）
- `claude/wrs_pc_environment.md`（onshape_env・`.env`・証明書変数の表・conda は PowerShell のみ・リネーム禁止・§4 起動手順・§5 進捗）
- 本ファイル

## 積み残し・次にやること

0. **（2026-09-16 時点の最新）** 再エクスポートは完了・push 済み・棚卸し済み。**次は新しいチャットで学習戦略（`next_chat_briefing.md`）→ WRS側に `wrs_training_operator_instruction.md` を貼って学習。**Onshape API キーの Revoke、base 原点の位置、機構的可動域、actuator のグループ分け（HFE と KFE）が宿題。

1. ~~Step 4 / 停止点B~~ → 済。Step 6–7 と左右ズレの追加診断 → **停止点C（limit）で報告を受ける**
1a. **前方向（base の +X がロボットの前か）と初期姿勢の左右対称性の FK 確認** → 問題なければ Step 9–10、あれば止めて報告
1b. 左右ズレが「ゼロ点の角度差」なら、Onshape で直すか `init_state.joint_pos` 側で左右別に補正するかを決める
2. 停止点C: limit / effort を定格にするかピークにするか（ユーザー判断）
3. git 用の証明書変数（`GIT_SSL_CAINFO` か）を確認して `wrs_pc_environment.md` §3-1 に記録
4. 成功したら `project_handbook.md`（B3 パイプライン・A2/A4 環境と構成）を Windows / 新木構造に合わせて書き換え
