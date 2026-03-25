# =============================================================================
# CMJ Analysis — Main Entry Point
#
# Usage:
#   Rscript cmj_analysis.R                        # uses simulated data
#   Rscript cmj_analysis.R my_force_data.csv      # uses real force plate CSV
#
# Expected CSV columns (real data):
#   time   — time in seconds
#   force  — vertical ground reaction force in Newtons
#
# All other columns (acceleration, velocity, height) are computed here.
# =============================================================================

source("cmj_simulate_data.R")
source("cmj_phases.R")
source("cmj_metrics.R")
source("cmj_plot.R")

# ── Load data ─────────────────────────────────────────────────────────────────
args <- commandArgs(trailingOnly = TRUE)

if (length(args) > 0 && file.exists(args[1])) {
  # ── Real force plate CSV ───────────────────────────────────────────────────
  message("Loading: ", args[1])
  raw       <- read.csv(args[1])

  stopifnot("time"  %in% names(raw),
            "force" %in% names(raw))

  sample_rate <- round(1 / mean(diff(raw$time)))
  mass        <- as.numeric(args[2])   # bodyweight in kg (2nd argument)
  if (is.na(mass)) stop("Provide bodyweight_kg as 2nd argument, e.g.: Rscript cmj_analysis.R data.csv 80")

  bw_N        <- mass * 9.81
  dt          <- 1 / sample_rate

  raw$net_force    <- raw$force - bw_N
  raw$acceleration <- raw$net_force / mass
  raw$velocity     <- cumsum(raw$acceleration) * dt
  raw$height       <- cumsum(raw$velocity) * dt
  raw$phase        <- 0L   # placeholder; detect_phases() will override

  df <- raw

} else {
  # ── Simulated data ─────────────────────────────────────────────────────────
  message("No CSV provided — using simulated CMJ data")
  df          <- simulate_cmj(bodyweight_kg = 80, sample_rate = 1000)
  sample_rate <- 1000
}

# ── Run analysis ──────────────────────────────────────────────────────────────
results <- compute_cmj_metrics(df, sample_rate = sample_rate)

# ── Print metrics table ───────────────────────────────────────────────────────
cat("\n")
cat(strrep("=", 55), "\n")
cat("  CMJ Report — Hawkins Dynamics R\n")
cat(strrep("=", 55), "\n\n")
print(results$metrics, row.names = FALSE)
cat("\n")

# ── Save metrics CSV ──────────────────────────────────────────────────────────
write.csv(results$metrics, "cmj_metrics_output.csv", row.names = FALSE)
message("Metrics saved: cmj_metrics_output.csv")

# ── Generate plot ─────────────────────────────────────────────────────────────
plot_cmj(results, output_file = "cmj_hawkins_plot.png")
