from typing import List

from ppe.objects import GameObject
from ppe.collision import get_collisions, handle_collision


class World:
    def __init__(self, objects: List[GameObject]):
        self.objects = objects

    def update(self, dt: float):
        for obj in self.objects:
            obj.update(dt)

        for obj in self.objects:
            obj.color = (255, 255, 255)

        collisions = get_collisions(self.objects)
        for coll in collisions:
            # TODO handle collison: update velocities
            coll.obj1.color = (255, 0, 0)
            handle_collision(coll)
