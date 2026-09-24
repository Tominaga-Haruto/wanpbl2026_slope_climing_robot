import json, os, datetime
ROOT = "/tmp/claude-0/-home-claude/eb1afeb0-77b5-5529-b8bf-4ef73bbb4eb7/scratchpad/deck"
os.makedirs(ROOT + "/project/slides", exist_ok=True)

NAVY, BLUE, CYAN, ORANGE = "#102B46", "#1C5A85", "#32A5B5", "#E8783F"
SAND, PALE, LINE, INK, MUTED, PH = "#F3EEE6", "#E8F1F5", "#B7C7D1", "#17212B", "#56626B", "#FBF7F3"
OK, NG = "#2E7D52", "#B94A36"
FONT = "'Noto Sans JP', 'Yu Gothic', sans-serif"
SEC = f"background:#ffffff; color:{INK}; font-family:{FONT}; padding:96px 112px 150px; display:flex; flex-direction:column; gap:36px"

def head(title, lead=None):
    h = f'<h2 style="font-size:60px; font-weight:700; color:{NAVY}; line-height:1.15; border-bottom:3px solid {LINE}; padding-bottom:20px">{title}</h2>'
    if lead:
        h += f'<p style="font-size:34px; font-weight:700; color:{NAVY}; line-height:1.4">{lead}</p>'
    return h

def pageno(n):
    return f'<p style="position:absolute; right:112px; bottom:56px; width:200px; text-align:right; font-size:28px; font-weight:700; color:{ORANGE}">{n}</p>'

def ph(kind, what, h=None, extra=""):
    label = "▶ ここに動画を貼る" if kind == "動画" else "■ ここに画像を貼る"
    hh = f"height:{h}px; " if h else ""
    return (f'<div style="{hh}flex:1; display:flex; flex-direction:column; gap:8px; background:{PH}; border:3px dashed {ORANGE}; border-radius:8px; padding:20px 24px{extra}">'
            f'<p style="font-size:26px; font-weight:700; color:{ORANGE}">{label}</p>'
            f'<p style="font-size:24px; color:{MUTED}; line-height:1.4">{what}</p></div>')

def band(text, fill=SAND):
    return f'<p style="font-size:30px; font-weight:700; color:{NAVY}; background:{fill}; padding:18px 28px; text-align:center; line-height:1.4">{text}</p>'

def slide(sid, body, notes, n=None):
    s = f'<section id="{sid}" data-transition="fade" style="{SEC}">\n{body}\n'
    if n is not None:
        s += pageno(n) + "\n"
    s += f"<aside>{notes}</aside>\n</section>\n"
    open(f"{ROOT}/project/slides/{sid}.html", "w").write(s)

S = []

# 14 全体像
S.append("overview")
slide("overview", head("制御の全体像", "シミュレーターで歩き方を学習し、その“脳”をロボットに載せる") + f'''
<div style="display:flex; gap:40px; flex:1; align-items:stretch">
  <div style="flex:1.15; display:flex; flex-direction:column; gap:20px; background:{PALE}; border:3px solid {CYAN}; border-radius:12px; padding:28px">
    <h3 style="font-size:36px; font-weight:700; color:{CYAN}">学習用PC（Isaac Sim）</h3>
    {ph("動画", "4096 体が同時に練習している動画（引きの画、10〜20 秒）")}
    <p style="font-size:28px; font-weight:700; color:#ffffff; background:{BLUE}; padding:14px 20px; text-align:center; border-radius:8px">できあがるもの：ポリシー（次の行動を決めるルール）</p>
  </div>
  <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; gap:8px">
    <p style="font-size:26px; font-weight:700; color:{ORANGE}">載せる</p>
    <x-shape kind="arrow-right" style="width:90px; height:56px; background:{ORANGE}"></x-shape>
  </div>
  <div style="flex:1; display:flex; flex-direction:column; gap:22px; background:{SAND}; border:3px solid {ORANGE}; border-radius:12px; padding:28px">
    <h3 style="font-size:36px; font-weight:700; color:{ORANGE}">ロボット（実機）</h3>
    <ul style="font-size:30px; line-height:1.5; display:flex; flex-direction:column; gap:14px">
      <li>Jetson（ミニコンピューター）がポリシーで 1 秒に 50 回計算</li>
      <li>カメラ（T265）で胴体の傾き・速さを測る</li>
      <li>10 個のモーターを CAN 通信で動かす</li>
      <li>Switch 2 のプロコン（無線）で進む向き・速さを指示</li>
    </ul>
  </div>
</div>''', "制御の全体像です。人が歩き方をプログラムするのではなく、Isaac Simというシミュレーターの中で強化学習を行い、ロボットが自分で歩き方を学びます。左の動画のように、4096体が同時に練習します。学習の結果できあがるのが「ポリシー」で、これはロボットの次の行動を決めるルールのようなものです。実機では、このポリシーをJetsonというミニコンピューターにインポートします。Switch 2のプロコンのスティックで進む向きと速さを指示すると、Jetsonがカメラなどのセンサーの値をもとにポリシーに従って計算し、1秒間に50回、モーターへの指令を決めます。", 14)

# 15 ループ（画像を貼れる配置）
def node(title, sub, color, img):
    return (f'<div style="flex:1; display:flex; flex-direction:column; gap:12px">'
            f'{ph("画像", img, 190)}'
            f'<p style="font-size:28px; font-weight:700; color:#ffffff; background:{color}; padding:12px 10px; text-align:center; border-radius:8px; line-height:1.3">{title}<br><span style="font-size:24px; font-weight:400">{sub}</span></p></div>')
def arr(label=""):
    return (f'<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px; width:92px">'
            f'<x-shape kind="arrow-right" style="width:70px; height:40px; background:{BLUE}"></x-shape>'
            f'<p style="font-size:24px; color:{BLUE}; text-align:center; font-weight:700">{label}</p></div>')
S.append("loop")
slide("loop", head("ロボットの中の制御ループ", "測る → 計算する → 動かす を 1 秒に 50 回くり返す") + f'''
<div style="display:flex; align-items:flex-start; gap:0px">
  <div style="flex:1; display:flex; flex-direction:column; gap:16px">
    {node("Switch 2 のプロコン", "速度の指令（無線）", BLUE, "プロコンの写真")}
    {node("カメラ（T265）", "加速度・速度・位置", CYAN, "T265 の写真")}
  </div>
  {arr("")}
  <div style="flex:1.1; display:flex; flex-direction:column; gap:12px; padding-top:120px">
    {ph("画像", "Jetson の写真", 230)}
    <p style="font-size:28px; font-weight:700; color:#ffffff; background:{NAVY}; padding:12px 10px; text-align:center; border-radius:8px; line-height:1.3">Jetson<br><span style="font-size:24px; font-weight:400">ポリシーで 10 関節の目標角を計算</span></p>
  </div>
  {arr("目標角")}
  <div style="flex:1; display:flex; flex-direction:column; gap:12px; padding-top:120px">
    {ph("画像", "モーター（AK10-9 / AK80-9）の写真", 230)}
    <p style="font-size:28px; font-weight:700; color:#ffffff; background:{ORANGE}; padding:12px 10px; text-align:center; border-radius:8px; line-height:1.3">モーター × 10<br><span style="font-size:24px; font-weight:400">USB-CAN 変換経由</span></p>
  </div>
</div>
<p style="font-size:28px; color:{MUTED}; line-height:1.4">体が動く → カメラと各モーターの角度でまた測る（フィードバック）</p>''',
"次に制御の流れです。まず、カメラ（T265）で測った今の加速度・速度・位置と、Switch 2のプロコンからの速度の指令をミニコンピューター（Jetson）が受け取ります。Jetsonはそれに、モーターから返ってくる関節の角度を合わせて、Isaac Simで作ったポリシーで各モーターの次の目標角を計算し、USB-CAN変換を通してモーターに送ります。そして体が動き、その変化をまた測る。この一周を1秒間に50回くり返しています。", 15)

# 16 強化学習
S.append("rl")
def cyc(t, b, c):
    return (f'<div style="display:flex; flex-direction:column; align-items:center; gap:8px; flex:1">'
            f'<p style="font-size:34px; font-weight:700; color:#ffffff; background:{c}; padding:14px 0; width:100%; text-align:center; border-radius:40px">{t}</p>'
            f'<p style="font-size:26px; color:{INK}; text-align:center">{b}</p></div>')
def prep(n, t, b, c, fill):
    return (f'<div style="display:flex; gap:20px; align-items:center; background:{fill}; border:2px solid {c}; border-radius:10px; padding:20px 24px">'
            f'<p style="font-size:30px; font-weight:700; color:#ffffff; background:{c}; width:56px; height:56px; border-radius:28px; text-align:center; line-height:56px">{n}</p>'
            f'<div style="display:flex; flex-direction:column; gap:4px"><h3 style="font-size:32px; font-weight:700; color:{NAVY}">{t}</h3><p style="font-size:26px">{b}</p></div></div>')
slide("rl", head("強化学習とは：ご褒美と罰で歩き方を覚えさせる") + f'''
<div style="display:flex; gap:56px; flex:1">
  <div style="flex:1; display:flex; flex-direction:column; gap:28px; justify-content:center">
    <div style="display:flex; gap:16px; align-items:flex-start">
      {cyc("やってみる", "ポリシーが関節を動かす", BLUE)}
      <x-shape kind="arrow-right" style="width:50px; height:34px; background:{LINE}; align-self:center"></x-shape>
      {cyc("採点する", "ご褒美・罰で点数", ORANGE)}
      <x-shape kind="arrow-right" style="width:50px; height:34px; background:{LINE}; align-self:center"></x-shape>
      {cyc("少し直す", "点が上がる方へ", CYAN)}
    </div>
    <p style="font-size:30px; font-weight:700; color:{MUTED}; text-align:center">これを何百万回もくり返す（合計 25,000 回の更新）</p>
  </div>
  <div style="flex:0.95; display:flex; flex-direction:column; gap:18px">
    <h3 style="font-size:34px; font-weight:700; color:{NAVY}">人が用意するのは 3 つだけ</h3>
    {prep(1, "ロボットのモデル（URDF）", "CAD から作った形・重さ・関節", BLUE, PALE)}
    {prep(2, "練習する環境", "地形・滑りやすさ・重さ・押す力を毎回変える", BLUE, PALE)}
    {prep(3, "報酬", "何にご褒美、何に罰を与えるか", ORANGE, SAND)}
  </div>
</div>
{band("関節の動かし方は教えない。点数だけを手がかりに、ロボットが自分で見つける")}''',
"次に強化学習について少しだけ紹介します。強化学習はしつけに似ています。ロボットがやってみて、良い動きならご褒美、悪い動きなら罰を与え、点数が上がる方へ少しずつ直す。これを何百万回もくり返します。人が用意するのは、ロボットのモデル、練習する環境、どの行動にご褒美を与えてどの行動に罰を与えるかという報酬の3つだけです。また、学習は段階ごとに分けていて、次の段階は前の段階で覚えたポリシーから練習を続けました。", 16)

# 17 CAD
S.append("cad")
cols = ""
for i, (t, b, c) in enumerate([("CAD（Onshape）", "設計班の 3D モデルの画面", ORANGE), ("URDF", "関節とリンクのつながり（ツリー図）", BLUE), ("Isaac Sim", "シミュレーター上に立つロボット", CYAN)]):
    cols += (f'<div style="flex:1; display:flex; flex-direction:column; gap:12px"><h3 style="font-size:32px; font-weight:700; color:{c}; text-align:center">{t}</h3>{ph("画像", b, 260)}</div>')
    if i < 2:
        cols += f'<x-shape kind="arrow-right" style="width:44px; height:34px; background:{NAVY}; align-self:center"></x-shape>'
slide("cad", head("ロボットをシミュレーターに入れる") + f'''
<div style="display:flex; gap:16px">{cols}</div>
<p style="font-size:28px; line-height:1.45">URDF：ロボットの設計図。形・重さ・関節の位置と回る向きを書いたファイル</p>
<div style="display:flex; flex-direction:column; gap:10px; background:{SAND}; border:2px solid {ORANGE}; border-radius:10px; padding:22px 28px">
  <h3 style="font-size:30px; font-weight:700; color:{ORANGE}">つまずいた点</h3>
  <ul style="font-size:27px; line-height:1.5; display:flex; flex-direction:column; gap:6px">
    <li>Onshape の書き出し機能をそのまま使うと、モーターの中の部品までリンクになった（約 1,300 個）→ 変換ツールでまとめた</li>
    <li>前後と左右の向きが入れ替わっていた → 関節を 1 つずつ動かして確かめ、そろえた</li>
  </ul>
</div>''',
"シミュレーターにロボットを入れるには、設計班がOnshapeで作ったCADを、ロボットの設計図にあたるURDFというファイルに変換し、Isaac Simにインポートします。つまずいた点は2つあります。1つ目は、Onshapeの書き出し機能をそのまま使うと、モーターの中の歯車やねじなどの部品まですべて別々のリンクになり、約1,300個のリンクがつながった形になってしまったことです。ふつうは一緒に動く部品は1つにまとめるので、onshape-to-robotという変換ツールを使って、モーターを1つのかたまりにまとめました。2つ目は、出したままだと前後と左右が入れ替わっていたことで、関節を1つずつ動かして確認してそろえました。", 17)

# 18 報酬
S.append("reward")
def grp(t, tag, c, fill, items):
    rows = "".join(f'<div style="display:flex; justify-content:space-between; align-items:center; gap:12px; border-bottom:1px solid {LINE}; padding:10px 0"><p style="font-size:26px; line-height:1.3">{a}</p><p style="font-size:30px; font-weight:700; color:{c}; white-space:nowrap">{b}</p></div>' for a, b in items)
    return (f'<div style="flex:1; display:flex; flex-direction:column; gap:6px; background:{fill}; border:3px solid {c}; border-radius:10px; padding:22px 26px">'
            f'<div style="display:flex; justify-content:space-between; align-items:center"><h3 style="font-size:32px; font-weight:700; color:{c}">{t}</h3><p style="font-size:24px; font-weight:700; color:#ffffff; background:{c}; padding:4px 14px">{tag}</p></div>{rows}</div>')
M = "－"
slide("reward", head("報酬関数の全体像（最終形）", "13 項目の点数を毎回足し合わせる（＋ご褒美、－罰）") + f'''
<div style="display:flex; gap:28px; align-items:flex-start">
{grp("目的を達成する", "ご褒美", CYAN, PALE, [("指令どおりの速さで進む", "+1.0"), ("指令どおりに回る", "+1.0"), ("足を浮かせてから着地する", "+2.0")])}
{grp("きれいに歩く", "罰", ORANGE, SAND, [("胴体が上下に揺れる", M+"2.0"), ("胴体が傾く", M+"0.5"), ("足が地面を滑る", M+"0.25"), ("胴体が左右・前後に揺れる", M+"0.05"), ("指令を急に変える", M+"0.01"), ("力を使いすぎる", "極小")])}
{grp("安全に動く", "罰", NAVY, "#ffffff", [("足以外が地面に当たる", M+"1.0"), ("関節の限界に近づく", M+"1.0"), ("股の開き・ひねりが初期姿勢からずれる", M+"0.1"), ("膝の曲げ方が初期姿勢からずれる", M+"0.01")])}
</div>
{band("転んだら（胴体が地面に触れる・大きく傾く）その回は終わり、最初からやり直し", PALE)}''',
"今回の報酬関数の全体像です。報酬関数は13項目の点数の合計です。ご褒美は3つで、指令どおりの速さで進むこと、指令どおりに回ること、足をしっかり浮かせてから着地することです。罰は、胴体が揺れる・傾く、足が滑る、指令を急に変える、足以外が地面に当たる、関節の限界に近づく、などです。数字は各項目に掛ける重みで、そのまま重要度の順ではありません。", 18)

# 19 立ち往生とカニ歩き（下の帯を削除）
S.append("struggle")
def colm(t, sym, cause, fix, c):
    return (f'<div style="flex:1; display:flex; flex-direction:column; gap:14px">{ph("動画", sym, 250)}'
            f'<h3 style="font-size:36px; font-weight:700; color:{c}">{t}</h3>'
            + (f'<div style="display:flex; gap:14px"><p style="font-size:24px; font-weight:700; color:#ffffff; background:{c}; padding:4px 12px; height:40px; white-space:nowrap">原因</p><p style="font-size:26px; line-height:1.45">{cause}</p></div>' if cause else "")
            + f'<div style="display:flex; gap:14px"><p style="font-size:24px; font-weight:700; color:#ffffff; background:{OK}; padding:4px 12px; height:40px; white-space:nowrap">{"対策" if cause else "結果"}</p><p style="font-size:26px; line-height:1.45">{fix}</p></div></div>')
slide("struggle", head("学習で苦労した点：立ち往生とカニ歩き") + f'''
<div style="display:flex; gap:36px; flex:1">
{colm("立ち往生", "「進め」でもその場で立ち止まる様子", "立っているだけでも点がもらえ、足を上げると損をする採点だった", "片足で立つ時間にご褒美を出す形に変えた", NG)}
{colm("カニ歩き", "まっすぐ進めでも横に流れる様子", "前後と左右の向きが入れ替わっていた。横に流れても点がほとんど減らなかった", "向きをそろえ、横へのずれに強い罰を与えた", ORANGE)}
{colm("改善後", "指示どおりまっすぐ前へ歩く様子", "", "指示どおりの方向へまっすぐ歩けるようになった", OK)}
</div>''',
"学習で一番苦労したのは、立ち往生とカニ歩きです。立ち往生は、進めと指示してもその場で立ち止まってしまう現象で、立っているだけでも点が少しもらえるうえに、足上げの報酬がこの脚では足を上げるほど損をする式になっていたのが原因でした。カニ歩きは、まっすぐ進めと指示しても横に流れる現象で、CADのままでは前後と左右が入れ替わっていたことと、横に流れても点がほとんど減らない採点だったことが原因でした。向きをそろえ、横へのずれに強い罰を与え、片足で立つ時間にご褒美を出す形にしたことで、指示どおりまっすぐ歩けるようになりました。", 19)

# 20 シム結果
S.append("simresult")
cells = ["平地を前進", "坂 10°", "坂 15°", "でこぼこ 6 cm", "その場で旋回", "歩きながら旋回"]
rows = ""
for r in range(2):
    rows += '<div style="display:flex; gap:28px; flex:1">'
    for t in cells[r*3:(r+1)*3]:
        rows += f'<div style="flex:1; display:flex; flex-direction:column; gap:8px">{ph("動画", t + "（実験15の動画）", 250)}<p style="font-size:30px; font-weight:700; color:{NAVY}; text-align:center">{t}</p></div>'
    rows += "</div>"
slide("simresult", head("結果：シミュレーションでは坂・でこぼこ・旋回もできた") + rows +
      f'<p style="font-size:30px; font-weight:700; color:{CYAN}; text-align:center">どの場面でも 16 体中 1 体も転ばなかった（15 秒間）</p>',
"シミュレーションでは、平地だけでなく10度・15度の坂、6センチのでこぼこ、その場での旋回、歩きながらの旋回まで、どの場面でも16体中1体も転ばずに動けました。（参考：前進0.5 m/s の指示で平地は15秒で6.75 m、坂10°で6.44 m、坂15°で5.83 m、でこぼこ6 cmで5.26 m〔指示0.4 m/s〕、その場旋回0.37 rad/s、歩きながら旋回0.39 rad/s〔指示0.5 rad/s〕）", 20)

# 21 デプロイ A（段階）
S.append("deployA")
steps = [("1台ずつ動かす", "指令どおりに回るか", "完了", OK, "EAF4EE"), ("吊って全身", "10 台すべてにポリシーの指令", "完了", OK, "EAF4EE"),
         ("床で立つ", "決まった姿勢を保つ", "完了", OK, "EAF4EE"), ("床で歩く", "ポリシーに任せる", "ここで詰まっている", ORANGE, SAND), ("Jetson＋プロコン", "無線で好きな方向へ", "通信は確認済み", MUTED, "#ffffff")]
st = ""
for i, (t, b, s_, c, f) in enumerate(steps):
    st += (f'<div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:12px; background:{f}; border:2px solid {c}; border-radius:10px; padding:22px 12px">'
           f'<p style="font-size:28px; font-weight:700; color:#ffffff; background:{c}; width:52px; height:52px; border-radius:26px; text-align:center; line-height:52px">{i+1}</p>'
           f'<h3 style="font-size:30px; font-weight:700; color:{NAVY}; text-align:center">{t}</h3><p style="font-size:24px; text-align:center; line-height:1.35">{b}</p>'
           f'<p style="font-size:24px; font-weight:700; color:#ffffff; background:{c}; padding:4px 16px">{s_}</p></div>')
slide("deployA", head("デプロイ：学習したポリシーをロボットで動かす", "いきなり床で歩かせず、小さく確かめてから全身へ") + f'''
<div style="display:flex; gap:18px">{st}</div>
<div style="display:flex; gap:28px; flex:1">{ph("動画", "床の上で立っている動画")}{ph("動画", "床の上でポリシーに任せ、歩こうとする動画")}</div>''',
"学習したポリシーをロボットで動かすことをデプロイと呼びます。まずポリシーをどの計算機でも動く形式で書き出し、学習時と同じ入力で同じ答えが出るかを確かめました。そのうえで、モーター1台ずつ、吊った状態で全身、床で立つ、と段階的に進めてきましたが、今は床の上で歩かせるところで詰まっています。試験中は、傾きや電流・速度が上限を超えたら自動で止め、最後は人が主電源を切れる体制にしています。左が床の上で立っている様子、右がポリシーに任せて歩こうとしている様子です。プロコンの無線通信はJetsonで確認済みなので、床で歩けるようになれば、あとはJetsonに載せるだけです。", 21)

# 21 デプロイ B（別案：写真で進み具合を見せる／シム→実機の流れ）
S.append("deployB")
flow = [("学習用PC", "ポリシーを書き出す", BLUE), ("ノートPC（試験中）", "同じプログラムで実機を動かす", CYAN), ("Jetson（本番）", "ロボットに載せて無線操作", MUTED)]
fl = ""
for i, (t, b, c) in enumerate(flow):
    fl += (f'<div style="flex:1; display:flex; flex-direction:column; gap:4px; border:3px solid {c}; border-radius:10px; padding:16px 20px; background:{"#ffffff" if i==2 else PALE}">'
           f'<h3 style="font-size:30px; font-weight:700; color:{c}">{t}</h3><p style="font-size:24px">{b}</p></div>')
    if i < 2:
        fl += f'<x-shape kind="arrow-right" style="width:50px; height:36px; background:{NAVY}; align-self:center"></x-shape>'
ph4 = ""
for t, s_, c in [("1台ずつ", "完了", OK), ("吊って全身", "完了", OK), ("床で立つ", "完了", OK), ("床で歩く", "詰まっている", ORANGE)]:
    ph4 += (f'<div style="flex:1; display:flex; flex-direction:column; gap:10px">{ph("動画", t + "の写真・動画", 300)}'
            f'<div style="display:flex; justify-content:center; gap:14px; align-items:center"><p style="font-size:30px; font-weight:700; color:{NAVY}">{t}</p>'
            f'<p style="font-size:24px; font-weight:700; color:#ffffff; background:{c}; padding:2px 12px">{s_}</p></div></div>')
slide("deployB", head("デプロイ：学習したポリシーをロボットで動かす（別案）") + f'''
<div style="display:flex; gap:14px">{fl}</div>
<div style="display:flex; gap:22px; flex:1">{ph4}</div>
<p style="font-size:28px; font-weight:700; color:{NAVY}; text-align:center">床で歩ければ、あとは Jetson に載せるだけ（プロコンの無線通信は確認済み）</p>''',
"【別案】学習用PCで作ったポリシーを書き出し、今はノートPCで同じプログラムを動かして実機試験をしています。モーター1台ずつ、吊った状態で全身、床で立つ、までは完了しましたが、今は床の上で歩かせるところで詰まっています。プロコンの無線通信はJetsonで確認済みなので、床で歩けるようになれば、あとはJetsonに載せるだけです。", 21)

# 22 結果：実機（直したことはここ）
S.append("realresult")
slide("realresult", head("結果：実機") + f'''
<div style="display:flex; gap:32px">
  <div style="flex:1.25; display:flex; flex-direction:column; gap:10px; background:#EAF4EE; border:3px solid {OK}; border-radius:10px; padding:22px 28px">
    <h3 style="font-size:32px; font-weight:700; color:{OK}">できたこと</h3>
    <ul style="font-size:27px; line-height:1.45; display:flex; flex-direction:column; gap:6px">
      <li>床の上で立てる（CAD の「まっすぐ」が膝の曲がった姿勢だったずれを、読み替えで直した）</li>
      <li>荷重を減らしてポリシーに前進の指令を送ると、床の上で歩こうとする（最長 5 秒ほど）</li>
      <li>吊った状態なら、歩く動きが続く</li>
      <li>Switch 2 のプロコンの無線通信（Jetson）</li>
    </ul>
  </div>
  <div style="flex:0.75; display:flex; flex-direction:column; gap:10px; background:#FBEDEA; border:3px solid {NG}; border-radius:10px; padding:22px 28px">
    <h3 style="font-size:32px; font-weight:700; color:{NG}">まだできていないこと</h3>
    <ul style="font-size:27px; line-height:1.45; display:flex; flex-direction:column; gap:6px">
      <li>床の上で歩き続けること</li>
      <li>Jetson に載せてプロコンで操作すること</li>
    </ul>
  </div>
</div>
<div style="display:flex; gap:32px; flex:1">{ph("動画", "床の上で立っている／歩こうとする動画")}{ph("動画", "吊った状態で歩く動きが続く動画")}</div>''',
"実機の結果です。まず、床の上で立てるようになりました。CADで「まっすぐ」のつもりだった姿勢が実は膝の曲がった姿勢だったので、その分を読み替えて直しています。立っているのは、決まった姿勢を保つ制御によるものです。次に、荷重を減らした状態でポリシーに前進の速度指令を送ると、床の上で歩こうとする動きが出て、最長で5秒ほど続きました。吊った状態なら歩く動きが続きます。Switch 2のプロコンの無線通信もJetsonで確認できています。ただ、床の上で歩き続けることと、Jetsonに載せてプロコンで操作することはまだできていません。", 22)

# 23 考察（直していない違い＝原因、重要な順）
S.append("discussion")
rows = [("床で歩き続けられない原因（重要な順）", "これからの対策"),
        ("安全のための自動停止（電流・速度）が、シムのふつうの歩き方より厳しく、途中で止まる", "モーターの制限をシムに入れて学習し直す"),
        ("シムの歩き方が実機向きでない（膝を曲げたまま、1 秒に約 5 歩の小刻みなすり足）", "まっすぐに近い姿勢で、すり足に罰を与えて学習し直す"),
        ("シムでは毎回、空中から落として練習を始めていた", "止まって立った状態から始める"),
        ("モーターの摩擦がシムの 2〜3 倍", "摩擦をばらつかせて学習する")]
tb = '<table style="font-size:27px; width:100%">'
for i, (a, b) in enumerate(rows):
    if i == 0:
        tb += f'<tr><th style="background:{NAVY}; color:#ffffff; padding:14px 20px; text-align:left; width:60%">{a}</th><th style="background:{NAVY}; color:#ffffff; padding:14px 20px; text-align:left; width:40%">{b}</th></tr>'
    else:
        bg = "#ffffff" if i % 2 else PALE
        tb += f'<tr><td style="background:{bg}; padding:14px 20px; line-height:1.4">{a}</td><td style="background:{bg}; padding:14px 20px; line-height:1.4">{b}</td></tr>'
tb += "</table>"
slide("discussion", head("考察：なぜ床の上で歩き続けられないか") + tb + band("プログラム側の補正はやり尽くした → シムを実機に合わせて学習し直している"),
"床の上で歩き続けられない理由です。床での試験の記録を調べると、多くは安全のための自動停止、つまり電流や速度が上限を超えたことで止まっていました。ところがシミュレーターの歩き方を調べると、ふつうに歩くだけでこの上限を超えてしまいます。歩き方そのものも、膝を曲げたまま1秒に約5歩の小刻みなすり足で、実機向きではありませんでした。ほかに、シミュレーターでは毎回空中から落として練習を始めていて、止まって立った状態から始めたことがないこと、モーターの摩擦が2〜3倍あることも分かりました。プログラム側での補正はやり尽くしたので、今はこれらをシミュレーターに入れて学習し直しています。", 23)

# 24 今後の展望
S.append("future")
fut = [("平地でまっすぐ歩かせる", "モーターの制限・立った状態からの開始・実機向きの歩き方で学習し直す（進行中）", ORANGE, SAND),
       ("Switch 2 のプロコンで好きな方向へ", "Jetson に載せるだけ。無線通信は確認済み", CYAN, "#ffffff"),
       ("坂・でこぼこでも歩かせる", "シミュレーションではできているので、実機でも", NAVY, "#ffffff")]
fh = ""
for i, (t, b, c, f) in enumerate(fut):
    fh += (f'<div style="display:flex; gap:28px; align-items:center"><p style="font-size:34px; font-weight:700; color:#ffffff; background:{c}; width:72px; height:72px; border-radius:36px; text-align:center; line-height:72px">{i+1}</p>'
           f'<div style="flex:1; display:flex; flex-direction:column; gap:6px; background:{f}; border:3px solid {c}; border-radius:12px; padding:22px 30px">'
           f'<h3 style="font-size:38px; font-weight:700; color:{NAVY}">{t}</h3><p style="font-size:28px">{b}</p></div></div>')
slide("future", head("今後の展望") + f'<div style="display:flex; flex-direction:column; gap:30px">{fh}</div>',
"今後の展望です。まずは平地でまっすぐ歩かせることが目標で、そのために今、シミュレーターを実機に合わせて学習し直しています。それができると、Jetsonに載せて、Switch 2のプロコンで好きな方向に歩かせることを目指します。最後は、シミュレーションではできている坂やでこぼこ道でも、実機で歩けるようにしていきたいです。", 24)


# まとめ差し替え案
S.append("summary")
ms = ""
for t, b, c in [("設計", "足裏の接地と重心配置を起点に脚構造を考えた", ORANGE), ("配線", "電源と CAN 通信を分け、確認しやすい経路を整理した", BLUE),
                ("制御", "シミュレーションで坂・旋回まで歩けるポリシーを作り、実機で立つ・歩こうとするところまで進めた", CYAN)]:
    ms += (f'<div style="display:flex; gap:32px; align-items:center"><p style="font-size:34px; font-weight:700; color:#ffffff; background:{c}; width:170px; padding:14px 0; text-align:center">{t}</p>'
           f'<p style="flex:1; font-size:30px; line-height:1.45">{b}</p></div>')
slide("summary", head("まとめ・今後の展望", "二足歩行ロボットの移動基盤を、3 つの担当から形にした") + f'<div style="display:flex; flex-direction:column; gap:30px">{ms}</div>' + band("次の段階：実機で平地を歩かせ、プロコン操作、坂・でこぼこへ広げる"),
"【チーム共通まとめの差し替え案】制御の行と次の段階だけ更新。設計・配線の行は元のまま。", 25)

deck = {"v": 4, "createdOnFiles": {"v": 1, "at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")},
        "title": "制御パート ver4", "order": S, "cover": S[0],
        "sections": {"s1": {"description": "制御のしくみ：全体像・ループ・強化学習・URDF", "start": "overview"},
                     "s2": {"description": "学習：報酬、苦労した点、シミュレーションの結果", "start": "reward"},
                     "s3": {"description": "実機：デプロイ、結果と考察", "start": "deployA"},
                     "s4": {"description": "今後の展望とまとめ", "start": "future"}},
        "faces": {"noto-sans-jp": {"family": "Noto Sans JP", "href": "https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap"}},
        "designSystems": []}
json.dump(deck, open(f"{ROOT}/project/deck.json", "w"), ensure_ascii=False, indent=1)
print(S)
