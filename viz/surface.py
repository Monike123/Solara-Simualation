"""
surface.py

Potential grid surface logic

Generates and manages the gravitational potential surface visualization
that shows the "gravity wells" created by massive bodies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from constants import G, EPS_POTENTIAL, GRID_DEFAULT_RANGE_AU, GRID_COARSE_N, GRID_FOCUS_N
from constants import POTENTIAL_Y_SCALE, POTENTIAL_Y_CLAMP

__all__ = ["PotentialSurface", "compute_potential_grid"]

class PotentialSurface:
    """
    Manages the gravitational potential surface visualization.
    
    This creates a 2D grid in the x-z plane and computes the gravitational
    potential at each point, which is then rendered as a 3D surface showing
    the "gravity wells" of massive bodies.
    """
    
    def __init__(self, range_au=GRID_DEFAULT_RANGE_AU, resolution=GRID_COARSE_N):
        """
        Initialize the potential surface.
        
        Parameters
        ----------
        range_au : float
            Half-width of the grid in AU (grid spans [-range_au, range_au])
        resolution : int
            Number of grid points along each axis
        """
        self.range_au = range_au
        self.resolution = resolution
        
        # Create coordinate grids
        self.x = np.linspace(-range_au, range_au, resolution)
        self.z = np.linspace(-range_au, range_au, resolution)
        self.X, self.Z = np.meshgrid(self.x, self.z)
        
        # Potential values (will be computed)
        self.Y = np.zeros_like(self.X)
        
        # Visualization properties
        self.y_scale = POTENTIAL_Y_SCALE
        self.y_clamp = POTENTIAL_Y_CLAMP
    
    def update(self, bodies):
        """
        Update the potential surface based on current body positions.
        
        Parameters
        ----------
        bodies : list of Body
            All bodies contributing to the gravitational field
        """
        self.Y = compute_potential_grid(
            self.X, self.Z, bodies, 
            y_plane=0.0, 
            softening=EPS_POTENTIAL
        )
        
        # Apply scaling and clamping for visualization
        self.Y *= self.y_scale
        self.Y = np.clip(self.Y, -self.y_clamp, self.y_clamp)
    
    def get_mesh_data(self):
        """
        Get mesh data for rendering.
        
        Returns
        -------
        tuple of (np.ndarray, np.ndarray, np.ndarray)
            (X, Y, Z) coordinate arrays for 3D mesh
        """
        return self.X, self.Y, self.Z
    
    def get_wireframe_data(self, stride=5):
        """
        Get wireframe data for rendering (reduced resolution).
        
        Parameters
        ----------
        stride : int
            Take every Nth point to reduce wireframe density
            
        Returns
        -------
        tuple of (np.ndarray, np.ndarray, np.ndarray)
            (X, Y, Z) coordinate arrays for wireframe
        """
        return self.X[::stride, ::stride], self.Y[::stride, ::stride], self.Z[::stride, ::stride]

def compute_potential_grid(X, Z, bodies, y_plane=0.0, softening=EPS_POTENTIAL):
    """
    Compute gravitational potential on a 2D grid.
    
    Parameters
    ----------
    X, Z : np.ndarray
        Coordinate grids (from meshgrid)
    bodies : list of Body
        Bodies contributing to the gravitational field
    y_plane : float
        Y-coordinate of the plane (usually 0 for x-z plane)
    softening : float
        Softening parameter to avoid singularities
        
    Returns
    -------
    np.ndarray
        Gravitational potential values at each grid point
    """
    potential = np.zeros_like(X)
    
    for body in bodies:
        # Distance from each grid point to this body
        dx = X - body.pos[0]
        dy = y_plane - body.pos[1]
        dz = Z - body.pos[2]
        
        # Softened distance
        r = np.sqrt(dx**2 + dy**2 + dz**2 + softening**2)
        
        # Add this body's contribution to potential
        # U = -G*M/r (negative because it's a potential well)
        potential -= G * body.mass / r
    
    return potential

def create_focus_surface(center_pos, radius_au=2.0, resolution=GRID_FOCUS_N):
    """
    Create a high-resolution potential surface focused around a specific location.
    
    Parameters
    ----------
    center_pos : array_like
        Center position [x, y, z] in AU
    radius_au : float
        Radius of the focus region in AU
    resolution : int
        Grid resolution for the focus region
        
    Returns
    -------
    PotentialSurface
        High-resolution surface centered on the specified location
    """
    surface = PotentialSurface(range_au=radius_au, resolution=resolution)
    
    # Offset the grid to center on the specified position
    surface.X += center_pos[0]
    surface.Z += center_pos[2]
    
    return surface

def compute_potential_at_point(pos, bodies, softening=EPS_POTENTIAL):
    """
    Compute gravitational potential at a single point.
    
    Parameters
    ----------
    pos : array_like
        Position [x, y, z] in AU
    bodies : list of Body
        Bodies contributing to the gravitational field
    softening : float
        Softening parameter
        
    Returns
    -------
    float
        Gravitational potential at the specified point
    """
    potential = 0.0
    pos = np.array(pos)
    
    for body in bodies:
        r = np.linalg.norm(pos - body.pos)
        r_soft = np.sqrt(r**2 + softening**2)
        potential -= G * body.mass / r_soft
    
    return potential

