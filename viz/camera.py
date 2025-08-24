"""
camera.py

Camera modes (general vs focus)

Manages different camera modes and view transformations for the 3D visualization.
Supports both overview mode (showing the entire solar system) and focus mode
(following a specific body).
"""

import numpy as np
import math

__all__ = ["Camera", "CameraMode"]

class CameraMode:
    """Enumeration of camera modes."""
    OVERVIEW = "overview"
    FOCUS = "focus"
    FREE = "free"

class Camera:
    """
    3D camera for the solar system visualization.
    
    Supports multiple modes:
    - Overview: Shows the entire solar system
    - Focus: Follows a specific body
    - Free: User-controlled camera movement
    """
    
    def __init__(self, mode=CameraMode.OVERVIEW):
        """
        Initialize the camera.
        
        Parameters
        ----------
        mode : str
            Initial camera mode
        """
        self.mode = mode
        
        # Camera position and orientation
        self.position = np.array([0.0, 10.0, 20.0])  # AU
        self.target = np.array([0.0, 0.0, 0.0])      # AU
        self.up = np.array([0.0, 1.0, 0.0])
        
        # Spherical coordinates for orbit camera
        self.distance = 20.0  # AU
        self.azimuth = 0.0    # radians
        self.elevation = 0.3  # radians
        
        # Focus mode settings
        self.focus_body = None
        self.focus_distance = 5.0  # AU
        self.focus_height = 2.0    # AU above orbital plane
        
        # View parameters
        self.fov = 45.0  # degrees
        self.near = 0.01
        self.far = 1000.0
        
        # Animation
        self.smooth_factor = 0.1  # for smooth camera transitions
        
        self._update_position()
    
    def set_mode(self, mode):
        """Change camera mode."""
        self.mode = mode
        if mode == CameraMode.OVERVIEW:
            self.distance = 20.0
            self.target = np.array([0.0, 0.0, 0.0])
        elif mode == CameraMode.FOCUS and self.focus_body:
            self.distance = self.focus_distance
            self.target = self.focus_body.pos.copy()
    
    def focus_on_body(self, body):
        """
        Focus the camera on a specific body.
        
        Parameters
        ----------
        body : Body
            Body to focus on
        """
        self.focus_body = body
        self.mode = CameraMode.FOCUS
        self.target = body.pos.copy()
        
        # Adjust distance based on body size and orbital distance
        if body.name.lower() == "sun":
            self.distance = 10.0
        else:
            # Scale distance based on orbital distance
            orbital_radius = np.linalg.norm(body.pos)
            self.distance = max(0.5, min(5.0, orbital_radius * 0.3))
    
    def rotate(self, d_azimuth, d_elevation):
        """
        Rotate the camera around the target.
        
        Parameters
        ----------
        d_azimuth : float
            Change in azimuth angle (radians)
        d_elevation : float
            Change in elevation angle (radians)
        """
        self.azimuth += d_azimuth
        self.elevation += d_elevation
        
        # Clamp elevation to avoid gimbal lock
        self.elevation = np.clip(self.elevation, -math.pi/2 + 0.1, math.pi/2 - 0.1)
        
        self._update_position()
    
    def zoom(self, factor):
        """
        Zoom the camera in or out.
        
        Parameters
        ----------
        factor : float
            Zoom factor (>1 zooms in, <1 zooms out)
        """
        self.distance /= factor
        self.distance = np.clip(self.distance, 0.1, 100.0)
        self._update_position()
    
    def update(self, dt):
        """
        Update camera position (called each frame).
        
        Parameters
        ----------
        dt : float
            Time step in years
        """
        if self.mode == CameraMode.FOCUS and self.focus_body:
            # Smoothly follow the focused body
            target_pos = self.focus_body.pos.copy()
            self.target += (target_pos - self.target) * self.smooth_factor
            self._update_position()
    
    def _update_position(self):
        """Update camera position based on spherical coordinates."""
        # Convert spherical to Cartesian coordinates
        x = self.distance * math.cos(self.elevation) * math.cos(self.azimuth)
        y = self.distance * math.sin(self.elevation)
        z = self.distance * math.cos(self.elevation) * math.sin(self.azimuth)
        
        self.position = self.target + np.array([x, y, z])
    
    def get_view_matrix(self):
        """
        Get the view matrix for rendering.
        
        Returns
        -------
        np.ndarray
            4x4 view matrix
        """
        # Look-at matrix calculation
        forward = self.target - self.position
        forward = forward / np.linalg.norm(forward)
        
        right = np.cross(forward, self.up)
        right = right / np.linalg.norm(right)
        
        up = np.cross(right, forward)
        
        # Create view matrix
        view = np.eye(4)
        view[0, :3] = right
        view[1, :3] = up
        view[2, :3] = -forward
        view[:3, 3] = -np.array([
            np.dot(right, self.position),
            np.dot(up, self.position),
            np.dot(-forward, self.position)
        ])
        
        return view
    
    def get_projection_matrix(self, aspect_ratio):
        """
        Get the projection matrix for rendering.
        
        Parameters
        ----------
        aspect_ratio : float
            Screen aspect ratio (width/height)
            
        Returns
        -------
        np.ndarray
            4x4 projection matrix
        """
        fov_rad = math.radians(self.fov)
        f = 1.0 / math.tan(fov_rad / 2.0)
        
        proj = np.zeros((4, 4))
        proj[0, 0] = f / aspect_ratio
        proj[1, 1] = f
        proj[2, 2] = (self.far + self.near) / (self.near - self.far)
        proj[2, 3] = (2 * self.far * self.near) / (self.near - self.far)
        proj[3, 2] = -1
        
        return proj
    
    def world_to_screen(self, world_pos, screen_width=800, screen_height=600):
        """
        Convert world coordinates to screen coordinates.
        
        Parameters
        ----------
        world_pos : array_like
            World position [x, y, z]
        screen_width, screen_height : int
            Screen dimensions
            
        Returns
        -------
        tuple or None
            (screen_x, screen_y) or None if behind camera
        """
        # Transform to camera space
        view = self.get_view_matrix()
        proj = self.get_projection_matrix(screen_width / screen_height)
        
        # Convert to homogeneous coordinates
        world_pos_h = np.append(world_pos, 1.0)
        
        # Apply transformations
        view_pos = view @ world_pos_h
        if view_pos[2] > 0:  # Behind camera
            return None
        
        clip_pos = proj @ view_pos
        if clip_pos[3] == 0:
            return None
        
        # Perspective divide
        ndc = clip_pos[:3] / clip_pos[3]
        
        # Convert to screen coordinates
        screen_x = (ndc[0] + 1) * 0.5 * screen_width
        screen_y = (1 - ndc[1]) * 0.5 * screen_height
        
        return (screen_x, screen_y)
    
    def screen_to_world(self, screen_x, screen_y, screen_width=800, screen_height=600, depth=0.0):
        """
        Convert screen coordinates to world coordinates.
        
        Parameters
        ----------
        screen_x, screen_y : float
            Screen coordinates
        screen_width, screen_height : int
            Screen dimensions
        depth : float
            Depth in world space (distance from camera)
            
        Returns
        -------
        np.ndarray
            World position [x, y, z]
        """
        # Convert screen to normalized device coordinates
        ndc_x = (2.0 * screen_x / screen_width) - 1.0
        ndc_y = 1.0 - (2.0 * screen_y / screen_height)
        
        # Create ray from camera through screen point
        view = self.get_view_matrix()
        proj = self.get_projection_matrix(screen_width / screen_height)
        
        # Inverse transformations
        inv_proj = np.linalg.inv(proj)
        inv_view = np.linalg.inv(view)
        
        # Ray in clip space
        clip_pos = np.array([ndc_x, ndc_y, -1.0, 1.0])
        
        # Transform to world space
        view_pos = inv_proj @ clip_pos
        view_pos /= view_pos[3]
        
        world_pos = inv_view @ view_pos
        
        # Calculate world position at specified depth
        ray_dir = world_pos[:3] - self.position
        ray_dir = ray_dir / np.linalg.norm(ray_dir)
        
        return self.position + ray_dir * depth
    
    def get_scale_factor(self):
        """Get current scale factor for UI elements."""
        return 1.0 / self.distance
    
    def reset(self):
        """Reset camera to default position."""
        self.distance = 20.0
        self.azimuth = 0.0
        self.elevation = 0.3
        self.target = np.array([0.0, 0.0, 0.0])
        self.mode = CameraMode.OVERVIEW
        self.focus_body = None
        self._update_position()

