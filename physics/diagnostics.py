"""
diagnostics.py

Utilities to monitor how well the simulation is behaving physically.

We track:
  - total energy of the system (kinetic + potential)
  - total angular momentum vector
  - relative drift compared to the initial values

If the timestep (DT) or softening (EPS) is too large/small,
these numbers will drift over time. Watching them helps you tune stability.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from constants import G

__all__ = ["total_energy", "total_angular_momentum", "diagnostics_report"]

# ---------------------------
# Energy
# ---------------------------
def total_energy(bodies):
    """
    Compute total kinetic + potential energy of the system.

    Parameters
    ----------
    bodies : list of Body

    Returns
    -------
    E : float
        Total energy (internal units: AU^2 / yr^2 * M_sun)
    """
    E_kin = 0.0
    E_pot = 0.0

    # Kinetic: 1/2 m v^2
    for b in bodies:
        v2 = np.dot(b.vel, b.vel)
        E_kin += 0.5 * b.mass * v2

    # Potential: - G m_i m_j / r_ij (sum over pairs)
    n = len(bodies)
    for i in range(n):
        for j in range(i+1, n):
            rij = bodies[j].pos - bodies[i].pos
            dist = np.linalg.norm(rij)
            if dist > 0:
                E_pot -= G * bodies[i].mass * bodies[j].mass / dist

    return E_kin + E_pot

# ---------------------------
# Angular momentum
# ---------------------------
def total_angular_momentum(bodies):
    """
    Compute total angular momentum vector of the system.

    Parameters
    ----------
    bodies : list of Body

    Returns
    -------
    H_vec : np.ndarray, shape (3,)
        Angular momentum vector (AU^2 / yr * M_sun)
    """
    H_vec = np.zeros(3)
    for b in bodies:
        H_vec += b.mass * np.cross(b.pos, b.vel)
    return H_vec

# ---------------------------
# Reporting helper
# ---------------------------
def diagnostics_report(bodies, E0=None, H0=None):
    """
    Return a human-readable dict of diagnostics:
      - current energy
      - fractional energy drift (if E0 given)
      - angular momentum vector
      - angular momentum drift (if H0 given)

    Useful for printing/logging every N steps.
    """
    E = total_energy(bodies)
    H = total_angular_momentum(bodies)

    report = {
        "energy": E,
        "H_vec": H,
    }

    if E0 is not None:
        report["dE/E0"] = (E - E0) / E0

    if H0 is not None:
        dH = np.linalg.norm(H - H0)
        report["|dH|/|H0|"] = dH / np.linalg.norm(H0)

    return report
