"""CMJ Analyzer — FastAPI web app for macOS and iPhone."""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import numpy as np
from scipy.ndimage import gaussian_filter1d

app = FastAPI()

_BW = 700   # body weight (N)
_FS = 500   # sample rate (Hz)


def _cmj_curve():
    """Synthetic CMJ force-time curve (replicates generate_plots.py logic)."""
    t = np.arange(0, 2.90, 1 / _FS)
    f = np.ones_like(t) * _BW
    ix = lambda s: int(s * _FS)  # noqa: E731

    f[: ix(1.00)] = _BW + np.random.default_rng(0).normal(0, 4, ix(1.00))

    s, e = ix(1.00), ix(1.30)
    f[s:e] = _BW - 280 * np.sin(np.linspace(0, np.pi, e - s)) ** 1.4

    s, e = ix(1.30), ix(1.55)
    x = np.linspace(0, 1, e - s)
    f[s:e] = f[s - 1] + (_BW * 1.75 - f[s - 1]) * (3 * x**2 - 2 * x**3)

    s, e = ix(1.55), ix(1.81)
    f[s:e] = _BW * 2.1 * np.sin(np.pi * np.linspace(0, 1, e - s)) ** 0.75
    f[e - 30 : e] *= np.linspace(1, 0, 30)

    f[ix(1.81) : ix(2.42)] = 0

    s = ix(2.42)
    x = np.linspace(0, 1, len(f) - s)
    f[s:] = (
        _BW
        + 1800 * np.exp(-x * 12) * (1 - np.exp(-x * 60))
        + 400  * np.exp(-x * 5)  * np.cos(2 * np.pi * x * 3)
    )
    f[s : s + 8] = np.linspace(0, f[s + 8], 8)

    f_smooth = gaussian_filter1d(f, sigma=2)
    f_smooth[ix(1.81) : ix(2.42)] = 0.0  # clamp flight phase — filter bleeds landing spike backward
    return t.round(4), f_smooth.round(2)


@app.get("/api/cmj")
def api_cmj():
    t, f = _cmj_curve()

    pk  = lambda s, e: round(float(f[(t >= s) & (t <= e)].max()), 1)   # noqa: E731
    mn  = lambda s, e: round(float(f[(t >= s) & (t <= e)].min()), 1)   # noqa: E731
    avg = lambda s, e: round(float(f[(t >= s) & (t <= e)].mean()), 1)  # noqa: E731

    ft   = 2.42 - 1.81
    jh_m = round((9.81 * ft ** 2) / 8, 3)
    jh_c = round(jh_m * 100, 1)

    phases = {
        "quiet": {
            "label": "Quiet Phase", "color": "#A8D5E2",
            "start": 0.00, "end": 1.00,
            "description": "Athlete stands still for ≥1 s. System weight is established here — cue athletes to be completely still.",
            "metrics": {"Body Weight": f"{avg(0, 1)} N", "Duration": "1.00 s"},
        },
        "unweight": {
            "label": "Unweighting", "color": "#F5E642",
            "start": 1.00, "end": 1.30,
            "description": "Agonist muscles relax, force drops below body weight. The athlete is essentially in free fall.",
            "metrics": {
                "Min Force": f"{mn(1.0, 1.3)} N",
                "Deficit": f"{round(_BW - mn(1.0, 1.3), 1)} N below BW",
                "Duration": "0.30 s",
            },
        },
        "braking": {
            "label": "Braking Phase", "color": "#F08080",
            "start": 1.30, "end": 1.55,
            "description": "COM decelerates from peak negative velocity toward zero. Eccentric strength is the key driver here.",
            "metrics": {
                "Peak Force": f"{pk(1.3, 1.55)} N",
                "Relative": f"{round(pk(1.3, 1.55) / _BW, 2)}× BW",
                "Duration": "0.25 s",
            },
        },
        "transfer": {
            "label": "Transfer Point", "color": "#4472C4",
            "start": 1.55, "end": 1.55,
            "description": "COM velocity = 0. The amortization point. Less time here = more reactive, efficient athlete.",
            "metrics": {"Time": "1.55 s", "COM Velocity": "0 m/s"},
        },
        "propulsive": {
            "label": "Propulsive Phase", "color": "#90EE90",
            "start": 1.55, "end": 1.81,
            "description": "Forceful hip, knee, and ankle extension drives COM upward. Key metrics: PRPP and propulsive impulse.",
            "metrics": {
                "Peak Force": f"{pk(1.55, 1.81)} N",
                "Relative": f"{round(pk(1.55, 1.81) / _BW, 2)}× BW",
                "Jump Height": f"{jh_c} cm",
                "Duration": "0.26 s",
            },
        },
        "flight": {
            "label": "Flight Phase", "color": "#C8A2C8",
            "start": 1.81, "end": 2.42,
            "description": "Airborne phase. Jump height is derived from takeoff velocity — the industry gold standard.",
            "metrics": {
                "Flight Time": f"{round(ft, 3)} s",
                "Jump Height": f"{jh_c} cm ({jh_m} m)",
            },
        },
        "landing": {
            "label": "Landing Phase", "color": "#FFB347",
            "start": 2.42, "end": 2.90,
            "description": "Impact absorption from touchdown to COM stop. Bilateral asymmetry here is critical for return-to-play screening.",
            "metrics": {
                "Peak GRF": f"{pk(2.42, 2.9)} N",
                "Relative": f"{round(pk(2.42, 2.9) / _BW, 2)}× BW",
                "Duration": "0.48 s",
            },
        },
    }

    return {"time": t.tolist(), "force": f.tolist(), "bw": _BW, "phases": phases}


_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CMJ Analyzer · AlidoMartin</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d1117;color:#e6edf3;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
header{padding:1rem 1.25rem .5rem;border-bottom:1px solid #21262d}
.brand{font-size:.65rem;color:#58a6ff;letter-spacing:.12em;text-transform:uppercase;margin-bottom:.15rem}
h1{font-size:1.3rem;font-weight:700}
h1 em{font-style:normal;color:#58a6ff}
#chart-wrap{padding:.5rem}
#chart{height:280px}
@media(min-width:768px){#chart{height:400px}}
.pills-wrap{padding:.25rem 1rem .5rem;overflow-x:auto;white-space:nowrap;scrollbar-width:none;-webkit-overflow-scrolling:touch}
.pills-wrap::-webkit-scrollbar{display:none}
.pill{display:inline-block;margin-right:.4rem;padding:.42rem .9rem;border-radius:999px;border:2px solid;cursor:pointer;font-size:.78rem;font-weight:600;background:transparent;color:#e6edf3;transition:background .15s,color .15s;-webkit-tap-highlight-color:transparent;user-select:none}
.pill.active{color:#0d1117!important}
#phase-info{padding:.75rem 1.25rem 1.5rem;border-top:1px solid #21262d;min-height:120px}
.ph-name{font-size:1rem;font-weight:700;margin-bottom:.3rem}
.ph-desc{font-size:.78rem;color:#8b949e;line-height:1.55;margin-bottom:.7rem}
.metrics-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.45rem}
@media(min-width:420px){.metrics-grid{grid-template-columns:repeat(3,1fr)}}
@media(min-width:768px){.metrics-grid{grid-template-columns:repeat(4,1fr)}}
.mc{background:#161b22;border:1px solid #30363d;border-radius:.5rem;padding:.55rem .7rem}
.mc .lbl{font-size:.65rem;text-transform:uppercase;letter-spacing:.06em;color:#8b949e;margin-bottom:.15rem}
.mc .val{font-size:.95rem;font-weight:700}
footer{text-align:center;font-size:.65rem;color:#484f58;padding:.75rem;border-top:1px solid #21262d}
</style>
</head>
<body>
<header>
  <p class="brand">Sports Science Tool</p>
  <h1>CMJ <em>Analyzer</em></h1>
</header>
<div id="chart-wrap"><div id="chart"></div></div>
<div class="pills-wrap" id="pills"></div>
<div id="phase-info">
  <p style="color:#484f58;font-size:.82rem;padding-top:.25rem">Select a phase above to explore metrics</p>
</div>
<footer>by AlidoMartin &middot; Countermovement Jump Force-Time Analysis</footer>
<script>
let _d = null;

async function boot() {
  try {
    const res = await fetch('/api/cmj');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    _d = await res.json();
    renderChart(null);
    buildPills();
  } catch (err) {
    document.getElementById('phase-info').innerHTML =
      '<p style="color:#f87171;font-size:.85rem">Failed to load data. Is the server running? (' + err.message + ')</p>';
  }
}

function renderChart(activeKey) {
  const { time: t, force: f, bw, phases } = _d;
  const traces = [];

  traces.push({
    x: t, y: t.map(() => bw),
    mode: 'lines',
    line: { color: '#484f58', width: 1, dash: 'dot' },
    name: 'Body Weight (' + bw + ' N)',
    hoverinfo: 'skip',
  });

  Object.entries(phases).forEach(([key, ph]) => {
    if (ph.start === ph.end) return;
    const inR = (_, i) => t[i] >= ph.start && t[i] <= ph.end;
    traces.push({
      x: t.filter(inR), y: f.filter(inR),
      fill: 'tozeroy',
      fillcolor: ph.color + (key === activeKey ? '66' : '1a'),
      line: { width: 0 },
      showlegend: false,
      hoverinfo: 'skip',
    });
  });

  traces.push({
    x: t, y: f,
    mode: 'lines',
    line: { color: '#c9d1d9', width: 2 },
    name: 'Vertical GRF',
    hovertemplate: '%{y:.0f} N<extra></extra>',
  });

  const tp = phases.transfer;
  const ti = t.findIndex(v => Math.abs(v - tp.start) < 0.004);

  Plotly.react('chart', traces, {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { t: 6, r: 10, b: 38, l: 52 },
    xaxis: { title: 'Time (s)', color: '#8b949e', gridcolor: '#21262d', zeroline: false, tickfont: { size: 10, color: '#8b949e' } },
    yaxis: { title: 'Force (N)', color: '#8b949e', gridcolor: '#21262d', zeroline: false, tickfont: { size: 10, color: '#8b949e' } },
    legend: { x: 0, y: 1, font: { color: '#8b949e', size: 9 }, bgcolor: 'transparent', orientation: 'h' },
    hovermode: 'x unified',
    shapes: ti >= 0 ? [{ type: 'line', x0: tp.start, x1: tp.start, y0: 0, y1: f[ti] + 80, line: { color: '#4472C4', width: 2, dash: 'dash' } }] : [],
  }, { responsive: true, displayModeBar: false });
}

function buildPills() {
  const wrap = document.getElementById('pills');
  Object.entries(_d.phases).forEach(([key, ph]) => {
    const btn = document.createElement('button');
    btn.className = 'pill';
    btn.textContent = ph.label;
    btn.style.borderColor = ph.color;
    btn.dataset.key = key;
    btn.addEventListener('click', () => selectPhase(key));
    wrap.appendChild(btn);
  });
}

function selectPhase(key) {
  document.querySelectorAll('.pill').forEach(p => {
    p.classList.remove('active');
    p.style.background = 'transparent';
    p.style.color = '#e6edf3';
  });
  const btn = document.querySelector('.pill[data-key="' + key + '"]');
  const ph = _d.phases[key];
  btn.classList.add('active');
  btn.style.background = ph.color;
  renderChart(key);
  const cards = Object.entries(ph.metrics)
    .map(([l, v]) => '<div class="mc"><div class="lbl">' + l + '</div><div class="val">' + v + '</div></div>')
    .join('');
  document.getElementById('phase-info').innerHTML =
    '<p class="ph-name" style="color:' + ph.color + '">' + ph.label + '</p>' +
    '<p class="ph-desc">' + ph.description + '</p>' +
    '<div class="metrics-grid">' + cards + '</div>';
}

boot();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return _HTML
