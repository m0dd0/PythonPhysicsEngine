from typing import List

from ppe.objects import GameObject
from ppe.collision import get_collisions, handle_collision


class World:
    def __init__(self, objects: List[GameObject]):
        self.objects = objects

    def update(self, dt: float):
        for obj in self.objects:
            obj.update(dt)

        collisions = get_collisions(self.objects)
        for coll in collisions:
            # TODO handle collison: update velocities
            handle_collision(coll)
