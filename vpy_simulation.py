#!/usr/bin/env python3
"""
vpy_simulation.py - VPython Version of Solar System Simulation

Entry point: assemble physics + VPython viz + run loop

This follows the same structure as main.py but uses VPython for 3D visualization
instead of matplotlib.
"""

import sys
import time
import json
import math
from vpython import *

# Import our modules (assuming same structure as main.py)
try:
    from model.system import load_solar_system, create_test_system
    from physics.nbody import step_system
    from physics.diagnostics import total_energy, total_angular_momentum, diagnostics_report
    from constants import DT, DIAGNOSTIC_ENERGY_PRINT_EVERY
except ImportError:
    # Fallback if modules not available
    print("Warning: Some modules not found, using fallback implementations")
    DT = 0.001
    DIAGNOSTIC_ENERGY_PRINT_EVERY = 100

# VPython specific constants
G = 0.1
SUN_RADIUS_VISUAL = 5.0
PLANET_MIN_RADIUS = 0.4
PLANET_MAX_RADIUS = 2.0
SCALE_ORBIT = 40
GRID_SPACING = 20.0  # Increased for better performance
GRID_RANGE = 480     # Increased range
LINE_RADIUS = 0.09

class VPythonScene:
    """VPython 3D scene management."""
    
    def __init__(self, system):
        """Initialize VPython scene."""
        self.system = system
        self.show_trails = True
        self.show_grid = True
        self.show_labels = True
        self.selected_body = None
        
        # Setup VPython scene
        scene.title = "VPython Solar System Simulation"
        scene.background = color.black
        scene.width = 1200
        scene.height = 800
        scene.camera.pos = vector(0, 80, 120)
        scene.camera.axis = vector(0, -80, -120)
        
        # Create visual objects
        self.body_visuals = {}
        self.labels = {}
        self.grid_lines = []
        self.light = None
        
        # Info panel
        self.info_display = None
        self.create_info_panel()
        
        self._create_visuals()
        self._setup_grid()
        
    def create_info_panel(self):
        """Create info panel for selected body."""
        # Create text display for info panel
        self.info_display = wtext(pos=scene.title_anchor, text="Select a body for info\n")
        
    def update_info_panel(self):
        """Update info panel with selected body data."""
        if not self.selected_body:
            self.info_display.text = "Select a body for info\nControls: P-Pause, T-Trails, G-Grid, L-Labels, C-Clear, R-Reset, Q-Quit\n"
            return
            
        body = self.selected_body
        
        # Get position
        if hasattr(body, 'r'):
            pos = body.r
        elif hasattr(body, 'pos'):
            pos = body.pos
        elif hasattr(body, 'position'):
            pos = body.position
        else:
            pos = [0, 0]
            
        # Get velocity
        if hasattr(body, 'v'):
            vel = body.v
        elif hasattr(body, 'vel'):
            vel = body.vel
        elif hasattr(body, 'velocity'):
            vel = body.velocity
        else:
            vel = [0, 0]
        
        # Calculate orbital parameters
        if hasattr(body, 'name') and body.name.lower() != 'sun':
            distance = math.sqrt(pos[0]**2 + pos[1]**2)
            speed = math.sqrt(vel[0]**2 + vel[1]**2)
            orbital_period = 2 * math.pi * distance / max(speed, 1e-10)  # Avoid division by zero
        else:
            distance = 0
            speed = 0
            orbital_period = 0
        
        info_text = f"""Selected: {getattr(body, 'name', 'Unknown')}
Mass: {body.mass:.2e} kg
Position: ({pos[0]:.2f}, {pos[1]:.2f}) AU
Velocity: ({vel[0]:.2f}, {vel[1]:.2f}) AU/yr
Distance from Sun: {distance:.2f} AU
Orbital Speed: {speed:.2f} AU/yr
Orbital Period: {orbital_period:.1f} years

Controls: P-Pause, T-Trails, G-Grid, L-Labels, C-Clear, R-Reset, Q-Quit
"""
        self.info_display.text = info_text
        
    def _create_visuals(self):
        """Create visual objects for all bodies."""
        for body in self.system.bodies:
            # Get position (try different possible attribute names)
            if hasattr(body, 'r'):
                pos = body.r
            elif hasattr(body, 'pos'):
                pos = body.pos
            elif hasattr(body, 'position'):
                pos = body.position
            else:
                print(f"Warning: Could not find position for {body}, using (0,0)")
                pos = [0, 0]
            
            if hasattr(body, 'name') and body.name.lower() == 'sun':
                # Sun
                visual = sphere(
                    pos=vector(pos[0], 0, pos[1]),
                    radius=SUN_RADIUS_VISUAL,
                    color=vector(1, 1, 0),
                    emissive=True,
                    make_trail=False
                )
                # Add light source
                self.light = local_light(pos=visual.pos, color=vector(1, 1, 0.8))
            else:
                # Planet
                radius_visual = max(PLANET_MIN_RADIUS, min(PLANET_MAX_RADIUS, 
                                  getattr(body, 'radius', 1.0) * 1e5))
                
                # Get color or use default
                if hasattr(body, 'color'):
                    color_val = vector(*body.color)
                else:
                    color_val = color.white
                
                visual = sphere(
                    pos=vector(pos[0] * SCALE_ORBIT, 0, pos[1] * SCALE_ORBIT),
                    radius=radius_visual,
                    color=color_val,
                    make_trail=self.show_trails,
                    retain=200
                )
            
            self.body_visuals[body] = visual
            
            # Add label
            if self.show_labels:
                label_text = getattr(body, 'name', f"Body{id(body)}")
                lbl = label(
                    pos=visual.pos + vector(0, visual.radius * 2.5, 0),
                    text=label_text,
                    height=10,
                    box=False,
                    color=color.white
                )
                self.labels[body] = lbl
    
    def _setup_grid(self):
        """Setup spacetime curvature grid."""
        if not self.show_grid:
            return
            
        # Create grid lines
        num_lines = 2 * (2 * GRID_RANGE // int(GRID_SPACING) + 1)
        for _ in range(num_lines):
            self.grid_lines.append(curve(color=color.white, radius=LINE_RADIUS))
    
    def get_curvature_y(self, x, z):
        """Calculate spacetime curvature at position (x, z)."""
        total_y = 0
        for body in self.system.bodies:
            # Get position (try different possible attribute names)
            if hasattr(body, 'r'):
                body_pos = body.r
            elif hasattr(body, 'pos'):
                body_pos = body.pos
            elif hasattr(body, 'position'):
                body_pos = body.position
            else:
                body_pos = [0, 0]
            
            # Scale positions appropriately
            if hasattr(body, 'name') and body.name.lower() == 'sun':
                body_x = body_pos[0]
                body_z = body_pos[1]
            else:
                body_x = body_pos[0] * SCALE_ORBIT
                body_z = body_pos[1] * SCALE_ORBIT
            
            distance_sq = (x - body_x)**2 + (z - body_z)**2 + 1e-3
            distance = math.sqrt(distance_sq)
            
            # Enhanced gravitational well visualization
            if hasattr(body, 'name') and body.name.lower() == 'sun':
                # Sun creates a deep well
                well_depth = -495.0
                well_width = 485.0
            else:
                # Planets create smaller wells
                well_depth = -2.0 * (body.mass / 1e4)  # Scale with planet mass
                well_width = 8.0
            
            # Gaussian well shape
            total_y += well_depth * math.exp(-distance_sq / (well_width**2))
            
        return total_y
    
    def update_grid(self):
        """Update spacetime curvature grid."""
        if not self.show_grid or not self.grid_lines:
            return
            
        curve_index = 0
        step_size = int(GRID_SPACING)
        
        # X-direction lines
        for x_coord in range(-GRID_RANGE, GRID_RANGE + 1, step_size):
            if curve_index >= len(self.grid_lines):
                break
            points = []
            for z in range(-GRID_RANGE, GRID_RANGE + 1, 4):  # 4-unit steps for performance
                y_val = self.get_curvature_y(x_coord, z)
                points.append(vector(x_coord, y_val, z))
            
            if points:  # Only update if we have points
                self.grid_lines[curve_index].clear()
                self.grid_lines[curve_index].append(points)
            curve_index += 1
        
        # Z-direction lines
        for z_coord in range(-GRID_RANGE, GRID_RANGE + 1, step_size):
            if curve_index >= len(self.grid_lines):
                break
            points = []
            for x in range(-GRID_RANGE, GRID_RANGE + 1, 4):  # 4-unit steps for performance
                y_val = self.get_curvature_y(x, z_coord)
                points.append(vector(x, y_val, z_coord))
            
            if points:  # Only update if we have points
                self.grid_lines[curve_index].clear()
                self.grid_lines[curve_index].append(points)
            curve_index += 1
    
    def update(self):
        """Update visual objects with current physics state."""
        for body in self.system.bodies:
            if body in self.body_visuals:
                visual = self.body_visuals[body]
                
                # Get position (try different possible attribute names)
                if hasattr(body, 'r'):
                    pos = body.r
                elif hasattr(body, 'pos'):
                    pos = body.pos
                elif hasattr(body, 'position'):
                    pos = body.position
                else:
                    continue  # Skip if no position found
                
                # Update position
                if hasattr(body, 'name') and body.name.lower() == 'sun':
                    visual.pos = vector(pos[0], 0, pos[1])
                else:
                    visual.pos = vector(
                        pos[0] * SCALE_ORBIT, 
                        0, 
                        pos[1] * SCALE_ORBIT
                    )
                
                # Highlight selected body
                if body == self.selected_body:
                    # Make selected body slightly larger and add glow
                    original_radius = getattr(visual, 'original_radius', visual.radius)
                    visual.radius = original_radius * 1.3
                    if hasattr(visual, 'emissive'):
                        visual.emissive = True
                else:
                    # Reset to normal size
                    if hasattr(visual, 'original_radius'):
                        visual.radius = visual.original_radius
                    elif hasattr(body, 'name') and body.name.lower() != 'sun':
                        if hasattr(visual, 'emissive'):
                            visual.emissive = False
                
                # Store original radius for selection highlighting
                if not hasattr(visual, 'original_radius'):
                    visual.original_radius = visual.radius
                
                # Update light source for sun
                if self.light and hasattr(body, 'name') and body.name.lower() == 'sun':
                    self.light.pos = visual.pos
                
                # Update labels
                if body in self.labels:
                    self.labels[body].pos = visual.pos + vector(0, visual.radius * 2.5, 0)
        
        # Update info panel
        self.update_info_panel()
    
    def handle_mouse_click(self, pos):
        """Handle mouse click for body selection."""
        click_pos = vector(pos.x, 0, pos.z) if hasattr(pos, 'x') else vector(pos[0], 0, pos[1])
        
        closest_body = None
        closest_distance = float('inf')
        
        for body, visual in self.body_visuals.items():
            distance = mag(visual.pos - click_pos)
            if distance < visual.radius * 3 and distance < closest_distance:  # Allow some tolerance
                closest_body = body
                closest_distance = distance
        
        if closest_body:
            self.selected_body = closest_body
            print(f"Selected: {getattr(closest_body, 'name', 'Unknown')}")
            return closest_body
        
        return None
    
    def toggle_trails(self):
        """Toggle orbital trails."""
        self.show_trails = not self.show_trails
        for body, visual in self.body_visuals.items():
            visual.make_trail = self.show_trails
    
    def toggle_grid(self):
        """Toggle spacetime grid."""
        self.show_grid = not self.show_grid
        for line in self.grid_lines:
            line.visible = self.show_grid
    
    def toggle_labels(self):
        """Toggle body labels."""
        self.show_labels = not self.show_labels
        for lbl in self.labels.values():
            lbl.visible = self.show_labels
    
    def clear_trails(self):
        """Clear all orbital trails."""
        for visual in self.body_visuals.values():
            visual.clear_trail()

class VPythonSolarSimulation:
    """
    VPython version of the solar system simulation.
    """
    
    def __init__(self, data_file=None, use_test_system=False):
        """Initialize the VPython simulation."""
        # Load solar system (with fallback)
        try:
            if use_test_system:
                print("Loading test system (Sun + Earth)...")
                self.system = create_test_system()
            else:
                data_file = data_file or "data/solar_params.json"
                print(f"Loading solar system from {data_file}...")
                self.system = load_solar_system(data_file)
        except (ImportError, FileNotFoundError):
            print("Using fallback system loading...")
            self.system = self._load_fallback_system(data_file)
        
        print(f"Loaded {len(self.system.bodies)} bodies:")
        for body in self.system.bodies:
            print(f"  {body}")
        
        # Initialize physics
        self.time = 0.0
        self.step_count = 0
        self.dt = DT
        
        # Store initial conditions for diagnostics
        try:
            self.E0 = total_energy(self.system.bodies)
            self.H0 = total_angular_momentum(self.system.bodies)
            print(f"Initial energy: {self.E0:.6e}")
            print(f"Initial angular momentum: {mag(vector(*self.H0)):.6e}")
        except:
            self.E0 = 0
            self.H0 = [0, 0, 0]
            print("Diagnostics not available")
        
        # Initialize VPython visualization
        self.scene = VPythonScene(self.system)
        
        # Animation control
        self.paused = False
        self.time_scale = 1.0
        self.frame_skip = 0
        self.skip_every = 2
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_time = time.time()
        self.fps_display_interval = 2.0
        
        # Setup controls
        self._setup_controls()
    
    def _load_fallback_system(self, data_file):
        """Fallback system loading if modules not available."""
        class SimpleBody:
            def __init__(self, name, mass, pos, vel, **kwargs):
                self.name = name
                self.mass = mass
                self.position = pos
                self.velocity = vel
                for k, v in kwargs.items():
                    setattr(self, k, v)
            
            def __str__(self):
                return f"{self.name} (m={self.mass:.2e})"
        
        class SimpleSystem:
            def __init__(self):
                self.bodies = []
        
        system = SimpleSystem()
        
        try:
            with open(data_file or "data/solar_params.json", "r") as f:
                data = json.load(f)
            
            # Sun
            sun_data = data["sun"]
            sun = SimpleBody(
                name="Sun",
                mass=sun_data["mass"] * 1000,
                pos=[0, 0],
                vel=[0, 0],
                color=sun_data.get("color", [1, 1, 0])
            )
            system.bodies.append(sun)
            
            # Planets
            for pdata in data["planets"]:
                planet = SimpleBody(
                    name=pdata["name"],
                    mass=pdata["mass"] * 1e4,
                    pos=[pdata["a"] * SCALE_ORBIT, 0],
                    vel=[0, math.sqrt(G * sun.mass / (pdata["a"] * SCALE_ORBIT))],
                    radius=pdata.get("radius", 1.0),
                    color=pdata.get("color", [1, 1, 1])
                )
                system.bodies.append(planet)
        
        except Exception as e:
            print(f"Error loading data: {e}, creating minimal system")
            # Create minimal system
            sun = SimpleBody("Sun", 1000, [0, 0], [0, 0], color=[1, 1, 0])
            earth = SimpleBody("Earth", 1, [40, 0], [0, 5], color=[0, 0, 1])
            system.bodies = [sun, earth]
        
        return system
    
    def _setup_controls(self):
        """Setup keyboard controls."""
        def handle_keys(evt):
            key = evt.key.lower()
            print(f"Key pressed: {key}")  # Debug print
            
            if key == 'p' or key == ' ':
                self.paused = not self.paused
                print(f"Simulation {'PAUSED' if self.paused else 'RESUMED'}")
            elif key == 't':
                self.scene.toggle_trails()
                print(f"Trails {'ON' if self.scene.show_trails else 'OFF'}")
            elif key == 'g':
                self.scene.toggle_grid()
                print(f"Grid {'ON' if self.scene.show_grid else 'OFF'}")
            elif key == 'l':
                self.scene.toggle_labels()
                print(f"Labels {'ON' if self.scene.show_labels else 'OFF'}")
            elif key == 'c':
                self.scene.clear_trails()
                print("Trails cleared")
            elif key == 'r':
                scene.camera.pos = vector(0, 80, 120)
                scene.camera.axis = vector(0, -80, -120)
                print("Camera reset")
            elif key in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                # Select body by number
                body_index = int(key) - 1
                if 0 <= body_index < len(self.system.bodies):
                    self.scene.selected_body = self.system.bodies[body_index]
                    body_name = getattr(self.system.bodies[body_index], 'name', f'Body {body_index+1}')
                    print(f"Selected: {body_name}")
            elif key == '+' or key == '=':
                self.time_scale = min(10.0, self.time_scale * 1.5)
                print(f"Time scale: {self.time_scale:.1f}x")
            elif key == '-':
                self.time_scale = max(0.1, self.time_scale / 1.5)
                print(f"Time scale: {self.time_scale:.1f}x")
            elif key == 'f':
                if self.skip_every == 1:
                    self.skip_every = 3
                    print("Performance: HIGH (skip 2/3 frames)")
                elif self.skip_every == 3:
                    self.skip_every = 1
                    print("Performance: QUALITY (all frames)")
                else:
                    self.skip_every = 2
                    print("Performance: BALANCED (skip 1/2 frames)")
            elif key == 'q':
                print("Exiting simulation...")
                sys.exit(0)
        
        def handle_mouse(evt):
            """Handle mouse clicks for body selection."""
            if evt.event == 'mousedown':
                # Get mouse position in world coordinates
                picked = scene.mouse.pick
                if picked:
                    # Find which body was clicked
                    for body, visual in self.scene.body_visuals.items():
                        if picked == visual:
                            self.scene.selected_body = body
                            body_name = getattr(body, 'name', 'Unknown')
                            print(f"Selected: {body_name}")
                            break
        
        # Bind events
        scene.bind('keydown', handle_keys)
        scene.bind('mousedown', handle_mouse)
    
    def step_physics(self):
        """Advance physics by one timestep."""
        if self.paused:
            return
            
        try:
            # Use imported physics if available
            step_system(self.system.bodies, dt=self.dt * self.time_scale)
        except:
            # Fallback physics
            self._fallback_step_physics()
        
        self.time += self.dt * self.time_scale
        self.step_count += 1
        
        # Print diagnostics
        if self.step_count % (DIAGNOSTIC_ENERGY_PRINT_EVERY * 4) == 0:
            try:
                report = diagnostics_report(self.system.bodies, self.E0, self.H0)
                print(f"Step {self.step_count:6d}, Time: {self.time:8.3f}, "
                      f"dE/E0: {report.get('dE/E0', 0):.2e}")
            except:
                print(f"Step {self.step_count:6d}, Time: {self.time:8.3f}")
    
    def _fallback_step_physics(self):
        """Simple fallback physics implementation."""
        # Calculate forces
        forces = {body: [0, 0] for body in self.system.bodies}
        
        for i, body in enumerate(self.system.bodies):
            for j, other in enumerate(self.system.bodies):
                if i == j:
                    continue
                
                # Get positions (try different possible attribute names)
                if hasattr(body, 'r'):
                    body_pos = body.r
                elif hasattr(body, 'pos'):
                    body_pos = body.pos
                elif hasattr(body, 'position'):
                    body_pos = body.position
                else:
                    continue
                
                if hasattr(other, 'r'):
                    other_pos = other.r
                elif hasattr(other, 'pos'):
                    other_pos = other.pos
                elif hasattr(other, 'position'):
                    other_pos = other.position
                else:
                    continue
                
                # Vector from body to other
                dx = other_pos[0] - body_pos[0]
                dy = other_pos[1] - body_pos[1]
                r_sq = dx*dx + dy*dy + 1e-5  # Softening
                r = math.sqrt(r_sq)
                
                # Gravitational force
                F = G * body.mass * other.mass / r_sq
                
                # Force components
                forces[body][0] += F * dx / r
                forces[body][1] += F * dy / r
        
        # Update velocities and positions
        for body in self.system.bodies:
            # Get velocity (try different possible attribute names)
            if hasattr(body, 'v'):
                vel = body.v
            elif hasattr(body, 'vel'):
                vel = body.vel
            elif hasattr(body, 'velocity'):
                vel = body.velocity
            else:
                continue
            
            # Get position
            if hasattr(body, 'r'):
                pos = body.r
            elif hasattr(body, 'pos'):
                pos = body.pos
            elif hasattr(body, 'position'):
                pos = body.position
            else:
                continue
            
            # Acceleration
            ax = forces[body][0] / body.mass
            ay = forces[body][1] / body.mass
            
            # Update velocity
            vel[0] += ax * self.dt * self.time_scale
            vel[1] += ay * self.dt * self.time_scale
            
            # Update position
            pos[0] += vel[0] * self.dt * self.time_scale
            pos[1] += vel[1] * self.dt * self.time_scale
    
    def run(self):
        """Run the interactive VPython simulation."""
        print("VPython Solar System Simulation")
        print("Controls:")
        print("  P/SPACE - Pause/Resume")
        print("  T - Toggle trails")
        print("  G - Toggle spacetime grid")
        print("  L - Toggle labels")
        print("  C - Clear trails")
        print("  R - Reset camera")
        print("  1-9 - Select body by number")
        print("  Click - Select body with mouse")
        print("  +/- - Adjust time scale")
        print("  F - Toggle performance mode")
        print("  Q - Quit")
        print("\nInitial grid update...")
        self.scene.update_grid()  # Initial grid update
        print("Starting simulation...")
        
        # Main simulation loop
        while True:
            # Control frame rate
            rate(60)  # Target 60 FPS
            
            # Step physics
            self.step_physics()
            
            # Update visuals
            self.frame_skip += 1
            if self.frame_skip >= self.skip_every:
                self.frame_skip = 0
                self.scene.update()
                
                # Update grid less frequently (every 20 steps for better performance)
                if self.step_count % 20 == 0:
                    self.scene.update_grid()
            
            # Update FPS counter
            self.fps_counter += 1
            current_time = time.time()
            if current_time - self.fps_time > self.fps_display_interval:
                fps = self.fps_counter / (current_time - self.fps_time)
                print(f"FPS: {fps:.1f}")
                self.fps_counter = 0
                self.fps_time = current_time

def main():
    """Main entry point for VPython simulation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='VPython Solar System Simulation')
    parser.add_argument('--data', type=str, default='data/solar_params.json',
                       help='Path to solar system data file')
    parser.add_argument('--test', action='store_true',
                       help='Use simple test system (Sun + Earth)')
    parser.add_argument('--fast', action='store_true',
                       help='Start in high performance mode')
    
    args = parser.parse_args()
    
    try:
        # Create simulation
        sim = VPythonSolarSimulation(data_file=args.data, use_test_system=args.test)
        
        # Set initial performance mode
        if args.fast:
            sim.skip_every = 3
            print("Starting in HIGH performance mode")
        
        # Run simulation
        sim.run()
        
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())