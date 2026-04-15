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

print("\nAll images generated successfully!")


# ══════════════════════════════════════════════════════════════
# STATS ONE–INSPIRED ADDITIONS
# 1. CMJ TREND MONITORING DASHBOARD
# 2. CMJ NORMATIVE BENCHMARKS
# ══════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────
# 1. CMJ TREND MONITORING DASHBOARD
#    Multi-metric trend chart across a training block.
#    Inspired by Stats One's Weekly Load / Wellness dashboards.
# ──────────────────────────────────────────────────────────────

rng = np.random.default_rng(42)

sessions = np.arange(1, 25)   # 24 sessions (~12 weeks, 2x/week)
labels_short = [f"W{(s - 1) // 2 + 1}S{(s - 1) % 2 + 1}" for s in sessions]

# Simulated athlete metrics across a pre-season block
# Jump Height (cm): starts moderate, peaks mid-block, slight taper at end
jh_base = 42 + 6 * np.sin(np.linspace(0, np.pi, 24)) - np.linspace(0, 1.5, 24)
jump_height = jh_base + rng.normal(0, 1.0, 24)

# mRSI: follows similar arc, dips slightly post-match weeks
mrsi_base = 0.88 + 0.12 * np.sin(np.linspace(0, np.pi, 24)) - np.linspace(0, 0.04, 24)
mrsi = mrsi_base + rng.normal(0, 0.018, 24)
mrsi[np.array([5, 11, 17, 21])] -= 0.06  # post-match dips

# Limb Symmetry Index (LSI, %) — propulsive force asymmetry
lsi_base = 96 + 2 * np.sin(np.linspace(0, 2 * np.pi, 24))
lsi = lsi_base + rng.normal(0, 1.5, 24)
lsi = np.clip(lsi, 82, 100)

# Match days (sessions after which athlete played)
match_sessions = [6, 12, 18, 22]

# Traffic-light thresholds
JH_AMBER, JH_GREEN = 38, 42        # cm
MRSI_AMBER, MRSI_GREEN = 0.75, 0.85
LSI_AMBER, LSI_GREEN = 90, 95       # %

fig, axes = plt.subplots(3, 1, figsize=(13, 9), sharex=True)
fig.suptitle("CMJ Trend Monitoring Dashboard", fontsize=16, fontweight="bold", y=0.98)

panel_cfg = [
    (axes[0], jump_height,  "Jump Height (cm)",          JH_AMBER,   JH_GREEN,   30,   52,  "#1a6faf", "Jump Height"),
    (axes[1], mrsi,         "mRSI",                      MRSI_AMBER, MRSI_GREEN, 0.58, 1.05, "#2a9d8f", "mRSI"),
    (axes[2], lsi,          "Propulsive LSI (%)",         LSI_AMBER,  LSI_GREEN,  78,   102,  "#7b4f9e", "LSI"),
]

for ax, data, ylabel, amber_t, green_t, ymin, ymax, color, label in panel_cfg:
    # Traffic-light bands
    ax.axhspan(ymin,    amber_t, color="#f5e6e6", alpha=0.55, zorder=0)
    ax.axhspan(amber_t, green_t, color="#fff4e0", alpha=0.55, zorder=0)
    ax.axhspan(green_t, ymax,    color="#e8f5e9", alpha=0.55, zorder=0)

    # Threshold lines
    ax.axhline(amber_t, color="#e07b39", linewidth=0.9, linestyle="--", alpha=0.7)
    ax.axhline(green_t, color="#43a047", linewidth=0.9, linestyle="--", alpha=0.7)

    # Match-day verticals
    for ms in match_sessions:
        ax.axvline(ms, color="#c0392b", linewidth=1.2, linestyle=":", alpha=0.55, zorder=1)

    # Rolling 3-session mean
    roll = np.convolve(data, np.ones(3) / 3, mode="same")
    roll[:1]  = data[:1]
    roll[-1:] = data[-1:]
    ax.plot(sessions, roll, color=color, linewidth=2.2, zorder=3, label="3-session avg")

    # Individual session dots, colored by traffic light
    for s, v in zip(sessions, data):
        dot_color = "#43a047" if v >= green_t else ("#e07b39" if v >= amber_t else "#c0392b")
        ax.scatter(s, v, color=dot_color, s=38, zorder=4, edgecolors="white", linewidths=0.6)

    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_ylim(ymin, ymax)
    ax.tick_params(labelsize=8)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    # Band labels on right
    ax.text(24.6, amber_t - (amber_t - ymin) * 0.5, "Below\nThreshold", fontsize=6.5,
            color="#c0392b", va="center", ha="left")
    ax.text(24.6, (amber_t + green_t) / 2,         "Caution",          fontsize=6.5,
            color="#e07b39", va="center", ha="left")
    ax.text(24.6, green_t + (ymax - green_t) * 0.4, "Optimal",          fontsize=6.5,
            color="#43a047", va="center", ha="left")

axes[2].set_xticks(sessions)
axes[2].set_xticklabels(labels_short, rotation=45, ha="right", fontsize=7.5)
axes[2].set_xlabel("Training Session", fontsize=10)

# Legend
legend_elements = [
    plt.Line2D([0], [0], color="#1a6faf", lw=2, label="3-session rolling avg"),
    plt.scatter([], [], color="#43a047", s=38, label="Optimal"),
    plt.scatter([], [], color="#e07b39", s=38, label="Caution"),
    plt.scatter([], [], color="#c0392b", s=38, label="Below threshold"),
    plt.Line2D([0], [0], color="#c0392b", lw=1.2, ls=":", alpha=0.7, label="Match day"),
]
fig.legend(handles=legend_elements, loc="upper right", fontsize=8,
           bbox_to_anchor=(0.99, 0.96), frameon=True)

plt.tight_layout(rect=[0, 0, 0.93, 0.97])
plt.savefig("images/cmj_trend_monitoring.png", dpi=150, bbox_inches="tight")
plt.close()
print("cmj_trend_monitoring.png saved")


# ──────────────────────────────────────────────────────────────
# 2. CMJ NORMATIVE BENCHMARKS
#    Athlete result vs population bands (below / average / good / elite).
#    Inspired by Stats One's benchmark dashboards.
# ──────────────────────────────────────────────────────────────

metrics = [
    # (label,                    unit,  athlete, p25, p50, p75, elite,  direction)
    ("Jump Height",              "cm",  46.2,    32,  38,  44,  52,     "higher"),
    ("Peak Propulsive Force",    "× BW", 2.18,   1.7, 1.9, 2.2, 2.6,   "higher"),
    ("Braking RFD",              "N/s",  4820,  2800,3500,4500, 6000,   "higher"),
    ("Loading Rate",             "kN/s", 38.4,   25,  32,  42,  58,    "higher"),
    ("mRSI",                     "",     0.91,   0.6, 0.75,0.90,1.10,  "higher"),
    ("LSI — Propulsive",         "%",    96.8,   88,  92,  96,  99,    "higher"),
    ("Control Time",             "ms",   23.5,   28,  24,  20,  15,    "lower"),
    ("Takeoff Velocity",         "m/s",  3.01,   2.4, 2.7, 3.0, 3.5,  "higher"),
]

fig, ax = plt.subplots(figsize=(11, 7))
ax.set_xlim(0, 100)
n = len(metrics)
ax.set_ylim(-0.5, n - 0.5)
ax.axis("off")
fig.patch.set_facecolor("white")

fig.suptitle("CMJ Normative Benchmarks", fontsize=16, fontweight="bold", y=0.97)
ax.text(50, n - 0.1, "Athlete result vs population percentile bands",
        ha="center", va="bottom", fontsize=9, color="#555", style="italic")

BAND_COLORS = ["#f5c6c6", "#fde8c8", "#d4edda", "#b8dfc8"]
BAND_LABELS = ["Below Avg\n(<P25)", "Average\n(P25–P50)", "Good\n(P50–P75)", "Elite\n(>P75)"]
BAND_TEXT_COLORS = ["#c0392b", "#e07b39", "#27ae60", "#1a7a4a"]

bar_h = 0.52
label_x = 0
bar_start = 22
bar_width = 62   # px units in 0-100 space

for i, (label, unit, athlete, p25, p50, p75, elite, direction) in enumerate(metrics):
    y = n - 1 - i

    # Normalize positions to bar_start..bar_start+bar_width
    lo, hi = (min(p25, elite) * 0.88, max(p25, elite) * 1.12) if direction == "higher" \
             else (min(p25, elite) * 0.88, max(p25, elite) * 1.12)
    lo  = min(p25, p75, elite) * 0.88
    hi  = max(p25, p75, elite) * 1.10

    def norm(v):
        return bar_start + (v - lo) / (hi - lo) * bar_width

    breakpoints = sorted([p25, p50, p75, elite]) if direction == "higher" \
                  else sorted([elite, p75, p50, p25])

    # Draw bands
    band_edges = [lo] + sorted([p25, p50, p75, elite]) + [hi]
    for b in range(4):
        bx0 = norm(band_edges[b])
        bx1 = norm(band_edges[b + 1])
        bc = BAND_COLORS[b] if direction == "higher" else BAND_COLORS[3 - b]
        ax.barh(y, bx1 - bx0, left=bx0, height=bar_h, color=bc, zorder=1)
        ax.barh(y, bx1 - bx0, left=bx0, height=bar_h, color="none",
                edgecolor="#ccc", linewidth=0.5, zorder=2)

    # Percentile tick marks
    for v, pct in [(p25, "P25"), (p50, "P50"), (p75, "P75"), (elite, "Elite")]:
        xv = norm(v)
        ax.plot([xv, xv], [y - bar_h / 2, y + bar_h / 2],
                color="#888", linewidth=0.9, zorder=3)
        ax.text(xv, y - bar_h / 2 - 0.06, pct, ha="center", va="top", fontsize=5.5, color="#888")

    # Athlete marker
    ax_v = norm(athlete)
    ax.scatter(ax_v, y, color="#1a1a2e", s=90, zorder=5, marker="D")
    ax.plot([ax_v, ax_v], [y - bar_h / 2, y + bar_h / 2],
            color="#1a1a2e", linewidth=2.0, zorder=4)

    # Percentile label for athlete
    # Compute approximate percentile
    if direction == "higher":
        if   athlete >= elite: pct_label = "Elite"
        elif athlete >= p75:   pct_label = f"P{int(75 + 25 * (athlete - p75) / (elite - p75))}+"
        elif athlete >= p50:   pct_label = f"P{int(50 + 25 * (athlete - p50) / (p75 - p50))}"
        elif athlete >= p25:   pct_label = f"P{int(25 + 25 * (athlete - p25) / (p50 - p25))}"
        else:                  pct_label = f"<P25"
    else:
        if   athlete <= elite: pct_label = "Elite"
        elif athlete <= p75:   pct_label = f"P{int(75 + 25 * (p75 - athlete) / (p75 - elite))}+"
        elif athlete <= p50:   pct_label = f"P{int(50 + 25 * (p50 - athlete) / (p50 - p75))}"
        elif athlete <= p25:   pct_label = f"P{int(25 + 25 * (p25 - athlete) / (p25 - p50))}"
        else:                  pct_label = f"<P25"

    val_str = f"{athlete}" if isinstance(athlete, int) or athlete != int(athlete) else str(int(athlete))
    ax.text(ax_v + 1.2, y + 0.28, f"{athlete} {unit}  [{pct_label}]",
            ha="left", va="center", fontsize=8, fontweight="bold", color="#1a1a2e", zorder=6)

    # Metric label
    ax.text(label_x, y, label, ha="left", va="center", fontsize=9.5, color="#222")

# Legend
legend_patches = [
    mpatches.Patch(color=c, label=l)
    for c, l in zip(BAND_COLORS, BAND_LABELS)
]
legend_patches.append(
    plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="#1a1a2e",
               markersize=7, label="Athlete Result")
)
ax.legend(handles=legend_patches, loc="lower right", fontsize=8,
          bbox_to_anchor=(1.0, 0.0), frameon=True, title="Percentile Bands", title_fontsize=8)

ax.text(50, -0.85,
        "Reference: McMahon et al. (2018) · Moran et al. (2021) · Healy et al. (2022)  |  "
        "Bands represent professional / high-performance athlete populations",
        ha="center", va="center", fontsize=6.5, color="#777", style="italic")

plt.tight_layout(rect=[0, 0.02, 1, 0.96])
plt.savefig("images/cmj_benchmarks.png", dpi=150, bbox_inches="tight")
plt.close()
print("cmj_benchmarks.png saved")

print("\nStats One integration plots generated successfully!")
