# import time
# import logging
# import math

# import pygame

# from ppe.world import World
# from ppe.vector import Vector
# from ppe.bodies import Ball, ConvexPolygon
# from ppe.visualization import PyGameVisualizer

# BALL_RADIUS = 0.5
# BALL_INITIAL_POS = Vector(1, 1)
# FIXED_BOX_POS = Vector(2, 3)
# FIXED_BOX_SIZE = (1, 1)
# FIXED_BALL_POS = Vector(4, 3)
# FIXED_BALL_RADIUS = 0.5
# ROTATING_RECTANGLE_SIZE = (0.2, 2)
# ROTATING_RECTANGLE_POSITON = Vector(7, 3)
# ROTATING_RECTANGLE_ANGULAR_VEL = 50 * (2 * math.pi / 360)  # 50 degree per second

# SCREEN_DIMENSIONS_WORLD = (9, 5)
# SCALE = 150
# BACKGROUND_COLOR = (0, 0, 0)
# OBJECT_COLOR = (255, 255, 255)
# COLLISION_COLOR = (255, 0, 0)
# COLLISION_POINT_RECT_SIZE = 0.1

# FPS = 60
# STEPS_PER_FRAME = 1
# MANUAL_MOVEMENT_PER_STEP = 0.03

# logging.basicConfig(level=logging.WARNING)


# def collision_callback(obj, coll):
#     pass


# def draw_collision_point(screen, visualizer, coll):
#     coll_rect_world = [
#         Vector(
#             coll.contact_point_1.x - COLLISION_POINT_RECT_SIZE / 2,
#             coll.contact_point_1.y - COLLISION_POINT_RECT_SIZE / 2,
#         ),
#         Vector(
#             coll.contact_point_1.x + COLLISION_POINT_RECT_SIZE / 2,
#             coll.contact_point_1.y - COLLISION_POINT_RECT_SIZE / 2,
#         ),
#         Vector(
#             coll.contact_point_1.x + COLLISION_POINT_RECT_SIZE / 2,
#             coll.contact_point_1.y + COLLISION_POINT_RECT_SIZE / 2,
#         ),
#         Vector(
#             coll.contact_point_1.x - COLLISION_POINT_RECT_SIZE / 2,
#             coll.contact_point_1.y + COLLISION_POINT_RECT_SIZE / 2,
#         ),
#     ]

#     coll_rect_pixel = [visualizer.world_2_pixel_coord(pos) for pos in coll_rect_world]

#     pygame.draw.polygon(
#         screen, COLLISION_COLOR, [v.to_tuple() for v in coll_rect_pixel]
#     )


# if __name__ == "__main__":
#     screen = pygame.display.set_mode(
#         (SCREEN_DIMENSIONS_WORLD[0] * SCALE, SCREEN_DIMENSIONS_WORLD[1] * SCALE)
#     )
#     visualizer = PyGameVisualizer(screen, scale=SCALE)

#     fixed_box = ConvexPolygon.create_rectangle(
#         pos=FIXED_BOX_POS,
#         height=FIXED_BOX_SIZE[0],
#         width=FIXED_BOX_SIZE[1],
#         style_attributes={"color": OBJECT_COLOR},
#         collision_callbacks=[collision_callback],
#         name="fixed_box",
#     )
#     fixed_ball = Ball(
#         pos=FIXED_BALL_POS,
#         radius=FIXED_BALL_RADIUS,
#         style_attributes={"color": OBJECT_COLOR},
#         collision_callbacks=[collision_callback],
#         name="fixed_ball",
#     )
#     rotating_rectangle = ConvexPolygon.create_rectangle(
#         pos=ROTATING_RECTANGLE_POSITON,
#         height=ROTATING_RECTANGLE_SIZE[0],
#         width=ROTATING_RECTANGLE_SIZE[1],
#         style_attributes={"color": OBJECT_COLOR},
#         angular_vel=ROTATING_RECTANGLE_ANGULAR_VEL,
#         collision_callbacks=[collision_callback],
#         name="rotating_rectangle",
#         fixed=True,
#     )
#     ball = Ball(
#         pos=BALL_INITIAL_POS,
#         radius=BALL_RADIUS,
#         style_attributes={"color": OBJECT_COLOR},
#         collision_callbacks=[collision_callback],
#         name="ball",
#     )

#     world = World(
#         [fixed_box, fixed_ball, rotating_rectangle, ball],
#         world_bbox=(Vector(0, 0), Vector(*SCREEN_DIMENSIONS_WORLD)),
#     )

#     clock = pygame.time.Clock()

#     running = True
#     while running:
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 running = False

#         # control ball with arrow keys
#         keys = pygame.key.get_pressed()
#         if keys[pygame.K_RIGHT]:
#             ball.pos += Vector(MANUAL_MOVEMENT_PER_STEP, 0)
#         elif keys[pygame.K_LEFT]:
#             ball.pos += Vector(-MANUAL_MOVEMENT_PER_STEP, 0)
#         elif keys[pygame.K_UP]:
#             ball.pos += Vector(0, MANUAL_MOVEMENT_PER_STEP)
#         elif keys[pygame.K_DOWN]:
#             ball.pos += Vector(0, -MANUAL_MOVEMENT_PER_STEP)

#         physic_step_start = time.perf_counter()
#         for _ in range(STEPS_PER_FRAME):
#             world.update(1 / (FPS * STEPS_PER_FRAME))
#         physic_step_duration = time.perf_counter() - physic_step_start

#         render_step_start = time.perf_counter()
#         screen.fill(BACKGROUND_COLOR)
#         visualizer.draw(world)
#         for coll in world.collisions:
#             draw_collision_point(screen, visualizer, coll)
#         pygame.display.flip()
#         render_step_duration = time.perf_counter() - render_step_start

#         logging.info(f"{physic_step_duration:.3f}s, {render_step_duration:.3f}s")
#         if physic_step_duration + render_step_duration > 1 / FPS:
#             logging.warning(
#                 f"Warning: frame took {physic_step_duration} + {render_step_duration:.3f} = {physic_step_duration + render_step_duration:.3f}s, "
#                 f"which is longer than 1/{FPS:.0f}s = {1/FPS:.3f}s."
#             )

#         clock.tick(FPS)
