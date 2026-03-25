# =============================================================================
# CMJ Hawkins-Style Multi-Panel Plot
#
# Reproduces the 4-panel layout from the image:
#   Row 1 — Force (N)
#   Row 2 — Acceleration (m/s²)
#   Row 3 — Velocity (m/s)
#   Row 4 — Height (m)
#
# Phase bands (colour-coded):
#   0 Weighing    = #a8d8a8  (green)
#   1 Unweighting = #a8c4e0  (blue)
#   2 Braking     = #b8a8d8  (purple)
#   3 Propulsive  = #f5c97a  (orange)
#   4 Flight      = #e8e8e8  (light grey)
#   5 Landing     = #f5a8a8  (pink/red)
# =============================================================================

source("cmj_metrics.R")

# ── ggplot2 required ──────────────────────────────────────────────────────────
if (!requireNamespace("ggplot2",  quietly = TRUE)) install.packages("ggplot2")
if (!requireNamespace("patchwork",quietly = TRUE)) install.packages("patchwork")
if (!requireNamespace("dplyr",    quietly = TRUE)) install.packages("dplyr")

library(ggplot2)
library(patchwork)
library(dplyr)

# ── Phase colour palette (mirrors Hawkins R) ──────────────────────────────────
phase_colours <- c(
  "0" = "#a8d8a8",   # green   — Weighing
  "1" = "#a8c4e0",   # blue    — Unweighting
  "2" = "#b8a8d8",   # purple  — Braking
  "3" = "#f5c97a",   # orange  — Propulsive
  "4" = "#e8e8e8",   # grey    — Flight
  "5" = "#f5a8a8"    # pink    — Landing
)

phase_labels <- c(
  "0" = "Weighing",
  "1" = "Unweighting",
  "2" = "Braking",
  "3" = "Propulsive",
  "4" = "Flight",
  "5" = "Landing"
)

# ── Build phase background rectangles ────────────────────────────────────────
phase_rects <- function(df) {
  df %>%
    mutate(phase_f = as.character(phase_detected)) %>%
    group_by(phase_f) %>%
    summarise(xmin = min(time_norm), xmax = max(time_norm), .groups = "drop")
}

# ── Common theme (clean, Hawkins-like) ────────────────────────────────────────
theme_hawkins <- function() {
  theme_minimal(base_size = 11) +
    theme(
      panel.grid.minor  = element_blank(),
      panel.grid.major  = element_line(colour = "grey90", linewidth = 0.3),
      axis.title.y      = element_text(angle = 90, size = 9, colour = "grey30"),
      axis.title.x      = element_text(size = 9, colour = "grey30"),
      axis.text         = element_text(size = 8, colour = "grey40"),
      plot.background   = element_rect(fill = "white", colour = NA),
      panel.background  = element_rect(fill = "white", colour = NA),
      legend.position   = "none"
    )
}

# ── Single panel builder ──────────────────────────────────────────────────────
make_panel <- function(df, rects, y_var, y_lab,
                       bw_line = NULL, show_x = FALSE) {
  p <- ggplot(df, aes(x = time_norm))

  # phase background bands
  for (i in seq_len(nrow(rects))) {
    r <- rects[i, ]
    p <- p + annotate("rect",
                      xmin = r$xmin, xmax = r$xmax,
                      ymin = -Inf,   ymax = Inf,
                      fill = phase_colours[r$phase_f],
                      alpha = 0.55)
  }

  # horizontal reference line (bodyweight or zero)
  if (!is.null(bw_line)) {
    p <- p + geom_hline(yintercept = bw_line,
                        linetype = "dashed",
                        colour = "black", linewidth = 0.5)
  }

  p <- p +
    geom_line(aes(y = .data[[y_var]]),
              colour = "black", linewidth = 0.55) +
    labs(y = y_lab,
         x = if (show_x) "Time (s)" else NULL) +
    theme_hawkins()

  if (!show_x) {
    p <- p + theme(axis.text.x = element_blank(),
                   axis.ticks.x = element_blank())
  }

  p
}

# ── Legend strip ─────────────────────────────────────────────────────────────
legend_panel <- function() {
  leg_df <- data.frame(
    phase = factor(names(phase_labels), levels = names(phase_labels)),
    label = unname(phase_labels),
    x     = seq_along(phase_labels)
  )

  ggplot(leg_df, aes(x = x, y = 1, fill = phase)) +
    geom_tile(height = 0.8) +
    geom_text(aes(label = label), size = 3, fontface = "bold", colour = "grey20") +
    scale_fill_manual(values = phase_colours) +
    theme_void() +
    theme(legend.position = "none",
          plot.background = element_rect(fill = "white", colour = NA))
}

# ── Main plotting function ────────────────────────────────────────────────────
plot_cmj <- function(results, output_file = "cmj_hawkins_plot.png") {
  df     <- results$df
  bw_N   <- results$bw_N

  rects  <- phase_rects(df)

  p_force <- make_panel(df, rects, "force",        "Force (N)",       bw_line = bw_N)
  p_accel <- make_panel(df, rects, "acceleration",  "Acceleration\n(m/s²)", bw_line = 0)
  p_vel   <- make_panel(df, rects, "velocity",      "Velocity (m/s)",  bw_line = 0)
  p_hgt   <- make_panel(df, rects, "height",        "Height (m)",      bw_line = 0,
                         show_x = TRUE)

  # Metrics table panel
  met      <- results$metrics
  met_top  <- met[c(2, 6, 9, 15, 17, 18, 19), ]   # curated subset
  tbl_text <- paste0(met_top$metric, ":  ", met_top$value, collapse = "\n")

  p_tbl <- ggplot() +
    annotate("text", x = 0.05, y = 0.95,
             label    = tbl_text,
             hjust    = 0, vjust = 1,
             size     = 3.0,
             family   = "mono",
             colour   = "grey20") +
    labs(title = "CMJ — Hawkins Dynamics R Analysis") +
    theme_void() +
    theme(
      plot.title      = element_text(size = 13, face = "bold",
                                     colour = "grey15", hjust = 0.5),
      plot.background = element_rect(fill = "white", colour = NA)
    ) +
    xlim(0, 1) + ylim(0, 1)

  # Compose layout: title+metrics | 4 signal panels
  layout <- (p_tbl / legend_panel()) |
    (p_force / p_accel / p_vel / p_hgt)

  final <- layout +
    plot_layout(widths = c(1, 2.2)) &
    theme(plot.background = element_rect(fill = "white", colour = NA))

  ggsave(output_file, plot = final,
         width = 14, height = 9, dpi = 150, bg = "white")

  message("Plot saved: ", output_file)
  invisible(final)
}

# ── Run standalone ────────────────────────────────────────────────────────────
if (!interactive()) {
  df      <- simulate_cmj()
  results <- compute_cmj_metrics(df)
  plot_cmj(results)
}
