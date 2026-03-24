# P3-style athlete archetype clustering
# install.packages(c("ggplot2", "dplyr"))
library(ggplot2)
library(dplyr)

ARCHETYPE_LABELS <- c(
  "Specimens", "Hyper-Athletic Guards", "Kinematic Movers",
  "Force Movers", "Traditional Bigs", "Bigs Plus", "Misc Perimeter"
)
ARCHETYPE_COLORS <- c(
  "#f0c040", "#e05050", "#50c878",
  "#5090e0", "#c080e0", "#e08030", "#80c0c0"
)

plot_archetypes <- function(data_path  = "../data/sample_athletes.csv",
                             highlight  = "Scottie Barnes",
                             n_clusters = 7) {
  df <- read.csv(data_path)

  features <- c(
    "l_lateral_force", "r_lateral_force",
    "l_hip_abduction", "r_hip_abduction",
    "l_hip_ext_velocity", "r_hip_ext_velocity",
    "height_inches", "wingspan_inches",
    "vertical_jump", "weight_lbs"
  )

  X   <- scale(df[, features])
  k   <- min(n_clusters, nrow(df))
  set.seed(42)
  km  <- kmeans(X, centers = k, nstart = 10)
  df$cluster <- factor(km$cluster)

  pca     <- prcomp(X)
  df$pca1 <- pca$x[, 1]
  df$pca2 <- pca$x[, 2]

  centroids <- df %>%
    group_by(cluster) %>%
    summarise(pca1 = mean(pca1), pca2 = mean(pca2), .groups = "drop") %>%
    mutate(label = ARCHETYPE_LABELS[as.integer(cluster)])

  color_map <- setNames(ARCHETYPE_COLORS[seq_len(k)], levels(df$cluster))

  p <- ggplot(df, aes(x = pca1, y = pca2, color = cluster, fill = cluster)) +
    stat_ellipse(geom = "polygon", alpha = 0.12, level = 0.85, linewidth = 1) +
    geom_point(size = 2.5, alpha = 0.9) +
    geom_text(data = centroids, aes(label = label),
              color = "white", size = 3, fontface = "bold", inherit.aes = FALSE) +
    scale_color_manual(values = color_map) +
    scale_fill_manual(values  = color_map) +
    labs(
      title    = "ARCHETYPE ANALYSIS",
      subtitle = "Athletes grouped via KMeans on anthropometric, performance, and mechanical variables.",
      x = "PC1", y = "PC2"
    ) +
    theme_void() +
    theme(
      plot.background  = element_rect(fill = "#0d0d0d", color = NA),
      panel.background = element_rect(fill = "#0d0d0d", color = NA),
      panel.grid.major = element_line(color = "#222222", linewidth = 0.4),
      plot.title       = element_text(color = "white",   hjust = 0.5, size = 14, face = "bold"),
      plot.subtitle    = element_text(color = "#888888", hjust = 0.5, size = 8),
      axis.title       = element_text(color = "#555555", size = 9),
      legend.position  = "none"
    )

  if (!is.null(highlight) && highlight %in% df$athlete) {
    hl <- df[df$athlete == highlight, ]
    p  <- p +
      geom_point(data = hl, aes(x = pca1, y = pca2),
                 color = "white", size = 5, shape = 21,
                 fill = NA, stroke = 1.8, inherit.aes = FALSE) +
      geom_text(data = hl, aes(x = pca1, y = pca2, label = athlete),
                color = "white", size = 3.5, fontface = "bold",
                nudge_x = 0.15, nudge_y = 0.1, inherit.aes = FALSE)
  }

  ggsave("archetype_clustering.png", p, width = 10, height = 7,
         dpi = 150, bg = "#0d0d0d")
  message("Saved archetype_clustering.png")
}

plot_archetypes()
