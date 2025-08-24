#!/usr/bin/env python3
"""
test_simulation.py

Simple test script to verify the simulation works correctly.
"""

import numpy as np
import matplotlib.pyplot as plt
from model.system import load_solar_system, create_test_system
from physics.nbody import step_system
from physics.diagnostics import total_energy, total_angular_momentum, diagnostics_report
from physics.osculating import osculating_elements
from constants import G

def test_energy_conservation():
    """Test that energy is conserved in a simple two-body system."""
    print("Testing energy conservation...")
    
    system = create_test_system()
    E0 = total_energy(system.bodies)
    
    # Run for 100 steps
    for i in range(100):
        step_system(system.bodies, dt=0.001)
    
    E1 = total_energy(system.bodies)
    relative_error = abs(E1 - E0) / abs(E0)
    
    print(f"Initial energy: {E0:.6e}")
    print(f"Final energy: {E1:.6e}")
    print(f"Relative error: {relative_error:.2e}")
    
    if relative_error < 1e-3:
        print("✓ Energy conservation test PASSED")
        return True
    else:
        print("✗ Energy conservation test FAILED")
        return False

def test_orbital_elements():
    """Test orbital element calculations."""
    print("\nTesting orbital elements...")
    
    system = create_test_system()
    earth = system.planets[0]  # Earth
    
    # Calculate orbital elements
    elements = osculating_elements(earth.pos, earth.vel, mu=G)
    
    print(f"Semi-major axis: {elements['a']:.3f} AU (expected: ~1.0)")
    print(f"Eccentricity: {elements['e']:.3f} (expected: ~0.0)")
    print(f"Period: {elements['period']:.3f} years (expected: ~1.0)")
    
    # Check if values are reasonable
    a_ok = abs(elements['a'] - 1.0) < 0.1
    e_ok = elements['e'] < 0.1
    p_ok = abs(elements['period'] - 1.0) < 0.1 if elements['period'] else False
    
    if a_ok and e_ok and p_ok:
        print("✓ Orbital elements test PASSED")
        return True
    else:
        print("✗ Orbital elements test FAILED")
        return False

def test_full_system():
    """Test loading and running the full solar system."""
    print("\nTesting full solar system...")
    
    try:
        system = load_solar_system("data/solar_params.json")
        print(f"Loaded {len(system.bodies)} bodies")
        
        # Check that we have the expected planets
        expected_names = ["Sun", "Mercury", "Venus", "Earth", "Mars", 
                         "Jupiter", "Saturn", "Uranus", "Neptune"]
        
        body_names = [body.name for body in system.bodies]
        
        all_present = all(name in body_names for name in expected_names)
        
        if all_present:
            print("✓ All expected bodies present")
        else:
            print("✗ Missing some expected bodies")
            return False
        
        # Test a few simulation steps
        E0 = total_energy(system.bodies)
        for i in range(10):
            step_system(system.bodies, dt=0.001)
        E1 = total_energy(system.bodies)
        
        relative_error = abs(E1 - E0) / abs(E0)
        if relative_error < 1e-2:
            print("✓ Full system simulation test PASSED")
            return True
        else:
            print(f"✗ Energy drift too large: {relative_error:.2e}")
            return False
            
    except Exception as e:
        print(f"✗ Full system test FAILED: {e}")
        return False

def test_visualization_components():
    """Test that visualization components can be imported and initialized."""
    print("\nTesting visualization components...")
    
    try:
        from viz.scene import Scene
        from viz.camera import Camera
        from viz.surface import PotentialSurface
        from viz.ui import UIManager
        
        system = create_test_system()
        
        # Test basic initialization
        scene = Scene(system)
        camera = Camera()
        surface = PotentialSurface()
        ui = UIManager()
        
        print("✓ All visualization components imported and initialized")
        return True
        
    except Exception as e:
        print(f"✗ Visualization test FAILED: {e}")
        return False

def main():
    """Run all tests."""
    print("Running Solar Simulation Tests")
    print("=" * 40)
    
    tests = [
        test_energy_conservation,
        test_orbital_elements,
        test_full_system,
        test_visualization_components
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests PASSED! The simulation is working correctly.")
        return 0
    else:
        print("❌ Some tests FAILED. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())

