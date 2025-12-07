# Architecture
As outlined in the README, this physics engine is built with modularity and extensibility in mind.
<!-- Since performance is extremly poor anyways due to the use of pure Python, the focus is on clean architecture and easy experimentation rather than raw speed. -->
To achieve a high degree of modularity, the engine is built around several key abstract strategies whose implementations can be swapped out easily.
For example, one might experiment with different solver implementations.
To do so one would simply pass an instance of a different solver class to the `World` class upon initialization.
This approach allows users to experiment with different algorithms and implementations without modifying the core engine code.

From an application perspective, the project uses a classical model-view-controller (MVC) architecture.
The `World` class serves as the model, encapsulating the state and behavior of the physics simulation.
The view is completely decoupled from the model, allowing for different rendering implementations to be used interchangeably with the same physics engine.
This project implements a PyGame-based view but other rendering engines could be integrated with minimal effort.
Multiple controllers are implemented to handle user input and interact with the physics simulation.
The controller implmentations work on a generic `InputState` class, allowing for different input methods to be used without changing the controller logic.
Depending on the application, different controllers can be combined to achieve the desired user interaction.

## Project Structure
```
.
├── engine
│   ├── body.py # defines the Body class representing physical objects
│   ├── collision_broad.py # broad-phase collision detection algorithms
│   ├── collision_handlers.py # narrow-phase collision handling for specific shape pairs
│   ├── collision_narrow.py # narrow-phase collision detection
│   ├── common.py # common utilities like Vectors
│   ├── debug.py # utilities for graphical debugging
│   ├── force_generators.py # various force generators (e.g., gravity, springs)
│   ├── integrators.py # numerical integration methods (e.g., Euler, Verlet)
│   ├── joints.py # joint constraints between bodies
│   ├── shapes.py # geometric shape definitions for the bodies
│   ├── solvers.py # constraint solvers
│   └── world.py # the World class managing the simulation
├── frontend
│   ├── colors.py # basically a set of nice-looking colors
│   ├── controller.py # controller implementations for handling user input
│   ├── input.py # data structure for getting and storing user input
│   ├── view.py # view implementations for rendering the simulation
│   └── widgets.py # UI widgets for user interaction
└── utils
    ├── loops.py # generic main loop implementation
    └── profiler.py # simple profiling utility
```

## Strategy Pattern for Customizing the Behavior of the Engine
As you can see inthe examples, the core model `World` class is composed of several key components that define each aspect of the physics simulation.
Namely, these components include:
- Broad-phase collision detection strategy
- Narrow-phase collision detection strategy
- Integration strategy
- Constraint solving strategy
For each of these components, there exists an abstract base class defining the interface that all concrete implementations must adhere to.
When initializing a `World` instance, users can provide their own implementations of these strategies or use one of the implementations provided by the engine.
This design follows the Strategy Pattern, allowing for easy customization and experimentation with different algorithms and techniques within the physics engine.

Besides the strategies mentioned above, the `World` class also keepts track of the bodies in the simulations as well as joints and force generators.
Different methods are available to add or remove those entities from the simulation.
Note that the `World` class does not run the simulation loop itself.
Instead it provides a `step(dt)` method that advances the simulation by a given time step.
How and when this method is called is left up to the application using the engine.

## Application Level Architecture
The core engine module is defined in the `engine` submodule and can be used independently of any rendering or user input code.
One may use it without a visualiaztion for non-realtim applications while other applications may want to integrate it with a specific rendering engine.

While the engine itself is agnostic to rendering and input handling, this project provides a `frontend` submodule that implements a simple PyGame-based view and several controllers for user interaction.
The `frontend` module is structured around the classical Model-View-Controller (MVC) pattern.
Orchestrating the interaction between model, view, and controller is left up to the application using the engine.
A good example on how such a main loop could look like can be found in the `examples/02_click2spawn.py` file.

### Controllers, Input State, and Widgets
**Controllers** are self-contained components that might have references to the world instance or the camera instance and operate on an generic `InputState` instance.
Depending on the framework used for gathering user input, the `InputState` instance can be populated accordingly.
By using the `InputState` abstraction, controllers can be reused across different applications and input methods without modification.
A controller might implement logic for panning and zooming the camera, spawning new bodies, or applying forces to existing bodies based on user input.

**Widgets** are reusable UI components that are part of the view layer.
Similar to controllers, widgets also operate on an `InputState` instance to determine user interactions.
However, unlike controllers, widgets are primarily concerned with rendering UI elements based on user input or other factors.
Widgets have a `render(surface)` method that takes a rendering surface as an argument and draws the widget onto it.
As opposed to controllers, widgets are therefore specific to the view implementation (here PyGame) and cannot be easily reused across different rendering engines.

### Debug Visualization Tool
In oder to visualize internal states of the physics engine (like contact points, bounding boxes, etc.), a `DebugRecorder` is implemented in the `engine/debug.py` file.
The recorder can be used to collect generic draw commands within the engine code without having any dependencies on a specific rendering engine.
On the application side, the debug recorder's collected draw commands can then be visualized as needed.
Concretely we use a `PGDebugRecorderWidget` in the PyGame-based view to render the debug information onto the screen.