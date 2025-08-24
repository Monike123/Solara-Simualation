"""
model package

This folder contains the data structures and system setup for our simulation:
 - body.py    → Body class (mass, radius, pos, vel, acc)
 - system.py  → Load JSON, build solar system bodies, attach moons

We keep this separate from physics so we can easily swap different
planetary configurations or add/remove bodies.
"""

from .body import *
from .system import *

__all__ = []
__all__ += body.__all__
__all__ += system.__all__

