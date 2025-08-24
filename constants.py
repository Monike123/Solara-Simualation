"""
constants.py

Canonical units for the simulator:
  - Length:  Astronomical Unit (AU)
  - Time:    Julian year (yr) = 365.25 days
  - Mass:    Solar mass (M_sun)

Using these units simplifies Keplerian dynamics:
  G = 4 * pi^2  (AU^3 / (yr^2 * M_sun))

This file also contains:
  - conversion factors to/from SI (meters, kilograms, seconds)
  - numeric simulation knobs (dt, softening)
  - rendering / LOD defaults (grid sizes, visual radii scale)
"""

import math

# ---------------------------
# Basic unit conversions (SI ↔ internal units)
# ---------------------------
AU_IN_METERS = 149_597_870_700.0        # 1 AU in meters (exact IAU definition)
DAY_IN_SECONDS = 86400.0
DAYS_PER_YEAR = 365.25
SECONDS_PER_YEAR = DAY_IN_SECONDS * DAYS_PER_YEAR

M_SUN_IN_KG = 1.98847e30               # nominal solar mass (kg)
G_SI = 6.67430e-11                     # gravitational constant (m^3 kg^-1 s^-2)
C_SI = 299_792_458.0                   # speed of light (m/s)

# Derived constants in our internal units (AU, yr, M_sun)
# NOTE: In these units, G = 4*pi^2 exactly for Kepler's third law convenience.
G = 4.0 * math.pi**2                   # gravitational constant (AU^3 / (yr^2 * M_sun))

# Speed of light in AU / yr (useful for PN corrections)
C_AU_PER_YR = C_SI * SECONDS_PER_YEAR / AU_IN_METERS

# ---------------------------
# Simulation numeric knobs
# ---------------------------
# Default timestep (in years). 0.002 yr ≈ 0.73 days.
# - Decrease dt for higher accuracy or to resolve fast moons.
# - Increase dt for faster but less accurate, visually acceptable runs.
DT = 0.001

# Softening length for acceleration calculations (in AU)
# - Prevents singular forces when bodies get extremely close.
# - Choose small relative to planet radii but large enough to remain numerically stable.
EPS_ACCEL = 1e-5       # ~1.5e3 km (choose smaller for collisions, larger to smooth)

# Softening for potential grid sampling / visualization (in AU)
EPS_POTENTIAL = 1e-3   # larger than EPS_ACCEL to avoid large spikes in the mesh

# Toggle default: enable 1PN corrections (Schwarzschild/EIH) by default
ENABLE_1PN_DEFAULT = True

# ---------------------------
# Visualization / rendering defaults
# ---------------------------
# Visual scaling of physical radii for visibility (multiply real radius by this when rendering)
# Real planet radii are tiny compared to orbital distances; exaggerate so they are visible.
VISUAL_RADIUS_SCALE = 2000.0

# Trail / path decimation: store one trail sample every TRAIL_DECIMATE physics steps
TRAIL_DECIMATE = 10

# Grid defaults for potential surface (x-z plane)
GRID_DEFAULT_RANGE_AU = 20.0     # half-width of the grid in AU (grid spans [-L, L])
GRID_COARSE_N = 61               # coarse grid resolution (general view)
GRID_FOCUS_N = 121               # fine grid resolution (focus view around a planet)

# Potential-to-visual height scaling (tune for pleasing dips)
# Note: Newtonian potential at 1 AU for Sun ~ -4*pi^2 (~ -39.48). Choose ALPHA so resulting y is visually reasonable.
POTENTIAL_Y_SCALE = 2.0

# Maximum allowed visual height (absolute) to avoid exploding meshes; clamps after scaling
POTENTIAL_Y_CLAMP = 50.0

# ---------------------------
# Performance / LOD knobs
# ---------------------------
# Update far-field potential tiles only every N physics frames (coarse refresh)
FARFIELD_UPDATE_EVERY = 3

# Radius (AU) for the high-resolution focus patch around a selected planet
FOCUS_PATCH_RADIUS_AU = 2.0

# ---------------------------
# Diagnostic / logging defaults
# ---------------------------
DIAGNOSTIC_ENERGY_PRINT_EVERY = 250   # print total energy every N steps
DIAGNOSTIC_SAVE_HISTORY_LENGTH = 1000 # number of historical samples to keep for plots

# ---------------------------
# Convenience conversion helpers
# ---------------------------
def kg_to_solar_mass(kg: float) -> float:
    """Convert kilograms to units of M_sun used internally."""
    return kg / M_SUN_IN_KG

def solar_mass_to_kg(msun: float) -> float:
    """Convert internal solar-mass units to kilograms."""
    return msun * M_SUN_IN_KG

def m_to_AU(m: float) -> float:
    """Meters -> AU"""
    return m / AU_IN_METERS

def AU_to_m(au: float) -> float:
    """AU -> meters"""
    return au * AU_IN_METERS

def km_to_AU(km: float) -> float:
    """Kilometers -> AU"""
    return (km * 1000.0) / AU_IN_METERS

def seconds_to_years(s: float) -> float:
    """Seconds -> years (internal time unit)"""
    return s / SECONDS_PER_YEAR

def years_to_seconds(y: float) -> float:
    """Years -> seconds"""
    return y * SECONDS_PER_YEAR

# ---------------------------
# Helper: compute recommended DT in seconds (useful for timers/benchmarks)
# ---------------------------
DT_SECONDS = years_to_seconds(DT)

# ---------------------------
# Module metadata
# ---------------------------
__all__ = [
    "AU_IN_METERS", "SECONDS_PER_YEAR", "M_SUN_IN_KG", "G_SI", "C_SI",
    "G", "C_AU_PER_YR", "DT", "DT_SECONDS",
    "EPS_ACCEL", "EPS_POTENTIAL", "ENABLE_1PN_DEFAULT",
    "VISUAL_RADIUS_SCALE", "TRAIL_DECIMATE",
    "GRID_DEFAULT_RANGE_AU", "GRID_COARSE_N", "GRID_FOCUS_N",
    "POTENTIAL_Y_SCALE", "POTENTIAL_Y_CLAMP",
    "FARFIELD_UPDATE_EVERY", "FOCUS_PATCH_RADIUS_AU",
    "DIAGNOSTIC_ENERGY_PRINT_EVERY", "DIAGNOSTIC_SAVE_HISTORY_LENGTH",
    "kg_to_solar_mass", "solar_mass_to_kg", "m_to_AU", "AU_to_m", "km_to_AU",
    "seconds_to_years", "years_to_seconds",
]
