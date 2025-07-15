import pygame

from ppe.engine.common import Body, PolygonShape, Vec2
from ppe.engine.world import World
from ppe.engine.solvers import NoOpSolver
from ppe.engine.integrators import NoOpIntegrator
from ppe.engine.collision_broad import AABBBroadPhase
from ppe.engine.collision_narrow import DispatchNarrowPhase

# application components
from ppe.utils.view import PygameView, Camera
from ppe.utils.controller import CameraController, InputState

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
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

    # 2. Setup the world simulation
    world = World(
        integrator=NoOpIntegrator(),
        solver=NoOpSolver(),
        broad_phase=AABBBroadPhase(),
        narrow_phase=DispatchNarrowPhase(),
        bodies=[
            Body(
                shape=PolygonShape.create_rectangle(width=2, height=1),
                position=Vec2(0, 0),
                mass=None,  # Static body
                user_data={"color": (50, 50, 50)},
            ),
        ],
    )

    # 3. Initialize controllers
    controllers = [
        CameraController(view.camera, pan_mode="mouse"),
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
    debug_mode = True
    world.debug_drawer = view.create_debug_drawer()

    while running:
        dt = clock.tick(60) / 1000.0

        ## Input
        input_state = InputState.from_pygame()

        if "quit" in input_state.keys_pressed:
            running = False

        if "d" in input_state.keys_pressed:
            debug_mode = not debug_mode
            world.debug_drawer = view.create_debug_drawer() if debug_mode else None

        ## Controller Updates
        for controller in controllers:
            controller.update(input_state, dt)

        ## Physics Update
        world.step(dt)

        ## Rendering
        view.render_background()
        view.render_bodies(world.bodies)

        if world.debug_drawer:
            world.debug_drawer.render_all()

        ## Draw UI Text
        view.render_text(f"Debug Mode (D): {'ON' if debug_mode else 'OFF'}", (10, 10))
        view.render_text(
            "Click to select a box, then use WASD/QE to move/rotate.", (10, 30)
        )
        view.render_text(
            f"Current FPS: {int(clock.get_fps())}", (10, 50)
        )

        pygame.display.flip()

    pygame.quit() # pylint: disable=no-member


if __name__ == "__main__":
    main()
