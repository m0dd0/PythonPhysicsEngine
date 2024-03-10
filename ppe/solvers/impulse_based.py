from ppe.solvers.base import SolverBase
from typing import List

from ppe.collision.collision_detector import Collision
from ppe.joints import Joint


class ImpulseBasedSolver(SolverBase):
    def solve(
        self, collisions: List[Collision], joints: List[Joint], forces, dt: float
    ):
        ### https://www.chrishecker.com/images/e/e7/Gdmphys3.pdf ###
        # https://en.wikipedia.org/wiki/Elastic_collision#Two-dimensional
        # https://en.wikipedia.org/wiki/Coefficient_of_restitution#Speeds_after_impact
        # https://de.wikipedia.org/wiki/Sto%C3%9F_(Physik)#Realer_Sto%C3%9F

        for coll in collisions:
            assert not (coll.bodyA.kinematic and coll.bodyB.kinematic)

            # 1. Move objects so they don't overlap anymore
            # we never move kinematic objects
            # this might introduce new collisions, so we need to re-run the collision detection
            # it might also cause numerical instability
            # TODO check for alternative approach in e.g. pixelphysics tutiral
            if not coll.bodyA.kinematic and not coll.bodyB.kinematic:
                coll.bodyA.shape.com -= coll.normal * coll.depth * 0.5
                coll.bodyB.shape.com += coll.normal * coll.depth * 0.5
            elif coll.bodyA.kinematic:
                coll.bodyB.shape.com += coll.normal * coll.depth
            else:
                coll.bodyA.shape.com -= coll.normal * coll.depth

            restitution = (coll.bodyA.bounciness + coll.bodyB.bounciness) * 0.5

            impulse = (
                -(1 + restitution) * (coll.bodyA.vel - coll.bodyB.vel).dot(coll.normal)
            ) / (1 / coll.bodyA.mass + 1 / coll.bodyB.mass)

            if not coll.bodyA.kinematic:
                coll.bodyA.vel += impulse / coll.bodyA.mass * coll.normal
            if not coll.bodyB.kinematic:
                coll.bodyB.vel -= impulse / coll.bodyB.mass * coll.normal
