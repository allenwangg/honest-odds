const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";           // 13.3 x 7.5
pres.author = "Allen Wang";
pres.title = "Pythia — the options chain is a prediction market";

// palette
const INK = "12161B", PANEL = "1A2027", LINE = "2A323B";
const PARCH = "E7E1D3", FADED = "8B94A0", GOLD = "CBA84C", SLATE = "7C93A6";
const GAIN = "7BA886", LOSS = "C0655A";
const SERIF = "Bookman Old Style", SANS = "Calibri", MONO = "Courier New";

const W = 13.3, H = 7.5, M = 0.75;

function darkSlide() {
  const s = pres.addSlide();
  s.background = { color: INK };
  return s;
}
function title(s, text, y = 0.55) {
  s.addText(text, { x: M, y, w: W - 2 * M, h: 0.9, isTextBox: true, margin: 0,
    fontFace: SERIF, fontSize: 40, bold: true, color: PARCH });
}
function kicker(s, text, y = 1.42) {
  s.addText(text, { x: M, y, w: W - 2 * M, h: 0.4, isTextBox: true, margin: 0,
    fontFace: MONO, fontSize: 15, color: GOLD });
}
function card(s, x, y, w, h) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.06,
    fill: { color: PANEL }, line: { color: LINE, width: 1 } });
}
function footer(s, text) {
  s.addText(text, { x: M, y: H - 0.62, w: W - 2 * M, h: 0.3, isTextBox: true, margin: 0,
    fontFace: MONO, fontSize: 10, color: LINE });
}

/* 1 — title */
{
  const s = darkSlide();
  s.addText("PYTHIA", { x: M, y: 2.35, w: 8, h: 1.5, isTextBox: true, margin: 0,
    fontFace: SERIF, fontSize: 88, bold: true, color: PARCH, charSpacing: 2 });
  s.addText("the options chain is a prediction market", {
    x: M, y: 3.85, w: 10, h: 0.6, isTextBox: true, margin: 0,
    fontFace: MONO, fontSize: 24, color: GOLD });
  s.addShape(pres.ShapeType.line, { x: M, y: 4.75, w: 5.2, h: 0,
    line: { color: LINE, width: 1.5 } });
  s.addText("An AI agent that reads market-implied probabilities off the\noptions chain and trades the disagreements — behind eight risk gates.", {
    x: M, y: 4.95, w: 9, h: 0.9, isTextBox: true, margin: 0,
    fontFace: SANS, fontSize: 15, color: FADED, lineSpacing: 22 });
  footer(s, "Alpaca AI Trading Agents Hackathon  ·  Options Alpha Agents  ·  built solo  ·  Aug 28 – Sep 4 2026");
  s.addNotes("Open on the thesis, not the tech. Every option price is a probability in disguise.");
}

/* 2 — the hidden number */
{
  const s = darkSlide();
  title(s, "Every option price is a probability");
  kicker(s, "the number is already there — nobody publishes it");

  card(s, M, 2.3, 5.6, 3.6);
  s.addText("A bet that pays $1 if SPY\ncloses above 505 on Friday", {
    x: M + 0.4, y: 2.7, w: 4.8, h: 0.9, isTextBox: true, margin: 0,
    fontFace: SANS, fontSize: 17, color: PARCH, lineSpacing: 26 });
  s.addText("trades at", { x: M + 0.4, y: 3.65, w: 4.8, h: 0.3, isTextBox: true,
    margin: 0, fontFace: SANS, fontSize: 13, color: FADED });
  s.addText("$0.31", { x: M + 0.4, y: 3.95, w: 4.8, h: 1.1, isTextBox: true, margin: 0,
    fontFace: SERIF, fontSize: 62, bold: true, color: GOLD });

  card(s, M + 6.1, 2.3, 5.6, 3.6);
  s.addText("So the market believes", { x: M + 6.5, y: 2.7, w: 4.8, h: 0.4,
    isTextBox: true, margin: 0, fontFace: SANS, fontSize: 13, color: FADED });
  s.addText("31%", { x: M + 6.5, y: 3.1, w: 4.8, h: 1.3, isTextBox: true, margin: 0,
    fontFace: SERIF, fontSize: 76, bold: true, color: PARCH });
  s.addText("Price and probability are the same\nnumber wearing a different hat.", {
    x: M + 6.5, y: 4.5, w: 4.8, h: 0.9, isTextBox: true, margin: 0,
    fontFace: SANS, fontSize: 15, color: FADED, lineSpacing: 24 });
  footer(s, "a tight call spread around K is a digital contract on 'S above K'");
  s.addNotes("This is the whole insight. Spend time here.");
}

/* 3 — the curve (native chart) */
{
  const s = darkSlide();
  title(s, "Do it at every strike, and you get the whole curve");
  kicker(s, "the market's complete probability distribution for Friday's close");

  const ks = [], ps = [];
  const S = 500, T = 3 / 252, V = 0.18;
  const ncdf = x => 0.5 * (1 + erf(x / Math.SQRT2));
  function erf(x) { // Abramowitz-Stegun
    const t = 1 / (1 + 0.3275911 * Math.abs(x));
    const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t
      - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
    return x >= 0 ? y : -y;
  }
  for (let k = 488; k <= 512; k += 1) {
    ks.push(String(k));
    ps.push(+(ncdf((Math.log(S / k) - V * V / 2 * T) / (V * Math.sqrt(T))) * 100).toFixed(1));
  }
  s.addChart(pres.ChartType.line,
    [{ name: "P(close above K)", labels: ks, values: ps }],
    { x: M, y: 2.15, w: W - 2 * M, h: 4.0,
      chartColors: [GOLD], lineSize: 4, lineSmooth: true, showLegend: false,
      showTitle: false, catAxisLabelColor: FADED, valAxisLabelColor: FADED,
      catAxisLabelFontSize: 10, valAxisLabelFontSize: 11,
      catAxisLabelFontFace: MONO, valAxisLabelFontFace: MONO,
      valAxisMaxVal: 100, valAxisMinVal: 0,
      valGridLine: { color: LINE, size: 1 }, catGridLine: { style: "none" },
      plotArea: { fill: { color: INK } }, chartArea: { fill: { color: INK } } });
  footer(s, "−∂C/∂K = Q(S_T > K).  Breeden–Litzenberger, 1978.  Free, live, and almost nobody looks at it.");
  s.addNotes("Formal name-drop once. The math is 1970s vintage on purpose.");
}

/* 4 — the disagreement */
{
  const s = darkSlide();
  title(s, "The trade is the disagreement");
  kicker(s, "market probability vs. model probability, on the same event");

  s.addChart(pres.ChartType.bar,
    [{ name: "market", labels: ["SPY > 505", "QQQ > 480", "NVDA > 200"], values: [31, 62, 44] },
     { name: "Pythia", labels: ["SPY > 505", "QQQ > 480", "NVDA > 200"], values: [44, 55, 58] }],
    { x: M, y: 2.2, w: 7.4, h: 3.9, barDir: "col", barGrouping: "clustered",
      chartColors: [SLATE, GOLD], showLegend: true, legendPos: "t",
      legendColor: FADED, legendFontFace: MONO, legendFontSize: 11,
      showValue: true, dataLabelPosition: "outEnd", dataLabelColor: PARCH,
      dataLabelFontFace: MONO, dataLabelFontSize: 11,
      catAxisLabelColor: FADED, valAxisLabelColor: FADED,
      catAxisLabelFontFace: MONO, valAxisLabelFontFace: MONO,
      catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
      valAxisMaxVal: 100, valAxisMinVal: 0,
      valGridLine: { color: LINE, size: 1 }, catGridLine: { style: "none" },
      plotArea: { fill: { color: INK } }, chartArea: { fill: { color: INK } } });

  card(s, 8.55, 2.2, 4.0, 3.9);
  s.addText("+13", { x: 8.9, y: 2.5, w: 3.3, h: 1.1, isTextBox: true, margin: 0,
    fontFace: SERIF, fontSize: 60, bold: true, color: GOLD });
  s.addText("points of edge", { x: 8.9, y: 3.55, w: 3.3, h: 0.35, isTextBox: true,
    margin: 0, fontFace: MONO, fontSize: 13, color: FADED });
  s.addText([
    { text: "Trade only when the gap clears a threshold and the model's confidence clears a floor.", options: { breakLine: true } },
    { text: "Size ∝ edge × confidence, hard-capped. Fractional Kelly under model uncertainty.", options: {} },
  ], { x: 8.9, y: 4.1, w: 3.3, h: 1.7, isTextBox: true, margin: 0,
    fontFace: SANS, fontSize: 13, color: PARCH, lineSpacing: 20 });
  footer(s, "most of the day they agree — and the correct action is to do nothing");
}

/* 5 — architecture */
{
  const s = darkSlide();
  title(s, "How a cycle works");
  kicker(s, "every 15 minutes during market hours");

  const steps = [
    ["1", "READ", "Pull the chain from Alpaca.\nCompute −∂C/∂K across strikes.\nCross-check against puts."],
    ["2", "THINK", "Claude estimates the same\nprobabilities independently.\nMarket's number is the prior."],
    ["3", "GATE", "Eight hard rules. Defined risk,\nbudget, heat, breaker, liquidity,\nkill file, concentration, sanity."],
    ["4", "ACT", "Multi-leg limit order at net\ndebit. Journal the reasoning.\nBank winners automatically."],
  ];
  let x = M;
  const cw = (W - 2 * M - 0.9) / 4;
  steps.forEach(([n, head, body]) => {
    card(s, x, 2.2, cw, 3.9);
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.35, y: 2.55, w: 0.62, h: 0.62,
      fill: { color: GOLD } });
    s.addText(n, { x: x + 0.35, y: 2.61, w: 0.62, h: 0.5, isTextBox: true, margin: 0,
      align: "center", fontFace: SERIF, fontSize: 22, bold: true, color: INK });
    s.addText(head, { x: x + 0.35, y: 3.35, w: cw - 0.7, h: 0.45, isTextBox: true,
      margin: 0, fontFace: MONO, fontSize: 17, bold: true, color: PARCH });
    s.addText(body, { x: x + 0.35, y: 3.85, w: cw - 0.7, h: 2.0, isTextBox: true,
      margin: 0, fontFace: SANS, fontSize: 12.5, color: FADED, lineSpacing: 19 });
    x += cw + 0.3;
  });
  footer(s, "chain → implied curve → assessment → divergence → structure → gates → execution → journal");
}

/* 6 — the gates */
{
  const s = darkSlide();
  title(s, "Eight gates, none of them intelligent");
  kicker(s, "the model can be wrong — these cannot be argued with");

  const gates = [
    ["G1", "Defined risk only", "net debit, bounded loss, never a naked short"],
    ["G2", "Per-trade budget", "max loss ≤ a fixed slice of equity"],
    ["G3", "Portfolio heat", "ceiling on total open exposure"],
    ["G4", "Circuit breaker", "a bad enough day halts new entries"],
    ["G5", "Liquidity", "real bids, spread within tolerance"],
    ["G6", "Kill switch", "a file named KILL stops everything"],
    ["G7", "Concentration", "SPY and QQQ share one correlated bucket"],
    ["G8", "Sanity", "edge must survive the actual fill price"],
  ];
  let gy = 2.15;
  gates.forEach(([id, name, desc], i) => {
    const gx = i < 4 ? M : M + 6.15;
    if (i === 4) gy = 2.15;
    card(s, gx, gy, 5.65, 1.0);
    s.addText(id, { x: gx + 0.28, y: gy + 0.28, w: 0.62, h: 0.45, isTextBox: true,
      margin: 0, fontFace: MONO, fontSize: 17, bold: true, color: GOLD });
    s.addText(name, { x: gx + 1.0, y: gy + 0.16, w: 4.4, h: 0.36, isTextBox: true,
      margin: 0, fontFace: SANS, fontSize: 15, bold: true, color: PARCH });
    s.addText(desc, { x: gx + 1.0, y: gy + 0.52, w: 4.4, h: 0.34, isTextBox: true,
      margin: 0, fontFace: SANS, fontSize: 12, color: FADED });
    gy += 1.12;
  });
  footer(s, "all eight in pythia/risk.py · all eight exercised by tests/test_risk.py");
  s.addNotes("The unglamorous slide that decides whether a judge trusts the rest.");
}

/* 7 — stale data */
{
  const s = darkSlide();
  title(s, "The trap: stale quotes manufacture fake edges");
  kicker(s, "put–call parity as a lie detector");

  card(s, M, 2.3, 5.6, 3.5);
  s.addText("On any live chain", { x: M + 0.4, y: 2.65, w: 4.8, h: 0.35,
    isTextBox: true, margin: 0, fontFace: SANS, fontSize: 13, color: FADED });
  s.addText("C − P = S − K", { x: M + 0.4, y: 3.05, w: 4.8, h: 0.9, isTextBox: true,
    margin: 0, fontFace: MONO, fontSize: 34, bold: true, color: PARCH });
  s.addText("holds to within pennies for short-dated\ncontracts. It is arbitrage, not a model.", {
    x: M + 0.4, y: 4.0, w: 4.8, h: 0.8, isTextBox: true, margin: 0,
    fontFace: SANS, fontSize: 14, color: FADED, lineSpacing: 22 });

  card(s, M + 6.1, 2.3, 5.6, 3.5);
  s.addText("When it breaks by dollars", { x: M + 6.5, y: 2.65, w: 4.8, h: 0.35,
    isTextBox: true, margin: 0, fontFace: SANS, fontSize: 13, color: FADED });
  s.addText("the chain is lying", { x: M + 6.5, y: 3.05, w: 4.8, h: 0.7, isTextBox: true,
    margin: 0, fontFace: SERIF, fontSize: 30, bold: true, color: LOSS });
  s.addText("Pythia measures the median parity residual\nevery cycle and refuses to trade any symbol\nthat fails it. A naive agent 'arbitrages'\nphantoms all day and never knows.", {
    x: M + 6.5, y: 3.85, w: 4.8, h: 1.5, isTextBox: true, margin: 0,
    fontFace: SANS, fontSize: 13.5, color: PARCH, lineSpacing: 20 });
  footer(s, "clean chain residual: $0.00   ·   corrupted chain: flagged instantly (tests/test_implied.py)");
}

/* 8 — calibration */
{
  const s = darkSlide();
  title(s, "Every forecast gets graded");
  kicker(s, "Brier score — a rule you cannot game by hedging");

  s.addText([
    { text: "A proper scoring rule is uniquely minimized by reporting what you actually believe. ", options: { breakLine: true } },
    { text: "So the agent's own confidence becomes an empirical quantity instead of a mood.", options: {} },
  ], { x: M, y: 2.2, w: 6.6, h: 1.2, isTextBox: true, margin: 0,
    fontFace: SANS, fontSize: 16, color: PARCH, lineSpacing: 26 });

  card(s, M, 3.6, 3.15, 2.3);
  s.addText("PYTHIA", { x: M + 0.3, y: 3.85, w: 2.6, h: 0.35, isTextBox: true,
    margin: 0, fontFace: MONO, fontSize: 13, color: GOLD });
  s.addText("{B1}", { x: M + 0.3, y: 4.2, w: 2.6, h: 1.0, isTextBox: true, margin: 0,
    fontFace: SERIF, fontSize: 54, bold: true, color: PARCH });
  s.addText("Brier score", { x: M + 0.3, y: 5.25, w: 2.6, h: 0.3, isTextBox: true,
    margin: 0, fontFace: SANS, fontSize: 12, color: FADED });

  card(s, M + 3.45, 3.6, 3.15, 2.3);
  s.addText("MARKET", { x: M + 3.75, y: 3.85, w: 2.6, h: 0.35, isTextBox: true,
    margin: 0, fontFace: MONO, fontSize: 13, color: SLATE });
  s.addText("{B2}", { x: M + 3.75, y: 4.2, w: 2.6, h: 1.0, isTextBox: true, margin: 0,
    fontFace: SERIF, fontSize: 54, bold: true, color: PARCH });
  s.addText("same events", { x: M + 3.75, y: 5.25, w: 2.6, h: 0.3, isTextBox: true,
    margin: 0, fontFace: SANS, fontSize: 12, color: FADED });

  card(s, 8.0, 2.2, 4.55, 3.7);
  s.addText("The feedback loop", { x: 8.35, y: 2.5, w: 3.9, h: 0.4, isTextBox: true,
    margin: 0, fontFace: SANS, fontSize: 16, bold: true, color: PARCH });
  s.addText([
    { text: "Journal every forecast, resolved or not", options: { bullet: true, breakLine: true } },
    { text: "Grade against the actual close", options: { bullet: true, breakLine: true } },
    { text: "Grid-search the shrinkage λ that scores best", options: { bullet: true, breakLine: true } },
    { text: "Feed λ back into config as edge_shrinkage", options: { bullet: true, breakLine: true } },
    { text: "Overconfidence gets pulled toward the market", options: { bullet: true } },
  ], { x: 8.35, y: 3.0, w: 3.9, h: 2.6, isTextBox: true, margin: 0,
    fontFace: SANS, fontSize: 13, color: FADED, paraSpaceAfter: 8 });
  footer(s, "scripts/calibrate.py — blocked and dry-run decisions are graded too, so the brain scores even when the hands were tied");
}

/* 9 — infrastructure */
{
  const s = darkSlide();
  title(s, "Alpaca infrastructure");
  kicker(s, "autonomy on the API, judgment over MCP");

  const cols = [
    ["EXECUTION", "Trading API", "Atomic multi-leg (MLEG) limit orders at\nnet debit. Deterministic client order ids,\nso a restart cannot double-enter.\nAuto-retry on price-increment rejects."],
    ["DATA", "Options + stock feeds", "Chain snapshots with quotes, IV and greeks.\nBars and last trades for context.\nIndicative feed — free on paper."],
    ["SUPERVISION", "MCP server", "Claude connected to the same account.\n\"Close the SPY spread — I disagree with\ntoday's thesis.\" Human override in words."],
  ];
  let cx = M;
  const cw = (W - 2 * M - 0.6) / 3;
  cols.forEach(([tag, head, body]) => {
    card(s, cx, 2.2, cw, 3.85);
    s.addText(tag, { x: cx + 0.35, y: 2.5, w: cw - 0.7, h: 0.3, isTextBox: true,
      margin: 0, fontFace: MONO, fontSize: 11, color: GOLD, charSpacing: 2 });
    s.addText(head, { x: cx + 0.35, y: 2.85, w: cw - 0.7, h: 0.5, isTextBox: true,
      margin: 0, fontFace: SANS, fontSize: 19, bold: true, color: PARCH });
    s.addText(body, { x: cx + 0.35, y: 3.45, w: cw - 0.7, h: 2.3, isTextBox: true,
      margin: 0, fontFace: SANS, fontSize: 13, color: FADED, lineSpacing: 20 });
    cx += cw + 0.3;
  });
  footer(s, "paper trading only by construction — the client is hard-coded paper=True and there is no live code path");
}

/* 10 — results */
{
  const s = darkSlide();
  title(s, "Results");
  kicker(s, "fill these from scripts/snapshot.py before submitting");

  const stats = [
    ["{Z}", "final equity", GOLD],
    ["{P}", "return on $100k", GAIN],
    ["{N}", "trades placed", PARCH],
    ["{G}", "orders blocked by gates", SLATE],
  ];
  let sx = M;
  const sw = (W - 2 * M - 0.9) / 4;
  stats.forEach(([big, label, col]) => {
    card(s, sx, 2.3, sw, 2.1);
    s.addText(big, { x: sx + 0.3, y: 2.6, w: sw - 0.6, h: 1.0, isTextBox: true,
      margin: 0, fontFace: SERIF, fontSize: 48, bold: true, color: col });
    s.addText(label, { x: sx + 0.3, y: 3.65, w: sw - 0.6, h: 0.4, isTextBox: true,
      margin: 0, fontFace: SANS, fontSize: 12.5, color: FADED });
    sx += sw + 0.3;
  });

  s.addChart(pres.ChartType.line,
    [{ name: "equity", labels: ["Mon", "Tue", "Wed", "Thu", "Fri"],
       values: [100000, 100000, 100000, 100000, 100000] }],
    { x: M, y: 4.65, w: W - 2 * M, h: 2.0,
      chartColors: [GOLD], lineSize: 3, showLegend: false, showTitle: false,
      catAxisLabelColor: FADED, valAxisLabelColor: FADED,
      catAxisLabelFontFace: MONO, valAxisLabelFontFace: MONO,
      catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
      valGridLine: { color: LINE, size: 1 }, catGridLine: { style: "none" },
      plotArea: { fill: { color: INK } }, chartArea: { fill: { color: INK } } });
  footer(s, "replace the placeholder series with your real equity curve from journal/equity.jsonl");
  s.addNotes("Do not ship this slide with braces still in it.");
}

/* 11 — what makes it different */
{
  const s = darkSlide();
  title(s, "What makes this different");
  kicker(s, "four things most agents in this field will not have");

  const rows = [
    ["A thesis, not a heuristic", "Probability arbitrage between the market's measure and the model's — with the math mapped to the module that implements it."],
    ["Gates with no intelligence in them", "Eight ruin constraints that cannot be reasoned with, tested independently of the strategy."],
    ["A lie detector for its own data", "Put–call parity checked every cycle; a stale chain is refused rather than traded."],
    ["Forecasts that get graded", "Brier-scored against the market on resolved events, feeding a shrinkage term back into sizing."],
  ];
  let ry = 2.2;
  rows.forEach(([head, body], i) => {
    s.addShape(pres.ShapeType.ellipse, { x: M, y: ry + 0.08, w: 0.44, h: 0.44,
      fill: { color: PANEL }, line: { color: GOLD, width: 1.5 } });
    s.addText(String(i + 1), { x: M, y: ry + 0.13, w: 0.44, h: 0.36, isTextBox: true,
      margin: 0, align: "center", fontFace: MONO, fontSize: 14, bold: true, color: GOLD });
    s.addText(head, { x: M + 0.75, y: ry, w: 11.2, h: 0.4, isTextBox: true, margin: 0,
      fontFace: SANS, fontSize: 18, bold: true, color: PARCH });
    s.addText(body, { x: M + 0.75, y: ry + 0.42, w: 11.2, h: 0.55, isTextBox: true,
      margin: 0, fontFace: SANS, fontSize: 13.5, color: FADED, lineSpacing: 19 });
    ry += 1.15;
  });
  footer(s, "the novelty is the estimator and the verification loop — the calculus is 1970s vintage on purpose");
}

/* 12 — close */
{
  const s = darkSlide();
  s.addText("The chain talks.", { x: M, y: 2.5, w: 11, h: 0.95, isTextBox: true,
    margin: 0, fontFace: SERIF, fontSize: 52, bold: true, color: PARCH });
  s.addText("Pythia listens, disagrees carefully,\nand writes everything down.", {
    x: M, y: 3.5, w: 11, h: 1.5, isTextBox: true, margin: 0,
    fontFace: SERIF, fontSize: 52, bold: true, color: GOLD, lineSpacing: 62 });
  s.addShape(pres.ShapeType.line, { x: M, y: 5.35, w: 5.2, h: 0,
    line: { color: LINE, width: 1.5 } });
  s.addText("github.com/allenwangg/pythia   ·   built solo   ·   paper trading only", {
    x: M, y: 5.6, w: 11, h: 0.4, isTextBox: true, margin: 0,
    fontFace: MONO, fontSize: 14, color: FADED });
  s.addNotes("End on the line, not on a thank-you slide.");
}

pres.writeFile({ fileName: "/home/claude/pythia/video/pythia-deck.pptx" })
  .then(f => console.log("wrote", f));
