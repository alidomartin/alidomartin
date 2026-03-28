# =============================================================================
# P1 / P2 Quadrant Analysis — Hawkins Dynamics
#
# Uses YOUR team data as benchmarks (not external norms).
# Athlete displayed as "Anonymous".
#
# Run after: get_access() and get_tests() have populated `allTests`
# =============================================================================

library(dplyr)
library(ggplot2)
library(ggrepel)

# ── 1. Build team CMJ dataset ─────────────────────────────────────────────────
team_CMJ <- allTests %>%
  filter(grepl("Countermovement Jump", testType_name, ignore.case = TRUE)) %>%
  mutate(
    total_impulse = coalesce(cmj_propulsive_impulse_n_s,   propulsive_impulse_n_s),
    p1            = coalesce(cmj_p1_propulsive_impulse_n_s, p1_propulsive_impulse_n_s),
    p2            = coalesce(cmj_p2_propulsive_impulse_n_s, p2_propulsive_impulse_n_s)
  ) %>%
  filter(!is.na(p1), !is.na(p2), !is.na(total_impulse))

# ── Team median thresholds ─────────────────────────────────────────────────────
team_p1_med <- median(team_CMJ$p1, na.rm = TRUE)
team_p2_med <- median(team_CMJ$p2, na.rm = TRUE)

cat(sprintf("Team P1 median: %.1f N.s\n", team_p1_med))
cat(sprintf("Team P2 median: %.1f N.s\n", team_p2_med))

# ── 2. Jade's data ────────────────────────────────────────────────────────────
CMJ <- allTests %>%
  filter(grepl("Countermovement Jump", testType_name, ignore.case = TRUE)) %>%
  filter(grepl("jade disquitado", athlete_name, ignore.case = TRUE)) %>%
  mutate(
    date         = as.Date(as.POSIXct(timestamp, origin = "1970-01-01")),
    athlete      = "Anonymous",
    total_impulse = coalesce(cmj_propulsive_impulse_n_s,   propulsive_impulse_n_s),
    p1           = coalesce(cmj_p1_propulsive_impulse_n_s, p1_propulsive_impulse_n_s),
    p2           = coalesce(cmj_p2_propulsive_impulse_n_s, p2_propulsive_impulse_n_s),
    p1_p2_ratio  = coalesce(cmj_p1_p2_propulsive_impulse_index, p1_p2_propulsive_impulse_index)
  ) %>%
  filter(!is.na(p1), !is.na(p2)) %>%
  arrange(date)

# ── 3. Classify trials into quadrants ─────────────────────────────────────────
CMJ <- CMJ %>%
  mutate(
    quadrant = case_when(
      p1 >= team_p1_med & p2 >= team_p2_med ~ "Balanced\n(High P1 + High P2)",
      p1 >= team_p1_med & p2 <  team_p2_med ~ "Low P2\n(High P1)",
      p1 <  team_p1_med & p2 >= team_p2_med ~ "Low P1\n(High P2)",
      TRUE                                   ~ "Low Bilateral\n(Low P1 + Low P2)"
    ),
    quadrant = factor(quadrant, levels = c(
      "Balanced\n(High P1 + High P2)",
      "Low P2\n(High P1)",
      "Low P1\n(High P2)",
      "Low Bilateral\n(Low P1 + Low P2)"
    )),
    session_label = format(date, "%d %b"),
    trial_num     = row_number()
  )

# ── 4. Most recent trial label ─────────────────────────────────────────────────
latest <- CMJ %>% slice_tail(n = 1)

# ── 5. Colour palette per quadrant ────────────────────────────────────────────
quad_cols <- c(
  "Balanced\n(High P1 + High P2)"      = "#2ecc71",   # green
  "Low P2\n(High P1)"                  = "#e67e22",   # orange
  "Low P1\n(High P2)"                  = "#3498db",   # blue
  "Low Bilateral\n(Low P1 + Low P2)"   = "#e74c3c"    # red
)

# ── 6. Axis limits ─────────────────────────────────────────────────────────────
x_range <- range(c(team_CMJ$p1, CMJ$p1), na.rm = TRUE)
y_range <- range(c(team_CMJ$p2, CMJ$p2), na.rm = TRUE)

x_pad   <- diff(x_range) * 0.10
y_pad   <- diff(y_range) * 0.10
xlims   <- c(x_range[1] - x_pad, x_range[2] + x_pad)
ylims   <- c(y_range[1] - y_pad, y_range[2] + y_pad)

# ── 7. Build plot ─────────────────────────────────────────────────────────────
p_quad <- ggplot() +

  # Quadrant background shading
  annotate("rect",
           xmin = team_p1_med, xmax = xlims[2],
           ymin = team_p2_med, ymax = ylims[2],
           fill = "#2ecc71", alpha = 0.06) +
  annotate("rect",
           xmin = team_p1_med, xmax = xlims[2],
           ymin = ylims[1],   ymax = team_p2_med,
           fill = "#e67e22", alpha = 0.06) +
  annotate("rect",
           xmin = xlims[1],   xmax = team_p1_med,
           ymin = team_p2_med, ymax = ylims[2],
           fill = "#3498db", alpha = 0.06) +
  annotate("rect",
           xmin = xlims[1],   xmax = team_p1_med,
           ymin = ylims[1],   ymax = team_p2_med,
           fill = "#e74c3c", alpha = 0.06) +

  # Median reference lines
  geom_vline(xintercept = team_p1_med,
             linetype = "dashed", colour = "grey50", linewidth = 0.5) +
  geom_hline(yintercept = team_p2_med,
             linetype = "dashed", colour = "grey50", linewidth = 0.5) +

  # Quadrant labels (corner text)
  annotate("text",
           x = xlims[2] - x_pad * 0.4,
           y = ylims[2] - y_pad * 0.4,
           label = "BALANCED\nHigh P1 + High P2",
           hjust = 1, vjust = 1, size = 3.2, colour = "#27ae60",
           fontface = "bold", lineheight = 0.85) +
  annotate("text",
           x = xlims[2] - x_pad * 0.4,
           y = ylims[1] + y_pad * 0.4,
           label = "LOW P2\nHigh P1",
           hjust = 1, vjust = 0, size = 3.2, colour = "#d35400",
           fontface = "bold", lineheight = 0.85) +
  annotate("text",
           x = xlims[1] + x_pad * 0.4,
           y = ylims[2] - y_pad * 0.4,
           label = "LOW P1\nHigh P2",
           hjust = 0, vjust = 1, size = 3.2, colour = "#2980b9",
           fontface = "bold", lineheight = 0.85) +
  annotate("text",
           x = xlims[1] + x_pad * 0.4,
           y = ylims[1] + y_pad * 0.4,
           label = "LOW BILATERAL\nLow P1 + Low P2",
           hjust = 0, vjust = 0, size = 3.2, colour = "#c0392b",
           fontface = "bold", lineheight = 0.85) +

  # Team cloud (all athletes, faded)
  geom_point(data = team_CMJ,
             aes(x = p1, y = p2),
             colour = "grey70", size = 1.2, alpha = 0.30) +

  # Athlete trial path (connecting line, chronological)
  geom_path(data = CMJ,
            aes(x = p1, y = p2),
            colour = "grey30", linewidth = 0.5, alpha = 0.6,
            arrow = arrow(length = unit(0.12, "cm"), ends = "last",
                          type = "open")) +

  # Trial points coloured by quadrant
  geom_point(data = CMJ,
             aes(x = p1, y = p2, fill = quadrant),
             shape = 21, size = 4, colour = "white", stroke = 0.8) +
  scale_fill_manual(values = quad_cols, name = "Quadrant") +

  # Date labels (repelled)
  geom_label_repel(data = CMJ,
                   aes(x = p1, y = p2, label = session_label,
                       colour = quadrant),
                   size = 2.8, fontface = "bold",
                   box.padding   = 0.35,
                   point.padding = 0.3,
                   segment.size  = 0.3,
                   segment.colour = "grey50",
                   fill = "white",
                   label.size = NA,
                   show.legend = FALSE,
                   max.overlaps = 20) +
  scale_colour_manual(values = quad_cols, guide = "none") +

  # Highlight latest trial
  geom_point(data = latest,
             aes(x = p1, y = p2),
             shape = 21, size = 6.5,
             fill = NA, colour = "black", stroke = 1.4) +

  # Axis settings
  scale_x_continuous(
    name   = "P1 Propulsive Impulse (N.s)  [Early Phase]",
    limits = xlims,
    expand = expansion(0)
  ) +
  scale_y_continuous(
    name   = "P2 Propulsive Impulse (N.s)  [Late Phase]",
    limits = ylims,
    expand = expansion(0)
  ) +

  # Title / caption
  labs(
    title    = "P1 | P2 Propulsive Impulse Quadrant",
    subtitle = sprintf(
      "Anonymous  |  %d trials  |  Team benchmarks: P1 median = %.1f N.s, P2 median = %.1f N.s",
      nrow(CMJ), team_p1_med, team_p2_med
    ),
    caption  = "Quadrant method: Pentheny (2025) via Hawkins Dynamics\nCircle = most recent trial"
  ) +

  theme_minimal(base_size = 12) +
  theme(
    plot.background    = element_rect(fill = "#0f0f0f", colour = NA),
    panel.background   = element_rect(fill = "#0f0f0f", colour = NA),
    panel.grid.major   = element_line(colour = "#2a2a2a", linewidth = 0.3),
    panel.grid.minor   = element_blank(),
    axis.title         = element_text(colour = "grey70", size = 10),
    axis.text          = element_text(colour = "grey55", size = 9),
    plot.title         = element_text(colour = "white", face = "bold",
                                       size = 16, hjust = 0.5),
    plot.subtitle      = element_text(colour = "grey60", size = 9,
                                       hjust = 0.5),
    plot.caption       = element_text(colour = "grey45", size = 7.5,
                                       hjust = 0.5),
    legend.background  = element_rect(fill = "#1a1a1a", colour = NA),
    legend.text        = element_text(colour = "grey70", size = 8),
    legend.title       = element_text(colour = "grey80", size = 9,
                                       face = "bold"),
    legend.key         = element_rect(fill = NA),
    plot.margin        = margin(20, 20, 20, 20)
  )

# ── 8. Save ───────────────────────────────────────────────────────────────────
ggsave("anonymous_p1p2_quadrant.png",
       plot   = p_quad,
       width  = 10,
       height = 10,
       dpi    = 300,
       bg     = "#0f0f0f")

message("Saved: anonymous_p1p2_quadrant.png")

# ── 9. Print classification table ─────────────────────────────────────────────
cat("\n=== Trial Classification ===\n\n")
CMJ %>%
  select(date, session_label, p1, p2, p1_p2_ratio, quadrant) %>%
  mutate(
    p1          = round(p1, 1),
    p2          = round(p2, 1),
    p1_p2_ratio = round(p1_p2_ratio, 3),
    quadrant    = gsub("\n", " ", quadrant)
  ) %>%
  print(n = Inf)
