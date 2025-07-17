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
    CameraController,
    InputState,
    ApplicationController,
    DebugController,
    AbstractController,
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
                mass=None,  # Static body
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
        CameraController(view.camera, pan_mode="keys"),
        app_controller,
        debug_controller,
        # BodyMovementController(
        #     is_body_selectable=True,
        #     world=world,
        #     camera=view.camera,
        #     control_mode="position",
        # ),
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
                "Debug Mode (D)": "ON" if debug_controller.debug_mode else "OFF",
                "Instructions": "Click to select a box, then use WASD/QE to move/rotate",
                "Current FPS": int(clock.get_fps()),
            },
        )
        view.update_display()

    pygame.quit()  # pylint: disable=no-member


if __name__ == "__main__":
    main()
