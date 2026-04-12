# ─────────────────────────────────────────────────────────────────────────────
# n1_tsa_calc.R
# N1 Performance Lab
# Total Score of Athleticism (TSA)
#
# Method:  Z = (x - mean) / sd  per metric
#          TSA = Z(Relative Peak Power) + Z(RSImod) + Z(Vertical Jump Height)
#
# Labels:  01_Identity/GLOSSARY.md
# Guide:   02_Reference/TSA+REPORT+GUIDE+(2).pdf
# Output:  03_Data_Lab/tsa_table.png
# ─────────────────────────────────────────────────────────────────────────────

library(ggplot2)
library(dplyr)

dir.create("03_Data_Lab", showWarnings = FALSE, recursive = TRUE)

# ── Japanese Editorial Palette ────────────────────────────────────────────────
BG     <- "#2C3E50"   # Slate background
ACCENT <- "#77DD77"   # Warm Eucalyptus
WHITE  <- "#FFFFFF"
DIM    <- "#8FA3B1"
HEADER <- "#1E2D3D"
STRIPE <- "#253545"
RULE   <- "#3D5568"

# ── Athlete Data ──────────────────────────────────────────────────────────────
# Columns per 01_Identity/GLOSSARY.md:
#   Relative Peak Power (W/kg) | RSImod (m/s) | Vertical Jump Height (m)
# Positions: full names only
athletes <- data.frame(
  Athlete          = c(
    "A. Torres", "M. Reyes", "K. Nakamura", "S. Okafor",
    "P. Andersen", "L. Ferreira", "H. Johansson", "C. Williams",
    "D. Osei", "R. Mateus"
  ),
  Position         = c(
    "Middle Blocker", "Outside Hitter", "Setter", "Middle Blocker",
    "Libero", "Outside Hitter", "Opposite Hitter", "Setter",
    "Libero", "Opposite Hitter"
  ),
  Rel_Peak_Power   = c(52.3, 48.7, 41.2, 55.1, 38.6, 50.2, 46.8, 39.4, 36.1, 49.5),
  RSImod           = c(0.62, 0.55, 0.44, 0.68, 0.39, 0.58, 0.52, 0.41, 0.37, 0.57),
  Vert_Jump_Height = c(0.48, 0.43, 0.35, 0.51, 0.31, 0.46, 0.41, 0.34, 0.29, 0.44),
  stringsAsFactors = FALSE
)

# ── Z-score Normalization + TSA Calculation ───────────────────────────────────
z <- function(x) (x - mean(x)) / sd(x)

tsa <- athletes |>
  mutate(
    z_RPP = z(Rel_Peak_Power),
    z_RSI = z(RSImod),
    z_JH  = z(Vert_Jump_Height),
    TSA   = z_RPP + z_RSI + z_JH
  ) |>
  arrange(desc(TSA)) |>
  mutate(Rank = row_number())

# ── Table Layout Parameters ───────────────────────────────────────────────────
COL_LABELS <- c(
  "RANK", "ATHLETE", "POSITION",
  "REL PEAK POWER\n(W/kg)", "RSImod\n(m/s)",
  "VERT JUMP HEIGHT\n(m)", "TSA"
)
COL_X     <- c(0.03, 0.09, 0.28, 0.54, 0.65, 0.76, 0.90)
COL_HJUST <- c(0.5,  0,    0,    0.5,  0.5,  0.5,  0.5)
DIVIDERS  <- c(0.06, 0.25, 0.51, 0.62, 0.73, 0.86)

N  <- nrow(tsa)
NC <- length(COL_LABELS)

row_y    <- function(i) N - i + 0.5
HEADER_Y <- N + 0.5

# ── Assemble Cell Dataframe ───────────────────────────────────────────────────
is_tsa <- c(FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, TRUE)

header_cells <- data.frame(
  x     = COL_X,
  y     = HEADER_Y,
  label = COL_LABELS,
  color = ACCENT,
  size  = 3.0,
  hjust = COL_HJUST,
  face  = "bold",
  stringsAsFactors = FALSE
)

data_cells <- do.call(rbind, lapply(seq_len(N), function(i) {
  vals <- c(
    as.character(tsa$Rank[i]),
    tsa$Athlete[i],
    tsa$Position[i],
    sprintf("%.1f",  tsa$Rel_Peak_Power[i]),
    sprintf("%.2f",  tsa$RSImod[i]),
    sprintf("%.2f",  tsa$Vert_Jump_Height[i]),
    sprintf("%+.2f", tsa$TSA[i])
  )
  data.frame(
    x     = COL_X,
    y     = row_y(i),
    label = vals,
    color = ifelse(is_tsa, ACCENT, WHITE),
    size  = ifelse(is_tsa, 3.4, 3.0),
    hjust = COL_HJUST,
    face  = ifelse(is_tsa, "bold", "plain"),
    stringsAsFactors = FALSE
  )
}))

cells       <- rbind(header_cells, data_cells)
cells_plain <- cells[cells$face == "plain", ]
cells_bold  <- cells[cells$face == "bold",  ]

# ── Row Stripes ───────────────────────────────────────────────────────────────
stripes <- data.frame(
  ymin = N - seq_len(N),
  ymax = N - seq_len(N) + 1,
  fill = ifelse(seq_len(N) %% 2 == 0, STRIPE, BG)
)

# ── Build Plot ────────────────────────────────────────────────────────────────
YMIN <- -0.3
YMAX <- N + 2.8

p <- ggplot() +

  # Base background
  geom_rect(
    aes(xmin = 0, xmax = 1, ymin = YMIN, ymax = YMAX),
    fill = BG, color = NA
  ) +

  # Alternating row stripes
  geom_rect(
    data = stripes,
    aes(xmin = 0, xmax = 1, ymin = ymin, ymax = ymax, fill = fill),
    color = NA
  ) +
  scale_fill_identity() +

  # Header band
  geom_rect(
    aes(xmin = 0, xmax = 1, ymin = N, ymax = N + 1),
    fill = HEADER, color = NA
  ) +

  # Accent bar on header left edge
  geom_rect(
    aes(xmin = 0, xmax = 0.005, ymin = N, ymax = N + 1),
    fill = ACCENT, color = NA
  ) +

  # Title
  geom_text(
    aes(x = 0.02, y = N + 2.1, label = "TOTAL SCORE OF ATHLETICISM"),
    color = ACCENT, size = 5.5, fontface = "bold", hjust = 0
  ) +

  # Formula subtitle
  geom_text(
    aes(
      x = 0.02, y = N + 1.65,
      label = "Z(Relative Peak Power)  +  Z(RSImod)  +  Z(Vertical Jump Height)"
    ),
    color = DIM, size = 2.7, hjust = 0
  ) +

  # Lab label
  geom_text(
    aes(x = 0.98, y = N + 2.1, label = "N1 PERFORMANCE LAB"),
    color = DIM, size = 2.8, fontface = "bold", hjust = 1
  ) +

  # Horizontal rules
  geom_segment(
    aes(x = 0, xend = 1, y = N + 1, yend = N + 1),
    color = RULE, linewidth = 0.3
  ) +
  geom_segment(
    aes(x = 0, xend = 1, y = 0, yend = 0),
    color = ACCENT, linewidth = 0.6
  ) +

  # Vertical column dividers
  geom_segment(
    data = data.frame(x = DIVIDERS, xend = DIVIDERS),
    aes(x = x, xend = xend, y = 0, yend = N + 1),
    color = RULE, linewidth = 0.2
  ) +

  # Plain cell text
  geom_text(
    data = cells_plain,
    aes(x = x, y = y, label = label, color = color, size = size, hjust = hjust),
    vjust = 0.5, lineheight = 0.85, fontface = "plain"
  ) +

  # Bold cell text (header + TSA column)
  geom_text(
    data = cells_bold,
    aes(x = x, y = y, label = label, color = color, size = size, hjust = hjust),
    vjust = 0.5, lineheight = 0.85, fontface = "bold"
  ) +

  scale_color_identity() +
  scale_size_identity() +

  coord_cartesian(
    xlim = c(0, 1),
    ylim = c(YMIN, YMAX),
    clip = "off"
  ) +

  theme_void() +
  theme(
    plot.background  = element_rect(fill = BG, color = NA),
    panel.background = element_rect(fill = BG, color = NA),
    plot.margin      = margin(20, 25, 20, 25)
  )

# ── Save ──────────────────────────────────────────────────────────────────────
ggsave(
  filename = "03_Data_Lab/tsa_table.png",
  plot     = p,
  width    = 14,
  height   = 9,
  dpi      = 200,
  bg       = BG
)

cat("Saved: 03_Data_Lab/tsa_table.png\n\n")
print(tsa[, c("Rank", "Athlete", "Position", "Rel_Peak_Power", "RSImod", "Vert_Jump_Height", "TSA")])
