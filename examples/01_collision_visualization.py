from typing import List, Tuple

import pygame

from ppe.engine.common import Body, PolygonShape, Vec2, CircleShape
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
from ppe.utils.view import PygameView, Camera, PygameDebugDrawer
from ppe.utils.controller import (
    CameraPanController,
    CameraZoomController,
    InputState,
    ApplicationController,
    DebugController,
    AbstractController,
    BodyDragController,
    HoverRotateController,
)
from ppe.utils.profiler import Profiler

## Constants
# (initial body config is in the code to not pollute the global namespace)
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
SCREEN_WIDTH_WORLD = 10.0  # World width in physics units
BODY_STYLE = {
    "is_filled": False,
    "outline_width": 3
}

def setup() -> (
    Tuple[
        PygameView,
        World,
        List[AbstractController],
        ApplicationController,
        Profiler,
        pygame.time.Clock,
    ]
):
    pygame.init()  # pylint: disable=no-member

    ## Initialize View
    view = PygameView(
        camera=Camera.with_world_width(
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
            world_width=SCREEN_WIDTH_WORLD,
        ),
        profiler_settings={
            "subsection_keys": ["world"]
        },
        body_style_defaults=BODY_STYLE
    )
    debug_drawer = PygameDebugDrawer(camera=view.camera, surface=view.screen)

    ## Initialize the profiler
    profiler = Profiler()

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
        bodies=initial_bodies,
        debug_drawer=debug_drawer,
        profiler=profiler,
    )

    ## Initialize controllers
    app_controller = ApplicationController(debug_drawer=debug_drawer)
    debug_controller = DebugController(
        controlled_debug_drawer=debug_drawer, debug_drawer=debug_drawer
    )
    controllers: List[AbstractController] = [
        app_controller,
        debug_controller,
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

    clock = pygame.time.Clock()

    return view, world, controllers, app_controller, profiler, clock


def main_loop(
    view: PygameView,
    world: World,
    controllers: List[AbstractController],
    app_controller: ApplicationController,
    profiler: Profiler,
    clock: pygame.time.Clock,
):
    ## Main Loop
    running = True

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
        view.render_profiler(profiler)
        view.update_display()
        # end = time.perf_counter()
        # print(f"Profiler rendering took {((end - start) * 1000):.2f} ms")
        # -> time that is not included in the profiler is negligible (<1 ms)

    ## keeping the window open for debugging purposes
    # import time
    # while True:
    #     time.sleep(0.1)

    pygame.quit()  # pylint: disable=no-member


def main():
    view, world, controllers, app_controller, profiler, clock = setup()
    main_loop(view, world, controllers, app_controller, profiler, clock)


if __name__ == "__main__":
    main()
