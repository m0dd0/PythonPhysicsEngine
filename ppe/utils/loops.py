from typing import List

import pygame

from ppe.engine.world import World

# application components
from ppe.utils.view import PygameView
from ppe.utils.controller import (
    InputState,
    ApplicationController,
    AbstractController,
)
from ppe.utils.profiler import Profiler

def main_loop(
    view: PygameView,
    world: World,
    controllers: List[AbstractController],
    app_controller: ApplicationController,
    profiler: Profiler,
    target_dt: int = 60,
    force_dt: bool = False,
    wait_for_dt: bool = True,
):
    clock = pygame.time.Clock()

    running = True

    while running:
        profiler.start_frame()

        if wait_for_dt and force_dt:
            clock.tick(1/target_dt)
            dt = target_dt
        elif wait_for_dt and not force_dt:
            dt = clock.tick(1/target_dt) / 1000.0
        elif not wait_for_dt and force_dt:
            dt = target_dt
        elif not wait_for_dt and not force_dt:
            dt = clock.tick() / 1000.0
        else:
            assert False

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
            world.debug_drawer.render_all()
            view.render_info([c.action_description for c in controllers])

        # Render profiler after timing is complete
        profiler.end_frame()
        view.render_profiler(profiler)
        view.update_display()

    pygame.quit()  # pylint: disable=no-member