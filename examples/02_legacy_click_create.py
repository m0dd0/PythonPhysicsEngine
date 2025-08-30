"""_summary_"""

from typing import List, Tuple
import random

import pygame

# engine components
from ppe.engine.common import Body, PolygonShape, Vec2, CircleShape
from ppe.engine.world import World
from ppe.engine.force_generators import GlobalForceField

# application components
from ppe.utils.view import PygameView, Camera, PygameDebugDrawer
from ppe.utils.controller import (
    InputState,
    ApplicationController,
    DebugController,
    AbstractController,
    BodySpawnController,
)
from ppe.utils.profiler import Profiler
from ppe.utils.colors import V1_COLORS


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

BACKGROUND_COLOR = (255, 255, 255)

STEPS_PER_FRAME = 10


def setup() -> Tuple[
    PygameView,
    World,
    List[AbstractController],
    ApplicationController,
    Profiler,
    pygame.time.Clock,
]:
    pygame.init()  # pylint: disable=no-member

    ## intiiaalize view
    view = PygameView(
        camera=Camera.with_world_width(
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
            world_width=SCREEN_WIDTH_WORLD,
        ),
        profiler_settings={"subsection_keys": ["world"]},
        body_style_defaults=BODY_STYLE_DEFAULTS,
    )
    debug_drawer = PygameDebugDrawer(camera=view.camera, surface=view.screen)

    ## Initialize the profiler
    profiler = Profiler()

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
        bodies=initial_bodies,
        debug_drawer=debug_drawer,
        profiler=profiler,
        force_generators=[GlobalForceField(strength=GRAVITY)],
    )

    ## Initialize controllers
    app_controller = ApplicationController(debug_drawer=debug_drawer)
    controllers: List[AbstractController] = [
        app_controller,
        DebugController(
            controlled_debug_drawer=debug_drawer, debug_drawer=debug_drawer
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
