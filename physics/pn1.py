"""
pn1.py

Implements 1st post-Newtonian (1PN) corrections for gravity.

- Newtonian gravity is fine for most planets.
- To capture effects like Mercury's perihelion precession,
  we add a small correction term based on general relativity.

This uses the weak-field, slow-motion approximation:
  - valid for the Solar System (v << c, GM/rc^2 << 1)
  - sometimes called the Einstein–Infeld–Hoffmann (EIH) equations

In practice:
  - compute Newtonian acceleration first (see nbody.py)
  - then call compute_pn_accelerations() to add the GR tweak
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from constants import G, C_AU_PER_YR, EPS_ACCEL

__all__ = ["compute_pn_accelerations"]

# ---------------------------
# Simplified 1PN correction
# ---------------------------
def compute_pn_accelerations(bodies):
    """
    Apply post-Newtonian corrections to each body's acceleration.

    Notes
    -----
    This is a simplified version where:
      - The Sun is the dominant central mass.
      - Corrections are applied to planet accelerations due to the Sun only.
      - Planet-planet relativistic effects are negligible (safe to ignore).

    Formula (test body around mass M at distance r, velocity v):

        a_PN = (GM / (c^2 * r^3)) * [ (4GM/r - v^2) * r_vec
                                      + 4 (r_vec · v_vec) * v_vec ]

    References:
      - Einstein–Infeld–Hoffmann equations (see Will, "Theory and Experiment in Gravitational Physics")
      - Brumberg, "Essential Relativistic Celestial Mechanics"
    """
    # Identify central body (assume Sun is bodies[0])
    sun = bodies[0]
    M = sun.mass

    for b in bodies[1:]:  # skip the Sun itself
        r_vec = b.pos - sun.pos
        v_vec = b.vel - sun.vel

        r2 = np.dot(r_vec, r_vec) + EPS_ACCEL**2
        r = np.sqrt(r2)

        v2 = np.dot(v_vec, v_vec)
        rv = np.dot(r_vec, v_vec)

        # Relativistic correction term
        factor = G * M / (C_AU_PER_YR**2 * r**3)
        correction = factor * ((4*G*M/r - v2) * r_vec + 4*rv * v_vec)

        # Add this tweak to the acceleration already computed
        b.acc += correction
