// 制御パート スライド生成（既存チームデッキと同じ配色・フォント・レイアウト）
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in（1280x720px 基準で座標を書く）
pres.title = "制御パート：強化学習による二足歩行制御";

const FONT = "Yu Gothic";
const C = { navy: "102B46", blue: "1C5A85", cyan: "32A5B5", orange: "E8783F", sand: "F3EEE6", ink: "17212B", muted: "5E6A73", pale: "E8F1F5", line: "B7C7D1", white: "FFFFFF", ph: "FBF7F3", ok: "2E8B57", ng: "C8553D" };
const P = (v) => v / 96; // px -> inch

function T(s, text, x, y, w, h, o = {}) {
  const opt = {
    x: P(x), y: P(y), w: P(w), h: P(h),
    fontFace: FONT, fontSize: o.size ?? 18, color: o.color ?? C.ink, bold: o.bold ?? false,
    align: o.align ?? "left", valign: o.valign ?? "middle", margin: o.margin ?? 0, isTextBox: true,
  };
  if (o.fill) opt.fill = { color: o.fill };
  if (o.border) opt.line = { color: o.border, width: o.bw ?? 1 };
  if (o.shape) opt.shape = o.shape;
  if (o.radius) { opt.shape = pres.shapes.ROUNDED_RECTANGLE; opt.rectRadius = o.radius; }
  if (o.para) opt.paraSpaceAfter = o.para;
  if (o.lineSp) opt.lineSpacingMultiple = o.lineSp;
  if (o.italic) opt.italic = true;
  s.addText(text, opt);
}
function R(s, x, y, w, h, fill, border, bw = 1, o = {}) {
  const opt = { x: P(x), y: P(y), w: P(w), h: P(h), fill: fill ? { color: fill } : { type: "none" }, line: border ? { color: border, width: bw, dashType: o.dash ?? "solid" } : { type: "none" } };
  if (o.radius) { opt.rectRadius = o.radius; s.addShape(pres.shapes.ROUNDED_RECTANGLE, opt); }
  else if (o.oval) s.addShape(pres.shapes.OVAL, opt);
  else s.addShape(pres.shapes.RECTANGLE, opt);
}
// 直線矢印（x1,y1 -> x2,y2）
function A(s, x1, y1, x2, y2, color = C.blue, width = 2.5, o = {}) {
  const opt = {
    x: P(Math.min(x1, x2)), y: P(Math.min(y1, y2)), w: P(Math.max(Math.abs(x2 - x1), 0.01)), h: P(Math.max(Math.abs(y2 - y1), 0.01)),
    line: { color, width, dashType: o.dash ?? "solid", endArrowType: o.noHead ? undefined : "triangle", beginArrowType: o.both ? "triangle" : undefined },
    flipH: x2 < x1, flipV: y2 < y1,
  };
  s.addShape(pres.shapes.LINE, opt);
}
function base(s, title, num) {
  s.background = { color: C.white };
  T(s, title, 66, 40, 1060, 60, { size: 30, bold: true, color: C.navy });
  T(s, num, 1130, 54, 84, 28, { size: 14, bold: true, color: C.orange, align: "right" });
  s.addShape(pres.shapes.LINE, { x: P(66), y: P(112), w: P(1148), h: 0, line: { color: C.line, width: 1.5 } });
  T(s, "PBL  二足歩行ロボットの開発", 66, 688, 360, 18, { size: 9, color: C.muted });
}
function lead(s, text, y = 132) { T(s, text, 66, y, 1148, 44, { size: 22, bold: true, color: C.navy }); }
// 画像・動画を後で貼る枠
function PH(s, x, y, w, h, kind, what, o = {}) {
  R(s, x, y, w, h, C.ph, C.orange, 1.75, { dash: "dash" });
  const label = kind === "動画" ? "▶ ここに動画を貼る" : "■ ここに画像を貼る";
  T(s, label, x + 14, y + 12, w - 28, 26, { size: o.lsize ?? 15, bold: true, color: C.orange });
  T(s, what, x + 14, y + 42, w - 28, h - 54, { size: o.size ?? 13, color: C.muted, valign: "top", lineSp: 1.1 });
}
function num(s, n, x, y, color, d = 40) { T(s, String(n), x, y, d, d, { size: 18, bold: true, color: C.white, fill: color, align: "center", shape: pres.shapes.OVAL }); }
function card(s, x, y, w, h, fill = C.sand, border = C.line) { R(s, x, y, w, h, fill, border, 1); }
function notes(s, t) { s.addNotes(t); }

// =============================================================
// ================= ver3：制御パート（コンパクト版・H 方策の数値なし） =================
// ユーザーが ver2 で直した文言は反映済み（全体像「その脳」「Isaac Sim」、ループ「カメラ」、RL「ロボットのモデル（URDF）」、
// URDF の説明「ロボットの設計図。…」、報酬「膝の曲げ方が初期姿勢からずれる」、デプロイの題「…実機ロボットに」、全角マイナス）
pres.title = "制御パート ver3";
const MINUS = "－";
const TAB = (rows, fs = 16) => rows.map((r, i) => r.map((c) => ({ text: c, options: { bold: i === 0, color: i === 0 ? C.white : C.ink, fill: { color: i === 0 ? C.navy : (i % 2 ? C.white : C.pale) }, fontFace: FONT, fontSize: fs, valign: "middle", margin: [3, 8, 3, 8] } })));

// ---------- 1. 制御の全体像（4096 体の動画をここへ） ----------
{
  const s = pres.addSlide(); base(s, "制御の全体像", "07");
  lead(s, "シミュレーターの中で歩き方を学習し、その脳をロボットに載せて動かす");
  R(s, 66, 196, 560, 470, C.pale, C.cyan, 2, { radius: 0.05 });
  T(s, "学習用PC（Isaac Sim）", 88, 206, 520, 34, { size: 21, bold: true, color: C.cyan });
  PH(s, 88, 246, 516, 250, "動画", "Isaac Sim で 4096 体が同時に練習している動画（引きの画。格子状に並んで一斉に歩こうとしている様子、10〜20 秒）。", { size: 14 });
  T(s, "4096 体のロボットが同時に練習し、報酬（ほめる・叱る）で歩き方が上達", 88, 504, 516, 60, { size: 17, color: C.ink, valign: "top" });
  T(s, "できあがるもの：方策\n（歩き方を決めるニューラルネット）", 88, 576, 516, 72, { size: 16, bold: true, color: C.white, fill: C.blue, align: "center", radius: 0.1 });
  A(s, 630, 430, 700, 430, C.orange, 4);
  T(s, "載せる", 626, 394, 80, 30, { size: 14, bold: true, color: C.orange, align: "center" });
  R(s, 706, 196, 508, 470, C.sand, C.orange, 2, { radius: 0.05 });
  T(s, "ロボット（実機）", 728, 206, 470, 34, { size: 21, bold: true, color: C.orange });
  T(s, [
    { text: "Jetson が方策を 1 秒間に 50 回計算", options: { bullet: true, breakLine: true } },
    { text: "T265 で胴体の傾き・速さを測る", options: { bullet: true, breakLine: true } },
    { text: "10 個のモーターを CAN 通信で動かす", options: { bullet: true, breakLine: true } },
    { text: "プロコン（無線）で進む向き・速さを指示", options: { bullet: true } },
  ], 728, 256, 466, 380, { size: 19, valign: "top", para: 14 });
  notes(s, "制御の全体像です。歩き方を人が1つずつプログラムするのではなく、Isaac Simというシミュレーターの中でロボットに練習させて覚えさせました。左の動画のように4096体が同時に練習します。できあがったものを「方策」と呼び、歩き方を決めるニューラルネットです。これをロボットのJetsonに載せ、センサの値から1秒間に50回モーターへの指令を計算します。人はプロコンで、どちらへどれくらいの速さで進むかだけを指示します。");
}

// ---------- 2. ロボットの中の制御ループ ----------
{
  const s = pres.addSlide(); base(s, "ロボットの中の制御ループ", "07");
  lead(s, "測る → 計算する → 動かす → また測る を 1 秒間に 50 回くり返す");
  PH(s, 66, 196, 230, 66, "画像", "T265 の写真（ver2 で貼ったもの）", { size: 11, lsize: 11 });
  T(s, "プロコン\n（Bluetooth 無線）", 470, 186, 340, 70, { size: 17, bold: true, color: C.white, fill: C.blue, align: "center", radius: 0.1 });
  T(s, "カメラ（T265）\n胴体の加速度・速度・自己位置", 66, 300, 230, 96, { size: 16, bold: true, color: C.white, fill: C.cyan, align: "center", radius: 0.1 });
  T(s, "Jetson\n方策（ニューラルネット）で\n10 個の関節の目標角を計算", 420, 290, 440, 116, { size: 18, bold: true, color: C.white, fill: C.navy, align: "center", radius: 0.1 });
  T(s, "USB-CAN\n変換", 984, 300, 230, 96, { size: 17, bold: true, color: C.white, fill: C.orange, align: "center", radius: 0.1 });
  T(s, "モーター × 10", 984, 500, 230, 80, { size: 18, bold: true, color: C.white, fill: C.navy, align: "center", radius: 0.1 });
  T(s, "ロボットの体が動く", 470, 510, 340, 60, { size: 18, bold: true, color: C.navy, fill: C.sand, border: C.orange, align: "center", radius: 0.1 });
  A(s, 640, 258, 640, 286, C.blue, 3); T(s, "進む向き・速さ", 650, 258, 180, 26, { size: 13, bold: true, color: C.blue });
  A(s, 298, 348, 416, 348, C.cyan, 3);
  A(s, 862, 348, 980, 348, C.orange, 3);
  A(s, 1099, 398, 1099, 496, C.orange, 3); T(s, "目標角", 1110, 432, 100, 26, { size: 14, bold: true, color: C.orange });
  A(s, 980, 540, 814, 540, C.navy, 3);
  A(s, 984, 568, 900, 568, C.orange, 2.5, { noHead: true, dash: "dash" });
  A(s, 900, 568, 900, 440, C.orange, 2.5, { noHead: true, dash: "dash" });
  A(s, 900, 440, 700, 440, C.orange, 2.5, { noHead: true, dash: "dash" });
  A(s, 700, 440, 700, 410, C.orange, 2.5, { dash: "dash" });
  T(s, "今の角度を返す", 720, 444, 170, 26, { size: 13, bold: true, color: C.orange });
  A(s, 466, 540, 181, 540, C.cyan, 2.5, { noHead: true, dash: "dash" });
  A(s, 181, 540, 181, 400, C.cyan, 2.5, { dash: "dash" });
  T(s, "体の動きをカメラが測る", 196, 546, 260, 26, { size: 13, bold: true, color: C.cyan });
  T(s, "実線：指令　破線：フィードバック", 66, 610, 400, 24, { size: 13, color: C.muted });
  T(s, "※ 現在の実機試験はノートPCで同じプログラムを動かし、速度は固定値で指示。プロコン操作は Jetson 単体で確認済み", 66, 636, 1148, 40, { size: 12, color: C.muted, valign: "top" });
  notes(s, "ロボットの中では、カメラ（T265）が胴体の動きと傾きを測り、プロコンからは進む向きと速さが無線で届きます。Jetsonはこれらとモーターから返ってきた関節の角度を集めて、方策で10個の関節の目標角を計算し、USB-CAN変換を通してモーターに送ります。モーターが動くと体が動き、その変化をまた測る、という一周を1秒間に50回くり返しています。");
}

// ---------- 3. 強化学習とは ----------
{
  const s = pres.addSlide(); base(s, "強化学習とは：ほめる・叱るで歩き方を覚えさせる", "07");
  const cyc = [["やってみる", "方策が関節を動かす", C.blue, 110, 170, 54], ["採点する", "報酬でほめる・叱る", C.orange, 110, 440, 54], ["少し直す", "点が上がる方へ方策を修正", C.cyan, 430, 305, -32]];
  cyc.forEach(([t, b, col, x, y, dy]) => { T(s, t, x, y, 220, 50, { size: 21, bold: true, color: C.white, fill: col, align: "center", radius: 0.2 }); T(s, b, x - 20, y + dy, 260, 30, { size: 14, color: C.ink, align: "center" }); });
  A(s, 220, 256, 220, 434, C.line, 3);
  A(s, 332, 460, 460, 358, C.line, 3);
  A(s, 428, 318, 332, 205, C.line, 3);
  T(s, "何百万回も\nくり返す", 236, 320, 150, 60, { size: 15, bold: true, color: C.muted, align: "center" });
  T(s, "人が用意するのは 3 つだけ", 720, 140, 494, 34, { size: 21, bold: true, color: C.navy });
  const prep = [["1", "ロボットのモデル（URDF）", "CAD から作った形・重さ・関節"], ["2", "練習する環境", "地形、床の滑りやすさ・重さ・押される力を毎回変える"], ["3", "報酬", "何をほめて、何を叱るか"]];
  prep.forEach(([n, t, b], i) => { const y = 186 + i * 118; card(s, 720, y, 494, 102, i === 2 ? C.sand : C.pale, i === 2 ? C.orange : C.line); num(s, n, 738, y + 28, i === 2 ? C.orange : C.blue, 44); T(s, t, 796, y + 10, 400, 36, { size: 20, bold: true, color: C.navy }); T(s, b, 796, y + 48, 400, 50, { size: 15, color: C.ink, valign: "top" }); });
  T(s, "前回までの学習結果を引き継ぎ、地形や指示を変えながら練習を重ねた（合計 25,000 回の更新）", 720, 544, 494, 56, { size: 14, color: C.muted, valign: "top" });
  T(s, "どう関節を動かせば歩けるかは教えない。点数だけを手がかりに、ロボットが自分で見つける", 66, 614, 1148, 46, { size: 17, bold: true, color: C.navy, fill: C.sand, align: "center" });
  notes(s, "強化学習は犬のしつけに似ています。ロボットがやってみて、良い動きならほめ、悪い動きなら叱り、点数が上がる方へ少しずつ直す。これを何百万回もくり返します。人が用意するのは、ロボットのモデル、練習する環境、何をほめて何を叱るかという報酬の3つだけです。学習は毎回ゼロからではなく、前回までの結果を引き継いで、地形や指示を変えながら積み重ねました。");
}

// ---------- 4. ロボットをシミュレーターに入れる ----------
{
  const s = pres.addSlide(); base(s, "ロボットをシミュレーターに入れる", "07");
  const st = [["CAD（Onshape）", "設計班の 3D モデルの画面"], ["URDF", "関節とリンクのつながり（ツリー図や一覧）の画面"], ["Isaac Sim", "シミュレーター上に立っている自分たちのロボット"]];
  st.forEach(([t, b], i) => {
    const x = 66 + i * 392;
    T(s, t, x, 132, 364, 34, { size: 20, bold: true, color: [C.orange, C.blue, C.cyan][i], align: "center" });
    PH(s, x, 172, 364, 300, "画像", b + "。", { size: 15 });
    if (i < 2) A(s, x + 368, 322, x + 388, 322, C.navy, 3);
  });
  T(s, "URDF：ロボットの設計図。ロボットの形・重さ・関節の位置と回る向きを書いたファイル。質量や重心は CAD の材質から自動で計算", 66, 486, 1148, 56, { size: 16, color: C.ink, valign: "top" });
  card(s, 66, 556, 1148, 100, C.sand, C.orange);
  T(s, "つまずいた点", 90, 564, 300, 28, { size: 16, bold: true, color: C.orange });
  T(s, "CAD から出したままだと「前後と左右の向きが入れ替わる」「左右の脚で関節の回る向きが逆になる」ことが分かり、10 個の関節を 1 つずつ動かして確かめ、そろえた", 90, 594, 1100, 58, { size: 15, valign: "top" });
  notes(s, "シミュレーターにロボットを入れるには、設計班がOnshapeで作ったCADを、ロボットの設計図にあたるURDFというファイルに変換し、Isaac Simに読み込みます。CADから出したままだと前後と左右が入れ替わっていたり、左右の脚で関節の回る向きが逆になっていたりしたので、10個の関節を1つずつ動かして確認してそろえました。");
}

// ---------- 5. 報酬関数の全体像 ----------
{
  const s = pres.addSlide(); base(s, "報酬関数の全体像（最終形）", "07");
  lead(s, "13 項目の点数を毎回足し合わせる。＋はほめる、" + MINUS + "は叱る");
  const m = (v) => MINUS + v;
  const groups = [
    ["目的を達成する", "ほめる", C.cyan, [["指令どおりの速さで進む", "+1.0"], ["指令どおりに回る", "+1.0"], ["足を浮かせてから着地する", "+2.0"]]],
    ["きれいに歩く", "叱る", C.orange, [["胴体が上下に揺れる", m("2.0")], ["胴体が傾く", m("0.5")], ["足が地面を滑る", m("0.25")], ["胴体が左右・前後に揺れる", m("0.05")], ["指令を急に変える", m("0.01")], ["力を使いすぎる", "ごく小"]]],
    ["安全に動く", "叱る", C.navy, [["足以外が地面に当たる", m("1.0")], ["関節の限界に近づく", m("1.0")], ["股の開き・ひねりがずれる", m("0.1")], ["膝の曲げ方が初期姿勢からずれる", m("0.01")]]],
  ];
  groups.forEach(([t, sub, col, items], gi) => {
    const x = 66 + gi * 390;
    R(s, x, 190, 368, 400, gi === 0 ? C.pale : C.sand, col, 1.5);
    T(s, t, x + 18, 204, 240, 32, { size: 20, bold: true, color: col });
    T(s, sub, x + 270, 206, 80, 28, { size: 14, bold: true, color: C.white, fill: col, align: "center" });
    items.forEach(([n, w], i) => {
      const y = 250 + i * 54;
      T(s, n, x + 18, y, 262, 44, { size: 15 });
      T(s, w, x + 270, y, 80, 44, { size: 17, bold: true, color: col, align: "right" });
      if (i < items.length - 1) s.addShape(pres.shapes.LINE, { x: P(x + 18), y: P(y + 48), w: P(332), h: 0, line: { color: C.line, width: 0.75 } });
    });
  });
  T(s, "転んだら（胴体が地面に触れる・大きく傾く）その回は終わり、最初からやり直し", 66, 610, 1148, 40, { size: 16, bold: true, color: C.navy, fill: C.pale, align: "center" });
  notes(s, "報酬関数は13項目の点数の合計です。ほめる項目は3つで、指令どおりの速さで進むこと、指令どおりに回ること、足をしっかり浮かせてから着地することです。叱る項目は、胴体が揺れる・傾く、足が滑る、指令をガタガタ変える、足以外が地面に当たる、関節の限界に近づく、などです。数字は重みで、項目ごとに値の大きさが違うので、数字の大小がそのまま重要度ではありません。");
}

// ---------- 6. 学習で苦労した点：立ち往生とカニ歩き ----------
{
  const s = pres.addSlide(); base(s, "学習で苦労した点：立ち往生とカニ歩き", "07");
  const cols = [
    ["立ち往生", "「進め」と指示しても、その場で立ち止まる", "・立っているだけでも速度の点が少しもらえた\n・足上げの報酬は、短く浮かせると減点。この脚の自然な歩幅では足を上げるほど損だった", "片足で立っている時間をほめる形に変えた", C.ng],
    ["カニ歩き", "まっすぐ進めと指示しても、横に流れる", "・CAD のままでは前後と左右の向きが入れ替わっていた\n・横に流れても点がほとんど減らない採点だった", "向きをそろえ、横へのずれを厳しく採点した", C.orange],
  ];
  cols.forEach(([t, sym, cause, fix, col], i) => {
    const x = 66 + i * 392;
    PH(s, x, 132, 364, 186, "動画", `${t}の動画（${sym}様子）`, { size: 13, lsize: 14 });
    T(s, t, x, 326, 364, 34, { size: 21, bold: true, color: col });
    T(s, "原因", x, 366, 60, 26, { size: 14, bold: true, color: C.white, fill: col, align: "center" });
    T(s, cause, x + 70, 364, 294, 150, { size: 14, valign: "top" });
    T(s, "対策", x, 526, 60, 26, { size: 14, bold: true, color: C.white, fill: C.ok, align: "center" });
    T(s, fix, x + 70, 524, 294, 60, { size: 14, valign: "top" });
  });
  PH(s, 850, 132, 364, 186, "動画", "改善後の動画（指示どおりまっすぐ前へ歩く様子）", { size: 13, lsize: 14 });
  T(s, "改善後", 850, 326, 364, 34, { size: 21, bold: true, color: C.ok });
  T(s, "指示どおりの方向へまっすぐ歩けるようになった", 850, 366, 364, 60, { size: 15, valign: "top" });
  A(s, 800, 225, 846, 225, C.navy, 3);
  T(s, "報酬は「こうしてほしい」と書くだけでは足りない。ロボットにとって何が得かを確かめる必要がある", 66, 606, 1148, 50, { size: 17, bold: true, color: C.navy, fill: C.sand, align: "center" });
  notes(s, "学習で一番苦労したのは、立ち往生とカニ歩きです。立ち往生は、進めと指示してもその場で立ち止まってしまう現象で、立っているだけでも速度の点が少しもらえるうえに、足上げの報酬がこの脚では足を上げるほど損をする式になっていたのが原因でした。カニ歩きは、まっすぐ進めと指示しても横に流れる現象で、CADのままでは前後と左右が入れ替わっていたことと、横に流れても点がほとんど減らない採点だったことが原因でした。向きをそろえ、横へのずれを厳しく採点し、片足で立つ時間をほめる形にしたことで、指示どおりまっすぐ歩けるようになりました。");
}

// ---------- 7. 結果：シミュレーション（動画メイン） ----------
{
  const s = pres.addSlide(); base(s, "結果：シミュレーションでは坂・でこぼこ・旋回もできた", "07");
  const cells = ["平地を前進", "坂 10°", "坂 15°", "でこぼこ 6 cm", "その場で旋回", "歩きながら旋回"];
  cells.forEach((t, i) => {
    const x = 66 + (i % 3) * 392, y = 128 + Math.floor(i / 3) * 262;
    PH(s, x, y, 364, 200, "動画", `${t}の動画（実験15の動画フォルダ videos_presentation_20260924 から）`, { size: 13, lsize: 14 });
    T(s, t, x, y + 204, 364, 40, { size: 18, bold: true, color: C.navy, align: "center" });
  });
  T(s, "どの場面でも 16 体中 1 体も転ばなかった（15 秒間・外からの押しなし）", 66, 646, 1148, 30, { size: 15, bold: true, color: C.cyan, align: "center" });
  notes(s, "シミュレーションでは、平地だけでなく10度・15度の坂、6センチのでこぼこ、その場での旋回、歩きながらの旋回まで、どの場面でも16体中1体も転ばずに動けました。（参考：前進0.5 m/s の指示で平地は15秒で6.75 m、坂10°で6.44 m、坂15°で5.83 m、でこぼこ6 cmで5.26 m〔指示0.4 m/s〕、その場旋回0.37 rad/s、歩きながら旋回0.39 rad/s〔指示0.5 rad/s〕）");
}

// ---------- 8. デプロイ ----------
{
  const s = pres.addSlide(); base(s, "デプロイ：学習した方策を実機ロボットに", "07");
  lead(s, "いきなり床で歩かせず、小さく確かめてから全身へ進める");
  const st = [["方策を書き出す", "ONNX形式で\n保存", "完了", C.ok], ["答えを確認", "学習時と同じ\n出力が出るか", "完了", C.ok], ["1台ずつ動かす", "指令どおりに\n回るか", "完了", C.ok], ["吊って全身", "10台すべてに\n方策の指令", "完了", C.ok], ["床に立たせる", "方策に任せて\n立つ・歩く", "実施中", C.orange], ["プロコン操作", "Jetson＋無線で\n好きな方向へ", "未実施", C.muted]];
  st.forEach(([t, b, stt, col], i) => {
    const x = 66 + i * 192;
    R(s, x, 190, 176, 208, stt === "完了" ? "EAF4EE" : stt === "実施中" ? C.sand : C.white, col, 1.5);
    num(s, i + 1, x + 68, 200, col, 40);
    T(s, t, x + 6, 248, 164, 36, { size: 16, bold: true, color: C.navy, align: "center" });
    T(s, b, x + 6, 288, 164, 60, { size: 13, color: C.ink, align: "center", valign: "top" });
    T(s, stt, x + 38, 356, 100, 30, { size: 14, bold: true, color: C.white, fill: col, align: "center" });
    if (i < 5) A(s, x + 178, 294, x + 190, 294, C.line, 2);
  });
  PH(s, 66, 416, 560, 244, "動画", "床の上で立っている動画。", { size: 15 });
  PH(s, 654, 416, 560, 244, "動画", "床の上で方策に任せて、歩こうとする動画。", { size: 15 });
  notes(s, "学習した方策をロボットで動かすことをデプロイと呼びます。方策を書き出し、学習時と同じ答えが出るかを確認してから、モーター1台ずつ、吊った状態で全身、と段階的に進め、今は床に立たせて方策に任せる段階です。左が床の上で立っている様子、右が方策に任せて歩こうとしている様子です。");
}

// ---------- 9. デプロイで見つかったシミュレーターとの違い ----------
{
  const s = pres.addSlide(); base(s, "デプロイで見つかった「シミュレーターとの違い」", "07");
  const rows = [
    ["見つかった違い", "どう対応したか"],
    ["一部の関節の回る向きが逆", "関節ごとの向きを表にまとめて修正"],
    ["CAD の「まっすぐ」が実は膝の曲がった姿勢（左 12°・右 7°）", "読み替えを入れて、床で立てるようになった"],
    ["モーターの摩擦がシミュレーターの 2〜3 倍", "摩擦をばらつかせて学習し直す"],
    ["シミュレーターでは毎回、空中から落として練習を始めていた", "止まって立った状態から始める練習を加える"],
    ["方策は股を内側に寄せて歩くが、実機ではそこで左右の足がぶつかる", "足どうしの衝突をシミュレーターに入れて学習し直す"],
  ];
  s.addTable(TAB(rows, 16), { x: P(66), y: P(132), w: P(1148), colW: [P(640), P(508)], rowH: P(70), border: { type: "solid", color: C.line, pt: 0.75 } });
  T(s, "上の 3 つは直した。下の 2 つが、床の上で歩き続けられない主な原因と考えている", 66, 580, 1148, 50, { size: 17, bold: true, color: C.navy, fill: C.sand, align: "center" });
  notes(s, "デプロイを進める中で、シミュレーターと実機の違いがいくつも見つかりました。関節の回る向き、CADで「まっすぐ」のつもりだった姿勢が実は膝が曲がっていたこと、モーターの摩擦などは記録データで原因を確かめて対応しました。下の2つ、シミュレーターでは毎回空中から落として練習を始めていて止まって立った状態から始めたことがないこと、そして方策が股を内側に寄せて歩くのに実機ではそこで左右の足がぶつかることが、床の上で歩き続けられない主な原因だと考えています。");
}

// ---------- 10. 結果と考察：実機 ----------
{
  const s = pres.addSlide(); base(s, "結果と考察：実機", "08");
  card(s, 66, 132, 560, 260, "EAF4EE", C.ok);
  T(s, "できたこと", 88, 144, 500, 32, { size: 20, bold: true, color: C.ok });
  T(s, [
    { text: "床の上で立てる", options: { bullet: true, breakLine: true } },
    { text: "方策に任せると、床の上で歩こうとする（最長 5 秒ほど）", options: { bullet: true, breakLine: true } },
    { text: "吊った状態なら、歩く動きがずっと続く", options: { bullet: true } },
  ], 88, 186, 520, 200, { size: 18, valign: "top", para: 10 });
  card(s, 654, 132, 560, 260, "FBEDEA", C.ng);
  T(s, "まだできていないこと", 676, 144, 500, 32, { size: 20, bold: true, color: C.ng });
  T(s, [
    { text: "床の上で歩き続けること", options: { bullet: true, breakLine: true } },
    { text: "プロコンで操作して歩くこと", options: { bullet: true } },
  ], 676, 186, 520, 200, { size: 18, valign: "top", para: 10 });
  card(s, 66, 414, 1148, 240, C.pale, C.cyan);
  T(s, "考察", 90, 426, 300, 32, { size: 20, bold: true, color: C.cyan });
  T(s, [
    { text: "吊ると歩けるのに床では続かない → 方策やプログラムではなく、足が床や相手の足に触れたときの違いが原因", options: { bullet: true, breakLine: true } },
    { text: "方策の歩き方は股を内側に寄せる。シミュレーターでは足どうしがぶつからないが、実機ではぶつかって止まる", options: { bullet: true, breakLine: true } },
    { text: "プログラム側での補正はやり尽くした。次はシミュレーターを実機に合わせて学習し直す", options: { bullet: true } },
  ], 90, 464, 1100, 184, { size: 17, valign: "top", para: 8 });
  notes(s, "実機の結果です。床の上で立つことができ、方策に任せると床の上で歩こうとする動きが出るようになりました。吊った状態なら歩く動きがずっと続きます。ただ、床の上で歩き続けることはまだできていません。吊ると歩けるのに床では続かないので、方策やプログラムではなく、足が床や相手の足に触れたときの違いが原因と考えています。実際、方策の歩き方は股を内側に寄せるのですが、実機ではそこで左右の足がぶつかって止まっていました。プログラム側での補正はやり尽くしたので、次はシミュレーターを実機に合わせて学習し直します。");
}

// ---------- 11. 今後の展望 ----------
{
  const s = pres.addSlide(); base(s, "今後の展望", "08");
  const st = [
    ["平地で歩かせる", "足どうしの衝突・立った状態からの開始をシミュレーターに入れて学習し直す", C.orange],
    ["坂・でこぼこでも歩かせる", "シミュレーションではできているので、実機でも", C.cyan],
    ["プロコンで操作する", "好きな方向へ歩かせ、災害現場のような場所へ", C.navy],
  ];
  st.forEach(([t, b, col], i) => {
    const y = 150 + i * 150;
    num(s, i + 1, 90, y + 32, col, 56);
    R(s, 170, y, 1044, 120, i === 0 ? C.sand : C.white, col, 2, { radius: 0.06 });
    T(s, t, 196, y + 12, 980, 44, { size: 24, bold: true, color: C.navy });
    T(s, b, 196, y + 62, 980, 44, { size: 17, color: C.ink });
    if (i < 2) A(s, 118, y + 92, 118, y + 178, C.line, 2.5);
  });
  notes(s, "今後の展望です。まずは平地で歩かせることが目標で、そのために足どうしの衝突や、止まって立った状態から始めることをシミュレーターに入れて学習し直します。そのうえで、シミュレーションではできている坂やでこぼこでも実機で歩けるようにし、最後はプロコンで好きな方向に歩かせることを目指します。");
}

// ---------- まとめ（差し替え案） ----------
{
  const s = pres.addSlide(); base(s, "まとめ・今後の展望", "あと");
  T(s, "二足歩行ロボットの移動基盤を、3つの担当から形にした", 66, 150, 1148, 50, { size: 26, bold: true, color: C.navy });
  const e = [["設計", "足裏の接地と重心配置を起点に脚構造を考えた", C.orange], ["配線", "電源とCAN通信を分け、確認しやすい経路を整理した", C.blue], ["制御", "シミュレーションで坂・旋回まで歩ける方策を作り、実機で立つ・歩こうとするところまで進めた", C.cyan]];
  e.forEach(([t, b, col], i) => { const y = 250 + i * 100; T(s, t, 140, y, 150, 56, { size: 22, bold: true, color: C.white, fill: col, align: "center" }); T(s, b, 320, y, 860, 56, { size: 19 }); });
  T(s, "次の段階：実機で平地を歩かせ、坂・でこぼこへ広げる", 110, 590, 1060, 50, { size: 19, bold: true, color: C.navy, fill: C.sand, align: "center" });
  notes(s, "【差し替え案】元のまとめの制御の行と、次の段階の文言を更新したもの。設計・配線の行は元のまま。");
}

pres.writeFile({ fileName: "./制御パート_ver3.pptx" }).then((f) => console.log("wrote", f));
