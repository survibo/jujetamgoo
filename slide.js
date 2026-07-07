/* ══════════════════ Viewport scaling ══════════════════ */

function scaleViewport() {
  const vp = document.getElementById("slide-viewport");
  const scale = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
  const ox = (window.innerWidth - 1920 * scale) / 2;
  const oy = (window.innerHeight - 1080 * scale) / 2;
  vp.style.transform = `scale(${scale})`;
  vp.style.position = "absolute";
  vp.style.left = `${ox}px`;
  vp.style.top = `${oy}px`;
}
window.addEventListener("resize", scaleViewport);
scaleViewport();

/* ══════════════════ Navigation ══════════════════ */

const TOTAL = 11;
let current = 1;

function showSlide(n) {
  document.getElementById(`slide-${current}`).classList.remove("active");
  current = Math.max(1, Math.min(TOTAL, n));
  if (current === 3) popupDone = false; // 슬라이드 3에 다시 들어오면 팝업 재장전
  document.getElementById(`slide-${current}`).classList.add("active");
  document.getElementById(
    "slide-counter"
  ).textContent = `${current} / ${TOTAL}`;
  document.getElementById("btn-prev").disabled = current === 1;
  document.getElementById("btn-next").disabled = current === TOTAL;
}

function navigate(dir) {
  if (handlePopupNav(dir)) return; // 슬라이드 3의 예비 실험 팝업이 키를 소비
  showSlide(current + dir);
}

document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowRight" || e.key === "ArrowDown") navigate(1);
  if (e.key === "ArrowLeft" || e.key === "ArrowUp") navigate(-1);
  if (e.key === "Escape") closePopup(true);
  if ((e.key === "r" || e.key === "R") && current === 3) openPopup(1);
});
document
  .getElementById("btn-prev")
  .addEventListener("click", () => navigate(-1));
document
  .getElementById("btn-next")
  .addEventListener("click", () => navigate(1));

/* ══════════════════ Graph class (design.md canonical) ══════════════════ */

class Graph {
  constructor(id, { xMin, xMax, yMin, yMax }) {
    this.canvas = document.getElementById(id);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext("2d");
    this.W = this.canvas.width;
    this.H = this.canvas.height;
    this.xMin = xMin;
    this.xMax = xMax;
    this.yMin = yMin;
    this.yMax = yMax;
  }

  wx(x) {
    return ((x - this.xMin) / (this.xMax - this.xMin)) * this.W;
  }
  wy(y) {
    return ((this.yMax - y) / (this.yMax - this.yMin)) * this.H;
  }

  clear(bg = "#ffffff") {
    const { ctx, W, H } = this;
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);
  }

  drawGrid(stepX = 1, stepY = 1) {
    const { ctx, W, H } = this;
    ctx.beginPath();
    ctx.strokeStyle = "#ebebed";
    ctx.lineWidth = 1;
    for (let x = Math.floor(this.xMin); x <= this.xMax + 0.01; x += stepX) {
      const cx = this.wx(x);
      ctx.moveTo(cx, 0);
      ctx.lineTo(cx, H);
    }
    for (let y = Math.floor(this.yMin); y <= this.yMax + 0.01; y += stepY) {
      const cy = this.wy(y);
      ctx.moveTo(0, cy);
      ctx.lineTo(W, cy);
    }
    ctx.stroke();
  }

  drawAxes(color = "#bbb") {
    const { ctx, W, H } = this;
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    if (this.yMin <= 0 && this.yMax >= 0) {
      ctx.moveTo(0, this.wy(0));
      ctx.lineTo(W, this.wy(0));
    }
    if (this.xMin <= 0 && this.xMax >= 0) {
      ctx.moveTo(this.wx(0), 0);
      ctx.lineTo(this.wx(0), H);
    }
    ctx.stroke();
  }

  drawCurve(f, color, lw = 2.5, steps = 800) {
    const { ctx } = this;
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = lw;
    let pen = false;
    for (let i = 0; i <= steps; i++) {
      const x = this.xMin + ((this.xMax - this.xMin) * i) / steps;
      const y = f(x);
      const ok = isFinite(y) && y >= this.yMin - 0.8 && y <= this.yMax + 0.8;
      if (!ok) {
        pen = false;
        continue;
      }
      const cx = this.wx(x),
        cy = this.wy(y);
      pen ? ctx.lineTo(cx, cy) : (ctx.moveTo(cx, cy), (pen = true));
    }
    ctx.stroke();
  }

  drawDash(f, color, lw = 2) {
    this.ctx.setLineDash([12, 8]);
    this.drawCurve(f, color, lw);
    this.ctx.setLineDash([]);
  }

  dot(x, y, color, r = 7) {
    const { ctx } = this;
    ctx.beginPath();
    ctx.arc(this.wx(x), this.wy(y), r, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 2.5;
    ctx.stroke();
  }

  text(x, y, str, color = "#333", dx = 10, dy = -10, size = 18) {
    const { ctx } = this;
    ctx.fillStyle = color;
    ctx.font = `${size}px "IBM Plex Sans KR","IBM Plex Sans",sans-serif`;
    ctx.textAlign = "left";
    ctx.fillText(str, this.wx(x) + dx, this.wy(y) + dy);
  }

  ticksX(vals, labelFn, dy = 22, size = 18) {
    const { ctx } = this;
    ctx.fillStyle = "#999";
    ctx.font = `${size}px "IBM Plex Sans",sans-serif`;
    ctx.textAlign = "center";
    for (const v of vals) ctx.fillText(labelFn(v), this.wx(v), this.wy(0) + dy);
  }

  ticksY(vals, labelFn, dx = -8, size = 18) {
    const { ctx } = this;
    ctx.fillStyle = "#999";
    ctx.font = `${size}px "IBM Plex Sans",sans-serif`;
    ctx.textAlign = "right";
    for (const v of vals)
      ctx.fillText(labelFn(v), this.wx(0) + dx, this.wy(v) + 6);
  }
}

/* Extension: annotation helpers built on Graph (keeps all canvas work in one class family) */
class AnnotatedGraph extends Graph {
  vline(x, color = "#bbb", lw = 1.5, dash = [10, 8]) {
    const { ctx } = this;
    ctx.save();
    ctx.setLineDash(dash);
    ctx.strokeStyle = color;
    ctx.lineWidth = lw;
    ctx.beginPath();
    ctx.moveTo(this.wx(x), 0);
    ctx.lineTo(this.wx(x), this.H);
    ctx.stroke();
    ctx.restore();
  }

  // Horizontal double-headed arrow between (x1, y) and (x2, y)
  gapArrow(x1, x2, y, color = "#6e6e73", lw = 2.5) {
    const { ctx } = this;
    const cy = this.wy(y),
      a = this.wx(x1),
      b = this.wx(x2),
      h = 9;
    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = lw;
    ctx.beginPath();
    ctx.moveTo(a, cy);
    ctx.lineTo(b, cy);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(a, cy);
    ctx.lineTo(a + h * 1.6, cy - h);
    ctx.lineTo(a + h * 1.6, cy + h);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(b, cy);
    ctx.lineTo(b - h * 1.6, cy - h);
    ctx.lineTo(b - h * 1.6, cy + h);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  centeredText(x, y, str, color = "#333", size = 20, weight = 600) {
    const { ctx } = this;
    ctx.save();
    ctx.fillStyle = color;
    ctx.font = `${weight} ${size}px "IBM Plex Sans KR","IBM Plex Sans",sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(str, this.wx(x), this.wy(y));
    ctx.restore();
  }
}

/* ══════════════════ 예비 실험 실측 데이터 (grokking_data.js) ══════════════════ */

const HAS_GROK_DATA =
  typeof GROK_METRICS !== "undefined" && typeof GROK_META !== "undefined";
const ACC_XMAX = 5000; // 차트는 0~5k만 표시 (이후 20k까지 양쪽 모두 100% 유지)

// GROK_METRICS 행: [step, train_loss, train_acc, val_loss, val_acc]
function seriesInterp(colIdx, maxStep) {
  const rows = GROK_METRICS;
  return (x) => {
    if (x < rows[0][0] || x > maxStep || x > ACC_XMAX) return NaN;
    for (let i = 1; i < rows.length; i++) {
      if (rows[i][0] >= x) {
        const s0 = rows[i - 1][0],
          s1 = rows[i][0];
        const t = (x - s0) / (s1 - s0);
        return (
          rows[i - 1][colIdx] + t * (rows[i][colIdx] - rows[i - 1][colIdx])
        );
      }
    }
    return rows[rows.length - 1][colIdx];
  };
}

// 실측 정확도 곡선 렌더러 — 슬라이드 3 정적 차트와 팝업 2단계가 공유
function renderAccChart(canvasId, uptoStep, withAnnotations) {
  const g = new AnnotatedGraph(canvasId, {
    xMin: -160,
    xMax: 5320,
    yMin: -0.16,
    yMax: 1.14,
  });
  if (!g.canvas) return null;
  g.clear();
  g.drawGrid(1000, 0.25);
  g.drawAxes("#bbb");
  g.drawCurve(seriesInterp(2, uptoStep), "#0066cc", 4);
  g.drawCurve(seriesInterp(4, uptoStep), "#c0392b", 4);
  g.ticksX(
    [0, 1000, 2000, 3000, 4000, 5000],
    (v) => (v === 0 ? "0" : `${v / 1000}k`),
    30,
    19
  );
  g.text(0, 1.02, "정확도", "#999", 8, 4, 20);
  g.centeredText(4750, -0.135, "학습 step", "#999", 20, 400);

  if (withAnnotations) {
    const tT = GROK_META.tTrain,
      tV = GROK_META.tVal;
    g.vline(tT, "#bbb");
    g.vline(tV, "#bbb");
    g.gapArrow(tT, tV, 0.56);
    g.centeredText(
      (tT + tV) / 2,
      0.63,
      `Grokking gap = ${GROK_META.gap.toLocaleString()} steps`,
      "#1d1d1f",
      25,
      600
    );
    g.text(tT, 1.08, `암기 완료 (step ${tT})`, "#0066cc", 12, 0, 21);
    g.centeredText(
      tV,
      1.08,
      `일반화 (step ${tV.toLocaleString()})`,
      "#c0392b",
      21,
      600
    );
    g.centeredText(1450, 0.9, "훈련 정확도 100%", "#0066cc", 21, 400);
    g.centeredText(1075, 0.11, "검증 정확도는 바닥", "#c0392b", 21, 400);
    g.centeredText(
      4100,
      0.5,
      "이후 20,000 스텝까지 100% 유지",
      "#6e6e73",
      20,
      400
    );
  }
  return g;
}

/* ══════════════════ Slide 3: Grokking 개념 모식도 ══════════════════ */
/* 정적 차트는 이상적인 곡선으로 개념을 설명하고,
   실측 데이터는 팝업(예비 실험)에서 공개하는 흐름 */

function drawGrokkingGraph() {
  const g = new AnnotatedGraph("canvas-grokking", {
    xMin: -2.5,
    xMax: 53,
    yMin: -0.16,
    yMax: 1.14,
  });
  if (!g.canvas) return;

  const sig = (x, x0, k) => 1 / (1 + Math.exp(-k * (x - x0)));
  const clamp = (f) => (x) => x < 0 || x > 50 ? NaN : f(x);
  const trainAcc = clamp((x) => sig(x, 1.1, 4.2)); // 초기에 급격히 포화
  const valAcc = clamp((x) => 0.04 + 0.96 * sig(x, 40, 0.85)); // 오래 바닥, 그리고 급상승

  g.clear();
  g.drawGrid(10, 0.25);
  g.drawAxes("#bbb");

  const tTrain = 2.6,
    tVal = 43.5;
  g.vline(tTrain, "#bbb");
  g.vline(tVal, "#bbb");

  g.drawCurve(trainAcc, "#0066cc", 4);
  g.drawCurve(valAcc, "#c0392b", 4);

  g.gapArrow(tTrain, tVal, 0.56);
  g.centeredText((tTrain + tVal) / 2, 0.62, "Grokking gap", "#1d1d1f", 26, 600);

  g.text(tTrain, 1.08, "암기 완료", "#0066cc", 12, 0, 22);
  g.centeredText(tVal, 1.08, "일반화", "#c0392b", 22, 600);

  g.centeredText(
    10.5,
    0.9,
    "훈련 정확도 : 초기에 급격히 상승",
    "#0066cc",
    22,
    400
  );
  g.centeredText(
    20,
    0.135,
    "검증 정확도 : 충분히 긴 학습 후 급격히 상승",
    "#c0392b",
    22,
    400
  );

  g.ticksX([0, 10, 20, 30, 40, 50], (v) => (v === 0 ? "0" : `${v}k`), 30, 19);
  g.centeredText(48.5, -0.135, "학습 step", "#999", 20, 400);
  g.text(0, 1.02, "정확도", "#999", 8, 4, 20);
  g.centeredText(47.5, 0.12, "개념 모식도", "#6e6e73", 20, 500);
}

/* ══════════════════ 예비 실험 팝업 (슬라이드 3) ══════════════════ */

let popupStage = 0; // 0 = 닫힘, 1~3 = 단계
let popupDone = false;
let popupInstant = false; // 검수용: 애니메이션 없이 최종 화면 (해시 #3p2f)
const stageTimers = { raf: null };

function cancelStageAnims() {
  if (stageTimers.raf) cancelAnimationFrame(stageTimers.raf);
  stageTimers.raf = null;
}

function openPopup(n) {
  if (!HAS_GROK_DATA) return;
  const ov = document.getElementById("popup-exp");
  if (!ov) return;
  cancelStageAnims();
  ov.hidden = false;
  popupStage = n;
  for (let i = 1; i <= 3; i++) {
    const el = document.getElementById(`pstage-${i}`);
    if (el) el.hidden = i !== n;
  }
  const no = document.getElementById("popup-stageno");
  if (no) no.textContent = `${n} / 3`;
  if (n === 1) animTerminal();
  if (n === 2) animAccChart();
  if (n === 3) animEmbedding();
}

function closePopup(markDone) {
  if (popupStage === 0) return;
  cancelStageAnims();
  const ov = document.getElementById("popup-exp");
  if (ov) ov.hidden = true;
  popupStage = 0;
  if (markDone) popupDone = true;
}

// 슬라이드 3에서 →/← 키가 팝업 단계를 제어. true를 반환하면 키를 소비한 것.
function handlePopupNav(dir) {
  if (!HAS_GROK_DATA) return false;
  if (current !== 4) {
    if (popupStage) closePopup(false);
    return false;
  }
  if (dir > 0) {
    if (popupStage === 0) {
      if (popupDone) return false;
      openPopup(1);
      return true;
    }
    if (popupStage < 3) {
      openPopup(popupStage + 1);
      return true;
    }
    closePopup(true);
    return true;
  }
  if (popupStage > 1) {
    openPopup(popupStage - 1);
    return true;
  }
  if (popupStage === 1) {
    closePopup(false);
    return true;
  }
  return false;
}

/* ---------- 1단계: 실제 학습 로그 터미널 리플레이 ---------- */

function animTerminal() {
  const out = document.getElementById("term-out");
  if (!out) return;
  const M = GROK_META;
  const pad6 = (v) => String(v).padStart(6, " ");
  const last = GROK_METRICS[GROK_METRICS.length - 1];

  // 타임라인: [출력 시각(ms), 라인 HTML]
  // 급상승(step 3,000)까지만 리플레이하고 나머지는 '생략' 표시 — 마지막 화면에
  // 검증 정확도가 치솟는 줄들이 남도록 구성
  const timeline = [];
  let tCur = 0;
  const push = (line, dt) => {
    tCur += dt;
    timeline.push([tCur, line]);
  };

  [
    `num docs: ${M.numDocs}`,
    `vocab size: ${M.vocab}`,
    `num params: ${M.params}`,
    `device: ${M.device}`,
    `train pairs: ${M.trainPairs} | validation pairs: ${M.heldOut}`,
  ].forEach((l) => push(l, 160));

  const REPLAY_END = 5000; // 2단계 그래프와 같은 범위
  GROK_METRICS.forEach((r) => {
    const s = r[0];
    if (s > REPLAY_END) return;
    let line = `step ${pad6(s)} / ${pad6(
      M.numSteps
    )} | train loss ${r[1].toFixed(4)} | train acc ${r[2].toFixed(
      3
    )} | val loss ${r[3].toFixed(4)} | val acc ${r[4].toFixed(3)}`;
    if (r[4] >= 0.5)
      line = line.replace(
        /(val acc \d\.\d{3})$/,
        '<span class="tl-val">$1</span>'
      );
    push(line, 30); // 전 구간 일정한 속도
  });

  push("", 160);
  push(
    `<span class="tl-dim">... step  5,050 ~ 20,000 : train/val 정확도 1.000 유지 (생략)</span>`,
    220
  );
  push("", 120);
  push("--- evaluation ---", 160);
  push(
    `train:    loss ${last[1].toFixed(4)} | accuracy ${M.trainPairs}/${
      M.trainPairs
    } = 1.000`,
    160
  );
  push(
    `<span class="tl-note">validation: loss ${last[3].toFixed(4)} | accuracy ${
      M.heldOut
    }/${M.heldOut} = 1.000</span>`,
    180
  );

  // 전체 로그를 버퍼에 유지 → 리플레이 후 터미널 안에서 위로 스크롤해 되짚어볼 수 있음
  if (popupInstant) {
    out.innerHTML = timeline.map((e) => e[1]).join("\n");
    out.scrollTop = out.scrollHeight;
    return;
  }
  out.innerHTML = "";
  const t0 = performance.now();
  let shown = 0;
  const tick = (now) => {
    const t = now - t0;
    let count = 0;
    while (count < timeline.length && timeline[count][0] <= t) count++;
    if (count !== shown) {
      // 사용자가 위로 스크롤해 읽는 중이면 바닥 고정을 풀고, 바닥 근처면 따라 내려감
      const stick = out.scrollTop + out.clientHeight >= out.scrollHeight - 40;
      out.innerHTML = timeline
        .slice(0, count)
        .map((e) => e[1])
        .join("\n");
      if (stick) out.scrollTop = out.scrollHeight;
      shown = count;
    }
    if (count < timeline.length) stageTimers.raf = requestAnimationFrame(tick);
  };
  stageTimers.raf = requestAnimationFrame(tick);
}

/* ---------- 2단계: 정확도 곡선 애니메이션 ---------- */

function animAccChart() {
  if (popupInstant) {
    renderAccChart("pop-acc", GROK_META.numSteps, true);
    return;
  }
  const rows = GROK_METRICS.filter((r) => r[0] <= ACC_XMAX);
  // 급상승 구간(step 1,500~3,000)에서는 슬로모션
  const dwell = rows.map((r) => (r[0] >= 1500 && r[0] <= 3000 ? 60 : 34));
  const cum = [];
  let acc = 0;
  for (const d of dwell) {
    acc += d;
    cum.push(acc);
  }
  const total = acc;
  const t0 = performance.now();
  const tick = (now) => {
    const t = now - t0;
    if (t >= total) {
      renderAccChart("pop-acc", GROK_META.numSteps, true);
      return;
    }
    let k = cum.findIndex((c) => c >= t);
    if (k < 0) k = rows.length - 1;
    const g = renderAccChart("pop-acc", rows[k][0], false);
    if (g) {
      g.centeredText(
        4250,
        0.92,
        `step ${rows[k][0].toLocaleString()}`,
        "#1d1d1f",
        32,
        600
      );
      g.centeredText(
        4250,
        0.8,
        `훈련 ${(rows[k][2] * 100).toFixed(1)}%`,
        "#0066cc",
        25,
        500
      );
      g.centeredText(
        4250,
        0.7,
        `검증 ${(rows[k][4] * 100).toFixed(1)}%`,
        "#c0392b",
        25,
        500
      );
    }
    stageTimers.raf = requestAnimationFrame(tick);
  };
  stageTimers.raf = requestAnimationFrame(tick);
}

/* ---------- 3단계: 임베딩 무질서 → 원형 구조 ---------- */

const VIRIDIS = [
  [68, 1, 84],
  [59, 82, 139],
  [33, 145, 140],
  [94, 201, 98],
  [253, 231, 37],
];
function viridis(t) {
  const n = VIRIDIS.length - 1;
  const i = Math.min(Math.floor(t * n), n - 1);
  const f = t * n - i;
  const c = VIRIDIS[i].map((v, j) =>
    Math.round(v + f * (VIRIDIS[i + 1][j] - v))
  );
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

function animEmbedding() {
  const cv = document.getElementById("pop-emb");
  if (!cv) return;
  const ctx = cv.getContext("2d");
  const CX = 500,
    CY = 305,
    R = 245;
  // 프레임마다 최대 반지름이 1이 되도록 스케일 → 산점도가 항상 캔버스 안에 들어옴
  const frames = GROK_EMB_FRAMES.map((fr) => {
    const maxr = Math.max(...fr.xy.map(([x, y]) => Math.hypot(x, y)));
    return { step: fr.step, xy: fr.xy.map(([x, y]) => [x / maxr, y / maxr]) };
  });

  const phaseText = (step) =>
    step < 250
      ? "초기화 — 무질서"
      : step < 1500
      ? "암기 완료 — 하지만 검증 정확도는 아직 바닥"
      : step < 2800
      ? "전환 — 구조가 형성되는 중…"
      : "일반화 완료 — 원형 구조";

  function drawFrame(a, b, f, step, finalHold) {
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, cv.width, cv.height);
    if (finalHold) {
      // 최종 프레임의 평균 반지름에 점선 원 가이드
      const F = frames[frames.length - 1].xy;
      const meanR = F.reduce((s, [x, y]) => s + Math.hypot(x, y), 0) / F.length;
      ctx.beginPath();
      ctx.setLineDash([8, 8]);
      ctx.strokeStyle = "#e0e0e0";
      ctx.lineWidth = 2;
      ctx.arc(CX, CY, R * meanR, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.font = '600 20px "IBM Plex Sans KR","IBM Plex Sans",sans-serif';
    ctx.textAlign = "center";
    for (let n = 0; n < GROK_META.modulus; n++) {
      const x = a[n][0] + f * (b[n][0] - a[n][0]);
      const y = a[n][1] + f * (b[n][1] - a[n][1]);
      ctx.fillStyle = viridis(n / (GROK_META.modulus - 1));
      ctx.fillText(String(n).padStart(2, "0"), CX + x * R, CY - y * R + 7);
    }
    ctx.textAlign = "left";
    ctx.fillStyle = "#1d1d1f";
    ctx.font = '600 36px "IBM Plex Sans KR","IBM Plex Sans",sans-serif';
    ctx.fillText(`step ${step.toLocaleString()}`, 950, 120);
    ctx.fillStyle = "#6e6e73";
    ctx.font = '400 26px "IBM Plex Sans KR","IBM Plex Sans",sans-serif';
    ctx.fillText(phaseText(step), 950, 168);
    if (finalHold) {
      ctx.fillStyle = "#1d1d1f";
      ctx.font = '400 25px "IBM Plex Sans KR","IBM Plex Sans",sans-serif';
      ctx.fillText("반지름 편차 3.9% — 사실상 완전한 원", 950, 320);
      ctx.fillText(
        `배열 순서: ${GROK_META.freq}·x mod ${GROK_META.modulus} (적합도 0.999)`,
        950,
        362
      );
      ctx.fillStyle = "#6e6e73";
      ctx.font = '400 23px "IBM Plex Sans KR","IBM Plex Sans",sans-serif';
      ctx.fillText("임베딩 PCA 상위 2축 (최종 기저 고정)", 950, 430);
    }
  }

  if (popupInstant) {
    const F = frames[frames.length - 1];
    drawFrame(F.xy, F.xy, 0, F.step, true);
    return;
  }
  // 전환 i: frames[i] → frames[i+1], 전환 구간(step 1,500~3,500)은 슬로모션
  const durs = [];
  for (let i = 1; i < frames.length; i++) {
    const s = frames[i].step;
    durs.push(s >= 1500 && s <= 3000 ? 300 : 150);
  }
  const cum = [];
  let acc = 0;
  for (const d of durs) {
    acc += d;
    cum.push(acc);
  }
  const total = acc;
  const t0 = performance.now();
  const tick = (now) => {
    const t = now - t0;
    if (t >= total) {
      const F = frames[frames.length - 1];
      drawFrame(F.xy, F.xy, 0, F.step, true);
      return;
    }
    let i = cum.findIndex((c) => c >= t);
    if (i < 0) i = durs.length - 1;
    const tPrev = i === 0 ? 0 : cum[i - 1];
    const f = (t - tPrev) / durs[i];
    drawFrame(frames[i].xy, frames[i + 1].xy, f, frames[i + 1].step, false);
    stageTimers.raf = requestAnimationFrame(tick);
  };
  stageTimers.raf = requestAnimationFrame(tick);
}

/* ══════════════════ Init ══════════════════ */

document.addEventListener("DOMContentLoaded", () => {
  if (typeof renderMathInElement === "function") {
    renderMathInElement(document.body, {
      delimiters: [
        { left: "\\(", right: "\\)", display: false },
        { left: "\\[", right: "\\]", display: true },
      ],
      throwOnError: false,
      strict: false,
    });
  }
  requestAnimationFrame(() => {
    drawGrokkingGraph();
  });

  // deep-link: index.html#5 → 슬라이드 5, #3p2 → 슬라이드 3 + 팝업 2단계,
  // #3p2f → 애니메이션 생략하고 최종 화면 (리허설·검수용)
  const m = location.hash.match(/^#(\d+)(?:p([1-3])(f?))?$/);
  if (m) {
    const n = parseInt(m[1], 10);
    if (n >= 1 && n <= TOTAL) showSlide(n);
    if (m[2]) {
      popupInstant = !!m[3];
      openPopup(parseInt(m[2], 10));
    }
  }
});
