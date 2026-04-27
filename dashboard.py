"""
CMJ Force Plate Analysis Dashboard
Coaches upload CSV sessions; the app detects phases, computes metrics,
and renders a summary table + per-athlete phase overlay plots.

Run:
    streamlit run dashboard.py
"""

import io
import csv as csv_module
from dataclasses import fields as dc_fields

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.ndimage import gaussian_filter1d as _gf1

from batch_analyze import (
    smooth,
    estimate_body_weight,
    detect_phases,
    compute_metrics,
    PHASE_COLORS,
    CMJMetrics,
)

# ─────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CMJ Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 4px solid #1a1a2e;
    }
    .phase-legend span {
        display: inline-block;
        width: 12px; height: 12px;
        border-radius: 3px;
        margin-right: 4px;
        vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

METRIC_LABELS = {
    "body_weight_N":              ("Body Weight",        "N"),
    "jump_height_m":              ("Jump Height",        "m"),
    "peak_propulsive_force_N":    ("Peak Prop. Force",   "N"),
    "peak_propulsive_force_bw":   ("Peak Prop. Force",   "×BW"),
    "rfd_braking_Ns":             ("Braking RFD",        "N/s"),
    "quiet_duration_ms":          ("Quiet Duration",     "ms"),
    "unweighting_duration_ms":    ("Unweighting",        "ms"),
    "braking_duration_ms":        ("Braking",            "ms"),
    "propulsive_duration_ms":     ("Propulsive",         "ms"),
    "flight_duration_ms":         ("Flight Time",        "ms"),
    "peak_landing_force_N":       ("Peak Landing Force", "N"),
    "peak_landing_force_bw":      ("Peak Landing Force", "×BW"),
    "loading_rate_kNs":           ("Loading Rate",       "kN/s"),
    "landing_time_ms":            ("Landing Time",       "ms"),
}

HIGHLIGHT_METRICS = [
    "jump_height_m",
    "peak_propulsive_force_bw",
    "rfd_braking_Ns",
    "flight_duration_ms",
    "peak_landing_force_bw",
    "loading_rate_kNs",
    "landing_time_ms",
    "braking_duration_ms",
]


def parse_uploaded(uploaded_file) -> tuple[np.ndarray, np.ndarray]:
    content = uploaded_file.read().decode("utf-8")
    fh = io.StringIO(content)
    reader = csv_module.DictReader(fh)
    t, f = [], []
    for row in reader:
        t.append(float(row["time_s"]))
        f.append(float(row["force_N"]))
    return np.array(t), np.array(f)


def detect_fs(t: np.ndarray) -> float:
    if len(t) > 1:
        dt = float(np.median(np.diff(t)))
        if dt > 0:
            return round(1.0 / dt)
    return 1000.0


def process_file(uploaded_file) -> tuple[CMJMetrics, np.ndarray, np.ndarray, float, dict] | None:
    """Returns (metrics, t, f_smooth, bw, phase_indices) or None on error."""
    t, f = parse_uploaded(uploaded_file)
    fs = detect_fs(t)
    f_s = smooth(f)
    bw = estimate_body_weight(f_s, fs)
    ph = detect_phases(t, f_s, bw, fs)

    stem = uploaded_file.name.replace(".csv", "")
    parts = stem.rsplit("_", 3)
    if len(parts) >= 4:
        date = "_".join(parts[-3:])
        athlete_id = "_".join(parts[:-3])
    else:
        athlete_id = stem
        date = "unknown"

    metrics = compute_metrics(athlete_id, date, t, f, fs)
    return metrics, t, f_s, bw, ph


def phase_plot(t, f, bw, ph, metrics) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(11, 4))
    plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white"})

    ax.axhline(bw, color="#888", linewidth=1.2, linestyle="--",
               label=f"Body Weight ({bw:.0f} N)")
    ax.plot(t, f, color="#1a1a2e", linewidth=1.8, label="Vertical GRF", zorder=3)

    spans = [
        ("quiet",      0,                   ph["quiet_end"]),
        ("unweight",   ph["unweight_start"], ph["braking_start"]),
        ("braking",    ph["braking_start"],  ph["transfer_idx"]),
        ("propulsive", ph["transfer_idx"],   ph["propulsive_end"]),
        ("flight",     ph["propulsive_end"], ph["flight_end"]),
        ("landing",    ph["flight_end"],     ph["series_end"]),
    ]
    for name, s, e in spans:
        e_safe = min(e, len(t) - 1)
        ax.axvspan(t[s], t[e_safe], alpha=0.28, color=PHASE_COLORS[name],
                   label=name.title(), zorder=1)

    ax.set_xlabel("Time (s)", fontsize=11)
    ax.set_ylabel("Force (N)", fontsize=11)
    ax.set_title(
        f"{metrics.athlete_id}  ·  {metrics.date}  ·  "
        f"Jump Height: {metrics.jump_height_m:.3f} m  ·  "
        f"Peak Force: {metrics.peak_propulsive_force_bw:.2f}×BW",
        fontsize=12, fontweight="bold",
    )
    ax.legend(fontsize=8, loc="upper right", ncol=4,
              framealpha=0.9, edgecolor="#ccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


def metrics_to_row(m: CMJMetrics) -> dict:
    return {f.name: getattr(m, f.name) for f in dc_fields(m)}


def summary_df(all_metrics: list[CMJMetrics]) -> pd.DataFrame:
    rows = [metrics_to_row(m) for m in all_metrics]
    df = pd.DataFrame(rows)
    return df


def format_df_for_display(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for key, (label, unit) in METRIC_LABELS.items():
        if key in df.columns:
            rename[key] = f"{label} ({unit})"
    return df.rename(columns=rename)


# ─────────────────────────────────────────────────────────────────
# Demo data generator (so coaches can explore without real data)
# ─────────────────────────────────────────────────────────────────

def make_demo_csv(seed: int = 0, bw: float = 700.0, target_h_m: float = 0.40) -> str:
    """Generate physically consistent synthetic CMJ data for a given jump height."""
    rng = np.random.default_rng(seed)
    fs = 1000
    mass = bw / 9.81

    # Kinematics derived from target jump height
    v_takeoff = float(np.sqrt(2 * 9.81 * target_h_m))
    flight_time = 2 * v_takeoff / 9.81

    # Phase end-times (seconds)
    T_QUIET   = 1.00
    T_UNWEIGHT = 1.30
    T_BRAKING  = 1.55   # = transfer
    T_PROP     = 1.81
    T_FLIGHT   = T_PROP + flight_time
    T_LAND_END = T_FLIGHT + 0.40
    T_TOTAL    = T_LAND_END + 0.10

    def idx(ts): return int(ts * fs)

    t = np.arange(0, T_TOTAL, 1 / fs)
    f = np.ones_like(t) * bw

    # Quiet
    f[:idx(T_QUIET)] = bw + rng.normal(0, 4, idx(T_QUIET))

    # Unweighting
    s, e = idx(T_QUIET), idx(T_UNWEIGHT)
    x = np.linspace(0, np.pi, e - s)
    f[s:e] = bw - (260 + rng.uniform(-20, 20)) * np.sin(x) ** 1.4

    # Braking
    s, e = idx(T_UNWEIGHT), idx(T_BRAKING)
    x = np.linspace(0, 1, e - s)
    f[s:e] = f[s - 1] + (bw * 1.75 - f[s - 1]) * (3 * x**2 - 2 * x**3)

    # Propulsive: scale peak force so net impulse = mass * v_takeoff
    s, e = idx(T_BRAKING), idx(T_PROP)
    n_prop = e - s
    x = np.linspace(0, 1, n_prop)
    shape = np.sin(np.pi * x) ** 0.75
    shape[n_prop - 30:] *= np.linspace(1, 0, 30)
    # Required peak net force: integral(shape)/fs * peak_net = mass * v_takeoff
    peak_net = mass * v_takeoff * fs / float(np.sum(shape))
    f[s:e] = bw + peak_net * shape

    # Flight
    s, e = idx(T_PROP), idx(T_FLIGHT)
    if e > s:
        f[s:e] = 0

    # Landing
    s, e = idx(T_FLIGHT), idx(T_LAND_END)
    if e > s:
        n_land = e - s
        x_l = np.linspace(0, 1, n_land)
        peak_land = 1600 + rng.uniform(-200, 300)
        f[s:e] = (
            bw
            + peak_land * np.exp(-x_l * 12) * (1 - np.exp(-x_l * 60))
            + 400 * np.exp(-x_l * 5) * np.cos(2 * np.pi * x_l * 3)
        )
        f[s:s + 8] = np.linspace(0, f[s + 8], 8)

    # Pad tail with BW
    f[idx(T_LAND_END):] = bw

    f = _gf1(f, sigma=2)
    lines = ["time_s,force_N"]
    for ti, fi in zip(t, f):
        lines.append(f"{ti:.4f},{fi:.2f}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("CMJ Dashboard")
    st.caption("Countermovement Jump Force-Plate Analysis")
    st.divider()

    uploaded_files = st.file_uploader(
        "Upload session CSV files",
        type=["csv"],
        accept_multiple_files=True,
        help="Each file: two columns — `time_s` and `force_N`\nFilename: `athlete_name_YYYY-MM-DD.csv`",
    )

    use_demo = st.checkbox("Load demo sessions", value=not bool(uploaded_files))

    st.divider()
    st.markdown("**CSV format**")
    st.code("time_s,force_N\n0.000,693.2\n0.001,695.1\n...", language="text")
    st.markdown("**Filename convention**")
    st.code("jane_doe_2026-04-27.csv", language="text")
    st.divider()
    st.caption("Built with Streamlit · Analysis by batch_analyze.py")


# ─────────────────────────────────────────────────────────────────
# Build session list
# ─────────────────────────────────────────────────────────────────

sessions: list[tuple[CMJMetrics, np.ndarray, np.ndarray, float, dict]] = []
errors: list[str] = []

if uploaded_files:
    for uf in uploaded_files:
        try:
            result = process_file(uf)
            sessions.append(result)
        except Exception as exc:
            errors.append(f"{uf.name}: {exc}")

elif use_demo:
    demo_params = [
        ("athlete_alice", "2026-04-27", 42, 680.0, 0.45),
        ("athlete_bob",   "2026-04-27", 7,  750.0, 0.38),
        ("athlete_carol", "2026-04-26", 99, 615.0, 0.32),
    ]
    for athlete_id, date, seed, bw, target_h in demo_params:
        csv_str = make_demo_csv(seed=seed, bw=bw, target_h_m=target_h)

        class _FakeUpload:
            pass

        fu = _FakeUpload()
        fu.name = f"{athlete_id}_{date}.csv"  # type: ignore[attr-defined]
        fu._data = csv_str.encode()           # type: ignore[attr-defined]
        fu.read = lambda self=fu: self._data  # type: ignore[attr-defined]

        try:
            result = process_file(fu)
            sessions.append(result)
        except Exception as exc:
            errors.append(f"{athlete_id}: {exc}")


# ─────────────────────────────────────────────────────────────────
# Main content
# ─────────────────────────────────────────────────────────────────

if not sessions and not errors:
    st.markdown("## CMJ Force-Plate Analysis Dashboard")
    st.info(
        "Upload one or more CSV files in the sidebar to get started, "
        "or check **Load demo sessions** to explore with synthetic data.",
        icon="ℹ️",
    )
    st.stop()

if errors:
    for msg in errors:
        st.error(f"Failed to process: {msg}")

if not sessions:
    st.stop()

all_metrics = [s[0] for s in sessions]

tab_summary, tab_sessions = st.tabs(["Summary Table", "Individual Sessions"])

# ── Tab 1: Summary ──────────────────────────────────────────────
with tab_summary:
    st.subheader(f"{len(sessions)} session{'s' if len(sessions) != 1 else ''} processed")

    df_raw = summary_df(all_metrics)
    df_display = format_df_for_display(df_raw)

    # Colour-map numeric columns
    numeric_cols = df_display.select_dtypes(include="number").columns.tolist()
    styled = df_display.style.background_gradient(
        subset=numeric_cols, cmap="RdYlGn", axis=0
    ).format({c: "{:.3g}" for c in numeric_cols})
    st.dataframe(styled, use_container_width=True, height=min(400, 50 + 35 * len(sessions)))

    csv_bytes = df_raw.to_csv(index=False).encode()
    st.download_button(
        label="Download summary CSV",
        data=csv_bytes,
        file_name="cmj_summary.csv",
        mime="text/csv",
    )

    # Quick comparison bar chart for jump height
    if len(sessions) > 1:
        st.divider()
        st.markdown("**Jump Height Comparison**")
        labels = [f"{m.athlete_id}\n{m.date}" for m in all_metrics]
        heights = [m.jump_height_m for m in all_metrics]
        fig_bar, ax_bar = plt.subplots(figsize=(max(6, len(sessions) * 1.5), 4))
        bars = ax_bar.bar(labels, heights, color="#A8D5E2", edgecolor="#1a1a2e", linewidth=0.8)
        ax_bar.bar_label(bars, fmt="%.3f m", fontsize=9, padding=3)
        ax_bar.set_ylabel("Jump Height (m)", fontsize=11)
        ax_bar.set_ylim(0, max(heights) * 1.25)
        ax_bar.spines["top"].set_visible(False)
        ax_bar.spines["right"].set_visible(False)
        fig_bar.tight_layout()
        st.pyplot(fig_bar)
        plt.close(fig_bar)

# ── Tab 2: Individual sessions ───────────────────────────────────
with tab_sessions:
    for metrics, t, f_s, bw, ph in sessions:
        label = f"{metrics.athlete_id}  ·  {metrics.date}  ·  {metrics.jump_height_m:.3f} m"
        with st.expander(label, expanded=(len(sessions) == 1)):

            # Metric cards — 4 per row
            card_keys = HIGHLIGHT_METRICS
            cols = st.columns(4)
            for i, key in enumerate(card_keys):
                lbl, unit = METRIC_LABELS[key]
                val = getattr(metrics, key)
                fmt = f"{val:.3f}" if unit in ("m",) else f"{val:.2f}" if "×" in unit else f"{val:.1f}"
                cols[i % 4].metric(label=f"{lbl} ({unit})", value=fmt)

            st.divider()

            # Phase overlay plot
            fig = phase_plot(t, f_s, bw, ph, metrics)
            st.pyplot(fig)
            plt.close(fig)

            # Download individual plot
            buf = io.BytesIO()
            phase_plot(t, f_s, bw, ph, metrics).savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            st.download_button(
                label="Download plot",
                data=buf,
                file_name=f"{metrics.athlete_id}_{metrics.date}_plot.png",
                mime="image/png",
                key=f"dl_{metrics.athlete_id}_{metrics.date}",
            )

            # Phase duration breakdown
            st.divider()
            st.markdown("**Phase Durations**")
            phase_dur_data = {
                "Phase": ["Quiet", "Unweighting", "Braking", "Propulsive", "Flight", "Landing"],
                "Duration (ms)": [
                    metrics.quiet_duration_ms,
                    metrics.unweighting_duration_ms,
                    metrics.braking_duration_ms,
                    metrics.propulsive_duration_ms,
                    metrics.flight_duration_ms,
                    metrics.landing_time_ms,
                ],
                "Color": list(PHASE_COLORS.values())[:6],
            }
            df_phases = pd.DataFrame(phase_dur_data)

            fig_dur, ax_dur = plt.subplots(figsize=(8, 2.5))
            bars_dur = ax_dur.barh(
                df_phases["Phase"][::-1],
                df_phases["Duration (ms)"][::-1],
                color=df_phases["Color"][::-1],
                edgecolor="#555", linewidth=0.6,
            )
            ax_dur.bar_label(bars_dur, fmt="%.0f ms", fontsize=9, padding=4)
            ax_dur.set_xlabel("Duration (ms)", fontsize=10)
            ax_dur.spines["top"].set_visible(False)
            ax_dur.spines["right"].set_visible(False)
            fig_dur.tight_layout()
            st.pyplot(fig_dur)
            plt.close(fig_dur)
