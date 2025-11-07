"""
Example 02: Click2Spawn
This example demonstrates a simple interactive 2D physics simulation.
Users can spawn new polygon or circle bodies into the world by clicking with the mouse:
- Left click creates a random rectangle.
- Right click creates a random circle.
"""

from typing import List, Tuple
import random

import pygame

# engine components
from ppe.engine.common import Body, PolygonShape, Vec2, CircleShape
from ppe.engine.world import World
from ppe.engine.force_generators import GlobalForceField
from ppe.engine.collision_handlers import (
    CircleVsCircleHandler,
    CircleVsPolygonHandler,
    SatPolygonHandler,
)
from ppe.engine.collision_narrow import DispatchNarrowPhase
from ppe.engine.solvers import IterativeImpulseSolver
from ppe.engine.solvers import SemiImplicitEulerIntegrator

# application components
from ppe.frontend.view import PygameView, Camera
from ppe.frontend.controller import (
    InputState,
    ApplicationController,
    DebugController,
    AbstractController,
    BodySpawnController,
)
from ppe.utils.profiler import Profiler
from ppe.frontend.colors import V1_COLORS
from ppe.engine.debug import DebugRecorder
from ppe.frontend.widgets import (
    PGProfilerWidget,
    AbstractUIElement,
    PGControllerInfoWidget,
    PGDebugRecorderWidget,
)


## Constants
# (initial body config is in the code to not pollute the global namespace)
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
SCREEN_WIDTH_WORLD = 10.0  # World width in physics units
BODY_STYLE_DEFAULTS = {"circle_orientation_line": True}

CIRCLE_SPAWN_RADIUS_RANGE = (0.1, 0.3)
POLYGON_SPAWN_SIDE_RANGE = (0.1, 0.5)
GRAVITY = Vec2(0, -9.81)
BOUNCINESS = 0.5


def setup() -> Tuple[
    PygameView,
    World,
    List[AbstractController],
    ApplicationController,
    Profiler,
    pygame.time.Clock,
]:
    pygame.init()  # pylint: disable=no-member

    ## Initialize the profiler and debug recorder
    debug_recorder = DebugRecorder()
    profiler = Profiler()

    ## intiiaalize view
    view = PygameView(
        camera=Camera.with_world_width(
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
            world_width=SCREEN_WIDTH_WORLD,
            position=Vec2(0, 1),
        ),
        body_style_defaults=BODY_STYLE_DEFAULTS,
    )

    ## define initial bodies
    initial_bodies = [
        Body(
            shape=PolygonShape(
                vertices=[
                    Vec2(-2.5, -0.1),
                    Vec2(-2.5, 0.1),
                    Vec2(2.5, 0.1),
                    Vec2(2.5, -0.1),
                ],
            ),
            position=Vec2(0, 0),
            mass=None,
            user_data={"color": (0, 0, 0)},
            restitution=BOUNCINESS,
        )
    ]

    ## Setup the world simulation
    world = World(
        solver=IterativeImpulseSolver(),
        integrator=SemiImplicitEulerIntegrator(),
        bodies=initial_bodies,
        debug_recorder=debug_recorder,
        profiler=profiler,
        force_generators=[GlobalForceField(strength=GRAVITY)],
        narrow_phase=DispatchNarrowPhase(
            debug_recorder=debug_recorder,
            handlers={
                ("circle", "circle"): CircleVsCircleHandler(
                    debug_recorder=debug_recorder
                ),
                ("circle", "polygon"): CircleVsPolygonHandler(
                    debug_recorder=debug_recorder
                ),
                ("polygon", "polygon"): SatPolygonHandler(
                    debug_recorder=debug_recorder
                ),
            },
        ),
    )

    ## Initialize controllers
    app_controller = ApplicationController(debug_recorder=debug_recorder)
    controllers: List[AbstractController] = [
        app_controller,
        DebugController(
            controlled_debug_recorder=debug_recorder, debug_recorder=debug_recorder
        ),
        # CameraZoomController(view.camera, mode="keyboard"),
        # CameraPanController(view.camera, mode="keyboard"),
        BodySpawnController(
            world=world,
            camera=view.camera,
            mouse_spawn_objects={
                1: lambda: Body.create_with_density(
                    shape=PolygonShape.create_rectangle(
                        width=random.uniform(*POLYGON_SPAWN_SIDE_RANGE),
                        height=random.uniform(*POLYGON_SPAWN_SIDE_RANGE),
                    ),
                    density=1,
                    user_data={"color": random.sample(V1_COLORS, 1)[0]},
                    restitution=BOUNCINESS,
                    position=Vec2(
                        0, 0
                    ),  # gets overwritten with mouse position in controller
                ),
                3: lambda: Body.create_with_density(
                    shape=CircleShape(
                        radius=random.uniform(*CIRCLE_SPAWN_RADIUS_RANGE)
                    ),
                    density=1,
                    user_data={"color": random.sample(V1_COLORS, 1)[0]},
                    restitution=BOUNCINESS,
                    position=Vec2(
                        0, 0
                    ),  # gets overwritten with mouse position in controller
                ),
            },
        ),
    ]

    widgets = [
        PGProfilerWidget(
            position=(10, 10), profiler=profiler, subsection_keys=["world"]
        ),
        PGControllerInfoWidget(position=(10, -100), controllers=controllers),
        PGDebugRecorderWidget(debug_recorder=debug_recorder, camera=view.camera),
    ]

    clock = pygame.time.Clock()

    return (
        view,
        world,
        controllers,
        app_controller,
        profiler,
        clock,
        widgets,
        debug_recorder,
    )


def main_loop(
    view: PygameView,
    world: World,
    controllers: List[AbstractController],
    app_controller: ApplicationController,
    profiler: Profiler,
    clock: pygame.time.Clock,
    widgets: List[AbstractUIElement],
    debug_recorder: DebugRecorder,
):
    running = True

    while running:
        profiler.start_new_frame()

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
            world.step(dt)

        # Render the world
        with profiler.time("render"):
            view.render_background()
            view.render_bodies(world.bodies)
            for widget in widgets:
                widget.render(view.screen)

            view.update_display()

    pygame.quit()  # pylint: disable=no-member


if __name__ == "__main__":
    main_loop(*setup())
