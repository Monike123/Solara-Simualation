"""
nbody.py

Implements Newtonian gravity and the main integrator.

- Computes gravitational accelerations between all massive bodies
- Updates their velocities and positions using velocity-Verlet
- Optionally adds 1PN (relativistic) corrections if enabled

This file is the *engine* that advances the system forward in time.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from constants import G, DT, EPS_ACCEL, ENABLE_1PN_DEFAULT
from .pn1 import compute_pn_accelerations   # will be used for relativity

__all__ = ["compute_accelerations", "step_system"]

# ---------------------------
# Newtonian pairwise accelerations
# ---------------------------
def compute_accelerations(bodies):
    """
    Compute Newtonian gravitational accelerations on all bodies.

    Parameters
    ----------
    bodies : list of Body
        Each Body must have attributes:
          - mass (float)
          - pos (np.array, shape (3,))
          - acc (np.array, shape (3,))  (will be overwritten)

    Notes
    -----
    Uses softened gravity with EPS_ACCEL to avoid singularities.
    Acceleration on body i: sum over j != i of
        a_i = G * m_j * (r_j - r_i) / (|r_j - r_i|^2 + eps^2)^(3/2)
    """
    n = len(bodies)

    # Reset accelerations to zero
    for b in bodies:
        b.acc[:] = 0.0

    # Pairwise calculation (O(N^2), fine for solar system scale)
    for i in range(n):
        for j in range(i + 1, n):
            rij = bodies[j].pos - bodies[i].pos
            dist2 = np.dot(rij, rij) + EPS_ACCEL**2
            dist = np.sqrt(dist2)
            inv_r3 = 1.0 / (dist2 * dist)

            ai = G * bodies[j].mass * rij * inv_r3
            aj = -G * bodies[i].mass * rij * inv_r3

            bodies[i].acc += ai
            bodies[j].acc += aj

# ---------------------------
# One full integrator step (velocity Verlet)
# ---------------------------
def step_system(bodies, dt=DT, use_relativity=ENABLE_1PN_DEFAULT):
    """
    Advance the system by one timestep using velocity-Verlet.

    Parameters
    ----------
    bodies : list of Body
        Each Body has .pos, .vel, .acc, .mass
    dt : float
        Timestep (years)
    use_relativity : bool
        If True, add post-Newtonian corrections

    Returns
    -------
    None (updates bodies in-place)
    """

    # 1) v_half = v + 0.5 * a * dt
    for b in bodies:
        b.vel += 0.5 * b.acc * dt

    # 2) r_new = r + v_half * dt
    for b in bodies:
        b.pos += b.vel * dt

    # 3) Recompute accelerations at new positions
    compute_accelerations(bodies)

    if use_relativity:
        compute_pn_accelerations(bodies)  # adds small corrections in-place

    # 4) v_new = v_half + 0.5 * a_new * dt
    for b in bodies:
        b.vel += 0.5 * b.acc * dt
