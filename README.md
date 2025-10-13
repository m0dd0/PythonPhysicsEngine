# PythonPhysicsEngine
A modular 2D physics engine in Python, built from scratch to educate myself (and hopefully others) on the inner workings of physics simulations. 
Features a highly modular architecture that allows to compare different algorithms for integration, collision detection, and constraint solving.
<!-- I built this for educational purposes: Do not expect high performance; after all it's a pure Python implementation that does not use any optimized libraries. -->

## Motivation
The primary motivation behind this physics engine is to demystify how physics engines generally work by building one from scratch in pure Python without relying on any external physics or math libraries. 
This project serves as an educational tool for myself and others who want to understand the algorithms and architectural patterns that make physics simulations possible.

**Key goals include:**
- **Building from Scratch:** Every component, from vector math to the constraint solver, is implemented in pure Python to ensure a deep understanding of the underlying mechanics.
- **Clarity Over Performance:** Python was chosen for its simplicity. The goal is to write code that is easy to follow and learn from, rather than aiming for the performance of a C++ engine.
- **No "Black Box" Libraries:** The engine intentionally avoids external physics or math libraries like NumPy to ensure that no logic is hidden. The only major dependency is Pygame for visualization.
- **Focus on Architecture:** The project emphasizes a clean, modular, and extensible architecture using standard software design patterns.

## Features
- 2D Rigid Body Dynamics: Simulates the motion of 2D bodies with position, angle, velocity, and mass.
- Modular Architecture: Uses the Strategy Pattern extensively, allowing for swappable components:
    - Integrators (Semi-Implicit Euler, Position Verlet)
    - Solvers (Iterative Impulse, Position-Based)
    - Collision Detection (pluggable Broad and Narrow Phases)
- Different Collision Detection Algos Implemented:
    - Broad Phase: AABB checks to quickly eliminate non-colliding pairs.
    - Narrow Phase: A dispatch system that uses specific handlers for different shape pairs (Circle-vs-Circle, Polygon-vs-Polygon, etc.).
    - SAT + Clipping: A full implementation of the Separating Axis Theorem with a clipping algorithm to generate stable, multi-point contacts for polygon collisions.
- Currently Implemented Solvers:
    - Iterative Impulse-based Solver: A realistic physics solver that resolves collisions and stacking by applying impulses iteratively. Includes Baumgarte Stabilization for positional correction.
- Visualization, Debug and Control Tools: 
    - A Pygame-based renderer to visualize bodies, shapes, and collisions.
    - A selection of controllers that ease interaction with the simulation (camera controls, body dragging, spawning shapes).
    - A flexible debug drawing system to visualize AABBs, collision normals, contact points, and other internal states.

## How to Run an Example
Clone the repository:
```
Bash

git clone https://github.com/m0dd0/pythonphysicsengine.git
cd 
```
Set up a virtual environment:

Bash

python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install dependencies:

Bash

pip install pygame pytest
Perform an "Editable Install":
This crucial step makes your ppe package importable by your examples and tests.

Bash

pip install -e .
Run an example:

Bash

python examples/01_stacking_demo.py

## Using the Library
The idea is to provide a set of high-level building blocks that can be composed to create a highly customizable physics loop.
Checkout one of the examples in the `examples/` folder to see how to set up a simulation.
The library is thoroughly documented with docstrings and type hints.
I plan to give a more detailed 


## Project Structure
The project is structured to separate the reusable engine from the application/example code, following modern Python packaging standards.

engine-blocks/
├── src/
│   └── ppe/                  <-- The installable physics package (stands for Python Physics Engine)
│       ├── __init__.py
│       ├── common.py         # Core data structures (Body, Shape, Vec2)
│       ├── world.py          # The main World orchestrator
│       ├── integrators.py
│       ├── solvers.py
│       ├── collision_broad.py
│       ├── collision_narrow.py
│       ├── collision_handlers.py
│       └── debug.py          # AbstractDebugDrawer interface
│
├── tests/                    <-- Pytest unit tests for the engine
│   └── test_common.py
│
├── examples/                 <-- Runnable demonstration scripts
│   └── 01_stacking_demo.py
│
├── utils/                    <-- Reusable application-level code
│   ├── __init__.py
│   ├── view.py             # PygameView and concrete DebugDrawer
│   └── controllers.py      # CameraController, BodyDragger, etc.
│
└── pyproject.toml            <-- Project configuration

## Architectural Overview
The engine is built on a few key software design patterns:

**Model-View-Controller (MVC):** The architecture facilitates the use of an MVC pattern. All examples are structured this way.
  - Model: The `World` class that contauns all the core engine components. It is completely independent of any visualization.
  - View: The `PygameView` class, responsible for all rendering.
  - Controller: The `Controller` classes, responsible for handling user input.

Strategy Pattern & Dependeny Injection: Nearly every major component is an abstract "strategy" that can be swapped out. This allows for easy experimentation and "horizontal extension" of the engine. Instead of creating its own components, the World class is "injected" with the strategies it should use. This makes the system highly decoupled and configurable.
Key abstract strategies include:
- AbstractIntegrator: Implementations are used to determine the position and velocity updates of bodies each time step.
- AbstractSolver: Implementations are used to resolve collisions and constraints.
- AbstractBroadPhase: Implementations are used to filter potential collision pairs quickly.
- AbstractCollisionHandler: Implementations are used to detect whether two shapes are colliding and generate contact data if they are.

## License
This project is licensed under the MIT License.