# P3-style Lateral Performance Indicators radar chart
# install.packages("fmsb")
library(fmsb)

plot_radar <- function(athlete_name, data_path = "../data/sample_athletes.csv") {
  df  <- read.csv(data_path)
  row <- df[df$athlete == athlete_name, ]
  if (nrow(row) == 0) stop(paste("Athlete not found:", athlete_name))

  metrics <- data.frame(
    `L - Lateral Force`    = row$l_lateral_force,
    `R - Hip Abduction`    = row$r_hip_abduction,
    `R - Hip Ext Velocity` = row$r_hip_ext_velocity,
    `R - Lateral Force`    = row$r_lateral_force,
    `L - Hip Ext Velocity` = row$l_hip_ext_velocity,
    `L - Hip Abduction`    = row$l_hip_abduction,
    check.names = FALSE
  )

  # fmsb requires max/min rows prepended
  plot_data <- rbind(rep(100, 6), rep(0, 6), metrics)

  out_file <- paste0("radar_", gsub(" ", "_", athlete_name), ".png")
  png(out_file, width = 700, height = 700, bg = "#0d0d0d")
  par(bg = "#0d0d0d", mar = c(2, 2, 4, 2))

  radarchart(
    plot_data,
    axistype   = 1,
    pcol       = "#4da6ff",
    pfcol      = adjustcolor("#4da6ff", alpha.f = 0.15),
    plwd       = 2.5,
    cglcol     = "#333333",
    cglty      = 1,
    cglwd      = 0.8,
    axislabcol = "#555555",
    vlcex      = 0.85,
    calcex     = 0.7
  )

  title(main = "LATERAL SKATER", col.main = "white", cex.main = 1.4, font.main = 2)
  mtext("Percentile", col = "#aaaaaa", cex = 0.9)
  dev.off()
  message("Saved ", out_file)
}

plot_radar("Scottie Barnes")
