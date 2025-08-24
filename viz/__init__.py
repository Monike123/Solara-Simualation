"""
viz package

This folder contains all the visualization and user interface components:
 - surface.py  → Potential grid surface logic
 - ui.py       → Clicks, info panels
 - camera.py   → Camera modes (general vs focus)
 - scene.py    → Rendering setup

We keep this separate from physics so we can easily swap different
visualization backends or run headless simulations.
"""

from .surface import *
from .ui import *
from .camera import *
from .scene import *

__all__ = []
__all__ += surface.__all__
__all__ += ui.__all__
__all__ += camera.__all__
__all__ += scene.__all__

