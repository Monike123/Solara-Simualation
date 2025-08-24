"""
physics package

This folder contains all the "math brains" of our simulator:
 - elements.py     → convert orbital elements <-> state vectors
 - nbody.py        → Newtonian gravity + numerical integrator
 - pn1.py          → relativistic corrections (1PN terms)
 - osculating.py   → calculate orbital elements from current state
 - diagnostics.py  → check conservation of energy, momentum, etc.

We keep this separate from rendering so we can test the physics
without any 3D graphics.
"""

from .elements import *       # orbital element conversions
from .nbody import *          # Newtonian stepper
from .pn1 import *            # GR correction terms
from .osculating import *     # live orbital elements
from .diagnostics import *    # checks and logging

__all__ = []
__all__ += elements.__all__
__all__ += nbody.__all__
__all__ += pn1.__all__
__all__ += osculating.__all__
__all__ += diagnostics.__all__
