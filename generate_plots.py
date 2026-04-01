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
