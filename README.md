# PythonPhysicsEngine
A modular 2D physics engine built from scratch in pure Python. 
Its primary goal is to demystify the algorithms and architectural patterns behind physics simulations by providing a clear, readable implementation from first principles.
The engine intentionally avoids external math or physics libraries to ensure that no logic is hidden inside a "black box," making it a valuable resource for learning how components like collision detection, impulse solvers, and integrators work together.

Aming at being an educational resource, this projects also contains multiple write-ups on the key concepts and algorithms used in the engine.
The writeups are kept concise but contain all the relevant information and are linked to the corresponding sections in the codebase.
The following topics are covered by the writeups:
- [Basic Physics Loop](docs/01_basic_physics_loop.md): High-level overview on how physics simulations work.
- [Collision Detection](docs/02_collision_detection.md): Explains the broad and narrow phase collision detection algorithms.
- [Impulse Solvers](docs/03_impulse_solvers.md): Describes the different impulse solvers available in the engine.
- [Integrators](docs/04_integrators.md): Explains the different integrators available in the engine.

Note that this project is a work in progress and especially the physics solver is far from being good yet. 

## Features
See the Github Issues for planned features and improvements.
Currently the engines features are limited to the most essential parts needed for a basic 2D rigid body simulation:
- **2D Rigid Body Dynamics:** Simulates the motion of 2D bodies with position, angle, velocity, and mass.
- **Modular Architecture:** Uses the Strategy Pattern extensively, allowing for swappable components:
    - Integrators (Semi-Implicit Euler, Position Verlet)
    - Solvers (Iterative Impulse, Position-Based)
    - Collision Detection (pluggable Broad and Narrow Phases)
- **Implemented Collision Detection Algos:**
    - Broad Phase: AABB checks to quickly eliminate non-colliding pairs.
    - Narrow Phase: A dispatch system that uses specific handlers for different shape pairs (Circle-vs-Circle, Polygon-vs-Polygon, etc.).
    - SAT + Clipping: A full implementation of the Separating Axis Theorem with a clipping algorithm to generate stable, multi-point contacts for polygon collisions.
- **Implemented Solvers:**
    - Iterative Impulse-based Solver: A realistic physics solver that resolves collisions and stacking by applying impulses iteratively. Includes Baumgarte Stabilization for positional correction.
- **Visualization, Debug and Control Tools:**
    - A Pygame-based renderer to visualize bodies, shapes, and collisions.
    - A selection of controllers that ease interaction with the simulation (camera controls, body dragging, spawning shapes).
    - A flexible debug drawing system to visualize AABBs, collision normals, contact points, and other internal states.

## How to Run an Example
1. Clone the repository:
```
git clone https://github.com/m0dd0/pythonphysicsengine.git
cd pythonphysicsengine
```
2. Setup a virtual environment (optional but recommended):
```
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```
3. Install the module and its dependencies (using editable install to allow modifications in the source code to be reflected immediately):
```
pip install -e .
```
4. Run an example script:
```
python examples/02_legacy_click_create.py
```

## Using the Library
The philosophy of this library is to provide a set of high-level building blocks that can be composed to create a highly customizable but still easy-to-use physics loop.
The core of the engine is the `World` class, which is configured by injecting different implementations for handling motion, collision detection, and constraint resolution.
You can also add initial bodies and shapes to the world at construction time.
```python
# Assemble the engine by composing different strategies
world = World(
    integrator=SemiImplicitEulerIntegrator(),
    solver=IterativeImpulseSolver(iterations=10),
    broad_phase=AABBBroadPhase(),
    narrow_phase=DispatchNarrowPhase(...),
    initial_bodies=[
        Body(
            shape=PolygonShape.create_box(width=1.0, height=1.0), 
            position=Vec2(0, 5), 
            mass=1.0
        ),
    ],
)
```
In most cases, you will want to visualize the simulation and interact with it.
The library provides a Pygame-based view and several controller implementations to handle user input.
In this example, the only allowed interaction is panning and zooming the camera.
```python
# Set up the view and controller
view = PygameView(camera=Camera(screen_width=800, screen_height=600, zoom=20.0))
controllers = [CameraPanController(view.camera), CameraZoomController(view.camera)]
```
Finally, we can run the simulation loop, which will repeatedly update the world and render it using the view.
```python
# Run the simulation loop
while True:
    dt = clock.tick(60) / 1000.0  # Fixed time step of ~16ms
    
    input_state = InputState.from_pygame()  # Capture user input
    for controller in controllers:
        controller.update(input_state, dt)  # Update controllers with input
    
    world.step(dt)
    
    view.render_background()
    view.render_bodies(world.bodies)
    view.update_display()
    # alternatively: view.render_all(world.bodies) to render everything in one call
```

For a full working example, see the examples in the [`examples/`](examples) folder.
The examples also showcase more features like debug drawing, profiling tools, and different controllers.

The library is thoroughly documented with docstrings and type hints. 
A dedicated documentation website might be added in the future.

## Project Structure
A quick overview of the project structure:
```
.
├── ppe
│   ├── engine # Core engine components
│   │   ├── collision_broad.py # Abstract broad phase and implementations
│   │   ├── collision_handlers.py # Implementations of narrow phase collision handlers
│   │   ├── collision_narrow.py # Abstract narrow phase and dispatch system for collision handlers
│   │   ├── common.py # Core data structures (Body, Shape, Contact, etc.)
│   │   ├── debug.py # Debug drawing utilities
│   │   ├── force_generators.py # Implementations of force generators (gravity, drag, etc.)
│   │   ├── integrators.py # Abstract integrator and implementations
│   │   ├── solvers.py # Abstract solver and implementations
│   │   └── world.py # The World class that orchestrates the objects and simulation loop
│   ├── utils
│   │   ├── colors.py
│   │   ├── controller.py # Abstract controller and implementations
│   │   ├── profiler.py # Simple profiling utilities
│   │   └── view.py # Abstract view and Pygame implementation
│   └── __init__.py
├── examples
│   ├── 01_collision_visualization.py
│   ├── 02_legacy_click_create.py
│   └── 03_the_bowl.py
├── tests
│   ├── test_collision_broad.py
│   ├── test_collision_handlers.py
│   ├── test_common.py
│   ├── test_performance.py
│   └── test_solvers.py
├── .gitignore
├── LICENSE
├── README.md
└── setup.py
```

## Architectural Overview
The engine is built on a few key software design patterns:

**Strategy Pattern & Dependeny Injection:** Nearly every major component is an abstract "strategy" that can be swapped out. 
This allows for easy experimentation and "horizontal extension" of the engine. 
The World class is "injected" with the strategies it should use. 
This makes the system highly decoupled and configurable (for the cost of some overhead and setup complexity).

Key abstract strategies include:
- `AbstractIntegrator`: Implementations are used to determine the position and velocity updates of bodies each time step.
- `AbstractSolver`: Implementations are used to resolve collisions and constraints.
- `AbstractBroadPhase`: Implementations are used to filter potential collision pairs quickly.
- `AbstractCollisionHandler`: Implementations are used to detect whether two shapes are colliding and generate contact data if they are.

**Model-View-Controller (MVC):** The architecture facilitates the use of an MVC pattern. All examples are structured this way.
  - Model: The `World` class that contauns all the core engine components. It is completely independent of any visualization.
  - View: The `PygameView` class, responsible for all rendering.
  - Controller: The `Controller` classes, responsible for handling user input.

A more detailed discussion of the architecture and design patterns is available [here](docs/00_architecture_overview.md).

<!-- ## Concepts
I tried to document the key concepts and algorithms used in the engine.
Others already did a great job in explaining these concepts in more detail, but I wanted to have my own write-up to solidify my understanding.
Maybe my write-ups can also help others to get a quick overview of these concepts.
The following topics are planned to be covered (as of now, there are just highly incomplete drafts):
- [Basic Physics Loop`](docs/01_basic_physics_loop.md): High-level overview on how physics simulations work.
- [Collision Detection](docs/02_collision_detection.md): Explanation on how collision detection is implemented, including broad phase implementations and narrow phase with SAT.
- [Integrators](docs/03_integration.md): Overview of different numerical integration methods for updating body positions and velocities.
- [Constraint Solvers](docs/04_constraint_solvers.md): Explanation of impulse-based solvers and position-based solvers for resolving collisions and constraints. -->

## License
This project is licensed under the MIT License.