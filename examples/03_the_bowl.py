"""
Example 03: "The Bowl"
An example demonstrating a "bowl" made of static walls.
Bodies can be spawned by clicking on the screen.
This examples poses a stress test on the solver as there are many simultaneous collisions
that need to be resolved.
"""

from typing import List, Tuple
import random

import pygame

# engine components
from ppe.engine.common import Body, PolygonShape, Vec2, CircleShape
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
from ppe.frontend.view import PygameView, Camera
from ppe.frontend.controller import (
    CameraPanController,
    CameraZoomController,
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
    AbstractUIElement,
    PGProfilerWidget,
    PGControllerInfoWidget,
)

## Constants
# (initial body config is in the code to not pollute the global namespace)
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
SCREEN_WIDTH_WORLD = 10.0  # World width in physics units
BODY_STYLE_DEFAULTS = {}

CIRCLE_SPAWN_RADIUS_RANGE = (0.1, 0.3)
POLYGON_SPAWN_SIDE_RANGE = (0.1, 0.5)
GRAVITY = Vec2(0, -9.81)
BOUNCINESS = 0.8


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

    ## Initialize View
    view = PygameView(
        camera=Camera.with_world_width(
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
            world_width=SCREEN_WIDTH_WORLD,
            position=Vec2(0, 2.5),
        ),
        body_style_defaults=BODY_STYLE_DEFAULTS,
    )

    ## initialize bodies
    initial_bodies = [
        # left wall
        Body(
            shape=PolygonShape.create_rectangle(width=0.5, height=3),
            position=Vec2(-3.75, 2.75),
            mass=None,  # static body
            user_data={"color": [0, 0, 0]},
        ),
        # right wall
        Body(
            shape=PolygonShape.create_rectangle(width=0.5, height=3),
            position=Vec2(3.75, 2.75),
            mass=None,  # static body
            user_data={"color": [0, 0, 0]},
        ),
        # bottom wall
        Body(
            shape=PolygonShape.create_rectangle(width=8, height=0.5),
            position=Vec2(0, 1),
            mass=None,  # static body
            user_data={"color": [0, 0, 0]},
        ),
    ]

    ## Setup the world simulation
    world = World(
        integrator=SemiImplicitEulerIntegrator(),
        solver=IterativeImpulseSolver(debug_recorder=debug_recorder),
        broad_phase=AABBBroadPhase(debug_recorder=debug_recorder),
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
        force_generators=[GlobalForceField(strength=GRAVITY)],
        bodies=initial_bodies,
        debug_recorder=debug_recorder,
        profiler=profiler,
    )

    ## Initialize controllers
    app_controller = ApplicationController(debug_recorder=debug_recorder)
    debug_controller = DebugController(
        controlled_debug_recorder=debug_recorder, debug_recorder=debug_recorder
    )
    controllers: List[AbstractController] = [
        app_controller,
        debug_controller,
        CameraZoomController(view.camera, mode="keyboard"),
        CameraPanController(view.camera, mode="keyboard"),
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

    ## initialize widgets
    widgets = [
        PGProfilerWidget(profiler=profiler, position=(10, 10)),
        PGControllerInfoWidget(controllers=controllers, position=(10, -100)),
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
            view.render_debug_recorder(debug_recorder)
            view.render_info([c.action_description for c in controllers])
            for widget in widgets:
                widget.render(view.screen)

        view.update_display()

    pygame.quit()  # pylint: disable=no-member


if __name__ == "__main__":
    main_loop(*setup())
