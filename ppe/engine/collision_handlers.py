"""
Module containing classes for handling collisions between different shapes.

The module contains the following classes:

- `AbstractCollisionHandler`: An abstract base class for all collision handlers.
- `CircleVsCircleHandler`: Generates contacts for two colliding circles.
- `CircleVsPolygonHandler`: Generates contacts for a circle and a polygon.
- `SatPolygonHandler`: Generates contacts for two colliding convex polygons using SAT.

"""

import math
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

from ppe.engine.common import Body, CircleShape, PolygonShape, Contact, Vec2
from ppe.utils.debug import DebugRecorder


class AbstractCollisionHandler(ABC):
    """Defines the interface for a specific collision handler between two shapes."""

    def __init__(self, debug_recorder: Optional[DebugRecorder] = None):
        """
        Initializes the collision handler.

        Args:
            debug_recorder: An optional debug drawer for visualizing collisions.
        """
        self.debug_recorder = debug_recorder

    @abstractmethod
    def generate_contact(self, body_a: Body, body_b: Body) -> Optional[Contact]:
        """
        Takes two bodies and returns a Contact object if they collide,
        otherwise returns None.

        Args:
            body_a: The first body.
            body_b: The second body.

        Returns:
            A Contact object if a collision occurred, otherwise None.
        """
        pass


class CircleVsCircleHandler(AbstractCollisionHandler):
    """Generates contacts for two colliding circles."""

    def generate_contact(self, body_a: Body, body_b: Body) -> Optional[Contact]:
        """Checks for collision between two circles.
        
        Args:
            body_a: The first body.
            body_b: The second body.

        Returns:
            A Contact object if a collision occurred, otherwise None.
        """
        assert body_a.shape.get_type() == "circle"
        assert body_b.shape.get_type() == "circle"

        # we define body_a to be the reference body and body_b to be the incident body
        # we rename the variables to make the naming consistent
        reference_body, incident_body = body_a, body_b

        reference_shape: CircleShape = reference_body.shape
        incident_shape: CircleShape = incident_body.shape

        ref_to_inc = incident_body.position - reference_body.position
        sum_radii = reference_shape.radius + incident_shape.radius

        # using the squared distance to avoid a sqrt call for performance
        dist_sq = ref_to_inc.length_squared()
        # if self.debug_recorder:
        #     # draw line from reference body to incident body
        #     self.debug_recorder.draw_line(
        #         reference_body.position, body_b.position, color=(0, 0, 255), arrow=True
        #     )

        if dist_sq >= sum_radii * sum_radii:
            return None

        dist = math.sqrt(dist_sq)
        penetration = sum_radii - dist
        normal = ref_to_inc.normalize()
        contact_point = incident_body.position - normal * incident_shape.radius

        return Contact(
            reference_body, incident_body, normal, penetration, [contact_point]
        )


class SatPolygonHandler(AbstractCollisionHandler):
    """Generates contacts for two (potentially) colliding convex polygons using SAT."""

    def _clip_incident_edge(
        self,
        incident_edge: Tuple[Vec2, Vec2],
        clip_plane_normal: Vec2,
        clip_plane_offset: float,
    ) -> Tuple[Vec2, Vec2]:
        """
        Clip an incident edge against a clipping plane defined by a normal and offset.

        Args:
            incident_edge (Tuple[Vec2, Vec2]): The edge to clip defined by its two vertices.
            clip_plane_normal (Vec2): The normal of the clipping plane.
            clip_plane_offset (float): The offset of the clipping plane.

        Returns:
            Tuple[Vec2, Vec2]: The clipped edge.
        """
        v1, v2 = incident_edge
        clipped_points = []

        # Calculate the signed distance from each vertex to the plane (>= 0 means inside the plane)
        d1 = v1.dot(clip_plane_normal) - clip_plane_offset
        d2 = v2.dot(clip_plane_normal) - clip_plane_offset

        # Keep points that are on the "inside" of the plane
        if d1 >= 0:
            clipped_points.append(v1)
        if d2 >= 0:
            clipped_points.append(v2)

        assert (
            len(clipped_points) > 0
        ), "At least one point should be inside the clipping plane. Otherwise, there is no intersection/collision."

        # If the points are on opposite sides, find the intersection point by linear interpolation
        if d1 * d2 < 0:
            assert (
                len(clipped_points) == 1
            ), "There should be exactly one point inside the clipping plane."
            t = d1 / (d1 - d2)
            intersection_point = v1 + (v2 - v1) * t
            clipped_points.append(intersection_point)

        assert (
            len(clipped_points) == 2
        ), "There should be exactly two points after clipping the incident edge."

        return tuple(clipped_points)

    def _distances_from_edge(
        self, test_points: List[Vec2], edge_start: Vec2, edge_normal: Vec2
    ) -> float:
        """Calculates the signed distance from a point to an edge defined by a start point and a normal."""
        return [
            (test_point - edge_start).dot(edge_normal) for test_point in test_points
        ]

    def _find_overlap(
        self,
        own_normals: List[Vec2],
        own_vertices: List[Vec2],
        other_vertices: List[Vec2],
    ) -> Tuple[bool, float, Vec2, Tuple[Vec2, Vec2]]:
        """
        Checks whether there is a a given normal along which the projected vertices 
        of the other polygon are in front and behind the corresponding edge.
        If this is the case there might be an overlap along this normal of the two polygons.

        Args:
            own_normals (List[Vec2]): The normals of the edges of the polygon.
            own_vertices (List[Vec2]): The vertices of the polygon.
            other_vertices (List[Vec2]): The vertices of the other polygon.

        Returns:
            Tuple[bool, float, Vec2, Vec2]: A tuple containing information about the overlap:
                - bool: Whether the two polygons overlap along any of the given normals.
                - float: The overlap (the distance along the collision normal between the closest points of the two polygons).
                - Vec2: The collision normal (the normal of the edge that is being penetrated).
                - Tuple[Vec2, Vec2]: The reference edge (the edge of the first polygon that is being penetrated).
        """
        min_overlap = float("inf")
        collision_normal = None
        reference_edge = None
        # the shape whose normal has the smallest overlap "owns" the collision normal
        # this corresponding edge of this normal is the reference edge (getting penetrated)
        # contrary the incident edge (penetrating one) is defined as the edge on the incident 
        # shape whose normal is most aligned (but pointing in the opposite direction) with 
        # the collision normal
        # note that a definition using the most penetrating point would not work as it
        # would not work in the case of parallel edges (e.g. in a rectangle)

        # find overlap, reference edge and collision normal
        for i, normal_a_i in enumerate(own_normals):
            # checking onyl for overlap is not enough since in the case of parallel edges (e.g. in a rectangle)
            # the overlap along the normals of parallel edges is the same
            # in this case the opposite edge can be wrongly selected as the reference edge
            # thus we use another criterion: we check whether the vertices of the other shape are on different sides
            # of the edge defined by the reference edge
            # if this is the case, we save the overlap by computing the distance of the farthest vertex of the other shape
            # to the reference edge along the negative of the outward pointing normal

            distances = self._distances_from_edge(other_vertices, own_vertices[i], normal_a_i)
            # check the sign of the distances to know whether they are behind or in front of the edge
            if all(d >= 0 for d in distances):
                return False, None, None, None  # all vertices are in front of the edge -> no collision, we found a separating axis
            elif all(d <= 0 for d in distances):
                continue  # all points are "behind" the edge -> the opposite edge is "responible" for detecting potential collisions
            else:
                # some edges are in front of and other are behind the edge -> we have an overlap
                # the overlap is simply the distnace of the most penetrating point to the edge

                overlap = -min(distances)
                if overlap < min_overlap:
                    min_overlap = overlap
                    collision_normal = normal_a_i
                    reference_edge = (
                        own_vertices[i],
                        own_vertices[(i + 1) % len(own_vertices)],
                    )

        return True, min_overlap, collision_normal, reference_edge

    def generate_contact(self, body_a: Body, body_b: Body) -> Optional[Contact]:
        """
        Checks for collision between two polygons using the Separating Axis Theorem (SAT).

        SAT is a method to detect whether two convex shapes are overlapping.
        It is based on the idea that if two shapes do not overlap, there exists an axis
        (a line perpendicular to the edge of one of the shapes) on which the projections
        of the shapes do not overlap.

        If no such axis exists, the shapes are overlapping.

        Args:
            body_a (Body): The first body.
            body_b (Body): The second body.

        Returns:
            Contact: A Contact object if a collision occurred, otherwise None.
        """
        assert body_a.shape.get_type() == "polygon"
        assert body_b.shape.get_type() == "polygon"

        verts_a = body_a.shape.get_world_space_vertices(body_a.position, body_a.angle)
        verts_b = body_b.shape.get_world_space_vertices(body_b.position, body_b.angle)

        normals_a = body_a.shape.get_normals(body_a.position, body_a.angle)
        normals_b = body_b.shape.get_normals(body_b.position, body_b.angle)

        is_collision_a, min_overlap_a, collision_normal_a, reference_edge_a = self._find_overlap(
            normals_a, verts_a, verts_b
        )
        if not is_collision_a:
            return None
        
        is_collision_b, min_overlap_b, collision_normal_b, reference_edge_b = self._find_overlap(
            normals_b, verts_b, verts_a
        )
        if not is_collision_b:
            return None

        if min_overlap_a < min_overlap_b:
            min_overlap = min_overlap_a
            collision_normal = collision_normal_a
            reference_edge = reference_edge_a
            incident_shape_normals = normals_b
            incident_shape_verts = verts_b
            reference_body = body_a
            incident_body = body_b
        else:
            min_overlap = min_overlap_b
            collision_normal = collision_normal_b
            reference_edge = reference_edge_b
            incident_shape_normals = normals_a
            incident_shape_verts = verts_a
            reference_body = body_b
            incident_body = body_a

        incident_edge_index = min(
            range(len(incident_shape_normals)),
            key=lambda i: incident_shape_normals[i].dot(collision_normal),
        )
        incident_edge = (
            incident_shape_verts[incident_edge_index],
            incident_shape_verts[(incident_edge_index + 1) % len(incident_shape_verts)],
        )

        # debug drawing
        if self.debug_recorder is not None:
            # draw the reference edge
            self.debug_recorder.add_line(
                reference_edge[0],
                reference_edge[1],
                color=(0, 255, 0),
                arrow=True,
            )

            # draw the collision normal
            # self.debug_recorder.add_line(
            #     reference_edge[0],
            #     reference_edge[0] + collision_normal * min_overlap,
            #     color=(255, 255, 0),
            #     arrow=True,
            # )

            # draw the incident edge
            self.debug_recorder.add_line(
                incident_edge[0],
                incident_edge[1],
                color=(0, 0, 255),
                arrow=True,
            )

        ### clip the incident edge against the perpendicular planes at the end of the reference edge
        # define the clipping planes: each of the planes is defined by a normal and an offset (how far the plane is moved away from the origin along its normal)
        clip_plane_1_normal = (reference_edge[1] - reference_edge[0]).normalize()
        clip_plane_2_normal = (reference_edge[0] - reference_edge[1]).normalize()
        clip_plane_1_offset = reference_edge[0].dot(clip_plane_1_normal)
        clip_plane_2_offset = reference_edge[1].dot(clip_plane_2_normal)

        # clip the incident edge corners are against the first plane ...
        clipped_points = self._clip_incident_edge(
            incident_edge, clip_plane_1_normal, clip_plane_1_offset
        )
        # ... and against the second plane
        clipped_points = self._clip_incident_edge(
            clipped_points, clip_plane_2_normal, clip_plane_2_offset
        )

        # keep only clipped points that are behind the reference edge
        clipped_points = [
            p
            for p in clipped_points
            if (p - reference_edge[0]).dot(collision_normal) < 0
        ]

        return Contact(
            reference_body, incident_body, collision_normal, min_overlap, clipped_points
        )


class CircleVsPolygonHandler(AbstractCollisionHandler):
    """Generates contacts for a circle and a polygon."""

    def generate_contact(self, body_a: Body, body_b: Body) -> Optional[Contact]:
        """
        Checks for collision between a circle and a polygon.

        This handler generates a single contact if a collision is detected.
        The contact normal points outwards from the circle and into the polygon.
        The contact point is the point on the polygon's surface closest to the circle's center.
        The penetration depth is the distance required to separate the circle and the polygon.

        Args:
            body_a (Body): The circle body.
            body_b (Body): The polygon body.

        Returns:
            Contact: A Contact object if a collision occurred, otherwise None.
        """

        # the dispatch system ensures that the passed bodies are ordered by their shape type ID
        # the shape type ID is 0 for circles and 1 for polygons
        circle_body = body_a
        polygon_body = body_b
        assert circle_body.shape.get_type() == "circle"
        assert polygon_body.shape.get_type() == "polygon"

        circle_shape: CircleShape = circle_body.shape
        poly_shape: PolygonShape = polygon_body.shape

        verts = poly_shape.get_world_space_vertices(
            polygon_body.position, polygon_body.angle
        )
        closest_point = None
        min_dist_sq = float("inf")

        for i_vert in range(len(verts)):  # pylint: disable=consider-using-enumerate
            # compute edge vector on the polygon and the vector from the circle center to the polygon vertices on the edge
            p1 = verts[i_vert]
            p2 = verts[(i_vert + 1) % len(verts)]
            edge = p2 - p1  # from p1 to p2
            line_vec = circle_body.position - p1  # from p1 to circle center

            # Project the circle center onto the edge to find the closest point
            t = line_vec.dot(edge) / edge.length_squared()
            t = max(
                0, min(1, t)
            )  # clamp t to [0, 1] (0 means closest point on the line is p1, 1 means p2)
            closest_on_edge = p1 + edge * t

            # if self.debug_recorder:
            #     # draw line from circle center to closest point on edge in blue
            #     self.debug_recorder.draw_line(
            #         body_a.position, closest_on_edge, color=(0, 0, 255)
            #     )

            dist_sq = (circle_body.position - closest_on_edge).length_squared()
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_point = closest_on_edge

        assert (
            closest_point is not None
        ), "Closest point should be set if we reach here."

        if min_dist_sq >= circle_shape.radius * circle_shape.radius:
            return None

        dist = math.sqrt(min_dist_sq)
        # normal points from the closest point on the polygon edge to the circle center
        normal = (circle_body.position - closest_point).normalize()
        penetration = circle_shape.radius - dist
        collision_point = closest_point - normal * penetration

        return Contact(
            polygon_body, circle_body, normal, penetration, [collision_point]
        )
