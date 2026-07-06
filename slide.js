/* ══════════════════ Viewport scaling ══════════════════ */

function scaleViewport() {
  const vp = document.getElementById('slide-viewport');
  const scale = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
  const ox = (window.innerWidth  - 1920 * scale) / 2;
  const oy = (window.innerHeight - 1080 * scale) / 2;
  vp.style.transform = `scale(${scale})`;
  vp.style.position  = 'absolute';
  vp.style.left      = `${ox}px`;
  vp.style.top       = `${oy}px`;
}
window.addEventListener('resize', scaleViewport);
scaleViewport();

/* ══════════════════ Navigation ══════════════════ */

const TOTAL = 11;
let current = 1;

function showSlide(n) {
  document.getElementById(`slide-${current}`).classList.remove('active');
  current = Math.max(1, Math.min(TOTAL, n));
  document.getElementById(`slide-${current}`).classList.add('active');
  document.getElementById('slide-counter').textContent = `${current} / ${TOTAL}`;
  document.getElementById('btn-prev').disabled = current === 1;
  document.getElementById('btn-next').disabled = current === TOTAL;
}

function navigate(dir) { showSlide(current + dir); }

document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') navigate(1);
  if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   navigate(-1);
});
document.getElementById('btn-prev').addEventListener('click', () => navigate(-1));
document.getElementById('btn-next').addEventListener('click', () => navigate(1));

/* ══════════════════ Graph class (design.md canonical) ══════════════════ */

class Graph {
  constructor(id, { xMin, xMax, yMin, yMax }) {
    this.canvas = document.getElementById(id);
    if (!this.canvas) return;
    this.ctx  = this.canvas.getContext('2d');
    this.W    = this.canvas.width;
    this.H    = this.canvas.height;
    this.xMin = xMin; this.xMax = xMax;
    this.yMin = yMin; this.yMax = yMax;
  }

  wx(x) { return (x - this.xMin) / (this.xMax - this.xMin) * this.W; }
  wy(y) { return (this.yMax - y) / (this.yMax - this.yMin) * this.H; }

  clear(bg = '#ffffff') {
    const { ctx, W, H } = this;
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);
  }

  drawGrid(stepX = 1, stepY = 1) {
    const { ctx, W, H } = this;
    ctx.beginPath();
    ctx.strokeStyle = '#ebebed';
    ctx.lineWidth = 1;
    for (let x = Math.floor(this.xMin); x <= this.xMax + 0.01; x += stepX) {
      const cx = this.wx(x);
      ctx.moveTo(cx, 0); ctx.lineTo(cx, H);
    }
    for (let y = Math.floor(this.yMin); y <= this.yMax + 0.01; y += stepY) {
      const cy = this.wy(y);
      ctx.moveTo(0, cy); ctx.lineTo(W, cy);
    }
    ctx.stroke();
  }

  drawAxes(color = '#bbb') {
    const { ctx, W, H } = this;
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    if (this.yMin <= 0 && this.yMax >= 0) {
      ctx.moveTo(0, this.wy(0)); ctx.lineTo(W, this.wy(0));
    }
    if (this.xMin <= 0 && this.xMax >= 0) {
      ctx.moveTo(this.wx(0), 0); ctx.lineTo(this.wx(0), H);
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
      const x  = this.xMin + (this.xMax - this.xMin) * i / steps;
      const y  = f(x);
      const ok = isFinite(y) && y >= this.yMin - 0.8 && y <= this.yMax + 0.8;
      if (!ok) { pen = false; continue; }
      const cx = this.wx(x), cy = this.wy(y);
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
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2.5;
    ctx.stroke();
  }

  text(x, y, str, color = '#333', dx = 10, dy = -10, size = 18) {
    const { ctx } = this;
    ctx.fillStyle = color;
    ctx.font = `${size}px "IBM Plex Sans KR","IBM Plex Sans",sans-serif`;
    ctx.textAlign = 'left';
    ctx.fillText(str, this.wx(x) + dx, this.wy(y) + dy);
  }

  ticksX(vals, labelFn, dy = 22, size = 18) {
    const { ctx } = this;
    ctx.fillStyle = '#999';
    ctx.font = `${size}px "IBM Plex Sans",sans-serif`;
    ctx.textAlign = 'center';
    for (const v of vals) ctx.fillText(labelFn(v), this.wx(v), this.wy(0) + dy);
  }

  ticksY(vals, labelFn, dx = -8, size = 18) {
    const { ctx } = this;
    ctx.fillStyle = '#999';
    ctx.font = `${size}px "IBM Plex Sans",sans-serif`;
    ctx.textAlign = 'right';
    for (const v of vals) ctx.fillText(labelFn(v), this.wx(0) + dx, this.wy(v) + 6);
  }
}

/* Extension: annotation helpers built on Graph (keeps all canvas work in one class family) */
class AnnotatedGraph extends Graph {
  vline(x, color = '#bbb', lw = 1.5, dash = [10, 8]) {
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
  gapArrow(x1, x2, y, color = '#6e6e73', lw = 2.5) {
    const { ctx } = this;
    const cy = this.wy(y), a = this.wx(x1), b = this.wx(x2), h = 9;
    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = lw;
    ctx.beginPath();
    ctx.moveTo(a, cy); ctx.lineTo(b, cy);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(a, cy); ctx.lineTo(a + h * 1.6, cy - h); ctx.lineTo(a + h * 1.6, cy + h); ctx.closePath(); ctx.fill();
    ctx.beginPath();
    ctx.moveTo(b, cy); ctx.lineTo(b - h * 1.6, cy - h); ctx.lineTo(b - h * 1.6, cy + h); ctx.closePath(); ctx.fill();
    ctx.restore();
  }

  centeredText(x, y, str, color = '#333', size = 20, weight = 600) {
    const { ctx } = this;
    ctx.save();
    ctx.fillStyle = color;
    ctx.font = `${weight} ${size}px "IBM Plex Sans KR","IBM Plex Sans",sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText(str, this.wx(x), this.wy(y));
    ctx.restore();
  }
}

/* ══════════════════ Slide 3: Grokking curve ══════════════════ */

function drawGrokkingGraph() {
  const g = new AnnotatedGraph('canvas-grokking', { xMin: -2.5, xMax: 53, yMin: -0.16, yMax: 1.14 });
  if (!g.canvas) return;

  const sig = (x, x0, k) => 1 / (1 + Math.exp(-k * (x - x0)));
  const clamp01to50 = f => x => (x < 0 || x > 50) ? NaN : f(x);
  const trainAcc = clamp01to50(x => sig(x, 1.1, 4.2));          // saturates almost immediately
  const valAcc   = clamp01to50(x => 0.04 + 0.96 * sig(x, 40, 0.85)); // flat for a long time, then jumps

  g.clear();
  g.drawGrid(10, 0.25);
  g.drawAxes('#bbb');

  // memorization / generalization markers
  const tTrain = 2.6, tVal = 43.5;
  g.vline(tTrain, '#bbb');
  g.vline(tVal, '#bbb');

  g.drawCurve(trainAcc, '#0066cc', 4);
  g.drawCurve(valAcc, '#c0392b', 4);

  // grokking gap annotation
  g.gapArrow(tTrain, tVal, 0.56);
  g.centeredText((tTrain + tVal) / 2, 0.62, 'Grokking gap', '#1d1d1f', 26, 600);

  g.text(tTrain, 1.08, '암기 완료', '#0066cc', 12, 0, 22);
  g.centeredText(tVal, 1.08, '일반화', '#c0392b', 22, 600);

  g.centeredText(10.5, 0.90, '훈련 정확도 : 초기에 급격히 상승', '#0066cc', 22, 400);
  g.centeredText(20, 0.135, '검증 정확도 : 충분히 긴 학습 후 급격히 상승', '#c0392b', 22, 400);

  // axis labels & ticks
  g.ticksX([0, 10, 20, 30, 40, 50], v => v === 0 ? '0' : `${v}k`, 30, 19);
  g.centeredText(48.5, -0.135, '학습 step', '#999', 20, 400);
  g.text(0, 1.02, '정확도', '#999', 8, 4, 20);
}

/* ══════════════════ Init ══════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  if (typeof renderMathInElement === 'function') {
    renderMathInElement(document.body, {
      delimiters: [
        { left: '\\(', right: '\\)', display: false },
        { left: '\\[', right: '\\]', display: true },
      ],
      throwOnError: false,
      strict: false,
    });
  }
  requestAnimationFrame(() => {
    drawGrokkingGraph();
  });

  // deep-link: index.html#5 opens slide 5 (used for review screenshots too)
  const h = parseInt(location.hash.slice(1), 10);
  if (h >= 1 && h <= TOTAL) showSlide(h);
});
