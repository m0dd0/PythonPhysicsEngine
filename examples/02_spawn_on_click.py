from typing import List

import pygame

from ppe.engine.common import Body, PolygonShape, Vec2
from ppe.engine.world import World
from ppe.engine.solvers import IterativeImpulseSolver
from ppe.engine.integrators import SemiImplicitEulerIntegrator
from ppe.engine.collision_broad import AABBBroadPhase
from ppe.engine.collision_narrow import DispatchNarrowPhase
from ppe.engine.collision_handlers import (
    CircleVsCircleHandler,
    SatPolygonHandler,
    CircleVsPolygonHandler,
)
from ppe.engine.force_generators import GlobalForceField

# application components
from ppe.utils.view import PygameView, Camera
from ppe.utils.controller import (
    CameraPanController,
    CameraZoomController,
    InputState,
    ApplicationController,
    DebugController,
    AbstractController,
    BodySpawnController,
)
from ppe.utils.profiler import Profiler

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 512
SCREEN_WIDTH_WORLD = 10.0  # World width in physics units


def main():
    pygame.init()  # pylint: disable=no-member

    # 1. Initialize View
    view = PygameView(
        camera=Camera.with_world_width(
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
            world_width=SCREEN_WIDTH_WORLD,
            position=Vec2(0, 2.5),
        ),
        smooth_profiler=True,
        # define the default style for rendering bodies
        default_is_filled=False,
        default_outline_width=3,
    )
    debug_drawer = view.create_debug_drawer()

    # Initialize the profiler
    profiler = Profiler(smoothing_frames=30)

    # 2. Setup the world simulation
    world = World(
        integrator=SemiImplicitEulerIntegrator(),
        solver=IterativeImpulseSolver(debug_drawer=debug_drawer),
        broad_phase=AABBBroadPhase(debug_drawer=debug_drawer),
        narrow_phase=DispatchNarrowPhase(
            debug_drawer=debug_drawer,
            handlers={
                ("circle", "circle"): CircleVsCircleHandler(debug_drawer=debug_drawer),
                ("circle", "polygon"): CircleVsPolygonHandler(
                    debug_drawer=debug_drawer
                ),
                ("polygon", "polygon"): SatPolygonHandler(debug_drawer=debug_drawer),
            },
        ),
        force_generators=[GlobalForceField(strength=Vec2(0, -9.81))],
        bodies=[
            # left wall
            Body(
                shape=PolygonShape.create_rectangle(width=0.5, height=5),
                position=Vec2(-4.75, 2.5),
                mass=None,  # static body
            ),
            # right wall
            Body(
                shape=PolygonShape.create_rectangle(width=0.5, height=5),
                position=Vec2(4.75, 2.5),
                mass=None,  # static body
            ),
            # bottom wall
            Body(
                shape=PolygonShape.create_rectangle(width=10, height=0.5),
                position=Vec2(0, 0.25),
                mass=None, # static body
            ),
        ],
        debug_drawer=debug_drawer,
        profiler=profiler,
    )

    # 3. Initialize controllers
    app_controller = ApplicationController(debug_drawer=debug_drawer)
    debug_controller = DebugController(
        controlled_debug_drawer=debug_drawer, debug_drawer=debug_drawer
    )
    controllers: List[AbstractController] = [
        app_controller,
        debug_controller,
        CameraZoomController(view.camera, mode="keyboard"),
        CameraPanController(view.camera, mode="keyboard"),
        BodySpawnController(world=world, camera=view.camera),
    ]

    ## Main Loop
    running = True
    clock = pygame.time.Clock()

    while running:
        profiler.start_frame()

        # wait until at least 1/60 seconds have passed
        dt = clock.tick(60) / 1000.0

        ## Input
        with profiler.time("input"):
            input_state = InputState.from_pygame()

        ## Controller Updates
        with profiler.time("controller"):
            for controller in controllers:
                controller.update(input_state, dt)

        # Check if application should quit
        if app_controller.should_quit:
            running = False

        ## Physics Update
        with profiler.time("world"):
            try:
                world.step(dt)
            except Exception as e:
                print(f"Error during world step: {e}")
                running = False

        # Render the world
        with profiler.time("render"):
            view.render_background()
            view.render_bodies(world.bodies)
            world.debug_drawer.render_all()
            view.render_info([c.action_description for c in controllers])

        # Render profiler after timing is complete
        # start = time.perf_counter()
        profiler.end_frame()
        view.render_profiler(profiler, subsections=["world"])
        view.update_display()
        # end = time.perf_counter()
        # print(f"Profiler rendering took {((end - start) * 1000):.2f} ms")
        # -> time that is not included in the profiler is negligible (<1 ms)

    # for keeping the window open for debugging purposes
    # import time
    # while True:
    #     time.sleep(0.1)

    pygame.quit()  # pylint: disable=no-member


if __name__ == "__main__":
    main()
