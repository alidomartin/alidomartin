# =============================================================================
# CMJ Force Plate Data Simulator
# Generates realistic countermovement jump force-time data
# mimicking Hawkins Dynamics output format
# =============================================================================

simulate_cmj <- function(
  bodyweight_kg = 80,
  sample_rate   = 1000,   # Hz
  seed          = 42
) {
  set.seed(seed)
  bw_N <- bodyweight_kg * 9.81  # bodyweight in Newtons

  # ── Time parameters per phase (seconds) ─────────────────────────────────────
  t_weighing    <- 0.50   # quiet standing
  t_unweight    <- 0.25   # unweighting dip
  t_braking     <- 0.18   # eccentric braking
  t_propulsive  <- 0.18   # concentric propulsion
  t_flight      <- 0.42   # airborne (encodes jump height)
  t_landing     <- 0.25   # landing absorption

  dt <- 1 / sample_rate

  # ── Helper: smooth transition via cosine interpolation ─────────────────────
  cosine_interp <- function(n, from, to) {
    t  <- seq(0, pi, length.out = n)
    from + (to - from) * (1 - cos(t)) / 2
  }

  # ── Build force signal per phase ────────────────────────────────────────────

  # Phase 0 — Weighing: flat at BW with small noise
  n0     <- round(t_weighing * sample_rate)
  f_p0   <- rep(bw_N, n0) + rnorm(n0, 0, 5)

  # Phase 1 — Unweighting: dip below BW
  n1     <- round(t_unweight * sample_rate)
  peak_unweight <- bw_N * 0.45
  f_p1   <- cosine_interp(n1, bw_N, peak_unweight) + rnorm(n1, 0, 8)

  # Phase 2 — Braking: rise above BW (eccentric)
  n2          <- round(t_braking * sample_rate)
  peak_brake  <- bw_N * 2.4
  f_p2        <- cosine_interp(n2, peak_unweight, peak_brake) + rnorm(n2, 0, 15)

  # Phase 3 — Propulsive: peak then drop to 0 at takeoff
  n3          <- round(t_propulsive * sample_rate)
  peak_prop   <- bw_N * 2.6
  half        <- round(n3 * 0.45)
  f_p3_up     <- cosine_interp(half, peak_brake, peak_prop)
  f_p3_down   <- cosine_interp(n3 - half, peak_prop, 0)
  f_p3        <- c(f_p3_up, f_p3_down) + rnorm(n3, 0, 12)
  f_p3        <- pmax(f_p3, 0)

  # Phase 4 — Flight: zero force
  n4   <- round(t_flight * sample_rate)
  f_p4 <- rep(0, n4)

  # Phase 5 — Landing: sharp spike then decay to BW
  n5          <- round(t_landing * sample_rate)
  peak_land   <- bw_N * 4.2
  f_p5_up     <- cosine_interp(round(n5 * 0.20), 0, peak_land)
  f_p5_down   <- cosine_interp(n5 - round(n5 * 0.20), peak_land, bw_N)
  f_p5        <- c(f_p5_up, f_p5_down) + rnorm(n5, 0, 20)
  f_p5        <- pmax(f_p5, 0)

  # ── Concatenate ─────────────────────────────────────────────────────────────
  force  <- c(f_p0, f_p1, f_p2, f_p3, f_p4, f_p5)
  n_total <- length(force)
  time   <- seq(0, by = dt, length.out = n_total)

  # Phase labels (0–5)
  phase  <- c(
    rep(0, n0),
    rep(1, n1),
    rep(2, n2),
    rep(3, n3),
    rep(4, n4),
    rep(5, n5)
  )

  # ── Kinematics via numerical integration ────────────────────────────────────
  mass         <- bodyweight_kg
  net_force    <- force - bw_N          # net force (subtract bodyweight)
  acceleration <- net_force / mass      # a = F_net / m  (m/s²)

  # Velocity: cumulative trapezoidal integration of acceleration
  velocity <- cumsum(acceleration) * dt

  # Displacement (height): cumulative integration of velocity
  height   <- cumsum(velocity) * dt

  # ── Assemble data frame ──────────────────────────────────────────────────────
  df <- data.frame(
    time         = time,
    force        = force,
    net_force    = net_force,
    acceleration = acceleration,
    velocity     = velocity,
    height       = height,
    phase        = phase
  )

  # Normalise time so takeoff = 0 (Hawkins convention)
  takeoff_idx   <- min(which(df$phase == 4))
  df$time_norm  <- df$time - df$time[takeoff_idx]

  return(df)
}

# ── Run and save ────────────────────────────────────────────────────────────────
if (!interactive()) {
  df <- simulate_cmj()
  write.csv(df, "cmj_data.csv", row.names = FALSE)
  message("cmj_data.csv written — ", nrow(df), " rows at 1000 Hz")
}
