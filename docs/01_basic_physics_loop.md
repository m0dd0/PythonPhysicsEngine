## The Physics Simulation Loop
Physics engines do not simulate the real world continuously. 
Instead, they approximate reality by taking snapshots.
Between these snapshots, they perform a series of calculations to update the state of the simulation (i.e the position and other physical properties of the bodies in the simulation) in a way that mimics real-world physics as closely as possible.
These calculations are repeated in a loop, often referred to as the "physics simulation loop" or simply the "physics loop" and in each iteration of this loop, the engine computes the next state of the simulation based on the current state, the physical laws, and potential user interactions with the simulation.

There is a common way on how the computations in the physics loop are structured.
In its most basic form, the physics loop consists of the following steps:
- **Input Handling:** Capture any user inputs or external forces that might affect the simulation.
- **Integration:** Update the positions and velocities of the bodies based on the applied forces using numerical integration methods.
- **Collision Detection:** Check for collisions between bodies in the simulation.
- **Constraint Resolution:** Resolve any detected collisions using constraint solvers to ensure bodies respond appropriately (e.g., bouncing off each other) by updating their velocities and/or positions. This step can also include resolving other constraints like joints between objects or friction. This constraint resolution step can be seen as the "heart" of the physics simulation as it is repsonsible for making the objects move (and potentially deform) in a realistic way.
- **State Update:** Finalize the state of the simulation for the current time step.

For each of the components, different algorithms and techniques can be used, each with its own trade-offs in terms of performance, accuracy, and complexity.
We will focus on each of these computational components in detail in the following write-ups and elaborate on the algorithms and techniques implemented in this physics engine.
For now, it's import to understand that the physics loop is a repetitive process that constantly updates the simulation state.

## Fixed Time Step vs Variable Time Step
An important consideration is that the higher the frequency of the loop (i.e., the more iterations per simulatd second), the more accurate the simulation will appear.
Depending on the application, different strategies can be employed to determine how much delta time (dt) should be simulated in each iteration of the physics loop and whether this dt should be constant or variable over time.

For a system that does not require real-time performance (e.g., offline simulations), a fixed and short time step can be used to ensure high accuracy.
This ensures that each iteration of the physics loop simulates the same amount of time, leading to consistent and predictable results.

On the other hand, in real-time applications like video games, we want the physics loop to update the simulated world at a pace that matches what we would expect in the real world.
However, this means that if we need longer to compute a single iteration of the physics loop (e.g., due to a high computational load), the physics update should account for this and simulate a longer time span in that iteration.
This is where a variable time step can make sense, as it allows the physics loop to adapt to the available computational resources and still provide a smooth experience (up to a certain degree).


## Reactive vs Preventive Physics Loops
The type of loop described above is called a "reactive" physics loop because it reacts to collisions and constraints after they have occurred.
While in reality objects can not simply overlap and then be undone in the next timestep, this approach often provides a good balance between performance and realism for many applications, especially in real-time simulations like video games.
This project uses such a reactive physics loop.

However, its worth mentioning, that there are also "preventive" approaches that try to avoid collisions before they happen.
Preventive approaches are more complex and computationally intensive, as they require predicting future states of the simulation and adjusting object trajectories accordingly.
These approaches are less common in real-time applications like games, but they can be useful in scenarios where high precision is required, like in engineering applications.
Also some game engines use a mix of both approaches, where they primarily use a reactive loop but incorporate some preventive measures for specific scenarios.
A good example for when it makes sense to use preventive measures in an otherwise reactive loop is when simulating fast-moving objects like bullets that would otherwise "tunnel" through other objects without detecting a collision.