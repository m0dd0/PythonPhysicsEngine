"""
An example that visualizes the collision detection system.

This example sets up a world with a few static bodies (rectangles and circles).
The bodies do not move on their own, but can be dragged around with the mouse
and rotated by hovering over them.
Note that no collision resolution or other physical constraints are applied.

The debug drawer is used to visualize the different collision detection phases:
- Broad phase: Axis-Aligned Bounding Boxes (AABBs) are shown.
- Narrow phase: Collision points and normals are shown.

Controls:
- Left-click and drag a body to move it.
- Hover over a body to rotate it.
- Use the keyboard arrow keys to pan the camera.
- Use the mouse wheel to zoom the camera.
- Press 'd' to toggle debug drawing.
"""

from typing import List, Tuple

import pygame

from ppe.engine.collision_broad import AABBBroadPhase
from ppe.engine.collision_handlers import (
    CircleVsCircleHandler,
    CircleVsPolygonHandler,
    SatPolygonHandler,
)
from ppe.engine.collision_narrow import DispatchNarrowPhase

# engine components
from ppe.engine.common import Body, CircleShape, PolygonShape, Vec2
from ppe.engine.debug import DebugRecorder
from ppe.engine.integrators import NoOpIntegrator
from ppe.engine.solvers import NoOpSolver
from ppe.engine.world import World
from ppe.frontend.controller import (
    AbstractController,
    ApplicationController,
    BodyDragController,
    CameraPanController,
    CameraZoomController,
    DebugController,
    HoverRotateController,
    InputState,
)

# application components
from ppe.frontend.view import Camera, PygameView
from ppe.frontend.widgets import (
    AbstractUIElement,
    PGControllerInfoWidget,
    PGDebugRecorderWidget,
)
from ppe.utils.profiler import Profiler

## Constants
# (initial body config is in the code to not pollute the global namespace)
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
SCREEN_WIDTH_WORLD = 10.0  # World width in physics units
BODY_STYLE = {"is_filled": False, "outline_width": 3}


def setup() -> Tuple[
    PygameView,
    World,
    List[AbstractController],
    ApplicationController,
    Profiler,
    pygame.time.Clock,
    DebugRecorder,
    List[AbstractUIElement],
]:
    pygame.init()  # pylint: disable=no-member

    ## Initialize the debug recorder
    debug_recorder = DebugRecorder()

    ## Initialize View
    view = PygameView(
        camera=Camera.with_world_width(
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
            world_width=SCREEN_WIDTH_WORLD,
        ),
        body_style_defaults=BODY_STYLE,
    )

    ## define initial bodies
    initial_bodies = [
        Body(
            shape=PolygonShape.create_rectangle(width=0.5, height=0.5),
            position=Vec2(1, -1),
            mass=1,
        ),
        Body(
            shape=PolygonShape.create_rectangle(width=1, height=1),
            position=Vec2(1, 1),
            mass=1,
        ),
        Body(
            shape=CircleShape(radius=0.5),
            position=Vec2(-1, 1),
            mass=1,
        ),
        Body(
            shape=CircleShape(radius=0.5),
            position=Vec2(-1, -1),
            mass=1,
        ),
    ]

    ## Setup the world simulation
    world = World(
        integrator=NoOpIntegrator(),
        solver=NoOpSolver(),
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
        bodies=initial_bodies,
        debug_recorder=debug_recorder,
    )

    ## Initialize controllers
    app_controller = ApplicationController(debug_recorder=debug_recorder)
    controllers: List[AbstractController] = [
        app_controller,
        DebugController(
            controlled_debug_recorder=debug_recorder, debug_recorder=debug_recorder
        ),
        CameraZoomController(view.camera, mode="keyboard"),
        CameraPanController(view.camera, mode="keyboard"),
        BodyDragController(
            world=world,
            camera=view.camera,
            mode="position",
            mouse_button=1,
        ),
        HoverRotateController(world=world, camera=view.camera),
    ]

    widgets = [
        PGControllerInfoWidget(controllers=controllers, position=(10, -150)),
        PGDebugRecorderWidget(debug_recorder=debug_recorder, camera=view.camera),
    ]

    clock = pygame.time.Clock()

    return view, world, controllers, app_controller, clock, debug_recorder, widgets


def main_loop(
    view: PygameView,
    world: World,
    controllers: List[AbstractController],
    app_controller: ApplicationController,
    clock: pygame.time.Clock,
    debug_recorder: DebugRecorder,
    widgets: List[AbstractUIElement],
):
    ## Main Loop
    running = True

    while running:
        # wait until at least 1/60 seconds have passed
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
        try:
            world.step(dt)
        except Exception as e:
            print(f"Error during world step: {e}")
            running = False

        # Render the world
        view.render_background()
        view.render_bodies(world.bodies)
        for widget in widgets:
            widget.render(view.screen)
        view.update_display()

    pygame.quit()  # pylint: disable=no-member


def main():
    view, world, controllers, app_controller, clock, debug_recorder, widgets = setup()
    main_loop(view, world, controllers, app_controller, clock, debug_recorder, widgets)


if __name__ == "__main__":
    main()
