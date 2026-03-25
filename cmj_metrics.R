# =============================================================================
# CMJ Metrics — Hawkins Dynamics R Equivalents
#
# Metrics computed:
#   Jump Height (flight time method & impulse-momentum method)
#   Peak Force, Mean Force
#   Peak Power
#   Braking RFD (rate of force development)
#   Braking Impulse, Propulsive Impulse, Net Impulse
#   Contraction Time (braking + propulsive duration)
#   Eccentric Depth (peak negative displacement)
#   RSI-Modified (jump height / contraction time)
#   Peak Landing Force
# =============================================================================

source("cmj_phases.R")

# ── Impulse via trapezoidal rule ─────────────────────────────────────────────
trapz_impulse <- function(force_vec, dt) {
  sum(diff(seq_along(force_vec)) * (force_vec[-length(force_vec)] +
    force_vec[-1]) / 2) * dt
}

# ── Core metrics function ─────────────────────────────────────────────────────
compute_cmj_metrics <- function(df, sample_rate = 1000) {
  dt     <- 1 / sample_rate
  phases <- detect_phases(df)
  df     <- annotate_phases(df, phases)

  bw_N   <- phases$bw_N
  mass   <- bw_N / 9.81

  idx <- list(
    weighing   = phases$weighing_start:(phases$unweight_start - 1),
    unweight   = phases$unweight_start:(phases$braking_start - 1),
    braking    = phases$braking_start:(phases$propulsive_start - 1),
    propulsive = phases$propulsive_start:(phases$flight_start - 1),
    flight     = phases$flight_start:(phases$landing_start - 1),
    landing    = phases$landing_start:nrow(df)
  )

  # ── Jump Height (flight time method) ────────────────────────────────────────
  flight_time  <- length(idx$flight) * dt
  jump_height_ft <- (9.81 * flight_time^2) / 8   # metres

  # ── Jump Height (impulse-momentum method) ───────────────────────────────────
  net_impulse <- trapz_impulse(df$force[c(idx$unweight, idx$braking,
                                          idx$propulsive)] - bw_N, dt)
  takeoff_vel <- net_impulse / mass
  jump_height_imp <- takeoff_vel^2 / (2 * 9.81)   # metres

  # ── Braking phase metrics ───────────────────────────────────────────────────
  brake_force  <- df$force[idx$braking]
  brake_time   <- length(idx$braking) * dt
  peak_brake   <- max(brake_force)
  mean_brake   <- mean(brake_force)

  # RFD: steepest 50 ms window in braking phase
  win <- round(0.050 * sample_rate)
  rfd_vals <- sapply(seq_len(length(brake_force) - win),
                     function(i) (brake_force[i + win] - brake_force[i]) /
                       (win * dt))
  peak_braking_rfd <- max(rfd_vals)

  braking_impulse <- trapz_impulse(brake_force - bw_N, dt)

  # ── Propulsive phase metrics ─────────────────────────────────────────────────
  prop_force       <- df$force[idx$propulsive]
  prop_time        <- length(idx$propulsive) * dt
  peak_prop_force  <- max(prop_force)
  mean_prop_force  <- mean(prop_force)
  propulsive_impulse <- trapz_impulse(prop_force - bw_N, dt)

  # ── Power = Force × Velocity ─────────────────────────────────────────────────
  prop_power  <- df$force[idx$propulsive] * df$velocity[idx$propulsive]
  peak_power  <- max(prop_power)
  mean_power  <- mean(prop_power)

  # ── Contraction time & RSI-Modified ─────────────────────────────────────────
  contraction_time <- brake_time + prop_time    # seconds
  rsi_mod          <- jump_height_ft / contraction_time

  # ── Eccentric depth (peak negative displacement) ────────────────────────────
  eccentric_depth  <- abs(min(df$height[c(idx$unweight, idx$braking)]))

  # ── Landing ──────────────────────────────────────────────────────────────────
  peak_landing_force <- max(df$force[idx$landing])

  # ── Assemble results ─────────────────────────────────────────────────────────
  metrics <- data.frame(
    metric  = c(
      "Bodyweight (N)",
      "Jump Height — Flight Time (cm)",
      "Jump Height — Impulse-Momentum (cm)",
      "Takeoff Velocity (m/s)",
      "Flight Time (s)",
      "Peak Braking Force (N)",
      "Mean Braking Force (N)",
      "Braking Impulse (N·s)",
      "Braking RFD — Peak 50ms (N/s)",
      "Braking Time (s)",
      "Peak Propulsive Force (N)",
      "Mean Propulsive Force (N)",
      "Propulsive Impulse (N·s)",
      "Propulsive Time (s)",
      "Peak Power (W)",
      "Mean Propulsive Power (W)",
      "Contraction Time (s)",
      "RSI-Modified",
      "Eccentric Depth (cm)",
      "Peak Landing Force (N)"
    ),
    value = round(c(
      bw_N,
      jump_height_ft * 100,
      jump_height_imp * 100,
      takeoff_vel,
      flight_time,
      peak_brake,
      mean_brake,
      braking_impulse,
      peak_braking_rfd,
      brake_time,
      peak_prop_force,
      mean_prop_force,
      propulsive_impulse,
      prop_time,
      peak_power,
      mean_power,
      contraction_time,
      rsi_mod,
      eccentric_depth * 100,
      peak_landing_force
    ), 2)
  )

  list(metrics = metrics, df = df, phases = phases, bw_N = bw_N)
}

# ── Run standalone ────────────────────────────────────────────────────────────
if (!interactive()) {
  df      <- simulate_cmj()
  results <- compute_cmj_metrics(df)

  cat("\n=== CMJ Metrics (Hawkins R Style) ===\n\n")
  print(results$metrics, row.names = FALSE)
}
