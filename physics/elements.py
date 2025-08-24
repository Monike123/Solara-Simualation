"""
elements.py

Keplerian orbital elements <-> Cartesian state vector conversions.

We use the "classical" set of 6 orbital elements:
  - a : semi-major axis (AU)
  - e : eccentricity (0=circle, <1=ellipse)
  - i : inclination (radians)
  - Ω : longitude of ascending node (radians)
  - ω : argument of periapsis (radians)
  - M : mean anomaly at epoch (radians)

Given these and the central mass, we can compute:
  - position vector r (AU)
  - velocity vector v (AU/yr)

And vice versa: from r and v we can derive elements again.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import numpy as np
from constants import G

__all__ = [
    "elements_to_state",
    "state_to_elements",
    "solve_kepler"
]

# ---------------------------
# Helper: solve Kepler’s equation for eccentric anomaly E
# M = E - e sin(E)
# Use Newton-Raphson iteration
# ---------------------------
def solve_kepler(M, e, tol=1e-10, max_iter=50):
    """Solve Kepler's equation M = E - e*sin(E) for E."""
    M = np.mod(M, 2*math.pi)  # wrap into [0, 2π)
    if e < 0.8:
        E = M
    else:
        E = math.pi

    for _ in range(max_iter):
        f = E - e*math.sin(E) - M
        fprime = 1 - e*math.cos(E)
        dE = -f/fprime
        E += dE
        if abs(dE) < tol:
            break
    return E

# ---------------------------
# Convert elements -> state vector
# ---------------------------
# physics/elements.py
import numpy as np

def elements_to_state(a, e, i, Omega, omega, M, mu=4*np.pi**2):
    """
    Convert orbital elements to Cartesian state vectors (r, v).
    
    Parameters
    ----------
    a : float
        Semi-major axis (AU)
    e : float
        Eccentricity
    i : float
        Inclination (rad)
    Omega : float
        Longitude of ascending node (rad)
    omega : float
        Argument of periapsis (rad)
    M : float
        Mean anomaly (rad)
    mu : float
        Gravitational parameter (AU^3/yr^2), defaults to Sun
    
    Returns
    -------
    (r, v) : tuple of np.ndarray
        Position [x,y,z] in AU and velocity [vx,vy,vz] in AU/yr
    """

    # --- Solve Kepler's equation for eccentric anomaly E ---
    def kepler(E, M, e): return E - e*np.sin(E) - M
    def kepler_prime(E, e): return 1 - e*np.cos(E)

    E = M
    for _ in range(10):  # Newton-Raphson iteration
        E -= kepler(E, M, e) / kepler_prime(E, e)

    # --- Position in orbital plane ---
    x_prime = a * (np.cos(E) - e)
    y_prime = a * np.sqrt(1 - e**2) * np.sin(E)
    r_orb = np.array([x_prime, y_prime, 0.0])

    # --- Velocity in orbital plane ---
    n = np.sqrt(mu / a**3)  # mean motion
    vx_prime = -a * n * np.sin(E) / (1 - e*np.cos(E))
    vy_prime = a * n * np.sqrt(1 - e**2) * np.cos(E) / (1 - e*np.cos(E))
    v_orb = np.array([vx_prime, vy_prime, 0.0])

    # --- Rotate into 3D space ---
    cosO, sinO = np.cos(Omega), np.sin(Omega)
    cosi, sini = np.cos(i), np.sin(i)
    cosw, sinw = np.cos(omega), np.sin(omega)

    R = np.array([
        [cosO*cosw - sinO*sinw*cosi, -cosO*sinw - sinO*cosw*cosi, sinO*sini],
        [sinO*cosw + cosO*sinw*cosi, -sinO*sinw + cosO*cosw*cosi, -cosO*sini],
        [sinw*sini,                  cosw*sini,                   cosi]
    ])

    r = R @ r_orb
    v = R @ v_orb

    return r, v

# ---------------------------
# Convert state vector -> elements
# ---------------------------
def state_to_elements(r, v, mu=G*(1.0+0.0)):
    """
    Convert Cartesian state (r,v) into orbital elements.
    
    Parameters:
        r : np.array([x,y,z]) in AU
        v : np.array([vx,vy,vz]) in AU/yr
        mu: G * (M_central + m_body)

    Returns:
        (a, e, i, Ω, ω, M)
        All angles in radians.
    """
    rmag = np.linalg.norm(r)
    vmag = np.linalg.norm(v)

    # Specific angular momentum
    h = np.cross(r, v)
    hmag = np.linalg.norm(h)

    # Inclination
    i = math.acos(h[2] / hmag)

    # Node line
    K = np.array([0, 0, 1])
    N = np.cross(K, h)
    Nmag = np.linalg.norm(N)

    # Eccentricity vector
    e_vec = (1/mu) * ((vmag**2 - mu/rmag)*r - np.dot(r,v)*v)
    e = np.linalg.norm(e_vec)

    # Semi-major axis from vis-viva
    a = 1 / (2/rmag - vmag**2/mu)

    # Longitude of ascending node
    if Nmag != 0:
        Omega = math.atan2(N[1], N[0])
    else:
        Omega = 0.0

    # Argument of periapsis
    if Nmag != 0 and e > 1e-10:
        omega = math.atan2(np.dot(np.cross(N, e_vec), h)/hmag,
                           np.dot(N, e_vec)/Nmag)
    else:
        omega = 0.0

    # True anomaly
    if e > 1e-10:
        nu = math.atan2(np.dot(np.cross(e_vec, r), h)/hmag,
                        np.dot(e_vec, r)/(e*rmag))
    else:
        nu = math.atan2(r[1], r[0])

    # Eccentric anomaly from true anomaly
    E = 2*math.atan2(math.tan(nu/2), math.sqrt((1+e)/(1-e)))
    M = E - e*math.sin(E)

    return a, e, i, Omega, omega, M
