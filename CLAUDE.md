# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Regenerate all images
python generate_plots.py

# Install dependencies
pip install numpy matplotlib scipy
```

After running the script, commit the updated PNGs in `images/` alongside any script changes — the README embeds them directly from that directory.

## Architecture

This is a single-file data-visualisation project. `generate_plots.py` builds synthetic CMJ (Countermovement Jump) force-time data and saves 11 PNG charts to `images/`, which `README.md` references as a visual reference guide.

**Two independent curve builders:**

- `build_cmj_curve()` — constructs a full jump sequence (quiet → unweight → brake → propulsive → flight → landing) using piecewise sinusoidal/polynomial segments, then smooths with `gaussian_filter1d`. Returns `(T, F, PH)` used by all jump-phase plots.
- `build_landing_curve()` — constructs a high-resolution landing GRF + COM-velocity signal (0–180 ms) using Gaussian peaks. Returns `(T_L, GRF_L, VEL_L, PH_L)` used by the three landing-detail plots.

**Two plot helpers:**

- `plot_phase(ax, phase_key, ...)` — draws the full jump curve, shades the named phase, and applies consistent axis styling. Called once per jump-phase image.
- `plot_landing_phase(ax1, highlight, ...)` — draws the landing GRF with a twin-axis COM-velocity overlay. Called for each of the three landing-detail images and the summary figure.

The bottom of the file is a sequential series of `fig/ax` blocks (one per output image) that call these helpers, add annotations, and save to `images/`.
