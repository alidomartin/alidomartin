"""P3-style Lateral Performance Indicators radar chart."""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from math import pi


def plot_radar(athlete_row: pd.Series, title: str = "LATERAL SKATER") -> None:
    categories = [
        "L - Lateral Force",
        "R - Hip\nAbduction",
        "R - Hip Ext\nVelocity",
        "R - Lateral Force",
        "L - Hip Ext\nVelocity",
        "L - Hip\nAbduction",
    ]
    values = [
        athlete_row["l_lateral_force"],
        athlete_row["r_hip_abduction"],
        athlete_row["r_hip_ext_velocity"],
        athlete_row["r_lateral_force"],
        athlete_row["l_hip_ext_velocity"],
        athlete_row["l_hip_abduction"],
    ]

    N = len(categories)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    values_plot = values + values[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#0d0d0d")
    ax.set_facecolor("#0d0d0d")

    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels([])
    ax.yaxis.grid(color="#333333", linewidth=0.8)
    ax.xaxis.grid(color="#333333", linewidth=0.8)

    ax.plot(angles, values_plot, color="#4da6ff", linewidth=2.5)
    ax.fill(angles, values_plot, color="#4da6ff", alpha=0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, color="white", fontsize=10, fontweight="bold")
    ax.tick_params(axis="x", pad=18)

    fig.text(0.5, 0.97, title, ha="center", va="top",
             color="white", fontsize=14, fontweight="bold")
    fig.text(0.5, 0.93, "Percentile", ha="center", va="top",
             color="#aaaaaa", fontsize=10)

    plt.tight_layout()
    out = f"radar_{athlete_row['athlete'].replace(' ', '_')}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved {out}")
    plt.close()


if __name__ == "__main__":
    df = pd.read_csv("../data/sample_athletes.csv")
    plot_radar(df.iloc[0])
    # To plot all athletes:
    # for _, row in df.iterrows():
    #     plot_radar(row)
