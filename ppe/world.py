from typing import List, Tuple

from ppe.objects import GameObject
from ppe.collision import get_collisions, handle_collision, point_in_box
from ppe.vector import Vector


class World:
    def __init__(
        self, objects: List[GameObject], world_bbox: Tuple[Vector, Vector] = None
    ):
        self.world_bbox = world_bbox
        self.objects = objects
        self._collisions = tuple()

    @property
    def collisions(self):
        return self._collisions

    def update(self, dt: float):
        for obj in self.objects:
            obj.update(dt)

        collisions = get_collisions(self.objects)
        for coll in collisions:
            handle_collision(coll)

        if self.world_bbox:
            objects_in_world = [
                obj for obj in self.objects if point_in_box(obj.pos, self.world_bbox)
            ]
            self.objects = objects_in_world

        self._collisions = tuple(collisions)
