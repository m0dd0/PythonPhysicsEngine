from typing import List

import pygame

from ppe.engine.common import Body, PolygonShape, Vec2
from ppe.engine.world import World
from ppe.engine.solvers import NoOpSolver
from ppe.engine.integrators import NoOpIntegrator
from ppe.engine.collision_broad import AABBBroadPhase
from ppe.engine.collision_narrow import DispatchNarrowPhase
from ppe.engine.collision_handlers import (
    CircleVsCircleHandler,
    SatPolygonHandler,
    CircleVsPolygonHandler,
)

# application components
from ppe.utils.view import PygameView, Camera
from ppe.utils.controller import (
    CameraPanController,
    CameraZoomController,
    InputState,
    ApplicationController,
    DebugController,
    AbstractController,
    BodyDragController,
    BodySpawnController,
    BodySteeringController,
    HoverRotateController,
)

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
SCREEN_WIDTH_WORLD = 10.0  # World width in physics units


def main():
    pygame.init()  # pylint: disable=no-member

    # 1. Initialize View
    view = PygameView(
        camera=Camera.with_world_width(
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
            world_width=SCREEN_WIDTH_WORLD,
        )
    )
    debug_drawer = view.create_debug_drawer()

    # 2. Setup the world simulation
    world = World(
        integrator=NoOpIntegrator(),
        solver=NoOpSolver(),
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
        bodies=[
            Body(
                shape=PolygonShape.create_rectangle(width=2, height=1),
                position=Vec2(0, 0),
                mass=10,  # Static body
                user_data={"color": (50, 50, 50)},
            ),
        ],
        debug_drawer=debug_drawer,
    )

    # 3. Initialize controllers
    app_controller = ApplicationController(debug_drawer=debug_drawer)
    debug_controller = DebugController(
        controlled_debug_drawer=debug_drawer, debug_drawer=debug_drawer
    )
    controllers: List[AbstractController] = [
        # CameraPanController(view.camera, mode="mouse", mouse_button=2),
        # CameraZoomController(view.camera, mode="mousewheel"),
        app_controller,
        debug_controller,
        BodyDragController(
            world=world,
            camera=view.camera,
            mode="position",
            mouse_button=2,
        ),
        BodySpawnController(world=world, camera=view.camera),
        # BodySteeringController(body=world.bodies[0]),
        HoverRotateController(world=world, camera=view.camera),
    ]

    ## Main Loop
    running = True
    clock = pygame.time.Clock()

    while running:
        dt = clock.tick(60) / 1000.0

        ## Input
        input_state = InputState.from_pygame()

        ## Controller Updates
        for controller in controllers:
            controller.update(input_state, dt)

        # Check if application should quit
        if app_controller.should_quit:
            running = False

        ## Physics Update
        world.step(dt)

        # Render the world
        view.render_all(
            world,
            info_data={
                "Current FPS": int(clock.get_fps()),
            },
        )
        view.update_display()

    pygame.quit()  # pylint: disable=no-member


if __name__ == "__main__":
    main()
