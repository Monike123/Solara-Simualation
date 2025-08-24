"""
scene.py

Rendering setup

Manages the 3D scene rendering including bodies, trails, potential surfaces,
and coordinate systems. This is the main rendering coordinator.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from scipy.ndimage import gaussian_filter
import matplotlib.patches as patches

from .surface import PotentialSurface
from .camera import Camera, CameraMode
from .ui import UIManager
from constants import VISUAL_RADIUS_SCALE, TRAIL_DECIMATE

__all__ = ["Scene", "MatplotlibRenderer"]

RADIUS_SCALE_PLANETS = 20   # makes planets visible
RADIUS_SCALE_SUN = 15        # keeps Sun large but not absurd

def get_display_radius(body):
    """Return scaled radius for visualization only."""
    if body.name.lower() == "sun":
        return body.radius * RADIUS_SCALE_SUN
    else:
        return body.radius * RADIUS_SCALE_PLANETS
    


class Scene:
    """
    Main scene manager for the solar system visualization.
    
    Coordinates all rendering components including bodies, trails,
    potential surfaces, and user interface elements.
    """
    
    def __init__(self, system, renderer_type="matplotlib"):
        """
        Initialize the scene.
        
        Parameters
        ----------
        system : SolarSystem
            Solar system to render
        renderer_type : str
            Type of renderer to use ("matplotlib", "opengl", etc.)
        """
        self.system = system
        self.camera = Camera()
        self.ui = UIManager()
        
        # Rendering components
        self.potential_surface = PotentialSurface()
        
        # Rendering settings
        self.show_trails = True
        self.show_surface = True
        self.show_axes = True
        self.show_labels = True
        
        # Create renderer
        if renderer_type == "matplotlib":
            self.renderer = MatplotlibRenderer(self)
        else:
            raise ValueError(f"Unknown renderer type: {renderer_type}")
        
        # Animation state
        self.paused = False
        self.time_scale = 1.0
        self.frame_count = 0
    
    def update(self, dt):
        """
        Update the scene for one frame.
        
        Parameters
        ----------
        dt : float
            Time step in years
        """
        # Update camera
        self.camera.update(dt)
        
        # Update UI
        self.ui.update(dt)
        
        # Update potential surface periodically
        if self.frame_count % 15 == 0:  # Update every 10 frames
            self.potential_surface.update(self.system.bodies)
        
        # Add trail points
        if self.frame_count % TRAIL_DECIMATE == 0:
            self.system.add_trail_points()
        
        self.frame_count += 1
    
    def render(self):
        """Render the current frame."""
        self.renderer.render()
    
    def handle_mouse_click(self, x, y):
        """Handle mouse click events."""
        return self.ui.handle_mouse_click(x, y, self.system.bodies, self.camera)
    
    def handle_key_press(self, key):
        """Handle keyboard input."""
        result = self.ui.handle_key_press(key, self.system, self.camera)
        
        if result == 'toggle_pause':
            self.paused = not self.paused
            return self.paused
        
        return None
    
    def toggle_trails(self):
        """Toggle trail visibility."""
        self.show_trails = not self.show_trails
        return self.show_trails
    
    def toggle_surface(self):
        """Toggle surface visibility."""
        self.show_surface = not self.show_surface
        return self.show_surface
    
    def set_camera_mode(self, mode):
        """Set camera mode."""
        self.camera.set_mode(mode)

class MatplotlibRenderer:
    """
    Matplotlib-based renderer for the solar system visualization.
    
    Provides a simple but functional 3D visualization using matplotlib.
    """
    
    def __init__(self, scene):
        """
        Initialize the matplotlib renderer.
        
        Parameters
        ----------
        scene : Scene
            Scene to render
        """
        self.scene = scene
        
        # Create figure and 3D axis
        self.fig = plt.figure(figsize=(12, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor("black")
        self.fig.patch.set_facecolor("black")
        self.ax.set_xlabel("X (AU)", color="white")
        self.ax.set_ylabel("Y (AU)", color="white")
        self.ax.set_zlabel("Z (AU)", color="white")
        self.ax.set_xlabel("X [AU]", color="white")
        self.ax.set_ylabel("Y [AU]", color="white")
        self.ax.set_zlabel("Potential", color="white")
        self.ax.tick_params(colors="white")
        
        # Set up the plot
        self._setup_plot()
        
        # Store plot elements for updating
        self.body_plots = {}
        self.trail_plots = {}
        self.surface_plot = None
        
        # Text elements
        self.info_text = None
        self.control_text = None

        #max_range = 5  # adjust as needed
        #self.ax.set_xlim(-max_range, max_range)
        #self.ax.set_ylim(-max_range, max_range)
        #self.ax.set_zlim(-max_range, max_range)

        self.ax.view_init(elev=20, azim=30)
        self.ax.dist = 8
    
    def _setup_plot(self):
        """Set up the 3D plot appearance."""
        self.ax.set_xlabel('X [AU]', color="white")
        self.ax.set_ylabel('Y [AU]', color="white")
        self.ax.set_zlabel('Z [AU]', color="white")

        self.ax.tick_params(colors="white")
        
        # Set equal aspect ratio
        self.ax.set_box_aspect([1,1,1])
        
        # Set initial view limits
        self._update_view_limits()

        for axis in [self.ax.xaxis, self.ax.yaxis, self.ax.zaxis]:
            axis.label.set_color("white")
            axis.set_tick_params(colors="white")
        
        # Style
        self.ax.set_facecolor("black")
        self.fig.patch.set_facecolor("black")
        self.ax.grid(True, alpha=0.3)
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False

    
    def _update_view_limits(self):
        """Update view limits based on camera and bodies."""
        if self.scene.camera.mode == CameraMode.FOCUS and self.scene.camera.focus_body:
            # Focus mode: tight view around selected body
            center = self.scene.camera.focus_body.pos
            radius = self.scene.camera.distance * 0.5
            
            self.ax.set_xlim(center[0] - radius, center[0] + radius)
            self.ax.set_ylim(center[1] - radius, center[1] + radius)
            self.ax.set_zlim(center[2] - radius, center[2] + radius)
        else:
            # Overview mode: show entire system
            max_dist = 0
            for body in self.scene.system.bodies:
                dist = np.linalg.norm(body.pos)
                max_dist = max(max_dist, dist)
            
            limit = max(max_dist * 1.2, 10.0)
            self.ax.set_xlim(-limit, limit)
            self.ax.set_ylim(-limit, limit)
            self.ax.set_zlim(-limit, limit)
    
    def render(self):
        """Render the current frame."""
        # Clear previous frame
        self.ax.clear()
        self._setup_plot()
        
        # Update view limits
        self._update_view_limits()
        
        # Render potential surface
        if self.scene.show_surface:
            self._render_surface()
        
        # Render bodies
        self._render_bodies()
        
        # Render trails
        if self.scene.show_trails:
            self._render_trails()
        
        # Render coordinate axes
        if self.scene.show_axes:
            self._render_axes()
        
        # Render UI elements
        self.scene.ui.render(self)
        
        # Update display
        plt.draw()
    
    def _render_bodies(self):
        """Render all celestial bodies."""
        for body in self.scene.system.bodies:
            # Calculate visual radius
            visual_radius = get_display_radius(body)
            self.ax.scatter(
            body.pos[0], body.pos[1], body.pos[2],
            s=max(20, visual_radius * 10000),  # scatter size is in points^2
            c=[body.color],
            alpha=0.9,
            edgecolors='white' if body == self.scene.ui.selected_body else 'none',
            linewidth=2
            )

            # Add label above the scaled "surface"
            if self.scene.show_labels:
                self.ax.text(
                    body.pos[0], body.pos[1], body.pos[2] + visual_radius,
                    body.name,
                    fontsize=8,
                    color='white',
                    ha='center'
                )

    
    def _render_trails(self):
        """Render orbital trails."""
        for body in self.scene.system.bodies:
            if len(body.trail) > 1:
                trail = np.array(body.trail)
                trail = trail[-300:]
                self.ax.plot(
                    trail[:, 0], trail[:, 1], trail[:, 2],
                    color=body.color,
                    alpha=0.6,
                    linewidth=1
                )
    
    def _render_surface(self):
        """Render gravitational potential surface."""
        if self.scene.potential_surface.Y is not None:
            X, Y, Z = self.scene.potential_surface.get_wireframe_data(stride=3)
            self.ax.plot_wireframe( X, Z, Y, alpha=0.2, color='cyan', linewidth=0.5 )
        
    
    def _render_axes(self):
        """Render coordinate system axes."""
        # Origin marker
        self.ax.scatter([0], [0], [0], c='white', s=50, marker='+')
        
        # Axis lines (small)
        axis_length = 2.0
        self.ax.plot([0, axis_length], [0, 0], [0, 0], 'r-', alpha=0.5, linewidth=2)  # X
        self.ax.plot([0, 0], [0, axis_length], [0, 0], 'g-', alpha=0.5, linewidth=2)  # Y
        self.ax.plot([0, 0], [0, 0], [0, axis_length], 'b-', alpha=0.5, linewidth=2)  # Z
    

    
    def render_text_panel(self, position, lines):
        """Render a text panel (for UI components)."""
        text = '\n'.join(lines)
        x, y = position
        
        # Convert to normalized coordinates
        x_norm = x / self.fig.get_size_inches()[0] / self.fig.dpi
        y_norm = 1.0 - (y / self.fig.get_size_inches()[1] / self.fig.dpi)
        
        self.ax.text2D(x_norm, y_norm, text, transform=self.ax.transAxes,
                      fontsize=8, color='white', verticalalignment='top',
                      bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
    
    def show(self):
        """Show the plot window."""
        plt.show()
    
    def save_frame(self, filename):
        """Save current frame to file."""
        self.fig.savefig(filename, facecolor='black', dpi=150)
