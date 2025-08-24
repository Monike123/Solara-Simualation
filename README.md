# Solar System N-Body Simulation

# 🌌 Solar System N-Body Simulation

![Header Image](<img width="1536" height="1024" alt="ChatGPT Image Aug 24, 2025, 10_29_57 PM" src="https://github.com/user-attachments/assets/5b224246-098e-4487-9470-12eb42a7a597" />)

A comprehensive solar system simulation implementing Newtonian gravity with optional post-Newtonian relativistic corrections. Features real-time 3D visualization, orbital mechanics calculations, and energy/momentum conservation monitoring.  

📄 [Read Documentation (PDF)](docs/simulation_docs.pdf) | 📝 [Read Documentation (Word)]([docs/simulation_docs.docx](https://github.com/Monike123/Solara-Simualation/blob/main/Solar_System_Simulation_Project_Enriched.docx))

---

## 📑 Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Interactive Controls](#interactive-controls)
  - [Configuration](#configuration)
- [Physics Implementation](#physics-implementation)
  - [Units](#units)
  - [Integration Method](#integration-method)
  - [Relativistic Corrections](#relativistic-corrections)
- [Testing](#testing)
- [Performance](#performance)
- [Accuracy](#accuracy)
- [Customization](#customization)
- [Known Limitations](#known-limitations)
- [Future Enhancements](#future-enhancements)
- [References](#references)
- [License](#license)

---

## Features

- **Accurate Physics**: Implements Newtonian gravity with velocity-Verlet integration  
- **Relativistic Corrections**: Optional 1PN (post-Newtonian) corrections for Mercury's perihelion precession  
- **Real-time Visualization**: Interactive 3D matplotlib-based visualization with adjustable camera controls  
- **Orbital Analysis**: Calculate and display osculating orbital elements (semi-major axis, eccentricity, inclination, etc.)  
- **Conservation Monitoring**: Track energy and angular momentum conservation over time with diagnostics  
- **Flexible Configuration**: JSON-based planetary parameter configuration for easy customization  
- **Labeling & Tracking**: Dynamically updated body labels for each planet, moon, or object in the system  
- **Scalable System**: Extendable to include moons, asteroids, comets, and custom celestial bodies  
- **Orbit Trails**: Option to display trajectory lines for visualizing orbital paths  
- **Performance Optimized**: Efficient handling of N-body calculations with support for large simulations  
- **Educational Use**: Designed for both research and teaching, making orbital mechanics concepts more intuitive  

---

## Project Structure

```
solar_sim/
├── constants.py        # Physical constants and simulation parameters
├── main.py           # Main entry point
├── test_simulation.py
├── vpy_simulation.py
├── physics/           # Core physics engine
│   ├── elements.py    # Orbital elements ↔ state vector conversion
│   ├── nbody.py       # N-body gravity and integrator
│   ├── pn1.py         # Post-Newtonian corrections
│   ├── osculating.py  # Instantaneous orbital element calculation
│   └── diagnostics.py # Energy/momentum conservation checks
├── model/             # Data structures
│   ├── body.py        # Body class (mass, position, velocity, etc.)
│   └── system.py      # Solar system loading and management
├── viz/               # Visualization system
│   ├── scene.py       # Main rendering coordinator
│   ├── camera.py      # Camera controls and modes
│   ├── surface.py     # Gravitational potential surface
│   └── ui.py          # User interface and controls
├── data/
│   └── solar_params.json # Planetary parameters
```

## Installation

### Prerequisites
- Python 3.7+  
- NumPy  
- Matplotlib  

### Setup
```bash
git clone https://github.com/your-username/solar_sim.git
cd solar_sim
pip install numpy matplotlib

### Setup

1. Clone or download the project files
2. Install dependencies:
   ```bash
   pip install numpy matplotlib vpython
   ```

## Usage

### Basic Usage

Run the full solar system 3d grid simulation:
```bash
python main.py
```
<img width="1919" height="1079" alt="Screenshot 2025-08-24 134447" src="https://github.com/user-attachments/assets/f8e3cef0-d087-4f82-bcd1-6ff23b2bff0c" />


Another Render engine (web based) for a unique View:
```bash
python vpy_simulation.py
```
<img width="1919" height="1036" alt="Screenshot 2025-08-24 134351" src="https://github.com/user-attachments/assets/91d642af-cd15-4190-b32e-8bae9ad20a1f" />


Run with a simple test system (Sun + Earth):
```bash
python main.py --test
```
<img width="675" height="613" alt="Screenshot 2025-08-24 134421" src="https://github.com/user-attachments/assets/99bd9ae8-ae89-4b62-8414-4d2c65d8ab75" />


Run headless (no visualization) for performance testing:
```bash
python main.py --headless --steps 1000
```

## Interactive Controls

When running the interactive visualization:

- **Mouse**: Click to select celestial bodies
- **Mouse Drag**: Rotate camera view
- **Space**: Pause/Resume simulation
- **R**: Reset camera to default position
- **C**: Clear orbital trails
- **T**: Toggle trail visibility
- **S**: Toggle gravitational potential surface
- **F**: Focus camera on selected body
- **1-8**: Select planets by number (1=Mercury, 2=Venus, etc.)
- **+/-**: Increase/decrease simulation time scale
- **Q**: Quit simulation

<img width="204" height="242" alt="controls" src="https://github.com/user-attachments/assets/968a6c6f-db50-4245-9dd9-ef5e59ba4e86" />


### Configuration

Edit `data/solar_params.json` to modify planetary parameters:

```json
{
  "sun": {
    "name": "Sun",
    "mass": 1.0,
    "radius": 0.00465,
    "color": [1.0, 1.0, 0.0]
  },
  "planets": [
    {
      "name": "Earth",
      "mass": 3.003e-6,
      "radius": 4.26e-5,
      "a": 1.000,
      "e": 0.017,
      "i": 0.000,
      "Omega": -0.196,
      "omega": 1.796,
      "M": 0.0,
      "color": [0.2, 0.4, 1.0]
    }
  ]
}
```

## Physics Implementation

### Units

The simulation uses astronomical units for consistency:
- **Length**: Astronomical Units (AU)
- **Time**: Julian years (365.25 days)
- **Mass**: Solar masses (M☉)
- **Gravitational constant**: G = 4π² (AU³/yr²/M☉)

### Integration Method

Uses velocity-Verlet integration for excellent long-term energy conservation:

1. Update velocities by half-step: `v += 0.5 * a * dt`
2. Update positions: `r += v * dt`
3. Compute new accelerations
4. Complete velocity update: `v += 0.5 * a_new * dt`

### Relativistic Corrections

Optional 1PN (first post-Newtonian) corrections capture general relativistic effects:
- Mercury's perihelion precession
- Time dilation effects
- Gravitational redshift corrections

Enable with `ENABLE_1PN_DEFAULT = True` in `constants.py`.

## Testing

Run the test suite to verify correct operation:

```bash
python test_simulation.py
```
<img width="675" height="613" alt="Screenshot 2025-08-24 134421" src="https://github.com/user-attachments/assets/b411695b-1534-40ea-8d9b-9b77987e16e0" />



Tests include:
- Energy conservation verification
- Orbital element calculations
- Full system loading and simulation
- Visualization component initialization

## Performance

Typical performance on modern hardware:
- **2-body system**: ~30,000 steps/second
- **9-body solar system**: ~3,000 steps/second
- **Real-time visualization**: ~20 FPS

## Accuracy

The simulation achieves excellent accuracy for solar system dynamics:
- Energy conservation: < 10⁻⁵ relative error over 100 time steps
- Angular momentum conservation: < 10⁻⁹ relative error
- Orbital period accuracy: < 0.1% for major planets

## Customization

### Adding New Bodies

1. Add parameters to `data/solar_params.json`
2. Optionally create a specific module in `planets/`
3. Restart the simulation

### Modifying Physics

- **Time step**: Adjust `DT` in `constants.py`
- **Softening**: Modify `EPS_ACCEL` for collision handling
- **Relativistic effects**: Toggle `ENABLE_1PN_DEFAULT`

### Visualization Options

- **Trail length**: Adjust `TRAIL_DECIMATE` in `constants.py`
- **Surface resolution**: Modify `GRID_COARSE_N` and `GRID_FOCUS_N`
- **Visual scaling**: Change `VISUAL_RADIUS_SCALE` for body sizes

🛠️ Contributing
Contributions are welcome!
Fork this repository
Create a feature branch (git checkout -b feature-name)
Commit changes (git commit -m "Add feature name")
Push to branch (git push origin feature-name)
Open a Pull Request 🎉

## Known Limitations

1. **Point masses**: Bodies are treated as point masses (no rotation, tides)
2. **No collisions**: Bodies can pass through each other
3. **No moons**: Currently only includes major planets
4. **Matplotlib rendering**: Limited to basic 3D visualization

## Future Enhancements

- OpenGL-based high-performance rendering
- Collision detection and merging
- Moon and asteroid support
- Variable time-stepping for close encounters
- Export capabilities (animations, data)

## References

- Wisdom, J. & Holman, M. (1991). Symplectic maps for the n-body problem. *Astronomical Journal*, 102, 1528-1538.
- Will, C. M. (2014). *Theory and Experiment in Gravitational Physics*. Cambridge University Press.
- Murray, C. D. & Dermott, S. F. (1999). *Solar System Dynamics*. Cambridge University Press.

  ![1](https://github.com/user-attachments/assets/0312a5ee-6de7-43dd-b019-edfec43ac0a0)


## License

This project is provided as-is for educational and research purposes.
