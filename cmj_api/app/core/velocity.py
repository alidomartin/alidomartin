import numpy as np
from scipy.integrate import cumulative_trapezoid


def compute_velocity(
    force: np.ndarray,
    time: np.ndarray,
    body_weight_n: float,
    mass_kg: float,
) -> np.ndarray:
    """COM velocity via impulse-momentum theorem: v(t) = integral((F - BW) / mass) dt"""
    net_force = force - body_weight_n
    return cumulative_trapezoid(net_force, time, initial=0.0) / mass_kg


def compute_displacement(velocity: np.ndarray, time: np.ndarray) -> np.ndarray:
    return cumulative_trapezoid(velocity, time, initial=0.0)
