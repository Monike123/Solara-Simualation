"""
system.py

Load JSON, build solar system bodies, attach moons

This module handles the initialization of the solar system from configuration
files and provides utilities for managing collections of bodies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import numpy as np
from .body import Body
from physics.elements import elements_to_state
from constants import G

__all__ = ["SolarSystem", "load_solar_system"]

class SolarSystem:
    """
    Container for all bodies in the solar system simulation.
    
    Attributes
    ----------
    bodies : list of Body
        All bodies in the system (Sun + planets + moons)
    sun : Body
        Reference to the central star
    planets : list of Body
        References to planetary bodies (excluding the Sun)
    """
    
    def __init__(self):
        self.bodies = []
        self.sun = None
        self.planets = []
    
    def add_body(self, body):
        """Add a body to the system."""
        self.bodies.append(body)
        if body.name.lower() == "sun":
            self.sun = body
        else:
            self.planets.append(body)
    
    def get_body_by_name(self, name):
        """Find a body by name (case-insensitive)."""
        name_lower = name.lower()
        for body in self.bodies:
            if body.name.lower() == name_lower:
                return body
        return None
    
    def get_total_mass(self):
        """Calculate total mass of all bodies."""
        return sum(body.mass for body in self.bodies)
    
    def get_center_of_mass(self):
        """
        Calculate center of mass position and velocity.
        
        Returns
        -------
        tuple of (np.ndarray, np.ndarray)
            (COM position, COM velocity) in system units
        """
        total_mass = self.get_total_mass()
        if total_mass == 0:
            return np.zeros(3), np.zeros(3)
        
        com_pos = np.zeros(3)
        com_vel = np.zeros(3)
        
        for body in self.bodies:
            com_pos += body.mass * body.pos
            com_vel += body.mass * body.vel
        
        return com_pos / total_mass, com_vel / total_mass
    
    def move_to_barycenter(self):
        """Move the entire system so center of mass is at origin."""
        com_pos, com_vel = self.get_center_of_mass()
        
        for body in self.bodies:
            body.pos -= com_pos
            body.vel -= com_vel
    
    def clear_all_trails(self):
        """Clear orbital trails for all bodies."""
        for body in self.bodies:
            body.clear_trail()
    
    def add_trail_points(self, decimation=1):
        """Add current positions to trails for all bodies."""
        for body in self.bodies:
            body.add_trail_point(decimation)

def load_solar_system(json_path):
    """
    Load solar system configuration from JSON file.
    
    Parameters
    ----------
    json_path : str
        Path to JSON configuration file
        
    Returns
    -------
    SolarSystem
        Initialized solar system with all bodies
    """
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    system = SolarSystem()
    
    # Create the Sun
    sun_data = data["sun"]
    sun = Body(
        name=sun_data["name"],
        mass=sun_data["mass"],
        radius=sun_data["radius"],
        pos=[0.0, 0.0, 0.0],
        vel=[0.0, 0.0, 0.0],
        color=sun_data["color"]
    )
    system.add_body(sun)
    
    # Create planets from orbital elements
    for planet_data in data["planets"]:
        # Extract orbital elements (angles assumed to be in radians)
        a = planet_data["a"]          # semi-major axis (AU)
        e = planet_data["e"]          # eccentricity
        i = planet_data["i"]          # inclination (rad)
        Omega = planet_data["Omega"]  # longitude of ascending node (rad)
        omega = planet_data["omega"]  # argument of periapsis (rad)
        M = planet_data["M"]          # mean anomaly (rad)
        
        # Standard gravitational parameter for Sun + planet
        # (planet mass is negligible compared to Sun for orbital calculation)
        mu = G * (sun.mass + planet_data["mass"])
        
        # Convert orbital elements to Cartesian state vectors
        pos, vel = elements_to_state(a, e, i, Omega, omega, M, mu)
        
        # Create planet body
        planet = Body(
            name=planet_data["name"],
            mass=planet_data["mass"],
            radius=planet_data["radius"],
            pos=pos,
            vel=vel,
            color=planet_data["color"]
        )
        
        system.add_body(planet)
    
    # Move system to barycenter (though Sun dominates, this is good practice)
    system.move_to_barycenter()
    
    return system

def create_test_system():
    """
    Create a simple test system with Sun and Earth for debugging.
    
    Returns
    -------
    SolarSystem
        Simple two-body system
    """
    system = SolarSystem()
    
    # Sun at origin
    sun = Body(
        name="Sun",
        mass=1.0,
        radius=0.00465,
        pos=[0.0, 0.0, 0.0],
        vel=[0.0, 0.0, 0.0],
        color=[1.0, 1.0, 0.0]
    )
    system.add_body(sun)
    
    # Earth in circular orbit
    earth_distance = 1.0  # 1 AU
    earth_speed = np.sqrt(G * sun.mass / earth_distance)  # circular orbital speed
    
    earth = Body(
        name="Earth",
        mass=3.003e-6,
        radius=4.26e-5,
        pos=[earth_distance, 0.0, 0.0],
        vel=[0.0, earth_speed, 0.0],
        color=[0.2, 0.4, 1.0]
    )
    system.add_body(earth)
    
    return system

