"""
body.py

Body class (mass, radius, pos, vel, acc)

Represents a single celestial body in the simulation with all its physical
properties and state vectors. This is the fundamental data structure that
the physics engine operates on.
"""

import numpy as np

__all__ = ["Body"]

class Body:
    """
    Represents a celestial body in the N-body simulation.
    
    Attributes
    ----------
    name : str
        Human-readable name of the body (e.g., "Earth", "Sun")
    mass : float
        Mass in solar masses (M_sun)
    radius : float
        Physical radius in AU (for visualization and collision detection)
    pos : np.ndarray, shape (3,)
        Position vector in AU
    vel : np.ndarray, shape (3,)
        Velocity vector in AU/yr
    acc : np.ndarray, shape (3,)
        Acceleration vector in AU/yr^2 (computed by physics engine)
    color : list or tuple, length 3
        RGB color values for visualization (each component 0.0-1.0)
    trail : list of np.ndarray
        Historical positions for drawing orbital trails
    """
    
    def __init__(self, name, mass, radius, pos=None, vel=None, color=None):
        """
        Initialize a new Body.
        
        Parameters
        ----------
        name : str
            Name of the body
        mass : float
            Mass in solar masses
        radius : float
            Physical radius in AU
        pos : array_like, optional
            Initial position [x, y, z] in AU. Defaults to origin.
        vel : array_like, optional
            Initial velocity [vx, vy, vz] in AU/yr. Defaults to zero.
        color : array_like, optional
            RGB color [r, g, b] with values 0.0-1.0. Defaults to white.
        """
        self.name = name
        self.mass = float(mass)
        self.radius = float(radius)
        
        # State vectors
        self.pos = np.array(pos if pos is not None else [0.0, 0.0, 0.0], dtype=float)
        self.vel = np.array(vel if vel is not None else [0.0, 0.0, 0.0], dtype=float)
        self.acc = np.zeros(3, dtype=float)
        
        # Visualization
        self.color = list(color if color is not None else [1.0, 1.0, 1.0])
        self.trail = []
        
    def __repr__(self):
        return f"Body(name='{self.name}', mass={self.mass:.3e}, radius={self.radius:.3e})"
    
    def __str__(self):
        return f"{self.name}: mass={self.mass:.3e} M_sun, radius={self.radius:.3e} AU"
    
    def add_trail_point(self, decimation=1):
        """
        Add current position to the trail for visualization.
        
        Parameters
        ----------
        decimation : int
            Only add every Nth call to reduce memory usage
        """
        if len(self.trail) % decimation == 0:
            self.trail.append(self.pos.copy())
    
    def clear_trail(self):
        """Clear the orbital trail."""
        self.trail.clear()
    
    def get_kinetic_energy(self):
        """
        Calculate kinetic energy of this body.
        
        Returns
        -------
        float
            Kinetic energy in internal units (AU^2/yr^2 * M_sun)
        """
        return 0.5 * self.mass * np.dot(self.vel, self.vel)
    
    def get_momentum(self):
        """
        Calculate momentum vector of this body.
        
        Returns
        -------
        np.ndarray, shape (3,)
            Momentum vector in internal units (AU/yr * M_sun)
        """
        return self.mass * self.vel
    
    def get_angular_momentum(self, origin=None):
        """
        Calculate angular momentum vector of this body about a point.
        
        Parameters
        ----------
        origin : array_like, optional
            Reference point. Defaults to coordinate origin.
            
        Returns
        -------
        np.ndarray, shape (3,)
            Angular momentum vector in internal units (AU^2/yr * M_sun)
        """
        if origin is None:
            r = self.pos
        else:
            r = self.pos - np.array(origin)
        return self.mass * np.cross(r, self.vel)
    
    def distance_to(self, other):
        """
        Calculate distance to another body.
        
        Parameters
        ----------
        other : Body
            Another body
            
        Returns
        -------
        float
            Distance in AU
        """
        return np.linalg.norm(self.pos - other.pos)
    
    def copy(self):
        """
        Create a deep copy of this body.
        
        Returns
        -------
        Body
            New Body instance with copied state
        """
        new_body = Body(
            name=self.name,
            mass=self.mass,
            radius=self.radius,
            pos=self.pos.copy(),
            vel=self.vel.copy(),
            color=self.color.copy()
        )
        new_body.acc = self.acc.copy()
        new_body.trail = [p.copy() for p in self.trail]
        return new_body

