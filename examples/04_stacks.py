"""
Example 04: Stacks
This example contains some benchamrk scenarios where a fixed number of bodies is spawned
initially in a challenging configuration.
"""

from typing import List, Tuple

import pygame

# engine components
from ppe.engine.common import Body, PolygonShape, Vec2
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
from ppe.engine.debug import DebugRecorder

# application components
from ppe.frontend.view import PygameView, Camera
from ppe.frontend.controller import (
    ApplicationController,
    DebugController,
    AbstractController,
    CameraZoomController,
)
from ppe.frontend.widgets import PGProfilerWidget, PGControllerInfoWidget
from ppe.frontend.colors import V1_COLORS
from ppe.utils.profiler import Profiler
from ppe.utils.loops import main_loop


## Constants
# (initial body config is in the code to not pollute the global namespace)
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
SCREEN_WIDTH_WORLD = 10.0  # World width in physics units
BODY_STYLE_DEFAULTS = {"circle_orientation_line": True}

BODY_BOUNCINESS = 0.5
GRAVITY = Vec2(0, -9.81)

GROUND_BODY = Body(  # ground
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
    restitution=BODY_BOUNCINESS,
)

BODIES_STACK = [
    Body.create_with_density(
        shape=PolygonShape.create_rectangle(4 - i * 0.5, 0.3),
        position=Vec2(0, 0.5 + 0.35 * i),
        restitution=BODY_BOUNCINESS,
        density=0.1,
        user_data={"color": V1_COLORS[i % len(V1_COLORS)]},
    )
    for i in range(5)
]

BODIES_PYRAMID = [
    # TODO
]


def setup() -> Tuple[
    PygameView,
    World,
    List[AbstractController],
    ApplicationController,
    Profiler,
    pygame.time.Clock,
]:
    pygame.init()  # pylint: disable=no-member

    # initialize debug_recorder and profiler
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
        # profiler_settings={"subsection_keys": ["world"]},
        body_style_defaults=BODY_STYLE_DEFAULTS,
    )
    ## Initialize controllers
    app_controller = ApplicationController(debug_recorder=debug_recorder)
    controllers: List[AbstractController] = [
        app_controller,
        DebugController(
            controlled_debug_recorder=debug_recorder,
            debug_recorder=debug_recorder,
            initial_debug_mode=False,
        ),
        CameraZoomController(view.camera),
    ]

    ## initialize widgets
    widgets = [
        PGProfilerWidget(
            profiler=profiler, position=(10, 10), subsection_keys=["world"]
        ),
        PGControllerInfoWidget(controllers=controllers, position=(10, -100)),
    ]

    ## Setup the world simulation
    world = World(
        solver=IterativeImpulseSolver(),
        integrator=SemiImplicitEulerIntegrator(),
        bodies=[GROUND_BODY, *BODIES_STACK],
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


    return view, world, controllers, app_controller, profiler, widgets


def main():
    view, world, controllers, app_controller, profiler, widgets = setup()
    main_loop(
        view,
        world,
        controllers,
        app_controller,
        profiler,
        widgets,
        target_fps=60,
        use_fixed_simulation_timestep=False,
        cap_fps=True,
        substeps=1,
    )


if __name__ == "__main__":
    main()
