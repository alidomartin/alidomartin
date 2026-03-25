# =============================================================================
# CMJ Phase Detection — Hawkins Dynamics R Methodology
#
# Phases:
#   0 = Weighing     (quiet standing)
#   1 = Unweighting  (COM moving down, force < BW)
#   2 = Braking      (COM moving down, force > BW)
#   3 = Propulsive   (COM moving up,   force > 0)
#   4 = Flight       (force ≈ 0)
#   5 = Landing      (force spike after flight)
# =============================================================================

source("cmj_simulate_data.R")

# ── Detect phases from raw force signal ─────────────────────────────────────
detect_phases <- function(df, bw_threshold = 0.02, flight_threshold = 20) {
  n    <- nrow(df)
  bw_N <- mean(df$force[df$phase == 0])   # use quiet-standing mean as BW

  # ── Takeoff: last sample where force > flight_threshold before force = 0 ──
  takeoff_idx  <- which(df$force <= flight_threshold)[1]

  # ── Landing: first sample after flight where force > flight_threshold ──────
  flight_start <- takeoff_idx
  post_flight  <- which(df$force > flight_threshold & seq_len(n) > flight_start)
  landing_idx  <- if (length(post_flight)) post_flight[1] else n

  # ── Unweighting onset: last sample in quiet standing before force < BW ─────
  bw_low      <- bw_N * (1 - bw_threshold)
  pre_takeoff <- seq_len(takeoff_idx)
  below_bw    <- which(df$force[pre_takeoff] < bw_low)
  unweight_idx <- if (length(below_bw)) below_bw[1] else 1

  # ── Braking onset: velocity crosses zero (downward → upward reversal) ──────
  # In the unweighting→braking transition velocity is negative;
  # braking ends / propulsive begins when velocity = 0 (min displacement)
  pre_takeoff_vel <- df$velocity[seq_len(takeoff_idx)]
  # velocity goes negative then returns to 0 → find the sign change (neg→pos)
  sign_changes <- which(diff(sign(pre_takeoff_vel)) > 0)
  braking_end_idx <- if (length(sign_changes)) sign_changes[length(sign_changes)] else takeoff_idx

  # Phase boundaries
  list(
    weighing_start   = 1,
    unweight_start   = unweight_idx,
    braking_start    = which.min(df$force[seq_len(takeoff_idx)]),  # force nadir
    propulsive_start = braking_end_idx,
    flight_start     = takeoff_idx,
    landing_start    = landing_idx,
    landing_end      = n,
    bw_N             = bw_N
  )
}

# ── Annotate data frame with detected phase labels ───────────────────────────
annotate_phases <- function(df, phases) {
  n       <- nrow(df)
  p_label <- integer(n)

  p_label[phases$weighing_start:(phases$unweight_start - 1)]   <- 0
  p_label[phases$unweight_start:(phases$braking_start - 1)]    <- 1
  p_label[phases$braking_start:(phases$propulsive_start - 1)]  <- 2
  p_label[phases$propulsive_start:(phases$flight_start - 1)]   <- 3
  p_label[phases$flight_start:(phases$landing_start - 1)]      <- 4
  p_label[phases$landing_start:n]                               <- 5

  df$phase_detected <- p_label
  df
}

# ── Quick check ──────────────────────────────────────────────────────────────
if (!interactive()) {
  df     <- simulate_cmj()
  phases <- detect_phases(df)
  df     <- annotate_phases(df, phases)

  cat("Phase boundaries (sample index):\n")
  cat(sprintf("  0 Weighing:    %d\n",   phases$weighing_start))
  cat(sprintf("  1 Unweighting: %d\n",   phases$unweight_start))
  cat(sprintf("  2 Braking:     %d\n",   phases$braking_start))
  cat(sprintf("  3 Propulsive:  %d\n",   phases$propulsive_start))
  cat(sprintf("  4 Flight:      %d\n",   phases$flight_start))
  cat(sprintf("  5 Landing:     %d\n",   phases$landing_start))
  cat(sprintf("  Bodyweight:    %.1f N\n", phases$bw_N))
}
