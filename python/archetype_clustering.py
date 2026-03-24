"""P3-style athlete archetype clustering using KMeans + PCA."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from scipy.spatial import ConvexHull

ARCHETYPE_LABELS = [
    "Specimens",
    "Hyper-Athletic\nGuards",
    "Kinematic\nMovers",
    "Force Movers",
    "Traditional\nBigs",
    "Bigs Plus",
    "Misc\nPerimeter",
]

ARCHETYPE_COLORS = [
    "#f0c040",
    "#e05050",
    "#50c878",
    "#5090e0",
    "#c080e0",
    "#e08030",
    "#80c0c0",
]

FEATURES = [
    "l_lateral_force", "r_lateral_force",
    "l_hip_abduction", "r_hip_abduction",
    "l_hip_ext_velocity", "r_hip_ext_velocity",
    "height_inches", "wingspan_inches",
    "vertical_jump", "weight_lbs",
]


def draw_convex_hull(ax, points, color):
    if len(points) < 3:
        ax.scatter(points[:, 0], points[:, 1], s=60, color=color, zorder=3)
        return
    hull = ConvexHull(points)
    ax.fill(points[hull.vertices, 0], points[hull.vertices, 1],
            color=color, alpha=0.15)
    verts = np.append(hull.vertices, hull.vertices[0])
    ax.plot(points[verts, 0], points[verts, 1],
            color=color, linewidth=1.5, alpha=0.7)


def plot_archetypes(data_path: str = "../data/sample_athletes.csv",
                    highlight_athlete: str = None,
                    n_clusters: int = 7) -> None:
    df = pd.read_csv(data_path)
    X = StandardScaler().fit_transform(df[FEATURES])

    k = min(n_clusters, len(df))
    df = df.copy()
    df["cluster"] = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X)

    coords = PCA(n_components=2).fit_transform(X)
    df["pca1"], df["pca2"] = coords[:, 0], coords[:, 1]

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("#0d0d0d")
    ax.set_facecolor("#0d0d0d")
    ax.grid(color="#222222", linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")

    for cid in range(k):
        mask = df["cluster"] == cid
        pts = df.loc[mask, ["pca1", "pca2"]].values
        color = ARCHETYPE_COLORS[cid % len(ARCHETYPE_COLORS)]
        label = ARCHETYPE_LABELS[cid % len(ARCHETYPE_LABELS)]
        draw_convex_hull(ax, pts, color)
        ax.scatter(pts[:, 0], pts[:, 1], s=40, color=color, zorder=4, alpha=0.9)
        cx, cy = pts[:, 0].mean(), pts[:, 1].mean()
        ax.text(cx, cy, label, color=color, fontsize=7.5, ha="center", va="center",
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="#0d0d0d", ec="none", alpha=0.7))

    if highlight_athlete:
        row = df[df["athlete"] == highlight_athlete]
        if not row.empty:
            ax.scatter(row["pca1"], row["pca2"], s=120, color="white",
                       zorder=6, edgecolors="white", linewidths=1.5)
            ax.annotate(highlight_athlete,
                        xy=(row["pca1"].values[0], row["pca2"].values[0]),
                        xytext=(10, 10), textcoords="offset points",
                        color="white", fontsize=9, fontweight="bold")

    fig.text(0.5, 0.97, "ARCHETYPE ANALYSIS", ha="center", va="top",
             color="white", fontsize=13, fontweight="bold")
    fig.text(0.5, 0.93,
             "Athletes grouped via KMeans on anthropometric, performance, and mechanical variables.",
             ha="center", va="top", color="#888888", fontsize=8)
    ax.set_xlabel("PC1", color="#555555", fontsize=9)
    ax.set_ylabel("PC2", color="#555555", fontsize=9)
    ax.tick_params(colors="#555555")

    plt.tight_layout()
    plt.savefig("archetype_clustering.png", dpi=150,
                bbox_inches="tight", facecolor=fig.get_facecolor())
    print("Saved archetype_clustering.png")
    plt.close()


if __name__ == "__main__":
    plot_archetypes(highlight_athlete="Scottie Barnes")
