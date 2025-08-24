"""
osculating.py

Given instantaneous Cartesian state vectors (r, v) for a body (in AU, AU/yr),
compute its osculating orbital elements relative to a central mass.

Returned elements (angles in radians):
  - a      : semi-major axis (AU)
  - e      : eccentricity (unitless)
  - i      : inclination (rad)
  - Omega  : longitude of ascending node (rad)
  - omega  : argument of periapsis (rad)
  - nu     : true anomaly (rad)
  - M      : mean anomaly (rad)

Also returns diagnostics:
  - specific_energy (epsilon)
  - specific_angular_momentum (h_vec and |h|)
  - period (Keplerian approximation in years; None for unbound orbits)

Notes / practical points:
  - This code is forgiving about near-circular or near-equatorial orbits.
  - It uses the standard vis-viva equation and vector definitions.
  - mu should be provided (G*(M_central + m_body)) in the same internal units.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import numpy as np
from constants import G

__all__ = ["osculating_elements", "elements_from_state_dict"]

# TOLERANCES for numerical edge cases
_EPS = 1e-12
_SMALL = 1e-8

def _wrap_to_2pi(angle):
    """Return angle wrapped to [0, 2π)."""
    a = angle % (2.0 * math.pi)
    if a < 0:
        a += 2.0 * math.pi
    return a

def osculating_elements(r, v, mu=G):
    """
    Compute osculating orbital elements from position and velocity vectors.

    Parameters
    ----------
    r : array_like, shape (3,)
        Position vector (AU) relative to central body.
    v : array_like, shape (3,)
        Velocity vector (AU/yr) relative to central body.
    mu : float
        Standard gravitational parameter (G*(M_central + m_body)) in internal units.

    Returns
    -------
    elements : dict
        {
          'a'  : semi-major axis (AU) or None for parabolic/hyperbolic,
          'e'  : eccentricity (>=0),
          'i'  : inclination (rad),
          'Omega' : longitude of ascending node (rad),
          'omega' : argument of periapsis (rad),
          'nu'    : true anomaly (rad),
          'M'     : mean anomaly (rad),
          'specific_energy' : epsilon (AU^2 / yr^2),
          'h_vec' : specific angular momentum vector (AU^2 / yr),
          'h'     : norm of h_vec,
          'period' : Keplerian period in years (None if unbound)
        }

    Notes
    -----
    - The function is robust to circular (e ~ 0) and equatorial (i ~ 0) edge cases.
    - For hyperbolic orbits (e >= 1), 'a' will be negative; period is None.
    """
    r = np.asarray(r, dtype=float)
    v = np.asarray(v, dtype=float)

    rmag = np.linalg.norm(r)
    vmag = np.linalg.norm(v)

    # Specific angular momentum
    h_vec = np.cross(r, v)
    h = np.linalg.norm(h_vec)

    # Node vector (points toward ascending node)
    K = np.array([0.0, 0.0, 1.0])
    N_vec = np.cross(K, h_vec)
    N = np.linalg.norm(N_vec)

    # Specific orbital energy (vis-viva form)
    specific_energy = 0.5 * vmag**2 - mu / rmag

    # Eccentricity vector (Laplace-Runge-Lenz style)
    # e_vec = (1/mu) * ( (v^2 - mu/r)*r - (r·v) v )
    rv_dot = np.dot(r, v)
    e_vec = ( (vmag**2 - mu/rmag) * r - rv_dot * v ) / mu
    e = np.linalg.norm(e_vec)

    # Semi-major axis from vis-viva (handle parabolic/hyperbolic cases)
    if abs(specific_energy) < _EPS:
        a = float('inf')   # parabolic; a -> infinity
    else:
        a = - mu / (2.0 * specific_energy)

    # Inclination
    if h > _SMALL:
        i = math.acos(max(-1.0, min(1.0, h_vec[2] / h)))
    else:
        i = 0.0

    # Longitude of ascending node Ω
    if N > _SMALL:
        Omega = math.atan2(N_vec[1], N_vec[0])
        Omega = _wrap_to_2pi(Omega)
    else:
        Omega = 0.0

    # Argument of periapsis ω
    if e > _SMALL and N > _SMALL:
        # Compute cos(ω) = (N · e_vec) / (N * e)
        cos_omega = np.dot(N_vec, e_vec) / (N * e)
        cos_omega = max(-1.0, min(1.0, cos_omega))
        sin_omega = np.dot(np.cross(N_vec, e_vec), h_vec) / (N * e * h)
        omega = math.atan2(sin_omega, cos_omega)
        omega = _wrap_to_2pi(omega)
    elif e > _SMALL and N <= _SMALL:
        # Equatorial orbit: ω measured from x-axis in orbital plane
        cos_omega = e_vec[0] / e
        cos_omega = max(-1.0, min(1.0, cos_omega))
        sin_omega = e_vec[1] / e
        omega = math.atan2(sin_omega, cos_omega)
        omega = _wrap_to_2pi(omega)
    else:
        omega = 0.0

    # True anomaly ν
    if e > _SMALL:
        cos_nu = np.dot(e_vec, r) / (e * rmag)
        cos_nu = max(-1.0, min(1.0, cos_nu))
        sin_nu = np.dot(np.cross(e_vec, r), h_vec) / (e * rmag * h) if h > _SMALL else 0.0
        nu = math.atan2(sin_nu, cos_nu)
        nu = _wrap_to_2pi(nu)
    else:
        # Circular orbit: true anomaly from position vector measured in orbital plane
        # Project r onto node/ref frame to get a meaningful angle.
        if N > _SMALL:
            cos_nu = np.dot(N_vec / N, r) / rmag
            cos_nu = max(-1.0, min(1.0, cos_nu))
            sin_nu = np.dot(np.cross(N_vec / N, r), h_vec) / (rmag * h) if h > _SMALL else 0.0
            nu = math.atan2(sin_nu, cos_nu)
            nu = _wrap_to_2pi(nu)
        else:
            # Equatorial & circular: fallback to angle in x-y plane
            nu = math.atan2(r[1], r[0])
            nu = _wrap_to_2pi(nu)

    # Eccentric anomaly E and mean anomaly M (for elliptic orbits only)
    if e < 1.0 - 1e-8:
        # For elliptical orbits, compute eccentric anomaly E from true anomaly ν:
        # E = 2*atan( sqrt((1-e)/(1+e)) * tan(nu/2) )
        E = 2.0 * math.atan2(math.sqrt(1.0 - e) * math.sin(nu / 2.0),
                              math.sqrt(1.0 + e) * math.cos(nu / 2.0))
        M = E - e * math.sin(E)
        # Normalize M to [0, 2π)
        M = _wrap_to_2pi(M)
    else:
        # Parabolic/hyperbolic: M not defined in the same way (skip)
        M = None

    # Keplerian period (years) for bound elliptical orbits
    if e < 1.0 - 1e-8 and a != float('inf'):
        period = 2.0 * math.pi * math.sqrt(abs(a**3 / mu))
    else:
        period = None

    result = {
        'a': a,
        'e': e,
        'i': i,
        'Omega': Omega,
        'omega': omega,
        'nu': nu,
        'M': M,
        'specific_energy': specific_energy,
        'h_vec': h_vec,
        'h': h,
        'period': period
    }

    return result

def elements_from_state_dict(state_dict):
    """
    Convenience wrapper: accept an object/dict with keys 'pos' and 'vel'
    and return the osculating elements dict.

    Intended to be used with Body instances that have `.pos` and `.vel`.
    """
    r = state_dict['pos']
    v = state_dict['vel']
    mu = state_dict.get('mu', G)
    return osculating_elements(r, v, mu=mu)
