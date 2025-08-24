"""
ui.py

Clicks, info panels

Handles user interface elements including mouse interactions,
information displays, and control panels for the simulation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

__all__ = ["UIManager", "InfoPanel", "ControlPanel"]

class UIManager:
    """
    Manages all user interface interactions and displays.
    
    Handles mouse clicks, keyboard input, and coordinates between
    different UI components.
    """
    
    def __init__(self):
        self.info_panel = InfoPanel()
        self.control_panel = ControlPanel()
        self.selected_body = None
        self.mouse_pos = (0, 0)
        self.is_dragging = False
        
    def handle_mouse_click(self, x, y, bodies, camera):
        """
        Handle mouse click events.
        
        Parameters
        ----------
        x, y : float
            Mouse coordinates (screen space)
        bodies : list of Body
            All bodies in the simulation
        camera : Camera
            Current camera object for coordinate transformations
            
        Returns
        -------
        Body or None
            Selected body if any, None otherwise
        """
        # Convert screen coordinates to world coordinates
        world_pos = camera.screen_to_world(x, y)
        
        # Find the closest body to the click
        closest_body = None
        min_distance = float('inf')
        
        for body in bodies:
            # Project body position to screen
            screen_pos = camera.world_to_screen(body.pos)
            if screen_pos is None:
                continue
                
            # Calculate distance in screen space
            dx = x - screen_pos[0]
            dy = y - screen_pos[1]
            distance = np.sqrt(dx**2 + dy**2)
            
            # Consider body size for selection (larger bodies easier to click)
            selection_radius = max(10, body.radius * camera.get_scale_factor())
            
            if distance < selection_radius and distance < min_distance:
                closest_body = body
                min_distance = distance
        
        self.selected_body = closest_body
        if closest_body:
            self.info_panel.set_body(closest_body)
        
        return closest_body
    
    def handle_mouse_drag(self, dx, dy, camera):
        """
        Handle mouse drag events for camera control.
        
        Parameters
        ----------
        dx, dy : float
            Mouse movement delta
        camera : Camera
            Camera to update
        """
        if self.is_dragging:
            camera.rotate(dx * 0.01, dy * 0.01)
    
    def handle_key_press(self, key, system, camera):
        """
        Handle keyboard input.
        
        Parameters
        ----------
        key : str
            Key that was pressed
        system : SolarSystem
            Solar system to control
        camera : Camera
            Camera to control
        """
        if key == 'r':
            # Reset camera
            camera.reset()
        elif key == 'c':
            # Clear trails
            system.clear_all_trails()
        elif key == 'space':
            # Toggle pause (handled by main loop)
            return 'toggle_pause'
        elif key == 'f':
            # Focus on selected body
            if self.selected_body:
                camera.focus_on_body(self.selected_body)
        elif key.isdigit():
            # Select planet by number (1-8)
            planet_index = int(key) - 1
            if 0 <= planet_index < len(system.planets):
                self.selected_body = system.planets[planet_index]
                self.info_panel.set_body(self.selected_body)
                camera.focus_on_body(self.selected_body)
        
        return None
    
    def update(self, dt):
        """Update UI components."""
        self.info_panel.update(dt)
        self.control_panel.update(dt)
    
    def render(self, renderer):
        """Render UI components."""
        self.info_panel.render(renderer)
        self.control_panel.render(renderer)

class InfoPanel:
    """
    Displays information about the selected body and simulation state.
    """
    
    def __init__(self):
        self.body = None
        self.visible = True
        self.position = (10, 10)  # Screen position
        
    def set_body(self, body):
        """Set the body to display information for."""
        self.body = body
        self.visible = True
    
    def hide(self):
        """Hide the info panel."""
        self.visible = False
    
    def update(self, dt):
        """Update panel contents."""
        pass
    
    def render(self, renderer):
        """Render the info panel."""
        if not self.visible or not self.body:
            return
        
        # Prepare text content
        lines = [
            f"Name: {self.body.name}",
            f"Mass: {self.body.mass:.3e} M☉",
            f"Radius: {self.body.radius:.3e} AU",
            f"Position: ({self.body.pos[0]:.3f}, {self.body.pos[1]:.3f}, {self.body.pos[2]:.3f}) AU",
            f"Velocity: ({self.body.vel[0]:.3f}, {self.body.vel[1]:.3f}, {self.body.vel[2]:.3f}) AU/yr",
            f"Speed: {np.linalg.norm(self.body.vel):.3f} AU/yr"
        ]
        
        # Calculate orbital elements if not the Sun
        if self.body.name.lower() != "sun":
            try:
                from physics.osculating import osculating_elements
                from constants import G
                
                # Assume Sun is at origin for orbital elements calculation
                elements = osculating_elements(self.body.pos, self.body.vel, mu=G)
                
                lines.extend([
                    "",
                    "Orbital Elements:",
                    f"Semi-major axis: {elements['a']:.3f} AU",
                    f"Eccentricity: {elements['e']:.3f}",
                    f"Inclination: {np.degrees(elements['i']):.1f}°",
                    f"Period: {elements['period']:.1f} years" if elements['period'] else "Period: Unbound"
                ])
            except:
                pass
        
        # Render text (implementation depends on rendering backend)
        renderer.render_text_panel(self.position, lines)

class ControlPanel:
    """
    Displays simulation controls and status.
    """
    
    def __init__(self):
        self.visible = True
        self.position = (10, 200)  # Screen position
        self.paused = False
        self.time_scale = 1.0
        self.show_trails = True
        self.show_surface = True
        
    def update(self, dt):
        """Update control panel."""
        pass
    
    def render(self, renderer):
        """Render the control panel."""
        if not self.visible:
            return
        
        lines = [
            "Controls:",
            "Mouse: Click to select body",
            "Drag: Rotate camera",
            "R: Reset camera",
            "C: Clear trails",
            "F: Focus on selected",
            "Space: Pause/Resume",
            "1-8: Select planet",
            "+/-: Adjust time scale",
            "",
            f"Status: {'PAUSED' if self.paused else 'RUNNING'}",
            f"Time scale: {self.time_scale:.1f}x",
            f"Trails: {'ON' if self.show_trails else 'OFF'}",
            f"Surface: {'ON' if self.show_surface else 'OFF'}"
        ]

        renderer.fig.text(
        0.02, 0.15,          # ⬅ shift higher if it overlaps control panel
        "\n".join(lines),
        ha="left", va="bottom",
        fontsize=8, color="black",
        bbox=dict(facecolor="white", alpha=0.5, boxstyle="round,pad=0.5")
        )
    
    def toggle_pause(self):
        """Toggle pause state."""
        self.paused = not self.paused
        return self.paused
    
    def set_time_scale(self, scale):
        """Set simulation time scale."""
        self.time_scale = max(0.1, min(10.0, scale))
    
    def toggle_trails(self):
        """Toggle trail visibility."""
        self.show_trails = not self.show_trails
        return self.show_trails
    
    def toggle_surface(self):
        """Toggle surface visibility."""
        self.show_surface = not self.show_surface
        return self.show_surface

