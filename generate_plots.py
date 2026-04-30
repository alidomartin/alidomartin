"""
Generate CMJ phase visualization plots for GitHub profile README.
Produces styled matplotlib charts matching the reference style.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.ndimage import gaussian_filter1d
import os

os.makedirs("images", exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

BW = 700  # Body weight in Newtons
FS = 500  # samples/sec

# ──────────────────────────────────────────────
# Build a realistic CMJ jump force-time curve
# ──────────────────────────────────────────────
def build_cmj_curve():
    """Return (time_s, force_N, phase_dict)."""
    # Phase boundaries in seconds
    PH = {
        "quiet":      (0.00, 1.00),
        "unweight":   (1.00, 1.30),
        "braking":    (1.30, 1.55),
        "transfer":   1.55,
        "propulsive": (1.55, 1.81),
        "flight":     (1.81, 2.42),
        "landing":    (2.42, 2.90),
    }

    t = np.arange(0, 2.90, 1 / FS)
    f = np.ones_like(t) * BW

    def idx(ts): return int(ts * FS)

    # Quiet phase – steady BW with tiny noise
    f[: idx(1.00)] = BW + np.random.default_rng(0).normal(0, 4, idx(1.00))

    # Unweighting – smooth dip
    s, e = idx(1.00), idx(1.30)
    x = np.linspace(0, np.pi, e - s)
    f[s:e] = BW - 280 * np.sin(x) ** 1.4

    # Braking – rise from bottom to ~1.8× BW
    s, e = idx(1.30), idx(1.55)
    x = np.linspace(0, 1, e - s)
    start = f[s - 1]
    peak_b = BW * 1.75
    f[s:e] = start + (peak_b - start) * (3 * x**2 - 2 * x**3)

    # Propulsive – peak ~2.1× BW then taper to 0
    s, e = idx(1.55), idx(1.81)
    x = np.linspace(0, 1, e - s)
    f[s:e] = BW * 2.1 * np.sin(np.pi * x) ** 0.75
    f[e - 30 : e] *= np.linspace(1, 0, 30)

    # Flight – zero
    s, e = idx(1.81), idx(2.42)
    f[s:e] = 0

    # Landing – sharp impact peak, oscillating settle
    s = idx(2.42)
    n_land = len(f) - s
    x = np.linspace(0, 1, n_land)
    f[s:] = (
        BW
        + 1800 * np.exp(-x * 12) * (1 - np.exp(-x * 60))
        + 400 * np.exp(-x * 5) * np.cos(2 * np.pi * x * 3)
    )
    f[s : s + 8] = np.linspace(0, f[s + 8], 8)

    f = gaussian_filter1d(f, sigma=2)
    return t, f, PH


T, F, PH = build_cmj_curve()

# Color palette matching the reference style
COLORS = {
    "quiet":      "#A8D5E2",   # light blue
    "unweight":   "#F5E642",   # yellow
    "braking":    "#F08080",   # coral/red
    "transfer":   "#4472C4",   # blue dot
    "propulsive": "#90EE90",   # green
    "flight":     "#C8A2C8",   # lilac
    "landing":    "#FFB347",   # orange
}

LINE_COLOR = "#1a1a2e"
BW_COLOR   = "#888888"

# ──────────────────────────────────────────────
# Helper: draw the full curve, shade one phase
# ──────────────────────────────────────────────
def plot_phase(ax, phase_key, shade_alpha=0.35, show_bw=True):
    if show_bw:
        ax.axhline(BW, color=BW_COLOR, linewidth=1.2, linestyle="--", label=f"Body Weight ({BW} N)")

    ax.plot(T, F, color=LINE_COLOR, linewidth=2.0, label="Vertical GRF", zorder=3)

    color = COLORS[phase_key]
    if phase_key == "transfer":
        # single vertical line + dot
        ax.axvline(PH["transfer"], color=color, linewidth=2, linestyle="--", zorder=4)
        ti = int(PH["transfer"] * FS)
        ax.scatter([T[ti]], [F[ti]], color=color, s=80, zorder=5)
    else:
        s, e = PH[phase_key]
        mask = (T >= s) & (T <= e)
        ax.fill_between(T, F, BW if show_bw else 0,
                        where=mask, color=color, alpha=shade_alpha, zorder=2)
        ax.fill_between(T, F, 0,
                        where=mask, color=color, alpha=0.15, zorder=1)

    ax.set_xlabel("Time (s)", fontsize=11)
    ax.set_ylabel("Force (N)", fontsize=11)
    ax.set_xlim(T[0], T[-1])
    ax.set_ylim(-50, BW * 2.5)
    ax.tick_params(labelsize=9)

    # X-axis tick labels matching Hawkin style
    ticks = [0, 1.0, 1.4, 1.55, 1.81, 2.42]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(v) for v in ticks])


# ──────────────────────────────────────────────
# 1. QUIET PHASE
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
plot_phase(ax, "quiet")
ax.set_title("Quiet Phase", fontsize=14, fontweight="bold", pad=10)
ax.text(0.50, 1580,
        "\"The quiet phase sets the stage\nfor all other metrics.\"",
        fontsize=8.5, style="italic", color="#444", ha="center",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#aaa", lw=0.8))
legend_patches = [
    mpatches.Patch(color=COLORS["quiet"], alpha=0.6, label="Quiet Phase"),
    plt.Line2D([0], [0], color=LINE_COLOR, lw=2, label="Vertical GRF"),
    plt.Line2D([0], [0], color=BW_COLOR, lw=1.2, ls="--", label=f"Body Weight ({BW} N)"),
]
ax.legend(handles=legend_patches, fontsize=8, loc="upper right")
plt.tight_layout()
plt.savefig("images/quiet_phase.png", dpi=150, bbox_inches="tight")
plt.close()
print("quiet_phase.png saved")

# ──────────────────────────────────────────────
# 2. UNWEIGHTING PHASE
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
plot_phase(ax, "unweight")
ax.set_title("Unweighting Phase", fontsize=14, fontweight="bold", pad=10)
ax.text(1.15, 1580,
        "\"The first half of the\nunweighting phase can be\nthought of as a free fall.\"",
        fontsize=8, style="italic", color="#444", ha="center",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#aaa", lw=0.8))
legend_patches = [
    mpatches.Patch(color=COLORS["unweight"], alpha=0.6, label="Unweighting Phase"),
    plt.Line2D([0], [0], color=LINE_COLOR, lw=2, label="Vertical GRF"),
    plt.Line2D([0], [0], color=BW_COLOR, lw=1.2, ls="--", label=f"Body Weight ({BW} N)"),
]
ax.legend(handles=legend_patches, fontsize=8, loc="upper right")
plt.tight_layout()
plt.savefig("images/unweighting_phase.png", dpi=150, bbox_inches="tight")
plt.close()
print("unweighting_phase.png saved")

# ──────────────────────────────────────────────
# 3. BRAKING PHASE
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
plot_phase(ax, "braking")
ax.set_title("Braking Phase", fontsize=14, fontweight="bold", pad=10)
legend_patches = [
    mpatches.Patch(color=COLORS["braking"], alpha=0.6, label="Braking Phase"),
    plt.Line2D([0], [0], color=LINE_COLOR, lw=2, label="Vertical GRF"),
    plt.Line2D([0], [0], color=BW_COLOR, lw=1.2, ls="--", label=f"Body Weight ({BW} N)"),
]
ax.legend(handles=legend_patches, fontsize=8, loc="upper right")
plt.tight_layout()
plt.savefig("images/braking_phase.png", dpi=150, bbox_inches="tight")
plt.close()
print("braking_phase.png saved")

# ──────────────────────────────────────────────
# 4. TRANSFER POINT
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
plot_phase(ax, "transfer")
ax.set_title("Transfer Point", fontsize=14, fontweight="bold", pad=10)
ti = int(PH["transfer"] * FS)
ax.annotate("Transfer Point\n(v = 0)", xy=(T[ti], F[ti]),
            xytext=(T[ti] + 0.12, F[ti] + 350),
            fontsize=8.5, color=COLORS["transfer"],
            arrowprops=dict(arrowstyle="->", color=COLORS["transfer"]))
legend_patches = [
    mpatches.Patch(color=COLORS["transfer"], alpha=0.6, label="Transfer Point"),
    plt.Line2D([0], [0], color=LINE_COLOR, lw=2, label="Vertical GRF"),
    plt.Line2D([0], [0], color=BW_COLOR, lw=1.2, ls="--", label=f"Body Weight ({BW} N)"),
]
ax.legend(handles=legend_patches, fontsize=8, loc="upper right")
plt.tight_layout()
plt.savefig("images/transfer_point.png", dpi=150, bbox_inches="tight")
plt.close()
print("transfer_point.png saved")

# ──────────────────────────────────────────────
# 5. PROPULSIVE PHASE
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
plot_phase(ax, "propulsive")
ax.set_title("Propulsive Phase", fontsize=14, fontweight="bold", pad=10)
legend_patches = [
    mpatches.Patch(color=COLORS["propulsive"], alpha=0.6, label="Propulsive Phase"),
    plt.Line2D([0], [0], color=LINE_COLOR, lw=2, label="Vertical GRF"),
    plt.Line2D([0], [0], color=BW_COLOR, lw=1.2, ls="--", label=f"Body Weight ({BW} N)"),
]
ax.legend(handles=legend_patches, fontsize=8, loc="upper right")
plt.tight_layout()
plt.savefig("images/propulsive_phase.png", dpi=150, bbox_inches="tight")
plt.close()
print("propulsive_phase.png saved")

# ──────────────────────────────────────────────
# 6. FLIGHT PHASE
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
plot_phase(ax, "flight", show_bw=False)
ax.set_title("Flight Phase", fontsize=14, fontweight="bold", pad=10)
legend_patches = [
    mpatches.Patch(color=COLORS["flight"], alpha=0.6, label="Flight Phase"),
    plt.Line2D([0], [0], color=LINE_COLOR, lw=2, label="Vertical GRF"),
]
ax.legend(handles=legend_patches, fontsize=8, loc="upper right")
plt.tight_layout()
plt.savefig("images/flight_phase.png", dpi=150, bbox_inches="tight")
plt.close()
print("flight_phase.png saved")

# ──────────────────────────────────────────────
# 7. LANDING PHASE (on jump curve)
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
plot_phase(ax, "landing")
ax.set_title("Landing Phase", fontsize=14, fontweight="bold", pad=10)
legend_patches = [
    mpatches.Patch(color=COLORS["landing"], alpha=0.6, label="Landing Phase"),
    plt.Line2D([0], [0], color=LINE_COLOR, lw=2, label="Vertical GRF"),
    plt.Line2D([0], [0], color=BW_COLOR, lw=1.2, ls="--", label=f"Body Weight ({BW} N)"),
]
ax.legend(handles=legend_patches, fontsize=8, loc="upper right")
plt.tight_layout()
plt.savefig("images/landing_phase.png", dpi=150, bbox_inches="tight")
plt.close()
print("landing_phase.png saved")


# ══════════════════════════════════════════════
# CMJ LANDING DETAIL CURVES (reference style)
# Matching: Phase 1 Loading / Phase 2 Attenuation / Phase 3 Control
# ══════════════════════════════════════════════

def build_landing_curve():
    """Realistic CMJ landing GRF + COM velocity."""
    # Time in milliseconds, 0‑180ms
    t_ms = np.arange(0, 181, 0.5)
    t_s  = t_ms / 1000

    # GRF shape: double-hump characteristic of landing
    grf = (
        200 * np.exp(-((t_ms -  9) ** 2) / (2 * 8**2))   # early small hump
        + 2744 * np.exp(-((t_ms - 62) ** 2) / (2 * 22**2)) # main loading peak
        + 1050 * np.exp(-((t_ms - 152) ** 2) / (2 * 20**2)) # control hump
        + 638  # body weight baseline
    )
    # Add small first-contact hump
    grf += 1200 * np.exp(-((t_ms - 10) ** 2) / (2 * 12**2))
    grf = gaussian_filter1d(grf, sigma=2)

    # COM velocity: starts at -3.16 m/s, increases (becomes less negative) to 0
    # Simple sigmoid-like rise with slight overshoot
    v_com = -3.16 + 3.16 * (t_ms / 148) ** 0.6
    v_com[t_ms > 148] = 0 + (t_ms[t_ms > 148] - 148) * (-3.5 / 32)
    v_com = np.clip(v_com, -3.5, 0.55)
    v_com = gaussian_filter1d(v_com, sigma=3)

    phases = {
        "loading":     (0,   62),   # ms
        "attenuation": (62,  125),
        "control":     (125, 148),
    }
    return t_ms, grf, v_com, phases

T_L, GRF_L, VEL_L, PH_L = build_landing_curve()

LAND_COLORS = {
    "loading":     "#E8A0A0",  # pinkish red
    "attenuation": "#F5C89A",  # orange
    "control":     "#A8D5C8",  # teal
}

def plot_landing_phase(ax1, highlight=None, title="", show_all_labels=True):
    # BW line
    ax1.axhline(638, color="#999", linewidth=1.1, linestyle="--", zorder=1)

    # Shaded regions
    shades = {
        "loading":     LAND_COLORS["loading"],
        "attenuation": LAND_COLORS["attenuation"],
        "control":     LAND_COLORS["control"],
    }
    for ph, color in shades.items():
        s, e = PH_L[ph]
        mask = (T_L >= s) & (T_L <= e)
        alpha = 0.55 if ph == highlight else 0.18
        ax1.fill_between(T_L, GRF_L, 0, where=mask, color=color, alpha=alpha, zorder=2)

    # GRF line
    ax1.plot(T_L, GRF_L, color=LINE_COLOR, linewidth=2.2, label="Vertical GRF", zorder=3)
    ax1.set_ylabel("Vertical GRF (N)", fontsize=10)
    ax1.set_xlabel("Landing Time (ms)", fontsize=10)
    ax1.set_xlim(0, 180)
    ax1.set_ylim(0, 3200)
    ax1.tick_params(labelsize=9)

    # COM velocity on twin axis
    ax2 = ax1.twinx()
    ax2.plot(T_L, VEL_L, color="#4a4a7a", linewidth=1.8, linestyle="--",
             label="COM Velocity", zorder=3)
    ax2.set_ylabel("COM Velocity (m/s)", fontsize=10, color="#4a4a7a")
    ax2.set_ylim(-3.8, 0.8)
    ax2.tick_params(labelsize=9, colors="#4a4a7a")
    ax2.axhline(638, alpha=0)  # keep scale

    if title:
        ax1.set_title(title, fontsize=15, fontweight="bold", pad=12)

    return ax2

# ──────────────────────────────────────────────
# Phase 1: Loading
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
ax2 = plot_landing_phase(ax, highlight="loading", title="Phase 1: Loading")
fig.suptitle("", fontsize=12)

# Peak annotation
ax.scatter([62], [GRF_L[T_L == 62][0]], color="#cc3333", s=80, zorder=5)
ax.annotate("Peak: 2744 N\n(4.3× BW)",
            xy=(62, GRF_L[T_L == 62][0]),
            xytext=(40, 2500),
            fontsize=9, color="#cc3333", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#cc3333"))

# Phase label arrow at top
ax.annotate("", xy=(62, 3050), xytext=(0, 3050),
            arrowprops=dict(arrowstyle="->", color="#cc3333", lw=1.5))
ax.text(31, 3100, "LOADING", color="#cc3333", fontsize=9, ha="center", fontweight="bold")
ax.text(93, 3100, "ATTENUATION", color="#e8953a", fontsize=9, ha="center", alpha=0.5)

# Stats box
stats = ("— LOADING PHASE —\n"
         "Contact → Peak GRF\n\n"
         f"Peak GRF      2744 N\n"
         f"Peak Force    4.3× BW\n"
         f"Loading Time  62.9 ms\n"
         f"Loading Rate  43.6 kN/s\n"
         f"v at contact  3.161 m/s\n"
         f"Jump Height   0.509 m")
ax.text(135, 2700, stats, fontsize=7.5, family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#cc3333", lw=1.5),
        va="top")

legend_items = [
    plt.Line2D([0], [0], color=LINE_COLOR, lw=2, label="Vertical GRF"),
    plt.Line2D([0], [0], color="#999", lw=1.1, ls="--", label="Body Weight (~638 N)"),
    plt.Line2D([0], [0], color="#4a4a7a", lw=1.8, ls="--", label="COM Velocity"),
]
ax.legend(handles=legend_items, fontsize=8, loc="upper left")
plt.tight_layout()
plt.savefig("images/loading_phase.png", dpi=150, bbox_inches="tight")
plt.close()
print("loading_phase.png saved")

# ──────────────────────────────────────────────
# Phase 2: Attenuation
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
ax2 = plot_landing_phase(ax, highlight="attenuation", title="Phase 2: Attenuation")

ax.scatter([62], [GRF_L[T_L == 62][0]], color="#e8953a", s=80, zorder=5)
min_idx = np.argmin(GRF_L[(T_L >= 62) & (T_L <= 125)]) + np.searchsorted(T_L, 62)
ax.scatter([T_L[min_idx]], [GRF_L[min_idx]], color="#e8953a", s=80, zorder=5)
ax.annotate(f"Min: {int(GRF_L[min_idx])} N",
            xy=(T_L[min_idx], GRF_L[min_idx]),
            xytext=(T_L[min_idx] - 20, GRF_L[min_idx] - 250),
            fontsize=9, color="#e8953a", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#e8953a"))

ax.annotate("", xy=(125, 3050), xytext=(62, 3050),
            arrowprops=dict(arrowstyle="<->", color="#e8953a", lw=1.5))
ax.text(93, 3100, "ATTENUATION", color="#e8953a", fontsize=9, ha="center", fontweight="bold")
ax.text(31, 3100, "LOADING", color="#cc3333", fontsize=9, ha="center", alpha=0.5)

stats = ("— ATTENUATION PHASE —\n"
         "Peak GRF → Local Min\n\n"
         f"Atten Time    61.6 ms\n"
         f"Avg Force     1688 N\n"
         f"Force Atten   30.3 kN/s\n"
         f"Min GRF        875 N\n"
         f"v start       1.88 m/s ↓\n"
         f"v end         0.44 m/s ↓")
ax.text(135, 2700, stats, fontsize=7.5, family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#e8953a", lw=1.5),
        va="top")

legend_items = [
    plt.Line2D([0], [0], color=LINE_COLOR, lw=2, label="Vertical GRF"),
    plt.Line2D([0], [0], color="#999", lw=1.1, ls="--", label="Body Weight (~638 N)"),
    plt.Line2D([0], [0], color="#4a4a7a", lw=1.8, ls="--", label="COM Velocity"),
]
ax.legend(handles=legend_items, fontsize=8, loc="upper left")
plt.tight_layout()
plt.savefig("images/attenuation_phase.png", dpi=150, bbox_inches="tight")
plt.close()
print("attenuation_phase.png saved")

# ──────────────────────────────────────────────
# Phase 3: Control
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
ax2 = plot_landing_phase(ax, highlight="control", title="Phase 3: Control")

ctrl_end_idx = np.searchsorted(T_L, 148)
ax.scatter([T_L[ctrl_end_idx]], [GRF_L[ctrl_end_idx]], color="#2a9d8f", s=80, zorder=5)
ax.annotate("v = 0 m/s\n(COM stops)",
            xy=(T_L[ctrl_end_idx], GRF_L[ctrl_end_idx]),
            xytext=(T_L[ctrl_end_idx] - 30, GRF_L[ctrl_end_idx] + 400),
            fontsize=8.5, color="#2a9d8f", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#2a9d8f"))

ax.annotate("", xy=(148, 3050), xytext=(125, 3050),
            arrowprops=dict(arrowstyle="<->", color="#2a9d8f", lw=1.5))
ax.text(136, 3100, "CONTROL", color="#2a9d8f", fontsize=9, ha="center", fontweight="bold")
ax.text(31, 3100, "LOADING", color="#cc3333", fontsize=9, ha="center", alpha=0.4)
ax.text(93, 3100, "ATTENUATION", color="#e8953a", fontsize=9, ha="center", alpha=0.4)

stats = ("— CONTROL PHASE —\n"
         "Local Min → v = 0\n\n"
         f"Control Time  23.5 ms\n"
         f"Total Land T  148.0 ms\n"
         f"Avg Force      941 N\n"
         f"Amort Force   1025 N\n"
         f"Jump Height   0.509 m\n"
         f"LPI           3.44 m/s\n"
         f"mRSI          0.876")
ax.text(135, 2700, stats, fontsize=7.5, family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#2a9d8f", lw=1.5),
        va="top")

legend_items = [
    plt.Line2D([0], [0], color=LINE_COLOR, lw=2, label="Vertical GRF"),
    plt.Line2D([0], [0], color="#999", lw=1.1, ls="--", label="Body Weight (~638 N)"),
    plt.Line2D([0], [0], color="#4a4a7a", lw=1.8, ls="--", label="COM Velocity"),
]
ax.legend(handles=legend_items, fontsize=8, loc="upper left")
plt.tight_layout()
plt.savefig("images/control_phase.png", dpi=150, bbox_inches="tight")
plt.close()
print("control_phase.png saved")

# ──────────────────────────────────────────────
# Full Landing Summary (all 3 phases)
# ──────────────────────────────────────────────
fig = plt.figure(figsize=(11, 8))
ax_main = fig.add_axes([0.08, 0.42, 0.88, 0.50])
ax2 = plot_landing_phase(ax_main, highlight=None, title="CMJ Landing — Full Phase Summary")

# Annotations
ax_main.scatter([62], [GRF_L[T_L == 62][0]], color="#cc3333", s=70, zorder=5)
ax_main.annotate("Peak\n2744 N (4.3×BW)", xy=(62, GRF_L[T_L == 62][0]),
                 xytext=(38, 2550), fontsize=8, color="#cc3333", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#cc3333"))
ax_main.scatter([T_L[min_idx]], [GRF_L[min_idx]], color="#e8953a", s=70, zorder=5)
ax_main.annotate("Min GRF\n875 N", xy=(T_L[min_idx], GRF_L[min_idx]),
                 xytext=(T_L[min_idx] + 8, GRF_L[min_idx] - 220),
                 fontsize=8, color="#e8953a", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#e8953a"))
ax_main.scatter([T_L[ctrl_end_idx]], [GRF_L[ctrl_end_idx]], color="#2a9d8f", s=70, zorder=5)
ax_main.annotate("v = 0 m/s\n(COM stops)", xy=(T_L[ctrl_end_idx], GRF_L[ctrl_end_idx]),
                 xytext=(T_L[ctrl_end_idx] - 32, GRF_L[ctrl_end_idx] + 450),
                 fontsize=8, color="#2a9d8f", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#2a9d8f"))

# Phase arrows at top
for (label, s, e, col) in [
    ("LOADING",     0,   62,  "#cc3333"),
    ("ATTENUATION", 62, 125,  "#e8953a"),
    ("CONTROL",    125, 148,  "#2a9d8f"),
]:
    mid = (s + e) / 2
    ax_main.annotate("", xy=(e, 3050), xytext=(s, 3050),
                     arrowprops=dict(arrowstyle="<->", color=col, lw=1.4))
    ax_main.text(mid, 3110, label, color=col, fontsize=8.5, ha="center", fontweight="bold")

legend_items = [
    plt.Line2D([0], [0], color=LINE_COLOR, lw=2, label="Vertical GRF"),
    plt.Line2D([0], [0], color="#999", lw=1.1, ls="--", label="Body Weight (~638 N)"),
    plt.Line2D([0], [0], color="#4a4a7a", lw=1.8, ls="--", label="COM Velocity"),
]
ax_main.legend(handles=legend_items, fontsize=8, loc="upper left")

# ─ Summary table ─
table_data = {
    "Phase 1: Loading":     {"color": "#cc3333", "sub": "Contact → Peak GRF",
                              "rows": [("Peak GRF:", "2744 N"), ("Peak Force:", "4.3× BW"),
                                       ("Loading Time:", "62.9 ms"), ("Loading Rate:", "43.6 kN/s"),
                                       ("v at Contact:", "3.161 m/s"), ("Jump Height:", "0.509 m")]},
    "Phase 2: Attenuation": {"color": "#e8953a", "sub": "Peak GRF → Local Min",
                              "rows": [("Atten Time:", "61.6 ms"), ("Avg Force:", "1688 N"),
                                       ("Force Atten:", "30.3 kN/s"), ("Min GRF:", "875 N"),
                                       ("v start:", "1.88 m/s ↓"), ("v end:", "0.44 m/s ↓")]},
    "Phase 3: Control":     {"color": "#2a9d8f", "sub": "Local Min → v = 0",
                              "rows": [("Control Time:", "23.5 ms"), ("Total Land T:", "148.0 ms"),
                                       ("Avg Force:", "941 N"), ("Amort Force:", "1025 N"),
                                       ("LPI:", "3.44 m/s"), ("mRSI:", "0.876")]},
}

box_width = 0.27
box_left  = [0.06, 0.37, 0.68]
box_bot   = 0.03
box_h     = 0.32

for i, (ph_name, ph_data) in enumerate(table_data.items()):
    ax_box = fig.add_axes([box_left[i], box_bot, box_width, box_h])
    ax_box.set_xlim(0, 1); ax_box.set_ylim(0, 1)
    ax_box.axis("off")
    ax_box.add_patch(mpatches.FancyBboxPatch((0, 0), 1, 1,
        boxstyle="round,pad=0.02", fc="white", ec=ph_data["color"], lw=2))
    ax_box.text(0.5, 0.90, ph_name, ha="center", va="center", fontsize=10,
                fontweight="bold", color=ph_data["color"])
    ax_box.text(0.5, 0.80, ph_data["sub"], ha="center", va="center",
                fontsize=7.5, color="#666", style="italic")
    ax_box.axhline(0.74, color="#ddd", lw=0.8, xmin=0.05, xmax=0.95)
    for j, (label, val) in enumerate(ph_data["rows"]):
        y = 0.65 - j * 0.10
        ax_box.text(0.08, y, label, ha="left", va="center", fontsize=8.5, color="#333")
        ax_box.text(0.92, y, val, ha="right", va="center", fontsize=8.5,
                    fontweight="bold", color="#111")

plt.savefig("images/landing_summary.png", dpi=150, bbox_inches="tight")
plt.close()
print("landing_summary.png saved")

# ══════════════════════════════════════════════
# INDIVIDUALIZED WORKOUT PRESCRIPTION
# CMJ readiness metrics → training type distribution
# ══════════════════════════════════════════════

WORKOUT_TYPES = [
    "Speed", "Power", "Very Heavy", "Heavy",
    "Hypertrophy", "Light", "Very Light", "Base",
]
PRESC_COLORS = [
    "#E74C3C",  # Speed      — crimson
    "#E67E22",  # Power      — orange
    "#9B59B6",  # Very Heavy — violet
    "#3498DB",  # Heavy      — cobalt
    "#F39C12",  # Hypertrophy — amber
    "#77DD77",  # Light      — eucalyptus
    "#1ABC9C",  # Very Light — teal
    "#7F8C8D",  # Base       — slate-grey
]
ATHLETES_PRESC = [
    {"name": "Athlete 1", "rsi": 0.89, "jump_m": 0.52, "asym": 3,  "brfd": 4820,
     "pct": [5, 25, 35, 13, 22, 0, 0, 0]},
    {"name": "Athlete 2", "rsi": 0.71, "jump_m": 0.43, "asym": 8,  "brfd": 3540,
     "pct": [4, 10, 8, 18, 27, 18, 9, 6]},
    {"name": "Athlete 3", "rsi": 0.76, "jump_m": 0.47, "asym": 5,  "brfd": 3980,
     "pct": [8, 20, 12, 20, 15, 15, 7, 3]},
    {"name": "Athlete 4", "rsi": 0.58, "jump_m": 0.36, "asym": 19, "brfd": 2810,
     "pct": [0, 5, 5, 12, 20, 25, 20, 13]},
    {"name": "Athlete 5", "rsi": 0.81, "jump_m": 0.49, "asym": 6,  "brfd": 4320,
     "pct": [10, 22, 20, 18, 16, 9, 3, 2]},
]

_P_BG  = "#2C3E50"
_P_TXT = "#FFFFFF"
_P_DIM = "#95A5A6"
_prng  = np.random.default_rng(7)

with plt.rc_context({
    "figure.facecolor": _P_BG, "axes.facecolor": _P_BG,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
}):
    _pfig = plt.figure(figsize=(16, 9), facecolor=_P_BG)

    _pfig.text(0.03, 0.976, "INDIVIDUALIZED WORKOUT PRESCRIPTION",
               fontsize=17, fontweight="bold", color=_P_TXT, va="top")
    _pfig.text(0.97, 0.976, "CMJ READINESS  →  TRAINING PRESCRIPTION",
               fontsize=8.5, color=_P_DIM, va="top", ha="right")
    _pfig.text(0.03, 0.938,
               "Same system. Different prescriptions driven by CMJ readiness, "
               "neuromuscular output, and asymmetry index.",
               fontsize=8.5, color=_P_DIM, va="top")

    # Legend squares using figure-space patches
    _leg_y = 0.895
    for _li, (_wt, _pc) in enumerate(zip(WORKOUT_TYPES, PRESC_COLORS)):
        _lx = 0.215 + _li * 0.095
        _sq = mpatches.Rectangle((_lx, _leg_y - 0.014), 0.012, 0.026,
                                   facecolor=_pc, edgecolor="none",
                                   transform=_pfig.transFigure, clip_on=False)
        _pfig.add_artist(_sq)
        _pfig.text(_lx + 0.015, _leg_y, _wt, fontsize=7.5, color=_P_TXT, va="center")

    _pfig.text(0.215, 0.863, "SESSION TIMELINE",
               fontsize=7.5, color=_P_DIM, fontweight="bold", va="top")
    _pfig.text(0.455, 0.863, "WORKOUT TYPE DISTRIBUTION",
               fontsize=7.5, color=_P_DIM, fontweight="bold", va="top")

    _ROW_BOT = [0.685, 0.535, 0.385, 0.235, 0.075]
    _ROW_H   = 0.135

    for _i, _ath in enumerate(ATHLETES_PRESC):
        _y0  = _ROW_BOT[_i]
        _pct = np.array(_ath["pct"], dtype=float)

        _pfig.text(0.03, _y0 + _ROW_H * 0.88, _ath["name"],
                   fontsize=11, fontweight="bold", color=_P_TXT, va="top")
        _pfig.text(0.03, _y0 + _ROW_H * 0.60,
                   f"RSI: {_ath['rsi']:.2f}  |  JH: {_ath['jump_m']:.2f} m",
                   fontsize=7.5, color=_P_DIM, va="top")
        _ac = "#E8541D" if _ath["asym"] >= 15 else _P_TXT if _ath["asym"] <= 5 else _P_DIM
        _pfig.text(0.03, _y0 + _ROW_H * 0.35,
                   f"Asym: {_ath['asym']}%  |  Brk RFD: {_ath['brfd']:,} N/s",
                   fontsize=7.5, color=_ac, va="top")

        # Session timeline grid (2 rows × 16 cols = 32 sessions)
        _ax_t = _pfig.add_axes([0.215, _y0 + 0.005, 0.225, _ROW_H - 0.010],
                                 facecolor=_P_BG)
        _ax_t.set_xlim(0, 16); _ax_t.set_ylim(0, 2)
        _ax_t.axis("off")
        _probs = _pct / _pct.sum()
        _sess  = _prng.choice(len(WORKOUT_TYPES), size=32, p=_probs)
        for _j, _wi in enumerate(_sess):
            _ax_t.add_patch(plt.Rectangle(
                (_j % 16 + 0.07, 1.12 - _j // 16), 0.80, 0.72,
                facecolor=PRESC_COLORS[_wi],
                edgecolor=_P_BG, linewidth=0.7, zorder=2,
            ))

        # Stacked horizontal bar
        _ax_b = _pfig.add_axes([0.450, _y0 + 0.018, 0.520, _ROW_H - 0.034],
                                 facecolor=_P_BG)
        _ax_b.set_xlim(0, 100); _ax_b.set_ylim(0, 1)
        _ax_b.axis("off")
        _xp = 0.0
        for _p, _pc in zip(_pct, PRESC_COLORS):
            if _p <= 0:
                continue
            _ax_b.add_patch(plt.Rectangle(
                (_xp, 0.12), _p, 0.76,
                facecolor=_pc, edgecolor=_P_BG, linewidth=0.6,
            ))
            if _p >= 8:
                _ax_b.text(_xp + _p / 2, 0.50, f"{_p:.0f}%",
                           ha="center", va="center", fontsize=9,
                           color=_P_TXT if _p >= 15 else "#2C3E50",
                           fontweight="bold", zorder=3)
            _xp += _p

    for _ni, _nt in enumerate([
        "①  PRESCRIPTIONS CHANGE ATHLETE TO ATHLETE",
        "②  VOLUME AND INTENSITY DRIVEN BY CMJ READINESS",
        "③  NOBODY GETS THE EXACT SAME MIX",
    ]):
        _pfig.text(0.03 + _ni * 0.32, 0.035, _nt, fontsize=7.5, color=_P_DIM)

    plt.savefig("images/workout_prescription.png", dpi=150,
                bbox_inches="tight", facecolor=_P_BG)
    plt.close()
    print("workout_prescription.png saved")


# ══════════════════════════════════════════════
# SPORTS PERFORMANCE ML SYSTEM — ARCHITECTURE
# End-to-end CMJ pipeline: plates → prescription
# ══════════════════════════════════════════════

_A_BG   = "#2C3E50"
_A_TXT  = "#FFFFFF"
_A_DIM  = "#95A5A6"
_A_ARR  = "#BDC3C7"
_A_DATA = ("#1A3A2A", "#77DD77")   # eucalyptus — data / storage
_A_FLOW = ("#0D1F44", "#3498DB")   # cobalt     — Prefect flows
_A_REG  = ("#2D1244", "#9B59B6")   # violet     — model registry
_A_UI   = ("#0D2A2A", "#1ABC9C")   # teal       — dashboard / UI
_A_CI   = ("#2A1800", "#F39C12")   # amber      — CI/CD


def _abx(ax, x, y, w, h, title, sub="", fc="#0D1F44", ec="#3A7FD0", tfs=9):
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.10",
        facecolor=fc, edgecolor=ec, linewidth=1.8, zorder=2,
    ))
    ty = y + h / 2 + (0.17 if sub else 0)
    ax.text(x + w / 2, ty, title, ha="center", va="center",
            fontsize=tfs, fontweight="bold", color=_A_TXT, zorder=3)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.25, sub, ha="center", va="center",
                fontsize=7.5, color="#AAAAAA", zorder=3)


def _aar(ax, x1, y1, x2, y2, cs="arc3,rad=0.0", lbl=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="-|>", color=_A_ARR, lw=1.5,
                    mutation_scale=14, connectionstyle=cs,
                ), zorder=5)
    if lbl:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my, lbl, fontsize=7, color=_A_DIM, ha="center", va="center",
                bbox=dict(fc=_A_BG, ec="none", pad=1.5), zorder=6)


with plt.rc_context({
    "figure.facecolor": _A_BG, "axes.facecolor": _A_BG,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
}):
    _afig, _aax = plt.subplots(figsize=(16, 9), facecolor=_A_BG)
    _aax.set_facecolor(_A_BG)
    _aax.set_xlim(0, 16); _aax.set_ylim(0, 9)
    _aax.axis("off")

    _aax.text(8, 8.72, "SPORTS PERFORMANCE ML SYSTEM",
              ha="center", va="center", fontsize=21, fontweight="bold", color=_A_TXT)
    _aax.text(8, 8.36,
              "End-to-end CMJ readiness monitoring  ·  Kedro pipelines  ·  "
              "Prefect orchestration  ·  MLflow tracking",
              ha="center", va="center", fontsize=8.5, color=_A_DIM)

    # CI/CD bar
    _abx(_aax, 0.20, 7.82, 15.60, 0.38,
         "CI/CD  ·  Local → Lint / pytest / GitHub Actions → Docker Build → DigitalOcean (Production)",
         fc=_A_CI[0], ec=_A_CI[1], tfs=8)

    # Data Sources (col 1)
    _abx(_aax, 0.20, 5.80, 2.80, 1.75, "Force Plate Data",
         "Hawkin Dynamics\n(.parquet / .csv)", fc=_A_DATA[0], ec=_A_DATA[1])
    _abx(_aax, 0.20, 3.80, 2.80, 1.75, "Historical DB",
         "Session Archive\nSQLite + Docker",  fc=_A_DATA[0], ec=_A_DATA[1])
    _abx(_aax, 0.20, 1.80, 2.80, 1.75, "Unseen Session",
         "New .parquet\nAuto-ingested",       fc=_A_DATA[0], ec=_A_DATA[1])

    # Streaming App + Dashboard (col 2)
    _abx(_aax, 3.30, 3.55, 2.30, 2.75, "Data Streaming\nApp",
         "Python + Docker\nCMJ Phase Parser\nSession Formatter",
         fc=_A_DATA[0], ec=_A_DATA[1])
    _abx(_aax, 3.30, 1.80, 2.30, 1.50, "Prescription\nDashboard",
         "Dash + Docker\nReadiness Scores\nWorkout Output",
         fc=_A_UI[0], ec=_A_UI[1])

    # Three Prefect Flows (col 3)
    _abx(_aax, 5.90, 5.80, 5.00, 1.75, "Training Prefect Flow",
         "Trigger Checker  →  Feature Eng. (Kedro)  →  Model Training\n"
         "Champion / Challenger CMJ Readiness Model",
         fc=_A_FLOW[0], ec=_A_FLOW[1])
    _abx(_aax, 5.90, 3.75, 5.00, 1.80, "Inference Prefect Flow",
         "New Session Subscription  →  Feature Eng. (Kedro)  →  Readiness Score\n"
         "→  Individualized Workout Prescription Output",
         fc=_A_FLOW[0], ec=_A_FLOW[1])
    _abx(_aax, 5.90, 1.70, 5.00, 1.80, "Monitoring Prefect Flow",
         "Performance Drift Checker  →  Monitoring Pipeline (Kedro)\n"
         "Triggers Re-training if CMJ Distribution Shifts",
         fc=_A_FLOW[0], ec=_A_FLOW[1])

    # Model Registry + Orchestration (col 4)
    _abx(_aax, 11.20, 4.45, 4.50, 3.10, "Model Registry &\nTracking Server",
         "MLflow + SQLite\nChampion Model\nChallenger Model\nExperiment History",
         fc=_A_REG[0], ec=_A_REG[1])
    _abx(_aax, 11.20, 1.70, 4.50, 2.50, "Pipeline\nOrchestration Server",
         "Prefect + Docker\nFlow Scheduling\nRe-training Alerts",
         fc=_A_REG[0], ec=_A_REG[1])

    # Data Sources → Streaming App
    _aar(_aax, 3.00, 6.675, 3.30, 5.925)
    _aar(_aax, 3.00, 4.675, 3.30, 4.925)
    _aar(_aax, 3.00, 2.675, 3.30, 3.825)

    # Streaming App → Flows
    _aar(_aax, 5.60, 5.60,  5.90, 6.675)
    _aar(_aax, 5.60, 4.925, 5.90, 4.65)
    _aar(_aax, 5.60, 3.75,  5.90, 2.60)

    # Training → Registry, Registry → Inference
    _aar(_aax, 10.90, 6.675, 11.20, 6.45)
    _aar(_aax, 11.20, 5.30,  10.90, 4.65, lbl="Champion\nModel")

    # Monitoring → Orchestration
    _aar(_aax, 10.90, 2.60, 11.20, 2.95)

    # Re-training feedback loop (3 line segments + arrowhead into Training)
    _aax.plot([15.70, 15.82], [2.95, 2.95],  color=_A_ARR, lw=1.5, zorder=4)
    _aax.plot([15.82, 15.82], [2.95, 7.65],  color=_A_ARR, lw=1.5, zorder=4)
    _aax.plot([15.82, 10.90], [7.65, 7.65],  color=_A_ARR, lw=1.5, zorder=4)
    _aar(_aax, 10.90, 7.65, 10.90, 7.55)
    _aax.text(15.84, 5.30, "Re-training\ntrigger", fontsize=7,
              color=_A_DIM, ha="left", va="center")

    # Inference → Dashboard
    _aar(_aax, 5.90, 3.75, 5.60, 3.30)

    # Legend
    _leg_arch = [
        (_A_DATA, "Data / Storage"),
        (_A_FLOW, "Prefect Flows (Kedro)"),
        (_A_REG,  "Model Registry / Orchestration"),
        (_A_UI,   "Dashboard / UI"),
        (_A_CI,   "CI/CD Pipeline"),
    ]
    for _li, ((_fc, _ec), _lbl) in enumerate(_leg_arch):
        _lx = 0.50 + _li * 3.10
        _aax.add_patch(mpatches.FancyBboxPatch(
            (_lx, 0.18), 0.38, 0.52, boxstyle="round,pad=0.04",
            facecolor=_fc, edgecolor=_ec, linewidth=1.2, zorder=2,
        ))
        _aax.text(_lx + 0.52, 0.44, _lbl, fontsize=8, color=_A_TXT, va="center")

    plt.tight_layout(pad=0.4)
    plt.savefig("images/ml_system_architecture.png", dpi=150,
                bbox_inches="tight", facecolor=_A_BG)
    plt.close()
    print("ml_system_architecture.png saved")


print("\nAll images generated successfully!")


# ══════════════════════════════════════════════
# NU VOLLEYBALL — TEAM READINESS DASHBOARD
# Real Hawkin Dynamics CMJ data (Apr 3 vs Apr 17)
# Decision tree: Pentheny / Bishop et al. / Cabarkapa 2023
# ══════════════════════════════════════════════

_NU_MEN = [
    {"name": "Greg Ancheta",       "pos": "Setter",         "short": "ANCHETA",
     "apr3":  {"rsi": 0.999, "jh": 0.572, "mrsi": 0.832, "brfd": 9773,  "asym": 2.59},
     "apr17": {"rsi": 0.949, "jh": 0.568, "mrsi": 0.778, "brfd": 10573, "asym": 1.20}},
    {"name": "Jade Disquitado",    "pos": "Outside Hitter", "short": "DISQUITADO",
     "apr3":  {"rsi": 1.109, "jh": 0.589, "mrsi": 0.918, "brfd": 14635, "asym": 0.95},
     "apr17": {"rsi": 0.952, "jh": 0.538, "mrsi": 0.751, "brfd": 9827,  "asym": 1.79}},
    {"name": "Leo Ordiales",       "pos": "Utility",        "short": "ORDIALES",
     "apr3":  {"rsi": 1.058, "jh": 0.555, "mrsi": 0.833, "brfd": 11644, "asym": 6.08},
     "apr17": {"rsi": 0.908, "jh": 0.526, "mrsi": 0.696, "brfd": 9007,  "asym": 8.95}},
    {"name": "Michaelo Buddin",    "pos": "Outside Hitter", "short": "BUDDIN",
     "apr3":  {"rsi": 1.024, "jh": 0.548, "mrsi": 0.795, "brfd": 12767, "asym": 3.25},
     "apr17": {"rsi": 0.911, "jh": 0.538, "mrsi": 0.705, "brfd": 11389, "asym": 3.34}},
    {"name": "Obed Mukaba",        "pos": "Middle Blocker", "short": "MUKABA",
     "apr3":  {"rsi": 0.981, "jh": 0.531, "mrsi": 0.791, "brfd": 15962, "asym": 2.65},
     "apr17": {"rsi": 0.933, "jh": 0.517, "mrsi": 0.734, "brfd": 14566, "asym": 12.38}},
    {"name": "Rwenzmel Taguibolos","pos": "Middle Blocker", "short": "TAGUIBOLOS",
     "apr3":  {"rsi": 0.955, "jh": 0.522, "mrsi": 0.743, "brfd": 11051, "asym": 2.76},
     "apr17": {"rsi": 0.821, "jh": 0.484, "mrsi": 0.600, "brfd": 6964,  "asym": 8.11}},
]

_CAT = {
    "ELITE":        {"col": "#77DD77", "fc": "#0D2D1A", "ec": "#77DD77",
                     "rx": "Speed · Power · Very Heavy"},
    "EXPLOSIVE":    {"col": "#3498DB", "fc": "#0D1F35", "ec": "#3498DB",
                     "rx": "Power · Heavy · Short GCT"},
    "BALANCED":     {"col": "#F39C12", "fc": "#2D1E08", "ec": "#F39C12",
                     "rx": "Heavy · Hypertrophy · Force"},
    "DEVELOPMENTAL":{"col": "#9B59B6", "fc": "#2D1244", "ec": "#9B59B6",
                     "rx": "Hypertrophy · Strength Build"},
    "RED FLAG":     {"col": "#E74C3C", "fc": "#2D0A08", "ec": "#E74C3C",
                     "rx": "Light · Recovery · RTP Protocol"},
}

def _get_cat(rsi, asym):
    if asym >= 12: return "RED FLAG"
    if rsi >= 1.00: return "ELITE"
    if rsi >= 0.90: return "EXPLOSIVE"
    if rsi >= 0.80: return "BALANCED"
    if rsi >= 0.70: return "DEVELOPMENTAL"
    return "RED FLAG"

def _trend(v_now, v_prev, higher_better=True):
    pct = (v_now - v_prev) / abs(v_prev) * 100
    if abs(pct) < 1.5: return "→", "#95A5A6", f"{v_now:.3f}"
    improved = pct > 0 if higher_better else pct < 0
    return ("↑", "#77DD77", f"{v_now:.3f}") if improved else ("↓", "#E74C3C", f"{v_now:.3f}")

_DB = "#2C3E50"
_TW = "#FFFFFF"
_DM = "#95A5A6"

with plt.rc_context({"figure.facecolor": _DB, "axes.facecolor": _DB,
                     "font.family": "DejaVu Sans",
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.spines.left": False, "axes.spines.bottom": False}):
    _dfig = plt.figure(figsize=(18, 11), facecolor=_DB)

    # ── Header ──
    _dfig.text(0.03, 0.975, "NU VOLLEYBALL — TEAM READINESS REPORT",
               fontsize=17, fontweight="bold", color=_TW, va="top")
    _dfig.text(0.97, 0.975, "Assessment: April 17, 2026  |  Baseline: April 3, 2026",
               fontsize=9, color=_DM, va="top", ha="right")
    _dfig.text(0.03, 0.938,
               "Hawkin Dynamics CMJ  ·  Metrics: RSI, mRSI, Jump Height, Braking RFD, Bilateral Asymmetry  "
               "·  Classification: Pentheny Decision Tree  ·  Ref: Cabarkapa et al. 2023, Bishop et al.",
               fontsize=8, color=_DM, va="top")

    # ── Column headers ──
    _hdrs = [
        (0.03,  "ATHLETE"),
        (0.235, "CATEGORY"),
        (0.370, "RSI"),
        (0.470, "mRSI"),
        (0.570, "JUMP HEIGHT"),
        (0.680, "ASYM %"),
        (0.760, "BRK RFD (N/s)"),
        (0.870, "PRESCRIPTION"),
    ]
    for _hx, _hl in _hdrs:
        _dfig.text(_hx, 0.895, _hl, fontsize=7.5, color=_DM,
                   fontweight="bold", va="top")

    # ── Athlete rows ──
    _ROW_TOPS = [0.845, 0.715, 0.585, 0.455, 0.325, 0.195]
    _ROW_H    = 0.115

    for _i, _ath in enumerate(_NU_MEN):
        _y0  = _ROW_TOPS[_i] - _ROW_H
        _y_c = _ROW_TOPS[_i] - _ROW_H / 2   # vertical center
        _a17 = _ath["apr17"]
        _a03 = _ath["apr3"]
        _cat = _get_cat(_a17["rsi"], _a17["asym"])
        _ci  = _CAT[_cat]

        # Row background strip
        _bg = mpatches.Rectangle(
            (0.02, _y0 + 0.005), 0.960, _ROW_H - 0.010,
            facecolor=_ci["fc"], edgecolor=_ci["ec"],
            linewidth=0.8, alpha=0.55,
            transform=_dfig.transFigure, clip_on=False)
        _dfig.add_artist(_bg)

        # Athlete name + position
        _dfig.text(0.035, _y_c + 0.025, _ath["name"],
                   fontsize=11, fontweight="bold", color=_TW, va="center")
        _dfig.text(0.035, _y_c - 0.018, _ath["pos"],
                   fontsize=8, color=_DM, va="center")

        # Category badge
        _bx = mpatches.FancyBboxPatch(
            (0.235, _y0 + 0.018), 0.118, _ROW_H - 0.036,
            boxstyle="round,pad=0.008",
            facecolor=_ci["fc"], edgecolor=_ci["col"], linewidth=1.5,
            transform=_dfig.transFigure, clip_on=False)
        _dfig.add_artist(_bx)
        _dfig.text(0.294, _y_c, _cat,
                   fontsize=8, fontweight="bold", color=_ci["col"],
                   ha="center", va="center")

        # RSI
        _arr, _arc, _val = _trend(_a17["rsi"], _a03["rsi"])
        _dfig.text(0.370, _y_c + 0.018, _val,
                   fontsize=12, fontweight="bold", color=_arc, va="center")
        _dfig.text(0.370, _y_c - 0.020,
                   f"{_arr}  prev {_a03['rsi']:.3f}",
                   fontsize=7.5, color=_arc, va="center")

        # mRSI
        _arr, _arc, _val = _trend(_a17["mrsi"], _a03["mrsi"])
        _dfig.text(0.470, _y_c + 0.018, _val,
                   fontsize=12, fontweight="bold", color=_arc, va="center")
        _dfig.text(0.470, _y_c - 0.020,
                   f"{_arr}  prev {_a03['mrsi']:.3f}",
                   fontsize=7.5, color=_arc, va="center")

        # Jump Height
        _arr, _arc, _val = _trend(_a17["jh"], _a03["jh"])
        _dfig.text(0.570, _y_c + 0.018, f"{_a17['jh']:.3f} m",
                   fontsize=12, fontweight="bold", color=_arc, va="center")
        _dfig.text(0.570, _y_c - 0.020,
                   f"{_arr}  prev {_a03['jh']:.3f} m",
                   fontsize=7.5, color=_arc, va="center")

        # Asymmetry
        _ac = "#E74C3C" if _a17["asym"] >= 10 else "#F39C12" if _a17["asym"] >= 7 else _TW
        _flag = "  ⚑" if _a17["asym"] >= 10 else ""
        _dfig.text(0.680, _y_c + 0.018, f"{_a17['asym']:.1f}%{_flag}",
                   fontsize=12, fontweight="bold", color=_ac, va="center")
        _dfig.text(0.680, _y_c - 0.020,
                   f"prev {_a03['asym']:.1f}%",
                   fontsize=7.5, color=_DM, va="center")

        # Braking RFD
        _arr, _arc, _val = _trend(_a17["brfd"], _a03["brfd"])
        _dfig.text(0.760, _y_c + 0.018, f"{int(_a17['brfd']):,}",
                   fontsize=12, fontweight="bold", color=_arc, va="center")
        _dfig.text(0.760, _y_c - 0.020,
                   f"{_arr}  prev {int(_a03['brfd']):,}",
                   fontsize=7.5, color=_arc, va="center")

        # Prescription
        _dfig.text(0.870, _y_c, _ci["rx"],
                   fontsize=9, color=_ci["col"], va="center", fontweight="bold")

    # ── Category legend ──
    _dfig.text(0.03, 0.085, "PERFORMANCE CATEGORIES :", fontsize=7.5,
               color=_DM, va="center", fontweight="bold")
    for _li, (_cn, _cd) in enumerate(_CAT.items()):
        _lx = 0.21 + _li * 0.155
        _sq = mpatches.Rectangle((_lx, 0.075), 0.012, 0.022,
                                   facecolor=_cd["fc"], edgecolor=_cd["col"],
                                   linewidth=1.2,
                                   transform=_dfig.transFigure, clip_on=False)
        _dfig.add_artist(_sq)
        _dfig.text(_lx + 0.016, 0.086, _cn, fontsize=7.5, color=_cd["col"], va="center")

    # ── Footer ──
    _dfig.text(0.03, 0.035,
               "RSI = Reactive Strength Index  ·  mRSI = Modified RSI  ·  Asym = L|R Peak Braking Force  "
               "·  BRK RFD = Braking Rate of Force Development  ·  ⚑ = Asymmetry flag (≥10%)",
               fontsize=7, color=_DM, va="bottom")
    _dfig.text(0.03, 0.018,
               "Ref: Cabarkapa et al. (2023) J Strength Cond Res 38(2):e72–e77  ·  "
               "Bishop et al. Selecting Metrics That Matter  ·  "
               "Pentheny Force Plate Decision Tree",
               fontsize=7, color=_DM, va="bottom")

    plt.savefig("images/team_readiness_dashboard.png", dpi=150,
                bbox_inches="tight", facecolor=_DB)
    plt.close()
    print("team_readiness_dashboard.png saved")


# ══════════════════════════════════════════════
# FORCE-VELOCITY PROFILE — VBT ZONE PRESCRIBER
# Turner et al. 2020 Part I & II; Weakley et al. 2020
# Pareja-Blanco et al. 2016 (velocity loss thresholds)
# ══════════════════════════════════════════════

_FV_BG  = "#2C3E50"
_FV_TXT = "#FFFFFF"
_FV_DIM = "#95A5A6"

# 5 zones sourced from Turner et al. 2020, Table 2 & Figure 3 (squat velocity bands)
_FV_ZONES = [
    {
        "name": "ABSOLUTE\nSTRENGTH", "v_lo": 0.00, "v_hi": 0.30,
        "pct_hi": 100, "pct_lo": 85,
        "col": "#E74C3C", "bg": "#2D0A08",
        "goal": "Maximal force · Neural recruitment",
        "vl": "≤ 20%", "vl_col": "#E74C3C",
        "exercises": "Heavy Squat · Deadlift · Pin Press",
        "cmj_label": "< 7,000 N/s",
    },
    {
        "name": "STRENGTH", "v_lo": 0.30, "v_hi": 0.60,
        "pct_hi": 85, "pct_lo": 65,
        "col": "#F39C12", "bg": "#2D1500",
        "goal": "Force capacity · Hypertrophy",
        "vl": "20–30%", "vl_col": "#F39C12",
        "exercises": "Squat · Trap Bar DL · Bench Press",
        "cmj_label": "7,000–10,000 N/s",
    },
    {
        "name": "STRENGTH-\nSPEED", "v_lo": 0.60, "v_hi": 1.00,
        "pct_hi": 65, "pct_lo": 45,
        "col": "#77DD77", "bg": "#0D2D1A",
        "goal": "Peak power output ★",
        "vl": "20%", "vl_col": "#77DD77",
        "exercises": "Trap Bar Jump · JS 40–75% BM\nPower Clean (> 1.0 m/s)",
        "cmj_label": "10,000–13,000 N/s",
    },
    {
        "name": "SPEED-\nSTRENGTH", "v_lo": 1.00, "v_hi": 1.50,
        "pct_hi": 45, "pct_lo": 20,
        "col": "#3498DB", "bg": "#0D1F35",
        "goal": "Velocity expression · RFD",
        "vl": "15–20%", "vl_col": "#3498DB",
        "exercises": "Power Snatch · JS 20% BM\nMed Ball Throw (> 1.5 m/s)",
        "cmj_label": "13,000–16,000 N/s",
    },
    {
        "name": "SPEED /\nBALLISTIC", "v_lo": 1.50, "v_hi": 2.20,
        "pct_hi": 20, "pct_lo": 0,
        "col": "#9B59B6", "bg": "#2D1244",
        "goal": "Max velocity · SSC utilisation",
        "vl": "10–15%", "vl_col": "#9B59B6",
        "exercises": "CMJ · Drop Jump · Sprint Starts\nJS BW (> 2.0 m/s) · Plyometrics",
        "cmj_label": "> 16,000 N/s",
    },
]

# NU Men athlete zone mapping via Apr-17 BrkRFD
_ATH_FV = [
    {"short": "ANCHETA",    "brfd": 10573, "zone": 2},
    {"short": "DISQUITADO", "brfd": 9827,  "zone": 1},
    {"short": "ORDIALES",   "brfd": 9007,  "zone": 1},
    {"short": "BUDDIN",     "brfd": 11389, "zone": 2},
    {"short": "MUKABA",     "brfd": 14566, "zone": 3},
    {"short": "TAGUIBOLOS", "brfd": 6964,  "zone": 1},
]

# F-V curve (squat, linear approx): %1RM = 100·(1−(v−0.30)/1.90)  v∈[0.30, 2.20]
_v_fv   = np.linspace(0.30, 2.20, 300)
_f_fv   = 100 * (1 - (_v_fv - 0.30) / 1.90)
# Power: P ∝ F·v → peak at v ≈ 1.10 m/s
_p_fv   = _v_fv * _f_fv
_p_norm = _p_fv / _p_fv.max() * 100
_v_peak = _v_fv[np.argmax(_p_fv)]   # ≈ 1.10 m/s

with plt.rc_context({
    "figure.facecolor": _FV_BG, "axes.facecolor": _FV_BG,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False, "axes.spines.right": False,
}):
    _fvfig = plt.figure(figsize=(18, 10), facecolor=_FV_BG)

    # ── Header ──────────────────────────────────────────────
    _fvfig.text(0.03, 0.975, "FORCE-VELOCITY PROFILE",
                fontsize=18, fontweight="bold", color=_FV_TXT, va="top")
    _fvfig.text(0.03, 0.940,
                "Velocity-Based Training — Zone Prescriber  ·  "
                "Turner et al. 2020  ·  Weakley et al. 2020  ·  Pareja-Blanco et al. 2016",
                fontsize=8.5, color=_FV_DIM, va="top")
    _fvfig.text(0.97, 0.975, "N1 PERFORMANCE LAB PH",
                fontsize=8.5, color=_FV_DIM, va="top", ha="right")

    # ── LEFT PANEL: F-V curve ───────────────────────────────
    _axfv = _fvfig.add_axes([0.04, 0.13, 0.54, 0.78], facecolor=_FV_BG)

    # Zone background fills
    for _z in _FV_ZONES:
        _axfv.axvspan(_z["v_lo"], _z["v_hi"], facecolor=_z["bg"], alpha=1.0, zorder=1)
        _axfv.axvline(_z["v_hi"], color=_FV_DIM, lw=0.5, alpha=0.35, zorder=2)

    # Zone name labels (top of chart)
    for _z in _FV_ZONES:
        _vmid = (_z["v_lo"] + _z["v_hi"]) / 2
        _axfv.text(_vmid, 101, _z["name"], ha="center", va="bottom",
                   fontsize=8, fontweight="bold", color=_z["col"], zorder=4,
                   multialignment="center")

    # Isometric stub (v < 0.30, 100% 1RM line)
    _axfv.plot([0, 0.30], [100, 100], color=_FV_TXT, lw=2.0, ls="--", alpha=0.45, zorder=4)

    # F-V curve
    _axfv.plot(_v_fv, _f_fv, color=_FV_TXT, lw=2.5, zorder=5, label="F-V (Squat, linear approx)")

    # Power curve on twin axis
    _ax2 = _axfv.twinx()
    _ax2.set_facecolor(_FV_BG)
    _ax2.plot(_v_fv, _p_norm, color="#F39C12", lw=1.8, ls="--", alpha=0.75, zorder=3)
    _ax2.set_ylabel("Relative Power Output (%)", color="#F39C12", fontsize=8)
    _ax2.tick_params(axis="y", colors="#F39C12", labelsize=7)
    _ax2.set_ylim(0, 120)
    for _sp in _ax2.spines.values():
        _sp.set_color(_FV_DIM)

    # Peak power marker
    _pct_at_peak = 100 * (1 - (_v_peak - 0.30) / 1.90)
    _axfv.plot(_v_peak, _pct_at_peak, "o", color="#F39C12", ms=9, zorder=6)
    _axfv.annotate(f"Peak Power\n≈ {_v_peak:.2f} m/s",
                   xy=(_v_peak, _pct_at_peak),
                   xytext=(_v_peak + 0.10, _pct_at_peak + 10),
                   fontsize=7.5, color="#F39C12", zorder=6,
                   arrowprops=dict(arrowstyle="-", color="#F39C12", lw=0.8))

    # V1RM marker (squat)
    _axfv.axvline(0.30, color="#E74C3C", lw=1.2, ls=":", alpha=0.8, zorder=3)
    _axfv.text(0.32, 6, "V1RM Squat\n0.30 m/s", fontsize=6.5, color="#E74C3C", va="bottom")

    # Exercise example annotations per zone (placed inside each zone)
    _ex_annots = [
        (0.15, 30, "Squat\nDeadlift\n(near 1RM)"),
        (0.45, 30, "Squat 75–85%\nBench Press\nTrap Bar DL"),
        (0.80, 28, "Trap Bar Jump\nJump Squat 40–75% BM\nPower Clean"),
        (1.25, 30, "Power Snatch\nJump Squat 20% BM\nMed Ball Throw"),
        (1.85, 28, "CMJ · Drop Jump\nSprint Starts\nPlyometrics"),
    ]
    for _ex_v, _ex_pct, _ex_txt in _ex_annots:
        _zi = next(i for i, z in enumerate(_FV_ZONES) if z["v_lo"] <= _ex_v < z["v_hi"])
        _axfv.text(_ex_v, _ex_pct, _ex_txt, ha="center", va="top", fontsize=6.5,
                   color=_FV_ZONES[_zi]["col"], alpha=0.85, zorder=4,
                   multialignment="center",
                   bbox=dict(fc=_FV_ZONES[_zi]["bg"], ec="none", pad=2, alpha=0.7))

    # Axis styling
    _axfv.set_xlim(0, 2.20)
    _axfv.set_ylim(0, 110)
    _axfv.set_xlabel("Mean Concentric Velocity (m/s)", color=_FV_TXT, fontsize=9, labelpad=6)
    _axfv.set_ylabel("Relative Load (% 1RM)", color=_FV_TXT, fontsize=9, labelpad=6)
    _axfv.tick_params(colors=_FV_TXT, labelsize=8)
    for _sp in _axfv.spines.values():
        _sp.set_color(_FV_DIM)
    _axfv.set_xticks([0.0, 0.30, 0.60, 1.00, 1.50, 2.00])
    _axfv.set_yticks([0, 20, 40, 60, 80, 100])

    # Legend
    _axfv.plot([], [], color=_FV_TXT, lw=2.5, label="Force-Velocity (Squat)")
    _axfv.plot([], [], color="#F39C12", lw=1.8, ls="--", label="Power (F × v)")
    _axfv.legend(loc="upper right", fontsize=7.5, framealpha=0.25,
                 facecolor=_FV_BG, edgecolor=_FV_DIM, labelcolor=_FV_TXT)

    # ── RIGHT PANEL: Zone prescription cards ────────────────
    _rx0    = 0.615
    _card_h = 0.148
    _card_w = 0.355

    for _zi, _z in enumerate(_FV_ZONES):
        _ry0 = 0.895 - _zi * (_card_h + 0.010)

        # Card background
        _card_bg = mpatches.FancyBboxPatch(
            (_rx0, _ry0 - _card_h), _card_w, _card_h,
            boxstyle="round,pad=0.006",
            facecolor=_z["bg"], edgecolor=_z["col"], linewidth=1.2,
            transform=_fvfig.transFigure, clip_on=False)
        _fvfig.add_artist(_card_bg)

        # Left accent bar
        _acc = mpatches.Rectangle(
            (_rx0, _ry0 - _card_h + 0.006), 0.006, _card_h - 0.012,
            facecolor=_z["col"],
            transform=_fvfig.transFigure, clip_on=False)
        _fvfig.add_artist(_acc)

        _cy = _ry0 - _card_h / 2   # vertical center of card

        # Zone name
        _fvfig.text(_rx0 + 0.011, _cy + 0.028,
                    _z["name"].replace("\n", " "),
                    fontsize=9, fontweight="bold", color=_z["col"], va="center")
        # Goal
        _fvfig.text(_rx0 + 0.011, _cy + 0.006, _z["goal"],
                    fontsize=7.5, color=_FV_TXT, va="center")
        # Velocity range
        _fvfig.text(_rx0 + 0.011, _cy - 0.015,
                    f"Velocity: {_z['v_lo']:.2f} – {_z['v_hi']:.2f} m/s  ·  "
                    f"Load: {_z['pct_lo']}–{_z['pct_hi']}% 1RM",
                    fontsize=6.8, color=_FV_DIM, va="center")
        # VL threshold
        _fvfig.text(_rx0 + 0.011, _cy - 0.033,
                    f"VL: {_z['vl']}",
                    fontsize=7, color=_z["vl_col"], va="center", fontweight="bold")
        # CMJ BrkRFD connection
        _fvfig.text(_rx0 + 0.180, _cy - 0.020,
                    f"CMJ BrkRFD\n{_z['cmj_label']}",
                    fontsize=6.5, color=_FV_DIM, va="center", ha="center",
                    multialignment="center")

        # NU Men athlete dots for this zone
        _zone_athletes = [a for a in _ATH_FV if a["zone"] == _zi]
        for _ai, _ath in enumerate(_zone_athletes):
            _dot_x = _rx0 + 0.255 + _ai * 0.030
            _dot_y = _cy
            _fvfig.text(_dot_x, _dot_y + 0.012, "●",
                        fontsize=7, color=_z["col"], ha="center", va="center",
                        transform=_fvfig.transFigure)
            _fvfig.text(_dot_x, _dot_y - 0.006, _ath["short"],
                        fontsize=5.5, color=_FV_DIM, ha="center", va="center",
                        transform=_fvfig.transFigure)

    # ── VL consequence strip ─────────────────────────────────
    _fvfig.text(_rx0, 0.115,
                "VELOCITY LOSS THRESHOLD OUTCOMES   (Pareja-Blanco et al. 2016, Squat, 8 wk)",
                fontsize=7.5, color=_FV_DIM, fontweight="bold", va="center")

    _vl_data = [
        ("VL 20%", "#77DD77",
         "+9.5% CMJ  ·  Preserves MHC-IIX fibres  ·  40% fewer reps  ·  Less fatigue"),
        ("VL 40%", "#F39C12",
         "+3.5% CMJ  ·  Greater hypertrophy (CSA)  ·  Higher metabolic stress"),
    ]
    for _vli, (_vl_lbl, _vl_col, _vl_txt) in enumerate(_vl_data):
        _vy = 0.088 - _vli * 0.030
        _fvfig.text(_rx0, _vy, _vl_lbl,
                    fontsize=8, fontweight="bold", color=_vl_col, va="center")
        _fvfig.text(_rx0 + 0.055, _vy, _vl_txt,
                    fontsize=7.5, color=_FV_TXT, va="center")

    # ── Footer ──────────────────────────────────────────────
    _fvfig.text(0.03, 0.035,
                "F-V curve: linear approximation from literature (Sánchez-Medina & González-Badillo 2010; Turner et al. 2020)  ·  "
                "Velocity zones: Turner et al. 2020, Table 2 & Fig. 3  ·  "
                "V1RM squat ≈ 0.30 m/s (Weakley et al. 2020)",
                fontsize=6.5, color=_FV_DIM, va="bottom")
    _fvfig.text(0.03, 0.018,
                "VL = Velocity Loss threshold per set  ·  BrkRFD = CMJ Braking Rate of Force Development (Hawkin Dynamics)  ·  "
                "Athlete zones derived from Apr-17 session data",
                fontsize=6.5, color=_FV_DIM, va="bottom")

    plt.savefig("images/fv_profile.png", dpi=150,
                bbox_inches="tight", facecolor=_FV_BG)
    plt.close()
    print("fv_profile.png saved")


# ══════════════════════════════════════════════
# POWER DEVELOPMENT FRAMEWORK
# Turner et al. 2010 (SSC); Turner et al. 2020 Part I & II
# ══════════════════════════════════════════════

_PW_BG  = "#2C3E50"
_PW_TXT = "#FFFFFF"
_PW_DIM = "#95A5A6"

_PLY_LVLS = [
    {"name": "BILATERAL JUMPS",      "gct": "> 500 ms",   "ssc": "Long SSC",   "ex": "Box Jump  ·  CMJ  ·  Broad Jump",              "rsi": "—",      "col": "#77DD77", "bg": "#0D2D1A"},
    {"name": "UNILATERAL JUMPS",     "gct": "300–500 ms", "ssc": "Long SSC",   "ex": "Lunge Jump  ·  Single-Leg Box Jump",           "rsi": "≥ 0.70", "col": "#3498DB", "bg": "#0D1F35"},
    {"name": "LOADED JUMPS",         "gct": "250–400 ms", "ssc": "Transition", "ex": "Jump Squat 20–40% BM  ·  Hex Bar Jump",       "rsi": "≥ 0.90", "col": "#F39C12", "bg": "#2D1500"},
    {"name": "FAST PLYOMETRICS",     "gct": "150–250 ms", "ssc": "Short SSC",  "ex": "Hurdle Hops  ·  Rapid Rebound Jumps",         "rsi": "≥ 1.10", "col": "#E74C3C", "bg": "#2D0A08"},
    {"name": "REACTIVE PLYOMETRICS", "gct": "< 150 ms",   "ssc": "Short SSC",  "ex": "Drop Jump  ·  Depth Jump  ·  Sprint Bounds",  "rsi": "≥ 1.30", "col": "#9B59B6", "bg": "#2D1244"},
]

_PWR_EX = [
    ("Deadlift",     12, "#E74C3C"),
    ("Back Squat",   22, "#F39C12"),
    ("Trap Bar DL",  30, "#F39C12"),
    ("Power Clean",  55, "#77DD77"),
    ("Jump Shrug",   65, "#77DD77"),
    ("WL Deriv.",    80, "#9B59B6"),
]

with plt.rc_context({
    "figure.facecolor": _PW_BG, "axes.facecolor": _PW_BG,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False, "axes.spines.right": False,
}):
    _pwfig = plt.figure(figsize=(18, 10), facecolor=_PW_BG)

    _pwfig.text(0.03, 0.975, "POWER DEVELOPMENT FRAMEWORK",
                fontsize=18, fontweight="bold", color=_PW_TXT, va="top")
    _pwfig.text(0.03, 0.940,
                "SSC Mechanisms  ·  Plyometric Pyramid  ·  Exercise Power Outputs  ·  "
                "Turner et al. 2010 & 2020  ·  Short SSC: GCT < 250 ms  ·  Long SSC: GCT > 250 ms",
                fontsize=8.5, color=_PW_DIM, va="top")
    _pwfig.text(0.97, 0.975, "N1 PERFORMANCE LAB PH",
                fontsize=8.5, color=_PW_DIM, va="top", ha="right")

    # SSC mechanism boxes
    _ax_ssc = _pwfig.add_axes([0.03, 0.54, 0.46, 0.36], facecolor=_PW_BG)
    _ax_ssc.set_xlim(0, 3); _ax_ssc.set_ylim(0, 2); _ax_ssc.axis("off")

    _ssc_data = [
        ("ECCENTRIC",    "#3498DB", 0.05, "#0D1F35",
         ["Muscle lengthens under load", "Tendon stores elastic energy (EE)",
          "↑ Stiffness → ↑ EE stored", "GTO inhibition allows stretch"]),
        ("AMORTIZATION", "#F39C12", 1.07, "#2D1500",
         ["Isometric transition", "Short SSC: < 250 ms (Drop Jump)",
          "Long SSC: > 250 ms (CMJ)", "EE half-life 0.85 s — minimise!"]),
        ("CONCENTRIC",   "#77DD77", 2.09, "#0D2D1A",
         ["EE + contractile force", "CMJ vs SJ: +18–30% height",
          "↑ SSC efficiency → less ATP", "Trained: reverses at drop jump"]),
    ]
    for _sn, _sc, _sx, _sbg, _spts in _ssc_data:
        _ax_ssc.add_patch(mpatches.FancyBboxPatch(
            (_sx, 0.05), 0.88, 1.88, boxstyle="round,pad=0.04",
            facecolor=_sbg, edgecolor=_sc, linewidth=1.8, zorder=2))
        _ax_ssc.text(_sx + 0.44, 1.82, _sn, ha="center", va="top",
                     fontsize=9, fontweight="bold", color=_sc, zorder=3)
        for _pi, _pt in enumerate(_spts):
            _ax_ssc.text(_sx + 0.08, 1.48 - _pi * 0.34, f"· {_pt}",
                         ha="left", va="top", fontsize=7, color=_PW_TXT, zorder=3)
    for _arx in [0.93, 1.95]:
        _ax_ssc.annotate("", xy=(_arx + 0.14, 0.99), xytext=(_arx, 0.99),
                         arrowprops=dict(arrowstyle="-|>", color=_PW_DIM, lw=2.0), zorder=4)

    # Power output bars
    _pwfig.text(0.03, 0.517, "RELATIVE POWER OUTPUT BY EXERCISE  (W · kg⁻¹ BM)",
                fontsize=8, color=_PW_DIM, fontweight="bold", va="top")
    _ax_pwr = _pwfig.add_axes([0.10, 0.12, 0.39, 0.37], facecolor=_PW_BG)
    _ax_pwr.set_xlim(0, 90); _ax_pwr.set_ylim(-0.5, len(_PWR_EX) - 0.5)
    _ax_pwr.axis("off")
    for _pi, (_ex, _wt, _col) in enumerate(_PWR_EX):
        _ax_pwr.barh(_pi, _wt, height=0.60, facecolor=_col, alpha=0.85, zorder=2)
        _ax_pwr.text(-1.5, _pi, _ex, ha="right", va="center", fontsize=8, color=_PW_TXT)
        _ax_pwr.text(_wt + 1.5, _pi, f"{_wt} W/kg",
                     ha="left", va="center", fontsize=8.5, fontweight="bold", color=_col)

    # Plyometric pyramid
    _ax_pyr = _pwfig.add_axes([0.52, 0.10, 0.46, 0.82], facecolor=_PW_BG)
    _ax_pyr.set_xlim(-0.08, 1.12); _ax_pyr.set_ylim(-0.05, 1.10); _ax_pyr.axis("off")
    _pwfig.text(0.75, 0.932, "PLYOMETRIC PROGRESSION PYRAMID",
                fontsize=10, fontweight="bold", color=_PW_TXT, va="top", ha="center")
    _pwfig.text(0.75, 0.910,
                "Advance only when technically proficient at each level  ·  Turner et al. 2010",
                fontsize=7, color=_PW_DIM, va="top", ha="center")

    _nl = len(_PLY_LVLS)
    for _li, _lv in enumerate(_PLY_LVLS):
        _y0 = _li / _nl; _y1 = (_li + 1) / _nl
        _pts = np.array([[_y0/2, _y0], [1-_y0/2, _y0], [1-_y1/2, _y1], [_y1/2, _y1]])
        _ax_pyr.add_patch(mpatches.Polygon(
            _pts, facecolor=_lv["bg"], edgecolor=_lv["col"], linewidth=1.8, zorder=2))
        _ym = (_y0 + _y1) / 2
        _ax_pyr.text(0.50, _ym + 0.030, _lv["name"],
                     ha="center", va="center", fontsize=9, fontweight="bold",
                     color=_lv["col"], zorder=3)
        _ax_pyr.text(0.50, _ym + 0.002, _lv["ex"],
                     ha="center", va="center", fontsize=7, color=_PW_TXT, zorder=3)
        _ax_pyr.text(0.50, _ym - 0.025,
                     f"GCT {_lv['gct']}  ·  {_lv['ssc']}",
                     ha="center", va="center", fontsize=6.5, color=_PW_DIM, zorder=3)
        _ax_pyr.text(_y0/2 - 0.015, _ym, f"RSI {_lv['rsi']}",
                     ha="right", va="center", fontsize=6.5, color=_lv["col"], zorder=3)

    _ax_pyr.annotate("", xy=(1.07, 0.98), xytext=(1.07, 0.02),
                     arrowprops=dict(arrowstyle="-|>", color=_PW_DIM, lw=1.8), zorder=4)
    _ax_pyr.text(1.082, 0.50, "INTENSITY & COMPLEXITY",
                 fontsize=7.5, color=_PW_DIM, va="center", ha="left", rotation=90)

    for _lx0, _lw, _lc, _ltxt in [
        (0.05, 0.40, "#3498DB", "LONG SSC  ·  GCT > 250 ms  ·  CMJ / mRSI"),
        (0.52, 0.43, "#E74C3C", "SHORT SSC  ·  GCT < 250 ms  ·  RSI (Drop Jump)"),
    ]:
        _ax_pyr.add_patch(mpatches.FancyBboxPatch(
            (_lx0, -0.042), _lw, 0.055, boxstyle="round,pad=0.005",
            facecolor={"#3498DB":"#0D1F35","#E74C3C":"#2D0A08"}[_lc],
            edgecolor=_lc, linewidth=1.0, zorder=4))
        _ax_pyr.text(_lx0 + _lw/2, -0.014, _ltxt,
                     ha="center", va="center", fontsize=6, color=_lc, zorder=5)

    _pwfig.text(0.03, 0.035,
                "SSC = Stretch-Shortening Cycle  ·  GCT = Ground Contact Time  ·  "
                "EE = Elastic Energy  ·  BM = Body Mass  ·  WL = Weightlifting derivatives",
                fontsize=6.5, color=_PW_DIM, va="bottom")
    _pwfig.text(0.03, 0.018,
                "Turner & Jeffreys (2010) Strength Cond J  ·  "
                "Turner et al. (2020) Developing Powerful Athletes Part I & II  ·  "
                "Suchomel & Comfort cited in Turner 2020",
                fontsize=6.5, color=_PW_DIM, va="bottom")

    plt.savefig("images/power_framework.png", dpi=150,
                bbox_inches="tight", facecolor=_PW_BG)
    plt.close()
    print("power_framework.png saved")


# ══════════════════════════════════════════════
# WORKLOAD MONITORING — ACWR FRAMEWORK
# Soligard et al. 2016 (IOC Part 1); Gabbett 2016
# ══════════════════════════════════════════════

_WM_BG  = "#2C3E50"
_WM_TXT = "#FFFFFF"
_WM_DIM = "#95A5A6"

_WM_WKS  = np.arange(1, 21)
_WM_LOAD = np.array([260, 300, 360, 420, 450, 540, 460, 380,
                      480, 510, 540, 510, 470, 430, 510, 490,
                      380, 350, 330, 300], dtype=float)
_WM_CHR  = np.array([float(np.mean(_WM_LOAD[max(0,i-3):i+1]))
                      for i in range(20)])
_WM_ACWR = _WM_LOAD / _WM_CHR
_WM_RSI  = np.array([1.02, 1.04, 1.06, 1.03, 1.00, 0.92, 0.96, 1.00,
                      0.97, 0.94, 0.90, 0.88, 0.90, 0.92, 0.88, 0.87,
                      0.91, 0.94, 0.96, 0.99])

_WM_PHASES = [("Pre-Season", 1, 8), ("In-Season", 9, 16), ("Competition", 17, 20)]
_WM_PH_COL = ["#0D1F35", "#0D2D1A", "#2D1244"]
_WM_PH_EC  = ["#3498DB", "#77DD77", "#9B59B6"]

_WM_ZONES = [
    (1.50, 2.20, "#E74C3C", "DANGER",        "> 1.5",  "Injury risk spikes — reduce load immediately"),
    (1.30, 1.50, "#F39C12", "CAUTION",       "1.3–1.5","Elevated risk — monitor closely"),
    (0.80, 1.30, "#77DD77", "SWEET SPOT ★",  "0.8–1.3","Optimal adaptation zone — maintain"),
    (0.00, 0.80, "#3498DB", "UNDER-TRAINED", "< 0.8",  "Deconditioning risk — build gradually"),
]

with plt.rc_context({
    "figure.facecolor": _WM_BG, "axes.facecolor": _WM_BG,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False, "axes.spines.right": False,
}):
    _wmfig = plt.figure(figsize=(18, 10), facecolor=_WM_BG)

    _wmfig.text(0.03, 0.975, "WORKLOAD MONITORING — ACWR FRAMEWORK",
                fontsize=18, fontweight="bold", color=_WM_TXT, va="top")
    _wmfig.text(0.03, 0.940,
                "Acute:Chronic Workload Ratio  ·  IOC Consensus Statement (Soligard et al. 2016)  ·  "
                "Gabbett (2016)  ·  CMJ RSI as internal readiness marker",
                fontsize=8.5, color=_WM_DIM, va="top")
    _wmfig.text(0.97, 0.975, "N1 PERFORMANCE LAB PH",
                fontsize=8.5, color=_WM_DIM, va="top", ha="right")

    # Phase shading label
    _wmfig.text(0.03, 0.910, "SIMULATED 20-WEEK VOLLEYBALL SEASON",
                fontsize=7.5, color=_WM_DIM, fontweight="bold", va="top")

    # ── TOP: Weekly load + chronic average ──────────────────
    _ax_ld = _wmfig.add_axes([0.03, 0.545, 0.625, 0.335], facecolor=_WM_BG)
    for (_pn, _ps, _pe), _pfc, _pec in zip(_WM_PHASES, _WM_PH_COL, _WM_PH_EC):
        _ax_ld.axvspan(_ps - 0.5, _pe + 0.5, facecolor=_pfc, alpha=0.6, zorder=1)
        _ax_ld.text((_ps + _pe) / 2, 590, _pn,
                    ha="center", va="top", fontsize=8, color=_pec, fontweight="bold")
    _ax_ld.bar(_WM_WKS, _WM_LOAD, color="#3498DB", alpha=0.70, width=0.7, zorder=2, label="Weekly Load (AU)")
    _ax_ld.plot(_WM_WKS, _WM_CHR, color="#F39C12", lw=2.2, zorder=3, label="4-wk Chronic Average")
    _ax_ld.set_xlim(0.5, 20.5); _ax_ld.set_ylim(0, 620)
    _ax_ld.set_ylabel("Session Load (AU)", color=_WM_TXT, fontsize=8)
    _ax_ld.tick_params(colors=_WM_TXT, labelsize=7.5)
    _ax_ld.set_xticks([]); 
    for _sp in _ax_ld.spines.values(): _sp.set_color(_WM_DIM)
    _ax_ld.legend(loc="upper left", fontsize=7.5, framealpha=0.25,
                  facecolor=_WM_BG, edgecolor=_WM_DIM, labelcolor=_WM_TXT)

    # ── BOTTOM: ACWR ratio + zones ──────────────────────────
    _ax_ac = _wmfig.add_axes([0.03, 0.13, 0.625, 0.385], facecolor=_WM_BG)
    for _zlo, _zhi, _zcol, _zn, _zr, _zt in _WM_ZONES:
        _ax_ac.axhspan(_zlo, _zhi, facecolor=_zcol, alpha=0.12, zorder=1)
        _ax_ac.axhline(_zhi, color=_zcol, lw=0.6, ls="--", alpha=0.5, zorder=2)
        _ax_ac.text(20.6, (_zlo + min(_zhi, 2.0)) / 2, f"{_zn}\n{_zr}",
                    fontsize=6.5, color=_zcol, va="center", fontweight="bold")

    for (_pn, _ps, _pe), _pfc in zip(_WM_PHASES, _WM_PH_COL):
        _ax_ac.axvspan(_ps - 0.5, _pe + 0.5, facecolor=_pfc, alpha=0.4, zorder=1)

    _ax_ac.plot(_WM_WKS, _WM_ACWR, color=_WM_TXT, lw=2.2, zorder=4, marker="o",
                ms=5, label="ACWR")

    # Danger zone annotations
    for _wi in range(len(_WM_WKS)):
        if _WM_ACWR[_wi] >= 1.5:
            _ax_ac.annotate("⚑", xy=(_WM_WKS[_wi], _WM_ACWR[_wi]),
                            xytext=(_WM_WKS[_wi], _WM_ACWR[_wi] + 0.08),
                            fontsize=10, color="#E74C3C", ha="center", zorder=5)

    # CMJ RSI twin axis
    _ax_rsi = _ax_ac.twinx()
    _ax_rsi.set_facecolor(_WM_BG)
    _ax_rsi.plot(_WM_WKS, _WM_RSI, color="#77DD77", lw=1.8, ls="--",
                 alpha=0.85, zorder=3, label="CMJ RSI")
    _ax_rsi.set_ylabel("CMJ RSI", color="#77DD77", fontsize=8)
    _ax_rsi.tick_params(axis="y", colors="#77DD77", labelsize=7.5)
    _ax_rsi.set_ylim(0.80, 1.15)
    for _sp in _ax_rsi.spines.values(): _sp.set_color(_WM_DIM)

    _ax_ac.set_xlim(0.5, 20.5); _ax_ac.set_ylim(0, 2.20)
    _ax_ac.set_xlabel("Week", color=_WM_TXT, fontsize=8)
    _ax_ac.set_ylabel("ACWR", color=_WM_TXT, fontsize=8)
    _ax_ac.set_xticks(_WM_WKS)
    _ax_ac.set_xticklabels([f"W{w}" for w in _WM_WKS], fontsize=7)
    _ax_ac.tick_params(colors=_WM_TXT, labelsize=7.5)
    for _sp in _ax_ac.spines.values(): _sp.set_color(_WM_DIM)

    lines1, labels1 = _ax_ac.get_legend_handles_labels()
    lines2, labels2 = _ax_rsi.get_legend_handles_labels()
    _ax_ac.legend(lines1 + lines2, labels1 + labels2,
                  loc="upper left", fontsize=7.5, framealpha=0.25,
                  facecolor=_WM_BG, edgecolor=_WM_DIM, labelcolor=_WM_TXT)

    # ── RIGHT: Zone guide cards ─────────────────────────────
    _rx = 0.678
    _wmfig.text(_rx, 0.895, "ACWR ZONE GUIDE", fontsize=9,
                fontweight="bold", color=_WM_TXT, va="top")
    _wmfig.text(_rx, 0.872, "Gabbett (2016)  ·  IOC Part 1",
                fontsize=7, color=_WM_DIM, va="top")

    for _zi, (_zlo, _zhi, _zcol, _zn, _zr, _zt) in enumerate(_WM_ZONES):
        _cy = 0.825 - _zi * 0.140
        _wmfig.add_artist(mpatches.FancyBboxPatch(
            (_rx, _cy - 0.100), 0.300, 0.105,
            boxstyle="round,pad=0.006",
            facecolor={"#E74C3C":"#2D0A08","#F39C12":"#2D1500",
                       "#77DD77":"#0D2D1A","#3498DB":"#0D1F35"}[_zcol],
            edgecolor=_zcol, linewidth=1.2,
            transform=_wmfig.transFigure, clip_on=False))
        _wmfig.text(_rx + 0.010, _cy - 0.012, f"{_zn}  {_zr}",
                    fontsize=8.5, fontweight="bold", color=_zcol, va="center")
        _wmfig.text(_rx + 0.010, _cy - 0.038, _zt,
                    fontsize=7, color=_WM_TXT, va="center")

    # CMJ monitoring note
    _wmfig.add_artist(mpatches.FancyBboxPatch(
        (_rx, 0.270), 0.300, 0.175,
        boxstyle="round,pad=0.006",
        facecolor="#0D2D1A", edgecolor="#77DD77", linewidth=1.2,
        transform=_wmfig.transFigure, clip_on=False))
    _wmfig.text(_rx + 0.010, 0.432, "CMJ AS READINESS MARKER",
                fontsize=8, fontweight="bold", color="#77DD77", va="top")
    for _ni, _nt in enumerate([
        "RSI ↓ with ACWR spike → flag fatigue",
        "RSI recovery in taper → competition ready",
        "mRSI trend mirrors chronic load curve",
        "Asymmetry ↑ under high ACWR → injury risk",
        "Monitor 2× per week during congestion",
    ]):
        _wmfig.text(_rx + 0.010, 0.408 - _ni * 0.026, f"· {_nt}",
                    fontsize=6.8, color=_WM_TXT, va="top")

    _wmfig.text(0.03, 0.035,
                "ACWR = Acute:Chronic Workload Ratio  ·  "
                "Acute Load = 1-week sRPE  ·  Chronic Load = 4-week rolling average  ·  "
                "⚑ = ACWR ≥ 1.5 (danger zone flag)",
                fontsize=6.5, color=_WM_DIM, va="bottom")
    _wmfig.text(0.03, 0.018,
                "Soligard et al. (2016) Br J Sports Med 50:1030–1041  ·  "
                "Gabbett TJ (2016) Br J Sports Med 50:273–280  ·  "
                "CMJ data: Hawkin Dynamics",
                fontsize=6.5, color=_WM_DIM, va="bottom")

    plt.savefig("images/workload_acwr.png", dpi=150,
                bbox_inches="tight", facecolor=_WM_BG)
    plt.close()
    print("workload_acwr.png saved")


# ══════════════════════════════════════════════
# STRENGTH DEVELOPMENT — DOSE-RESPONSE
# Suchomel et al. 2018; Peterson et al. 2004
# ══════════════════════════════════════════════

_ST_BG  = "#2C3E50"
_ST_TXT = "#FFFFFF"
_ST_DIM = "#95A5A6"

_ST_BLOCKS = [
    {"phase": "ANATOMICAL\nADAPTATION", "weeks": "3–4 wks",
     "intensity": "50–70% 1RM", "sets": "2–4 sets",  "reps": "12–20 reps",
     "rest": "< 90 s",  "goal": "Work capacity · Tissue tolerance · Movement quality",
     "col": "#3498DB", "bg": "#0D1F35"},
    {"phase": "HYPERTROPHY",            "weeks": "4–6 wks",
     "intensity": "65–80% 1RM", "sets": "3–5 sets",  "reps": "8–12 reps",
     "rest": "60–90 s","goal": "↑ CSA · ↑ Pennation angle · ↑ Force production platform",
     "col": "#F39C12", "bg": "#2D1500"},
    {"phase": "MAXIMAL\nSTRENGTH",      "weeks": "4–6 wks",
     "intensity": "80–95% 1RM", "sets": "3–6 sets",  "reps": "2–6 reps",
     "rest": "2–5 min","goal": "Neural drive · Peak force · MU recruitment · Rate coding",
     "col": "#77DD77", "bg": "#0D2D1A"},
    {"phase": "POWER / SPEED",          "weeks": "3–5 wks",
     "intensity": "30–75% 1RM", "sets": "3–5 sets",  "reps": "3–5 reps",
     "rest": "2–5 min","goal": "RFD · Velocity expression · Ballistic transfer to sport",
     "col": "#9B59B6", "bg": "#2D1244"},
]

# Peterson 2004 — athletes: optimal at 85% 1RM, 8 sets/MG, 2 days/week
# Illustrative effect-size curves centred on reported optima
_st_int   = np.linspace(40, 100, 80)
_st_int_es= np.exp(-0.5 * ((_st_int - 85) / 18)**2) * 1.35

_st_freq  = np.array([1, 2, 3, 4, 5], dtype=float)
_st_fr_es = np.array([0.55, 0.87, 0.75, 0.62, 0.40])

_st_vol   = np.linspace(1, 16, 80)
_st_vol_es= np.exp(-0.5 * ((_st_vol - 8) / 4)**2) * 1.15

_ST_METHODS = [
    ("Bilateral Compound",   "#77DD77", 5),
    ("Eccentric / AEL",      "#77DD77", 5),
    ("Variable Resistance",  "#77DD77", 4),
    ("Heavy + Light Combo",  "#F39C12", 4),
    ("Unilateral",           "#F39C12", 3),
    ("Plyometric",           "#F39C12", 3),
    ("Isolation / Machine",  "#E74C3C", 2),
    ("BW / Kettlebell",      "#E74C3C", 2),
    ("Train to Failure",     "#E74C3C", 1),
]

with plt.rc_context({
    "figure.facecolor": _ST_BG, "axes.facecolor": _ST_BG,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False, "axes.spines.right": False,
}):
    _stfig = plt.figure(figsize=(18, 10), facecolor=_ST_BG)

    _stfig.text(0.03, 0.975, "STRENGTH DEVELOPMENT — DOSE-RESPONSE",
                fontsize=18, fontweight="bold", color=_ST_TXT, va="top")
    _stfig.text(0.03, 0.940,
                "Block Periodization Sequence  ·  Optimal Dose for Athletes  ·  "
                "Suchomel et al. 2018  ·  Peterson et al. 2004 (n = 370 effect sizes)",
                fontsize=8.5, color=_ST_DIM, va="top")
    _stfig.text(0.97, 0.975, "N1 PERFORMANCE LAB PH",
                fontsize=8.5, color=_ST_DIM, va="top", ha="right")

    # ── LEFT: Block periodization ────────────────────────────
    _stfig.text(0.03, 0.905, "BLOCK PERIODIZATION SEQUENCE  (Suchomel et al. 2018)",
                fontsize=8.5, color=_ST_DIM, fontweight="bold", va="top")

    _nb = len(_ST_BLOCKS)
    for _bi, _bl in enumerate(_ST_BLOCKS):
        _bx = 0.03 + _bi * 0.145
        _stfig.add_artist(mpatches.FancyBboxPatch(
            (_bx, 0.13), 0.138, 0.745,
            boxstyle="round,pad=0.006",
            facecolor=_bl["bg"], edgecolor=_bl["col"], linewidth=1.8,
            transform=_stfig.transFigure, clip_on=False))

        # Arrow between blocks
        if _bi < _nb - 1:
            _stfig.text(_bx + 0.143, 0.505, "→",
                        fontsize=14, color=_ST_DIM, va="center", ha="center")

        # Phase number + name
        _stfig.text(_bx + 0.069, 0.855, f"BLOCK {_bi+1}",
                    fontsize=7.5, color=_bl["col"], ha="center", va="top",
                    fontweight="bold")
        _stfig.text(_bx + 0.069, 0.830, _bl["phase"],
                    fontsize=9, color=_bl["col"], ha="center", va="top",
                    fontweight="bold", multialignment="center")
        _stfig.text(_bx + 0.069, 0.785, _bl["weeks"],
                    fontsize=8, color=_ST_DIM, ha="center", va="top")

        # Metrics
        for _mi, (_mk, _mv) in enumerate([
            ("Intensity", _bl["intensity"]),
            ("Volume",    _bl["sets"]),
            ("Reps",      _bl["reps"]),
            ("Rest",      _bl["rest"]),
        ]):
            _my = 0.730 - _mi * 0.075
            _stfig.text(_bx + 0.010, _my, _mk + ":",
                        fontsize=7, color=_ST_DIM, va="top")
            _stfig.text(_bx + 0.128, _my, _mv,
                        fontsize=7.5, color=_ST_TXT, va="top", ha="right",
                        fontweight="bold")

        # Goal
        _stfig.text(_bx + 0.069, 0.385, "GOAL",
                    fontsize=7, color=_bl["col"], ha="center", va="top",
                    fontweight="bold")
        _stfig.text(_bx + 0.069, 0.360, _bl["goal"],
                    fontsize=6.5, color=_ST_TXT, ha="center", va="top",
                    multialignment="center", wrap=True)

    # Key principle (Suchomel)
    _stfig.add_artist(mpatches.FancyBboxPatch(
        (0.03, 0.085), 0.572, 0.038,
        boxstyle="round,pad=0.005",
        facecolor="#0D2D1A", edgecolor="#77DD77", linewidth=1.0,
        transform=_stfig.transFigure, clip_on=False))
    _stfig.text(0.316, 0.105,
                "★  Weaker athletes: establish strength foundation first  ·  "
                "Stronger athletes: can layer power while maintaining strength",
                fontsize=7.5, color="#77DD77", ha="center", va="center")

    # ── MIDDLE: Dose-response curves ────────────────────────
    _stfig.text(0.638, 0.905,
                "OPTIMAL DOSE — ATHLETES  (Peterson et al. 2004, n = 370 ES)",
                fontsize=8.5, color=_ST_DIM, fontweight="bold", va="top")

    # Intensity curve
    _ax_int = _stfig.add_axes([0.625, 0.580, 0.175, 0.290], facecolor=_ST_BG)
    _ax_int.fill_between(_st_int, _st_int_es, alpha=0.20, color="#77DD77")
    _ax_int.plot(_st_int, _st_int_es, color="#77DD77", lw=2.0)
    _ax_int.axvline(85, color="#F39C12", lw=1.5, ls="--")
    _ax_int.text(85, _ax_int.get_ylim()[1] if _ax_int.get_ylim()[1] > 0 else 1.4,
                 "85%", fontsize=8, color="#F39C12", ha="center", va="bottom")
    _ax_int.set_xlabel("Intensity (% 1RM)", color=_ST_TXT, fontsize=7.5)
    _ax_int.set_ylabel("Effect Size", color=_ST_TXT, fontsize=7.5)
    _ax_int.set_title("INTENSITY", color="#77DD77", fontsize=8, fontweight="bold", pad=4)
    _ax_int.tick_params(colors=_ST_TXT, labelsize=7)
    for _sp in _ax_int.spines.values(): _sp.set_color(_ST_DIM)

    # Frequency bars
    _ax_fr = _stfig.add_axes([0.625, 0.200, 0.175, 0.290], facecolor=_ST_BG)
    _bars = _ax_fr.bar(_st_freq, _st_fr_es, color="#3498DB", alpha=0.80, width=0.60)
    _bars[1].set_facecolor("#F39C12")  # optimal = 2 days
    _ax_fr.set_xlabel("Frequency (days/week)", color=_ST_TXT, fontsize=7.5)
    _ax_fr.set_ylabel("Effect Size", color=_ST_TXT, fontsize=7.5)
    _ax_fr.set_title("FREQUENCY", color="#3498DB", fontsize=8, fontweight="bold", pad=4)
    _ax_fr.set_xticks(_st_freq)
    _ax_fr.tick_params(colors=_ST_TXT, labelsize=7)
    _ax_fr.text(2, _st_fr_es[1] + 0.02, "Optimal\n2 days",
                ha="center", va="bottom", fontsize=6.5, color="#F39C12")
    for _sp in _ax_fr.spines.values(): _sp.set_color(_ST_DIM)

    # Volume curve
    _ax_vol = _stfig.add_axes([0.820, 0.390, 0.155, 0.290], facecolor=_ST_BG)
    _ax_vol.fill_between(_st_vol, _st_vol_es, alpha=0.20, color="#9B59B6")
    _ax_vol.plot(_st_vol, _st_vol_es, color="#9B59B6", lw=2.0)
    _ax_vol.axvline(8, color="#F39C12", lw=1.5, ls="--")
    _ax_vol.text(8, 1.18, "8 sets", fontsize=8, color="#F39C12", ha="center", va="bottom")
    _ax_vol.set_xlabel("Volume (sets / MG)", color=_ST_TXT, fontsize=7.5)
    _ax_vol.set_ylabel("Effect Size", color=_ST_TXT, fontsize=7.5)
    _ax_vol.set_title("VOLUME", color="#9B59B6", fontsize=8, fontweight="bold", pad=4)
    _ax_vol.tick_params(colors=_ST_TXT, labelsize=7)
    for _sp in _ax_vol.spines.values(): _sp.set_color(_ST_DIM)

    # Optimal prescription callout
    _stfig.add_artist(mpatches.FancyBboxPatch(
        (0.820, 0.135), 0.155, 0.235,
        boxstyle="round,pad=0.006",
        facecolor="#0D2D1A", edgecolor="#77DD77", linewidth=1.5,
        transform=_stfig.transFigure, clip_on=False))
    _stfig.text(0.898, 0.355, "ATHLETE OPTIMAL",
                fontsize=8, fontweight="bold", color="#77DD77", ha="center", va="top")
    _stfig.text(0.898, 0.330, "Peterson et al. 2004",
                fontsize=6.5, color=_ST_DIM, ha="center", va="top")
    for _oi, (_ok, _ov) in enumerate([
        ("Intensity", "85% 1RM"),
        ("Volume",    "8 sets / MG"),
        ("Frequency", "2 days / wk"),
        ("Rest",      "2–5 min"),
        ("VL thresh", "≤ 20%"),
    ]):
        _oy = 0.302 - _oi * 0.034
        _stfig.text(0.828, _oy, _ok + ":", fontsize=7.5, color=_ST_DIM, va="top")
        _stfig.text(0.970, _oy, _ov, fontsize=7.5, color=_ST_TXT,
                    va="top", ha="right", fontweight="bold")

    _stfig.text(0.03, 0.035,
                "CSA = Cross-Sectional Area  ·  MU = Motor Unit  ·  AEL = Accentuated Eccentric Loading  ·  "
                "MG = Muscle Group  ·  RFD = Rate of Force Development  ·  VL = Velocity Loss",
                fontsize=6.5, color=_ST_DIM, va="bottom")
    _stfig.text(0.03, 0.018,
                "Suchomel et al. (2018) Sports Med  ·  "
                "Peterson, Rhea & Alvar (2004) J Strength Cond Res 18(2):377–382  ·  "
                "Bilateral > unilateral for max strength; eccentric + AEL produce greatest adaptations",
                fontsize=6.5, color=_ST_DIM, va="bottom")

    plt.savefig("images/strength_dose_response.png", dpi=150,
                bbox_inches="tight", facecolor=_ST_BG)
    plt.close()
    print("strength_dose_response.png saved")
