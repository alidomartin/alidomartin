"""
Batch CMJ analysis — processes a folder of force plate CSV files and writes
per-athlete metrics to a summary CSV plus individual phase plots.

Expected CSV format (one file per session):
    time_s,force_N
    0.000,693.2
    0.002,695.1
    ...

File naming convention: <athlete_id>_<YYYY-MM-DD>.csv
  e.g. athlete_jane_2026-04-27.csv

Usage:
    python batch_analyze.py --input data/ --output results/
    python batch_analyze.py --input data/ --output results/ --plots
"""

import argparse
import csv
import os
from dataclasses import dataclass, fields
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.ndimage import gaussian_filter1d


# ─────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────

@dataclass
class CMJMetrics:
    athlete_id: str
    date: str
    body_weight_N: float
    # Jump
    jump_height_m: float
    peak_propulsive_force_N: float
    peak_propulsive_force_bw: float
    rfd_braking_Ns: float         # rate of force development in braking
    # Phases (durations in ms)
    quiet_duration_ms: float
    unweighting_duration_ms: float
    braking_duration_ms: float
    propulsive_duration_ms: float
    flight_duration_ms: float
    # Landing
    peak_landing_force_N: float
    peak_landing_force_bw: float
    loading_rate_kNs: float
    landing_time_ms: float


# ─────────────────────────────────────────────────────────────────
# I/O helpers
# ─────────────────────────────────────────────────────────────────

def load_csv(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (time_s, force_N) arrays from a two-column CSV."""
    t, f = [], []
    with open(path) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            t.append(float(row["time_s"]))
            f.append(float(row["force_N"]))
    return np.array(t), np.array(f)


def parse_filename(path: Path) -> tuple[str, str]:
    """Extract (athlete_id, date) from '<athlete_id>_<YYYY-MM-DD>.csv'."""
    stem = path.stem
    parts = stem.rsplit("_", 3)
    if len(parts) >= 4:
        date = "_".join(parts[-3:])
        athlete_id = "_".join(parts[:-3])
    else:
        athlete_id = stem
        date = "unknown"
    return athlete_id, date


# ─────────────────────────────────────────────────────────────────
# Signal processing
# ─────────────────────────────────────────────────────────────────

def smooth(signal: np.ndarray, sigma: float = 2.0) -> np.ndarray:
    return gaussian_filter1d(signal, sigma=sigma)


def estimate_body_weight(force: np.ndarray, fs: float) -> float:
    """Mean force over the first quiet second."""
    n = int(fs)
    return float(np.mean(force[:n]))


def integrate_velocity(force: np.ndarray, bw: float, fs: float) -> np.ndarray:
    """Numerically integrate net force → COM velocity (m/s). Mass = bw/9.81."""
    mass = bw / 9.81
    net = force - bw
    vel = np.cumsum(net) / (mass * fs)
    return vel


# ─────────────────────────────────────────────────────────────────
# Phase detection
# ─────────────────────────────────────────────────────────────────

def detect_phases(t: np.ndarray, f: np.ndarray, bw: float, fs: float) -> dict:
    """
    Returns dict of phase boundary indices:
        quiet_end, unweight_start, braking_start, transfer_idx,
        propulsive_end, flight_end (= landing_start), series_end
    """
    vel = integrate_velocity(f, bw, fs)
    threshold = 0.05 * bw  # 5% BW below quiet level = start of unweighting

    # Quiet ends where force first drops below BW - threshold
    quiet_end = int(fs)  # at minimum 1 s quiet
    for i in range(int(fs), len(f)):
        if f[i] < bw - threshold:
            quiet_end = i
            break

    # Braking starts at peak negative velocity
    search_start = quiet_end
    search_end = min(quiet_end + int(fs), len(vel))
    braking_start = search_start + int(np.argmin(vel[search_start:search_end]))

    # Transfer: velocity crosses zero (braking → propulsive)
    transfer_idx = braking_start
    for i in range(braking_start, min(braking_start + int(0.5 * fs), len(vel))):
        if vel[i] >= 0:
            transfer_idx = i
            break

    # Propulsive ends at takeoff: force drops to near zero
    propulsive_end = transfer_idx
    for i in range(transfer_idx, len(f)):
        if f[i] < 20:
            propulsive_end = i
            break

    # Flight ends at landing: force rises above threshold again
    flight_end = propulsive_end
    for i in range(propulsive_end + int(0.05 * fs), len(f)):
        if f[i] > 50:
            flight_end = i
            break

    return {
        "quiet_end":      quiet_end,
        "unweight_start": quiet_end,
        "braking_start":  braking_start,
        "transfer_idx":   transfer_idx,
        "propulsive_end": propulsive_end,
        "flight_end":     flight_end,
        "series_end":     len(f) - 1,
    }


# ─────────────────────────────────────────────────────────────────
# Metrics computation
# ─────────────────────────────────────────────────────────────────

def compute_metrics(
    athlete_id: str,
    date: str,
    t: np.ndarray,
    f: np.ndarray,
    fs: float,
) -> CMJMetrics:
    f = smooth(f)
    bw = estimate_body_weight(f, fs)
    ph = detect_phases(t, f, bw, fs)

    def ms(n_samples: int) -> float:
        return n_samples / fs * 1000

    # Jump height via takeoff velocity impulse method
    vel = integrate_velocity(f, bw, fs)
    v_takeoff = vel[ph["propulsive_end"]]
    jump_height = max(v_takeoff**2 / (2 * 9.81), 0.0)

    # Peak propulsive force
    prop_slice = f[ph["transfer_idx"]:ph["propulsive_end"]]
    peak_prop = float(np.max(prop_slice)) if len(prop_slice) else 0.0

    # RFD during braking (slope of force rise)
    brake_slice = f[ph["braking_start"]:ph["transfer_idx"]]
    if len(brake_slice) > 1:
        rfd = (float(np.max(brake_slice)) - float(brake_slice[0])) / (len(brake_slice) / fs)
    else:
        rfd = 0.0

    # Landing metrics
    land_slice = f[ph["flight_end"]:]
    peak_land = float(np.max(land_slice)) if len(land_slice) else 0.0
    # Loading rate: force rise from contact to peak
    peak_land_idx = int(np.argmax(land_slice))
    if peak_land_idx > 0:
        loading_rate = peak_land / (peak_land_idx / fs) / 1000  # kN/s
    else:
        loading_rate = 0.0
    # Landing time: contact to COM velocity back to 0
    vel_land = integrate_velocity(land_slice, bw, fs)
    land_stop_idx = next((i for i, v in enumerate(vel_land) if v >= 0), len(vel_land))
    landing_time_ms = ms(land_stop_idx)

    return CMJMetrics(
        athlete_id=athlete_id,
        date=date,
        body_weight_N=round(bw, 1),
        jump_height_m=round(jump_height, 3),
        peak_propulsive_force_N=round(peak_prop, 1),
        peak_propulsive_force_bw=round(peak_prop / bw, 2) if bw else 0.0,
        rfd_braking_Ns=round(rfd, 1),
        quiet_duration_ms=round(ms(ph["quiet_end"]), 1),
        unweighting_duration_ms=round(ms(ph["braking_start"] - ph["unweight_start"]), 1),
        braking_duration_ms=round(ms(ph["transfer_idx"] - ph["braking_start"]), 1),
        propulsive_duration_ms=round(ms(ph["propulsive_end"] - ph["transfer_idx"]), 1),
        flight_duration_ms=round(ms(ph["flight_end"] - ph["propulsive_end"]), 1),
        peak_landing_force_N=round(peak_land, 1),
        peak_landing_force_bw=round(peak_land / bw, 2) if bw else 0.0,
        loading_rate_kNs=round(loading_rate, 2),
        landing_time_ms=round(landing_time_ms, 1),
    )


# ─────────────────────────────────────────────────────────────────
# Optional per-session plot
# ─────────────────────────────────────────────────────────────────

PHASE_COLORS = {
    "quiet":      "#A8D5E2",
    "unweight":   "#F5E642",
    "braking":    "#F08080",
    "propulsive": "#90EE90",
    "flight":     "#C8A2C8",
    "landing":    "#FFB347",
}


def save_session_plot(
    t: np.ndarray,
    f: np.ndarray,
    bw: float,
    ph: dict,
    metrics: CMJMetrics,
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axhline(bw, color="#888", linewidth=1.2, linestyle="--", label=f"Body Weight ({bw:.0f} N)")
    ax.plot(t, f, color="#1a1a2e", linewidth=1.8, label="Vertical GRF")

    spans = [
        ("quiet",      0,                    ph["quiet_end"]),
        ("unweight",   ph["unweight_start"],  ph["braking_start"]),
        ("braking",    ph["braking_start"],   ph["transfer_idx"]),
        ("propulsive", ph["transfer_idx"],    ph["propulsive_end"]),
        ("flight",     ph["propulsive_end"],  ph["flight_end"]),
        ("landing",    ph["flight_end"],      ph["series_end"]),
    ]
    for name, s, e in spans:
        ax.axvspan(t[s], t[min(e, len(t) - 1)], alpha=0.25, color=PHASE_COLORS[name], label=name.title())

    ax.set_xlabel("Time (s)", fontsize=11)
    ax.set_ylabel("Force (N)", fontsize=11)
    title = f"{metrics.athlete_id}  |  {metrics.date}  |  Jump Height: {metrics.jump_height_m:.3f} m"
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, loc="upper right", ncol=2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


# ─────────────────────────────────────────────────────────────────
# Summary CSV writer
# ─────────────────────────────────────────────────────────────────

def write_summary(metrics_list: list[CMJMetrics], out_path: Path) -> None:
    if not metrics_list:
        return
    header = [f.name for f in fields(CMJMetrics)]
    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for m in metrics_list:
            writer.writerow({f.name: getattr(m, f.name) for f in fields(m)})
    print(f"Summary written → {out_path}")


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Batch CMJ force plate analysis")
    parser.add_argument("--input",  default="data",    help="Folder of input CSV files")
    parser.add_argument("--output", default="results", help="Folder for output files")
    parser.add_argument("--plots",  action="store_true", help="Save per-session plots")
    parser.add_argument("--fs",     type=float, default=1000.0, help="Sample rate (Hz)")
    args = parser.parse_args()

    in_dir  = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(in_dir.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {in_dir}/")
        return

    all_metrics: list[CMJMetrics] = []

    for path in csv_files:
        print(f"Processing {path.name} ...", end=" ")
        try:
            t, f = load_csv(path)
            fs = args.fs
            # Auto-detect sample rate from time vector if possible
            if len(t) > 1:
                dt = np.median(np.diff(t))
                if dt > 0:
                    fs = round(1.0 / dt)

            athlete_id, date = parse_filename(path)
            f_smooth = smooth(f)
            bw = estimate_body_weight(f_smooth, fs)
            ph = detect_phases(t, f_smooth, bw, fs)
            metrics = compute_metrics(athlete_id, date, t, f, fs)
            all_metrics.append(metrics)

            if args.plots:
                plot_path = out_dir / f"{path.stem}.png"
                save_session_plot(t, f_smooth, bw, ph, metrics, plot_path)
                print(f"plot saved → {plot_path.name}", end=" ")

            print(f"jump={metrics.jump_height_m:.3f}m  peak={metrics.peak_propulsive_force_bw:.2f}xBW")

        except Exception as exc:
            print(f"ERROR: {exc}")

    write_summary(all_metrics, out_dir / "cmj_summary.csv")
    print(f"\nDone. {len(all_metrics)}/{len(csv_files)} sessions processed.")


if __name__ == "__main__":
    main()
