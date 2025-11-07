from typing import List

import pygame

from ppe.engine.world import World

# application components
from ppe.frontend.view import AbstractView
from ppe.frontend.controller import (
    InputState,
    ApplicationController,
    AbstractController,
)
from ppe.utils.profiler import Profiler

def main_loop(
    view: AbstractView,
    world: World,
    controllers: List[AbstractController],
    app_controller: ApplicationController,
    profiler: Profiler,
    target_fps: int = 60,
    use_fixed_timestep: bool = False,
    cap_fps: bool = True,
    render_profiler: bool = True,
    substeps: int = 1,
    max_iterations: int = None,
):
    """
    Runs the main application loop for the physics simulation.

    This function orchestrates input handling, controller updates, physics
    stepping, and rendering.

    Args:
        view (AbstractView): The PygameView object responsible for all rendering.
        world (World): The physics World object containing the simulation state.
        controllers (List[AbstractController]): A list of all active controllers for user input.
        app_controller (ApplicationController): The special controller for application-level events (like quitting).
        profiler (Profiler): The Profiler object for tracking performance.
        target_fps (int): The target frames per second.
        use_fixed_timestep (bool): If True, the physics `dt` will be a fixed value (1.0 / target_fps),
            even if the actual elapsed time is different (higher).
        cap_fps (bool): If True, the loop will wait (tick) to maintain the target_fps. 
            If False, it runs as fast as possible.
        render_profiler (bool): Whether to display the profiler.
        substeps (int): The number of physics steps to perform per rendering frame for better stability.
    """
    clock = pygame.time.Clock()
    running = True

    # Calculate the ideal fixed timestep
    fixed_dt = 1.0 / target_fps

    render_times = []
    world_times = []

    iterations = 0
    while running:
        profiler.start_frame()

        # --- 1. Calculate Delta Time (dt) ---
        if cap_fps:
            # Wait to maintain the target FPS. Returns actual ms elapsed.
            elapsed_ms = clock.tick(target_fps)
        else:
            # Run as fast as possible. Returns actual ms elapsed.
            elapsed_ms = clock.tick()
        
        # Use the actual elapsed time...
        actual_dt = elapsed_ms / 1000.0
        
        # ...unless we're forcing a fixed timestep.
        if use_fixed_timestep:
            dt = fixed_dt
        else:
            dt = actual_dt
            
        # --- 2. Input ---
        with profiler.time("input"):
            input_state = InputState.from_pygame()

        # --- 3. Controller Updates ---
        with profiler.time("controller"):
            for controller in controllers:
                controller.update(input_state, dt)

        # Check for quit signal from any controller
        if app_controller.should_quit:
            running = False

        # --- 4. Physics Update (with Substeps) ---
        with profiler.time("physics"):
            # We divide the total frame time by the number of steps
            substep_dt = dt / substeps
            for _ in range(substeps):
                world.step(substep_dt)

        # --- 5. Rendering ---
        with profiler.time("render"):
            view.render_background()
            view.render_bodies(world.bodies)
            view.render_debug_recorder(world.debug_recorder)
            view.render_info([c.action_description for c in controllers])

        # Render profiler after frame timing is complete
        profiler.end_frame()
        if render_profiler:
            view.render_profiler(profiler)
        
        render_times.append(profiler.timings["render"])
        world_times.append(profiler.timings["physics"])

        view.update_display()

        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            running = False

    print(f"Average render time: {sum(render_times) / len(render_times)} ms")
    print(f"Average world step time: {sum(world_times) / len(world_times)} ms")

    pygame.quit() # pylint: disable=no-member