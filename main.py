#!/usr/bin/env python3
"""
main.py - OPTIMIZED VERSION

Entry point: assemble physics + viz + run loop

This is the main entry point for the solar system simulation.
It assembles the physics engine, visualization system, and runs
the main simulation loop.
"""

import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Import our modules
from model.system import load_solar_system, create_test_system
from physics.nbody import step_system
from physics.diagnostics import total_energy, total_angular_momentum, diagnostics_report
from viz.scene import Scene
from constants import DT, DIAGNOSTIC_ENERGY_PRINT_EVERY
from viz.ui import InfoPanel, ControlPanel

class SolarSimulation:
    """
    Main simulation class that coordinates physics and visualization.
    """
    
    def __init__(self, data_file=None, use_test_system=False):
        """
        Initialize the simulation.
        
        Parameters
        ----------
        data_file : str, optional
            Path to solar system data file. Defaults to "data/solar_params.json"
        use_test_system : bool
            If True, use a simple test system instead of full solar system
        """
        # Load solar system
        if use_test_system:
            print("Loading test system (Sun + Earth)...")
            self.system = create_test_system()
        else:
            data_file = data_file or "data/solar_params.json"
            print(f"Loading solar system from {data_file}...")
            self.system = load_solar_system(data_file)
        
        print(f"Loaded {len(self.system.bodies)} bodies:")
        for body in self.system.bodies:
            print(f"  {body}")
        
        # Initialize physics
        self.time = 0.0
        self.step_count = 0
        self.dt = DT
        
        # Store initial conditions for diagnostics
        self.E0 = total_energy(self.system.bodies)
        self.H0 = total_angular_momentum(self.system.bodies)
        
        print(f"Initial energy: {self.E0:.6e}")
        print(f"Initial angular momentum: {np.linalg.norm(self.H0):.6e}")
        
        # Initialize visualization
        self.scene = Scene(self.system)
        
        # Animation control
        self.paused = False
        self.time_scale = 1.0
        
        # Performance tracking - OPTIMIZED
        self.last_time = time.time()
        self.fps_counter = 0
        self.fps_time = time.time()
        self.fps_display_interval = 2.0  # Show FPS every 2 seconds instead of 1
        
        # Skip frames for better performance
        self.frame_skip = 0
        self.skip_every = 2  # Skip every 2nd frame for rendering (but not physics)
    
    def step_physics(self):
        """Advance physics by one timestep."""
        if not self.paused:
            step_system(self.system.bodies, dt=self.dt * self.time_scale)
            self.time += self.dt * self.time_scale
            self.step_count += 1
            
            # Print diagnostics less frequently for better performance
            if self.step_count % (DIAGNOSTIC_ENERGY_PRINT_EVERY * 2) == 0:  # Half frequency
                report = diagnostics_report(self.system.bodies, self.E0, self.H0)
                print(f"Step {self.step_count:6d}, Time: {self.time:8.3f} yr, "
                      f"dE/E0: {report.get('dE/E0', 0):.2e}, "
                      f"|dH|/|H0|: {report.get('|dH|/|H0|', 0):.2e}")
    
    def update_frame(self, frame):
        """Update function for matplotlib animation - OPTIMIZED."""
        # Always step physics (important for accuracy)
        self.step_physics()
        
        # Always update scene (needed for trails, etc.)
        self.scene.update(self.dt)
        
        # Frame skipping for rendering only
        self.frame_skip += 1
        if self.frame_skip >= self.skip_every:
            self.frame_skip = 0
            # Only render every skip_every frames
            self.scene.render()
        
        # Update FPS counter less frequently
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.fps_time > self.fps_display_interval:
            fps = self.fps_counter / (current_time - self.fps_time)
            print(f"FPS: {fps:.1f})")
            self.fps_counter = 0
            self.fps_time = current_time
    
    def on_key_press(self, event):
        """Handle keyboard input - OPTIMIZED."""
        if event.key == ' ':
            self.paused = not self.paused
            print(f"Simulation {'PAUSED' if self.paused else 'RESUMED'}")
        elif event.key == 'r':
            self.scene.camera.reset()
            print("Camera reset")
        elif event.key == 'c':
            self.system.clear_all_trails()
            print("Trails cleared")
        elif event.key == 't':
            self.scene.toggle_trails()
            print(f"Trails {'ON' if self.scene.show_trails else 'OFF'}")
        elif event.key == 's':
            self.scene.toggle_surface()
            print(f"Surface {'ON' if self.scene.show_surface else 'OFF'}")
        elif event.key == 'f':
            if self.scene.ui.selected_body:
                self.scene.camera.focus_on_body(self.scene.ui.selected_body)
                print(f"Focusing on {self.scene.ui.selected_body.name}")
        elif event.key in '12345678':
            # Select planet by number
            planet_index = int(event.key) - 1
            if 0 <= planet_index < len(self.system.planets):
                body = self.system.planets[planet_index]
                self.scene.ui.selected_body = body
                self.scene.ui.info_panel.set_body(body)
                self.scene.camera.focus_on_body(body)
                print(f"Selected {body.name}")
        elif event.key == '+' or event.key == '=':
            self.time_scale = min(10.0, self.time_scale * 1.5)
            print(f"Time scale: {self.time_scale:.1f}x")
        elif event.key == '-':
            self.time_scale = max(0.1, self.time_scale / 1.5)
            print(f"Time scale: {self.time_scale:.1f}x")
        elif event.key == 'p':
            # Performance toggle
            if self.skip_every == 1:
                self.skip_every = 3  # More aggressive frame skipping
                print("Performance mode: HIGH (skip 2/3 render frames)")
            elif self.skip_every == 3:
                self.skip_every = 1  # No frame skipping
                print("Performance mode: QUALITY (render all frames)")
            else:
                self.skip_every = 2  # Default
                print("Performance mode: BALANCED (skip 1/2 render frames)")
        elif event.key == 'q' or event.key == 'escape':
            print("Exiting simulation...")
            plt.close('all')
            sys.exit(0)

    def on_scroll(self, event):
        """Handle mouse wheel zoom - OPTIMIZED."""
        if event.button == 'up':
            self.scene.camera.zoom(1.1)   # zoom in
        elif event.button == 'down':
            self.scene.camera.zoom(0.9)   # zoom out
        # Force immediate render for smooth zoom
        self.scene.render()
        plt.draw()

    def on_mouse_press(self, event):
        """Handle mouse click."""
        if event.inaxes == self.scene.renderer.ax:
            selected = self.scene.handle_mouse_click(event.xdata or 0, event.ydata or 0)
            if selected:
                print(f"Selected {selected.name}")
    
    def run_interactive(self):
        # Set matplotlib performance options
        plt.rcParams['path.simplify'] = True
        plt.rcParams['path.simplify_threshold'] = 0.1
        plt.rcParams['agg.path.chunksize'] = 10000
        
        # Set up event handlers
        self.scene.renderer.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.scene.renderer.fig.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.scene.renderer.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        
        print("Controls:")
        print("  SPACE - Pause/Resume")
        print("  P - Toggle performance mode")
        print("  S - Toggle gravity surface")
        print("  T - Toggle trails")
        print("  +/- - Adjust time scale")
        print("  Mouse wheel - Zoom")
        
        # Create animation with optimized settings
        self.animation = FuncAnimation(
            self.scene.renderer.fig,
            self.update_frame,
            interval=80,  # ~12 FPS (increased from 50)
            blit=False,
            cache_frame_data=False,
            repeat=True
        )
        
        # Show the plot
        plt.show()
    
    def run_headless(self, num_steps=1000, save_interval=100):
        """
        Run simulation without visualization (for testing/benchmarking).
        
        Parameters
        ----------
        num_steps : int
            Number of simulation steps to run
        save_interval : int
            Save diagnostics every N steps
        """
        print(f"Running headless simulation for {num_steps} steps...")
        
        diagnostics = []
        
        start_time = time.time()
        for step in range(num_steps):
            self.step_physics()
            
            if step % save_interval == 0:
                report = diagnostics_report(self.system.bodies, self.E0, self.H0)
                diagnostics.append({
                    'step': step,
                    'time': self.time,
                    'energy': report['energy'],
                    'dE/E0': report.get('dE/E0', 0),
                    '|dH|/|H0|': report.get('|dH|/|H0|', 0)
                })
                
                if step % (save_interval * 10) == 0:
                    print(f"Step {step:6d}/{num_steps}, Time: {self.time:8.3f} yr")
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"Simulation completed in {elapsed:.2f} seconds")
        print(f"Performance: {num_steps/elapsed:.1f} steps/second")
        
        # Final diagnostics
        final_report = diagnostics_report(self.system.bodies, self.E0, self.H0)
        print(f"Final energy drift: {final_report.get('dE/E0', 0):.2e}")
        print(f"Final momentum drift: {final_report.get('|dH|/|H0|', 0):.2e}")
        
        return diagnostics

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Solar System N-body Simulation')
    parser.add_argument('--data', type=str, default='data/solar_params.json',
                       help='Path to solar system data file')
    parser.add_argument('--test', action='store_true',
                       help='Use simple test system (Sun + Earth)')
    parser.add_argument('--headless', action='store_true',
                       help='Run without visualization')
    parser.add_argument('--steps', type=int, default=1000,
                       help='Number of steps for headless mode')
    parser.add_argument('--fast', action='store_true',
                       help='Start in high performance mode')
    
    args = parser.parse_args()
    
    try:
        # Create simulation
        sim = SolarSimulation(data_file=args.data, use_test_system=args.test)
        
        # Set initial performance mode
        if args.fast:
            sim.skip_every = 3
            print("Starting in HIGH performance mode")
        
        if args.headless:
            # Run headless
            sim.run_headless(num_steps=args.steps)
        else:
            # Run interactive
            sim.run_interactive()
            
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