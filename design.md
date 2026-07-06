## Overview

This is an **Apple-inspired HTML presentation system** optimized for academic and mathematical content. The design language emphasizes restraint, clarity, and typographic discipline — a single blue accent, generous whitespace, and IBM Plex Sans throughout. Mathematical notation is rendered with KaTeX; interactive graphs use HTML5 Canvas.

**Key principles:**
- Single accent color (`#0066cc`) for all interactive elements — never a second brand color.
- IBM Plex Sans KR as the only text font; KaTeX Math only for equations.
- Fixed 1920×1080 canvas scaled to fit any screen (no layout reflow).
- No decorative gradients, no drop-shadows on UI (shadows only on canvas elements).
- Consistent header / title-zone / content-zone across all standard slides.

---

## Technical Architecture

### File Structure

```
project/
├── index.html      ← All slide markup; one <div id="slide-N"> per slide
├── slide.css       ← All styles; single file
├── slide.js        ← Navigation, viewport scaling, KaTeX init, Graph class, all graph draw functions
└── design.md       ← This file
```

### HTML Skeleton

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>발표 제목</title>
  <link rel="stylesheet" href="slide.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
</head>
<body>

<div id="slide-viewport">
  <!-- slides go here -->
</div>

<!-- Navigation Bar -->
<div id="nav-bar">
  <button id="btn-prev">◀</button>
  <span id="slide-counter">1 / N</span>
  <button id="btn-next">▶</button>
</div>

<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<script src="slide.js"></script>
</body>
</html>
```

### Viewport Scaling

The slide viewport is **exactly 1920×1080 px** and is scaled (not reflowed) to fit any window size. All coordinates and font sizes in CSS are for the 1920×1080 canvas — do not use `vw`/`vh` units inside slides.

```javascript
// In slide.js — runs on load and resize
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
```

### Navigation

```javascript
const TOTAL = N; // replace with actual slide count
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
```

---

## Color System

Defined as CSS custom properties in `:root`. Always use these variables — never inline hex inside components.

```css
:root {
  --c-bg:        #f5f5f7;   /* Default slide background (Apple parchment) */
  --c-white:     #ffffff;   /* Pure white (graph backgrounds, cards) */
  --c-dark:      #1d1d1f;   /* Cover / Outro slide background (near-black) */
  --c-tile-dark: #272729;   /* Table headers, dark boxes */
  --c-ink:       #1d1d1f;   /* Primary text on light backgrounds */
  --c-muted:     #6e6e73;   /* Secondary text, chapter labels, captions */
  --c-accent:    #0066cc;   /* THE single interactive/emphasis color */
  --c-accent-dk: #2997ff;   /* Accent on dark surfaces (Cover, Outro) */
  --c-red:       #c0392b;   /* Graph curve 2, box-red, error / negative */
  --c-green:     #1a7a3c;   /* Graph curve 3, box-green, stable / positive */
  --c-border:    #e0e0e0;   /* Hairline borders, table rows, dividers */
  --margin-h:    90px;      /* Horizontal safe-margin for all content */
  --margin-v:    68px;      /* Header height (= top of title-zone) */
  --f-sans: 'IBM Plex Sans KR', 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
}
```

### Color Usage Rules

| Context | Variable |
|---|---|
| All links, buttons, highlights, box borders (light bg) | `--c-accent` |
| Same on dark backgrounds | `--c-accent-dk` |
| Second curve / negative emphasis | `--c-red` |
| Third curve / positive / stable | `--c-green` |
| Body text | `--c-ink` |
| Chapter label, page number, captions | `--c-muted` |
| Section dividers, table borders | `--c-border` |
| Standard slide background | `--c-bg` |
| Cover / Outro background | `--c-dark` |

**Rule:** Never introduce a second interactive color. `--c-accent` carries every "click me" signal.

---

## Typography

Font family: **IBM Plex Sans KR** (Korean) + **IBM Plex Sans** (Latin), loaded from Google Fonts. KaTeX Math only for equations.

```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&display=swap');
```

### Size Scale (for 1920×1080 canvas)

| Role | Size | Weight | Letter-spacing | Class / Element |
|---|---|---|---|---|
| Cover title | 82px | 700 | -0.03em | `.cover-title` |
| Outro main | 96px | 700 | -0.03em | `.outro-main` |
| Cover subtitle | 42px | 300 | -0.01em | `.cover-sub` |
| Slide title | 58px | 600 | -0.02em | `.slide-title` |
| Slide subtitle | 34px | 400 | -0.01em | `.slide-subtitle` |
| Body / bullet | 36px | 400 | 0 | `.bullet-list li` |
| Body small | 32px | 400 | 0 | `.bullet-list.sm li` |
| Box body | 34px | 400 | 0 | `.box-body` |
| Display math | 40px | 400 | 0 | `.display-math` |
| Display math sm | 34px | 400 | 0 | `.display-math-sm` |
| TOC entry | 36px | 400 | 0 | `.toc-text` |
| Chapter label | 22px | 500 | 0.08em | `.chapter-label` |
| Section label | 28px | 600 | 0.06em | `.section-label` |
| Box title | 26px | 600 | 0.04em | `.box-title` |
| Graph label | 26px | 400 | 0 | `.graph-label` |
| Badge | 26px | 600 | 0.02em | `.badge` |

**Minimum text size on a slide: 26px.** Never go below this — anything smaller is illegible at presentation distance.

**Weight ladder: 300 / 400 / 500 / 600 / 700.** Weight 600 for all headlines and labels. Weight 400 for body. Weight 300 for Cover subtitle / Outro subtitle only (airy, atmospheric feel).

---

## Spacing & Layout

### Slide Zones

Every standard slide is divided into three fixed zones:

```
┌──────────────────────────────────────────────────────┐  ← y=0
│  HEADER STRIP  (height: 68px)                        │
│  chapter-label (left)        page-num (right)        │
├──────────────────────────────────────────────────────┤  ← y=68px
│  TITLE ZONE  (from y=68px, padding-top 32px)         │
│  slide-title                                         │
│  slide-subtitle (optional)                           │
│  ── 2px solid var(--c-accent) border-bottom ──       │
├──────────────────────────────────────────────────────┤  ← y≈210–260px
│  CONTENT ZONE  (to bottom: 60px safe margin)         │
│  flex column, gap: 28px                              │
│                                                      │
└──────────────────────────────────────────────────────┘  ← y=1080px
```

### Content Zone Top Variants

```css
.content-zone          { top: 240px; }  /* default (title + subtitle) */
.content-zone.top-210  { top: 210px; }  /* title only, no subtitle */
.content-zone.top-260  { top: 260px; }  /* title + long subtitle or extra padding */
```

### Horizontal Margins

All content uses `padding: 0 var(--margin-h)` = 90px on each side. Never place text within 90px of the left/right edge.

### Column Layouts

```css
.cols   { display: flex; gap: 60px; align-items: flex-start; }
.col    { flex: 1; }         /* equal columns */
.col-4  { flex: 0 0 40%; }   /* 40% fixed */
.col-5  { flex: 0 0 50%; }   /* 50% fixed */
.col-6  { flex: 0 0 55%; }   /* 55% fixed */
```

---

## Component Library

All CSS for these components lives in `slide.css`.

### Highlight Boxes

Five semantic variants. Always use `border-radius: 16px` and `padding: 28px 36px`.

```html
<!-- Blue box (definition, key result) -->
<div class="box box-blue">
  <div class="box-title">THEOREM</div>
  <div class="box-body">Content here, supports KaTeX inline \(x^2\).</div>
</div>

<!-- Red box (warning, counterexample) -->
<div class="box box-red"> ... </div>

<!-- Green box (proof complete, stable case) -->
<div class="box box-green"> ... </div>

<!-- Gray box (neutral note, remark) -->
<div class="box box-gray"> ... </div>

<!-- Dark box (emphasis on light background) -->
<div class="box-dark"> ... </div>
```

Box border-left colors: blue=`--c-accent`, red=`--c-red`, green=`--c-green`, gray=`#aaaaaa`.

### Bullet Lists

```html
<ul class="bullet-list">
  <li>Normal item — 36px, weight 400</li>
  <li><strong>Bold item</strong> — weight 600</li>
</ul>

<ul class="bullet-list sm">
  <li>Smaller item — 32px</li>
</ul>
```

Bullets are 10px circles in `--c-accent`, absolute-positioned at 18px from top.

### Classification Table

```html
<table class="class-table">
  <thead>
    <tr>
      <th>Column A</th>
      <th>Column B</th>
      <th>Count</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Value</td>
      <td>Value</td>
      <td class="cnt">3</td>      <!-- blue bold count -->
    </tr>
    <tr>
      <td>Value</td>
      <td class="highlight">Highlighted</td>
      <td class="cnt-red">1</td>  <!-- red bold count -->
    </tr>
  </tbody>
</table>
```

Header: `--c-tile-dark` background, white text, 28px. Body: 30px, zebra striping at 3% opacity.

### Legend

```html
<div class="legend">
  <div class="legend-item">
    <div class="legend-line" style="background:#0066cc;"></div>
    <span class="txt-sm">\(f(x)\)</span>
  </div>
  <div class="legend-item">
    <div class="legend-line" style="background:#c0392b;"></div>
    <span class="txt-sm">\(g(x)\)</span>
  </div>
  <div class="legend-item">
    <div class="legend-dash" style="border-color:#888;"></div>
    <span class="txt-sm">dashed line label</span>
  </div>
</div>
```

### Interactive Slider

```html
<div class="slider-row">
  <span class="slider-label">\(a =\)</span>
  <input type="range" id="my-slider" min="0.1" max="3.0" step="0.01" value="1.5">
  <span class="slider-value" id="my-value">1.500</span>
</div>
<!-- Optional: preset buttons -->
<div class="special-point-row">
  <button type="button" class="special-point-btn" data-special-a="lower">Special Point A</button>
  <button type="button" class="special-point-btn" data-special-a="upper">Special Point B</button>
</div>
```

Slider thumb: 32×32px circle in `--c-accent`. Value display: 36px, weight 600, `--c-accent`.

### Badges / Tags

```html
<span class="badge badge-blue">Theorem</span>
<span class="badge badge-red">Warning</span>
<span class="badge badge-green">Proved</span>
<span class="badge badge-gray">Remark</span>
```

All badges: pill-shaped (`border-radius: 999px`), 26px, weight 600.

### Flow Diagram

```html
<div class="flow-row">
  <div class="flow-node">Step 1</div>
  <div class="flow-arrow">→</div>
  <div class="flow-node accent">Step 2</div>
  <div class="flow-arrow">→</div>
  <div class="flow-node dark">Result</div>
</div>
```

### Stability Blocks

```html
<div class="stability-row">
  <div class="stability-block stable">
    <div class="sb-title">Stable</div>
    Description or math here.
  </div>
  <div class="stability-block unstable">
    <div class="sb-title">Unstable</div>
    Description or math here.
  </div>
</div>
```

### Text Helpers (utility classes)

```css
.txt-sm     { font-size: 30px; }
.txt-md     { font-size: 36px; }
.txt-lg     { font-size: 42px; }
.txt-muted  { color: var(--c-muted); }
.txt-accent { color: var(--c-accent); }
.txt-red    { color: var(--c-red); }
.txt-green  { color: var(--c-green); }
.txt-bold   { font-weight: 600; }
.txt-center { text-align: center; }
.divider    { height: 1px; background: var(--c-border); margin: 8px 0; }
```

### Section Label

```html
<div class="section-label">Key Definition</div>
```

28px, weight 600, `--c-accent`, uppercase with 0.06em tracking.

---

## Graph & Canvas System

### Graph Container

Wrap every canvas in `.graph-wrap` for the shadow and label:

```html
<div class="graph-wrap">
  <canvas id="my-graph" width="800" height="500"></canvas>
  <div class="graph-label">Caption text</div>
</div>
```

Canvas style: `border-radius: 12px; box-shadow: rgba(0,0,0,0.12) 0 4px 24px;` (applied via `.graph-wrap canvas`).

### Graph Class API

Copy this class verbatim into `slide.js`. All drawing should use this class.

```javascript
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

  // World → Canvas coordinate transforms
  wx(x) { return (x - this.xMin) / (this.xMax - this.xMin) * this.W; }
  wy(y) { return (this.yMax - y) / (this.yMax - this.yMin) * this.H; }

  // Fill background
  clear(bg = '#ffffff') {
    const { ctx, W, H } = this;
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);
  }

  // Light gray grid lines
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

  // X and Y axes (only drawn if axis is within view)
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

  // Solid curve: f(x) → y, samples `steps` points
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

  // Dashed curve — same signature as drawCurve
  drawDash(f, color, lw = 2) {
    this.ctx.setLineDash([12, 8]);
    this.drawCurve(f, color, lw);
    this.ctx.setLineDash([]);
  }

  // Filled dot with white stroke (for intersection / special points)
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

  // Text label at world coordinates
  text(x, y, str, color = '#333', dx = 10, dy = -10, size = 18) {
    const { ctx } = this;
    ctx.fillStyle = color;
    ctx.font = `${size}px "IBM Plex Sans KR","IBM Plex Sans",sans-serif`;
    ctx.textAlign = 'left';
    ctx.fillText(str, this.wx(x) + dx, this.wy(y) + dy);
  }

  // Axis tick labels (x-axis)
  ticksX(vals, labelFn, dy = 22, size = 18) {
    const { ctx } = this;
    ctx.fillStyle = '#999';
    ctx.font = `${size}px "IBM Plex Sans",sans-serif`;
    ctx.textAlign = 'center';
    for (const v of vals) ctx.fillText(labelFn(v), this.wx(v), this.wy(0) + dy);
  }

  // Axis tick labels (y-axis)
  ticksY(vals, labelFn, dx = -8, size = 18) {
    const { ctx } = this;
    ctx.fillStyle = '#999';
    ctx.font = `${size}px "IBM Plex Sans",sans-serif`;
    ctx.textAlign = 'right';
    for (const v of vals) ctx.fillText(labelFn(v), this.wx(0) + dx, this.wy(v) + 6);
  }
}
```

### Graph Color Conventions

| Curve | Color | Hex |
|---|---|---|
| Primary / first function | Blue | `#0066cc` |
| Secondary / second function | Red | `#c0392b` |
| Reference line (y=x, asymptote) | Dashed gray | `#bbb` |
| Special / intersection point | Orange | `#ff6b00` |
| Branch point | Near-black | `#1d1d1f` |
| Grid | Light gray | `#ebebed` |
| Axes | Medium gray | `#bbb` |
| Tick labels | Muted | `#999` |

### Initializing Graphs

All graph draw functions must be called inside `DOMContentLoaded` → `requestAnimationFrame`:

```javascript
document.addEventListener('DOMContentLoaded', () => {
  renderMathInElement(document.body, { /* KaTeX config */ });
  requestAnimationFrame(() => {
    drawMyGraph();
    initInteractiveGraph();
  });
});
```

---

## Slide Types

### Cover Slide

```html
<div class="slide slide-cover active" id="slide-1">
  <div class="cover-inner">
    <div class="cover-tag">CHAPTER / COURSE LABEL</div>
    <h1 class="cover-title">Presentation Title</h1>
    <p class="cover-sub">Subtitle or tagline</p>
    <div class="cover-meta">
      <div>Author name(s)</div>
      <div>Date or context</div>
    </div>
  </div>
  <div class="cover-line"></div>  <!-- 6px accent bar at bottom -->
</div>
```

- Background: `--c-dark` (near-black). Text: white.
- `cover-tag`: small uppercase label in `--c-accent-dk`.
- `cover-line`: 6px blue bar fixed at the very bottom.
- No `.slide-header` on cover.

### Table of Contents Slide

```html
<div class="slide" id="slide-2">
  <div class="slide-header">
    <span class="chapter-label">목차</span>
    <span class="page-num">2 / N</span>
  </div>
  <div class="title-zone">
    <h1 class="slide-title">목차</h1>
  </div>
  <div class="content-zone top-210">
    <ol class="toc-list">
      <li class="toc-item">
        <span class="toc-num">01</span>
        <span class="toc-text">Section title with optional \(math\)</span>
      </li>
      <!-- repeat for each section -->
    </ol>
  </div>
</div>
```

### Standard Content Slide

```html
<div class="slide" id="slide-N">
  <div class="slide-header">
    <span class="chapter-label">CHAPTER NAME</span>
    <span class="page-num">N / TOTAL</span>
  </div>
  <div class="title-zone">
    <h1 class="slide-title">Slide Title</h1>
    <p class="slide-subtitle">Optional subtitle</p>
  </div>
  <div class="content-zone">
    <!-- Use .box-*, .bullet-list, .cols, .class-table, .display-math, etc. -->
  </div>
</div>
```

### Interactive Graph Slide

```html
<div class="slide" id="slide-N">
  <div class="slide-header">
    <span class="chapter-label">CHAPTER</span>
    <span class="page-num">N / TOTAL</span>
  </div>
  <div class="title-zone">
    <h1 class="slide-title">Title with \(math\)</h1>
  </div>
  <div class="content-zone top-210" style="gap:10px;">
    <div class="graph-wrap" style="gap:8px;">
      <canvas id="canvas-slideN" width="1200" height="500"></canvas>
      <div class="legend">
        <div class="legend-item">
          <div class="legend-line" style="background:#0066cc;"></div>
          <span class="txt-sm">\(f(x)\)</span>
        </div>
      </div>
    </div>
    <div class="slider-row">
      <span class="slider-label">\(a =\)</span>
      <input type="range" id="my-slider" min="0.1" max="3.0" step="0.01" value="1.5">
      <span class="slider-value" id="my-value">1.500</span>
    </div>
    <div class="intersect-info" id="my-info">
      count: <strong>—</strong>
    </div>
  </div>
</div>
```

### Dark / Section Divider Slide

```html
<div class="slide slide-dark" id="slide-N">
  <div class="slide-header">
    <span class="chapter-label">Section</span>
  </div>
  <div class="title-zone">
    <h1 class="slide-title">Section Title</h1>
    <p class="slide-subtitle">Description</p>
  </div>
  <div class="content-zone">
    <!-- content; bullets, boxes work on dark bg -->
  </div>
</div>
```

### Outro Slide

```html
<div class="slide slide-outro" id="slide-N">
  <div class="outro-inner">
    <div class="outro-main">감사합니다</div>
    <div class="outro-sub">Any final note, question prompt, or reference</div>
  </div>
  <div class="cover-line"></div>
</div>
```

---

## KaTeX Integration

### CDN Links (add to `<head>` and before `</body>`)

```html
<!-- In <head> -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">

<!-- Before </body>, after slide.css -->
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
```

### Initialization (in `slide.js`)

```javascript
document.addEventListener('DOMContentLoaded', () => {
  renderMathInElement(document.body, {
    delimiters: [
      { left: '\\(',  right: '\\)',  display: false },  // inline: \( ... \)
      { left: '\\[',  right: '\\]',  display: true  },  // display: \[ ... \]
    ],
    throwOnError: false,
    strict: false,
  });
  requestAnimationFrame(() => {
    // draw all graphs here
  });
});
```

### Usage in HTML

```html
<!-- Inline math -->
<p>The function \(f(x) = a^x\) has base \(a > 0\).</p>

<!-- Display math (centered, larger) -->
<div class="display-math">\[ W(x) e^{W(x)} = x \]</div>

<!-- Display math (smaller variant) -->
<div class="display-math-sm">\[ x = \frac{-W(-\ln a)}{\ln a} \]</div>
```

**Critical:** KaTeX font-size is set to `inherit` in CSS (`display.css` override: `.katex { font-size: inherit !important; }`), so it respects the containing element's size.

---

## Navigation Bar (CSS)

The nav bar is fixed, outside `#slide-viewport`, always visible:

```css
#nav-bar {
  position: fixed;
  right: 22px;
  bottom: 18px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(29,29,31,0.82);
  backdrop-filter: blur(12px);
  border-radius: 999px;
  padding: 6px 14px;
  z-index: 9999;
}
#nav-bar button {
  background: none;
  border: none;
  color: #fff;
  font-size: 17px;
  cursor: pointer;
  padding: 4px 9px;
  border-radius: 8px;
}
#nav-bar button:hover   { background: rgba(255,255,255,0.12); }
#nav-bar button:disabled { opacity: 0.3; cursor: default; }
#slide-counter {
  font-family: var(--f-sans);
  font-size: 13px;
  color: rgba(255,255,255,0.7);
  min-width: 44px;
  text-align: center;
}
```

---

## Do's and Don'ts

### Do
- Use `--c-accent` (#0066cc) for every interactive element, highlight, and link — no exceptions.
- Keep `--c-red` and `--c-green` only for semantic meaning (error/positive, graph curve 2/3).
- Set slide titles at 58px / weight 600 / letter-spacing -0.02em.
- Use `.content-zone.top-210` when there is no subtitle; `.content-zone` (240px) when there is.
- Use `requestAnimationFrame` inside `DOMContentLoaded` to draw all graphs after KaTeX renders.
- Use the `Graph` class for all canvas work — do not write raw canvas code outside of it.
- Keep all font sizes ≥ 26px inside slides.
- Use `.box-blue` for definitions/theorems, `.box-red` for warnings, `.box-green` for results.
- Use `.display-math` (40px) for the main equation on a slide, `.display-math-sm` (34px) for secondary.

### Don't
- Don't use `vw`/`vh` units inside slides — everything is in absolute px for the 1920×1080 canvas.
- Don't add shadows to boxes, buttons, or text — only canvas elements get shadows.
- Don't introduce decorative gradients.
- Don't use any font other than IBM Plex Sans (text) and KaTeX Math (equations).
- Don't put text below 26px inside `.slide`.
- Don't leave the bottom third of a content slide empty without a clear reason.
- Don't put two adjacent `.slide-cover`-style dark slides — mix light and dark.
- Don't hardcode hex colors; always use the CSS variables.

---

## Presentation Output Constraints

- Always generate slides in **1920×1080 px** (16:9) canvas. Scale via the viewport scaling JS.
- Do not generate, place, reference, or reserve space for any logo.
- Every slide must feel like part of one continuous presentation system.
- Standard slides must have `.slide-header` + `.title-zone` + `.content-zone`.

## Font System

Use IBM Plex Sans as the primary font for all text elements.

Primary typography:
- Use **IBM Plex Sans KR** / **IBM Plex Sans** as the default font for all titles, subtitles, body text, labels, captions, bullets, callouts, tables, and UI-like elements.
- Use **KaTeX Math** only for mathematical notation, formulas, equations, and technical symbols.
- Do not introduce any other font families.

Font usage rules:
- Do not use decorative, handwritten, serif, or display fonts.
- Preserve visual hierarchy through size, weight, spacing, alignment, and layout — not through font mixing.
- For Korean text, `IBM Plex Sans KR` handles all Korean characters correctly.

Recommended typography:
- Chapter label: IBM Plex Sans, 22px, weight 500, letter-spacing 0.08em, uppercase.
- Main title: IBM Plex Sans, 58px, weight 600, letter-spacing -0.02em.
- Subtitle: IBM Plex Sans, 34px, weight 400, letter-spacing -0.01em.
- Body text: IBM Plex Sans, 36px, weight 400.
- Equations: KaTeX Math (wrapped in `\( \)` inline or `\[ \]` display).

## Fixed Slide Structure

Maintain consistent placement across slides.

**Canvas size: 1920×1080 px.** All pixel values in CSS are for this canvas. The viewport JS scales to fit any screen.

For standard content slides:
- Chapter label: top-left of `.slide-header` (y=0, height 68px).
- Page number: top-right of `.slide-header`.
- Main title: `.slide-title` in `.title-zone` (starting at y=68px).
- Subtitle: `.slide-subtitle` directly below title.
- Body content: `.content-zone` (default top=240px, or top-210/top-260).
- Do not move the title block unless the slide is a cover, outro, or deliberate section divider.

## Content Density and Bottom Area Usage

Avoid leaving the lower half or bottom third of slides empty unless it is an intentional hero, cover, transition, or visual-impact slide.

For normal information slides:
- Fill the slide with useful supporting content while preserving readability.
- Use the lower area for secondary evidence, examples, small charts, key takeaways, footnotes, timeline strips, comparison rows, process steps, or supporting annotations.
- Do not overcrowd the slide, but avoid excessive empty whitespace that makes the slide feel unfinished.
- Prefer balanced, information-rich layouts over sparse layouts.
- If the main content is short, add a compact supporting element such as:
  - "Key implication"
  - "Why this matters"
  - "Example"
  - "Evidence"
  - "Assumption"
  - "Risk / limitation"
  - "Next step"
  - a small table
  - a mini diagram
  - a bottom summary bar

Density rule:
- Each slide should feel complete from top to bottom.
- Empty space is acceptable only when it improves hierarchy, emphasis, or visual clarity.
- Never leave large blank lower sections by accident.

## Visual Style Adaptation

Use the Apple-inspired design system for restraint, clarity, spacing discipline, minimal decoration, and strong typography, adapted for slide presentations.

Keep:
- Clean typography (IBM Plex Sans, large sizes, negative tracking on headings).
- Strong alignment (90px horizontal margins, consistent zone positions).
- Minimal decoration (no gradients, no unnecessary borders).
- Calm neutral surfaces (`--c-bg` = #f5f5f7, white canvas for graphs).
- Clear hierarchy (title → subtitle → content, accent color for emphasis only).
- Precise spacing (28px flex gap in content-zone, consistent padding).

Modify for presentations:
- Do not use webpage-like long vertical sections.
- Do not use product-tile layouts that assume scrolling.
- Do not rely on huge empty hero whitespace on every slide.
- Make each slide self-contained and information-dense enough for presentation use.

## Slide Types

Use these slide types consistently:

### Cover Slide
- `class="slide slide-cover"`.
- No `.slide-header`.
- Large title (82px), optional subtitle (42px/weight 300), cover-tag, cover-meta.
- Blue 6px line at the very bottom via `.cover-line`.

### Section Divider / Dark Slide
- `class="slide slide-dark"`.
- Chapter number and chapter title.
- Can use more whitespace than normal slides.
- Same typography, but text is white; accent line uses `--c-accent-dk`.

### Standard Content Slide
- `.slide-header` + `.title-zone` + `.content-zone`.
- Avoid empty lower regions.
- Use bottom area for supporting details, takeaways, or compact evidence.

### Interactive Graph Slide
- Same header/title structure.
- Canvas in `.graph-wrap`, legend below canvas.
- Slider row + optional preset buttons.
- Info line showing current state (intersection count, region name, etc.).

### Data / Chart Slide
- Chart (canvas) occupies main content zone.
- Use bottom or side annotation space for interpretation.
- Use IBM Plex Sans for labels; KaTeX for formulas.
- Avoid unnecessary decorative chart elements.

### Comparison Slide
- Use `.cols` for consistent columns.
- Keep headings aligned.
- Use bottom row or `.box` for conclusion or decision criteria.

### Summary / Outro Slide
- Use `.slide-outro` for the final slide.
- `class="slide slide-outro"`, no `.slide-header`.
- Centered layout, large main text (96px/700), subdued subtitle (38px/300).

## Prohibited Elements

Do not use:
- Logos or decorative brand marks.
- Random icons used as decoration.
- Multiple unrelated fonts.
- Non-1920×1080 slide canvas sizes.
- `vw`/`vh` units inside `.slide` elements.
- Excessively sparse layouts on normal content slides.
- Inconsistent title placement across slides.
- Large unused bottom whitespace.
- Decorative gradients.
- Heavy shadows on UI elements (shadows only on `<canvas>` via `.graph-wrap canvas`).
- Hardcoded hex colors (use CSS variables).
- Font sizes below 26px inside slides.

## Final Quality Check Before Output

Before generating the final HTML, verify:

1. Every slide canvas is 1920×1080 px; viewport scaling JS is present.
2. No logo or logo-like element appears anywhere.
3. IBM Plex Sans KR / IBM Plex Sans is the only text font (loaded via Google Fonts CDN).
4. KaTeX CDN links are present in `<head>` and before `</body>`.
5. KaTeX `renderMathInElement` is called inside `DOMContentLoaded`.
6. All graphs use the `Graph` class; `drawGraph*` functions are called inside `requestAnimationFrame`.
7. Chapter label, title, and subtitle positions are consistent across standard slides.
8. Every standard content slide uses `.slide-header` + `.title-zone` + `.content-zone`.
9. The bottom area of each normal content slide is meaningfully used.
10. Slide density is balanced: not crowded, not empty.
11. All CSS colors use `var(--c-*)` variables; no inline hex in components.
12. The output feels like one coherent system.
13. The first slide has `class="slide slide-cover active"` and the last has `class="slide slide-outro"`.
14. `TOTAL` in slide.js matches the actual number of slides.
