import functools
import math
import random
from abc import ABC, abstractmethod
from typing import List, Tuple

from ppe.engine.common import Vec2


class Shape(ABC):
    """An abstract base class for all collision shapes.
    Note that a shape does NOT have any notion of rotation or translations and is always defined
    in its own coordiante system. I.e. it does not know about the position of the body it is attached to.
    Thus most of its utility methods (that are dependent on the shape) require extra information from the body it is attached to.
    """

    @abstractmethod
    def get_type(self) -> str:
        """Returns the type of the shape as a string."""
        # we use a get_type method over isinstance checks to have less coupling between the shape and the rest of the code
        # also it provides more flexibility for future shape types
        pass

    @abstractmethod
    def calculate_inertia(self, mass: float) -> float:
        """Calculates the moment of inertia for this shape."""
        pass

    @abstractmethod
    def get_aabb(self, position: Vec2, angle: float) -> Tuple[Vec2, Vec2]:
        """
        Calculates the world-space AABB of the shape.

        Args:
            position: The world-space position of the shape's body.
            angle: The world-space angle of the shape's body.

        Returns:
            A tuple containing the min and max points of the AABB.
        """
        pass

    @abstractmethod
    def is_point_inside(self, point: Vec2, position: Vec2, angle: float) -> bool:
        """
        Checks if a point is inside the shape in world space.

        Args:
            point: The point to check.
            position: The world-space position of the shape's body.
            angle: The world-space angle of the shape's body.

        Returns:
            True if the point is inside the shape, False otherwise.
        """
        pass

    @abstractmethod
    def get_area(self) -> float:
        """
        Calculates the area of the shape.

        Returns:
            The area of the shape.
        """
        pass


class CircleShape(Shape):
    def __init__(self, radius: float):
        """Initializes a CircleShape with the given radius.

        Args:
            radius (float): The radius of the circle.
        """
        self.radius = radius

    @classmethod
    def create_random_circle(
        cls, min_radius: float = 0.05, max_radius: float = 1.0
    ) -> "CircleShape":
        """
        Creates a random circle shape with a radius between min_radius and max_radius.

        Args:
            min_radius: The minimum radius of the circle.
            max_radius: The maximum radius of the circle.

        Returns:
            A CircleShape with a random radius.
        """
        radius = random.uniform(min_radius, max_radius)
        return cls(radius)

    def get_type(self) -> str:
        return "circle"

    def calculate_inertia(self, mass: float) -> float:
        return 0.5 * mass * self.radius * self.radius

    def get_aabb(self, position: Vec2, angle: float) -> Tuple[Vec2, Vec2]:
        """
        Calculates the Axis-Aligned Bounding Box (AABB) of the circle in world space.

        Args:
            position (Vec2): The world-space position of the circle's body.
            angle (float): The world-space angle of the circle's body.

        Returns:
            A tuple containing the min and max points of the AABB.
        """
        # at the aabb narrow phase the aabbs get accessed for each pair of bodies and currently it is recomputed every time
        # however, this operation is so cheap that the overhead of caching is not worth it
        radius = self.radius
        return (
            Vec2(position.x - radius, position.y - radius),
            Vec2(position.x + radius, position.y + radius),
        )

    def is_point_inside(self, point: Vec2, position: Vec2, angle: float) -> bool:
        """
        Checks if a point is inside the circle in world space.

        Args:
            point (Vec2): The point to check.
            position (Vec2): The world-space position of the circle's body.
            angle (float): The world-space angle of the circle's body
                (ignored for circles but required for consistency with other shapes).

        Returns:
            True if the point is inside the circle, False otherwise.
        """
        distance_squared = (point.x - position.x) ** 2 + (point.y - position.y) ** 2
        return distance_squared <= self.radius**2

    def get_area(self) -> float:
        return math.pi * self.radius**2


class PolygonShape(Shape):
    def __init__(self, vertices: List[Vec2]):
        """
        Initializes and validates a convex polygon shape.

        The constructor will:
        1. Remove co-linear vertices.
        2. Ensure the vertex winding order is counter-clockwise (CCW).
        3. Validate that the final shape is convex.
        4. Center the vertices around the origin (0,0).

        Args:
            vertices (List[Vec2]): A list of Vec2 vertices defining the polygon's shape.
        """
        if len(vertices) < 3:
            raise ValueError("A polygon must have at least 3 vertices")

        # 1. Remove co-linear points
        cleaned_vertices = self._remove_colinear(vertices)
        if len(cleaned_vertices) < 3:
            raise ValueError(
                "Polygon has fewer than 3 unique vertices after removing co-linear points."
            )

        # 2. Check winding order using signed area (shoelace formula)
        signed_area = self._get_signed_area(cleaned_vertices)
        if signed_area < 0:
            # If area is negative, vertices are clockwise, so reverse them
            cleaned_vertices.reverse()

        # 3. Check for convexity
        if not self._is_convex(cleaned_vertices):
            raise ValueError("The provided vertices do not form a convex polygon.")

        # 4. Center the vertices around the origin (0,0) for better numerical stability
        cleaned_vertices = self._center_vertices(cleaned_vertices)

        self.vertices = cleaned_vertices

    def _remove_colinear(self, vertices: List[Vec2]) -> List[Vec2]:
        """
        Removes vertices that are co-linear with their neighbors.

        Two vertices are considered co-linear if the cross product of the two
        edge vectors is zero. This function iterates over the input vertices,
        checks for co-linear vertices, and returns a new list with the
        co-linear vertices removed.

        Args:
            vertices (List[Vec2]): A list of Vec2 vertices defining the polygon's shape.

        Returns:
            List[Vec2]: A new list with the co-linear vertices removed.
        """
        cleaned = []
        for i in range(len(vertices)):  # pylint: disable=consider-using-enumerate
            p_prev = vertices[i - 1]
            p_curr = vertices[i]
            p_next = vertices[(i + 1) % len(vertices)]

            # Check the cross product of the two edge vectors
            edge1 = p_curr - p_prev
            edge2 = p_next - p_curr

            # If the cross product is not zero (within a tolerance), the point is not co-linear
            if (
                abs(edge1.cross(edge2)) > 1e-6
            ):  # Use a small tolerance for float precision
                cleaned.append(p_curr)
        return cleaned

    def _get_signed_area(self, vertices: List[Vec2]) -> float:
        """Calculates the signed area using the shoelace formula.

        Args:
            vertices (List[Vec2]): A list of Vec2 vertices defining the polygon's shape.

        Returns:
            float: The signed area of the polygon.
        """
        # we are not reusing the get_area method here since we need the signed area for winding order
        # which doesnt make sense for the get_area method
        area = 0.0
        for i in range(len(vertices)):  # pylint: disable=consider-using-enumerate
            j = (i + 1) % len(vertices)
            area += vertices[i].cross(vertices[j])
        return area / 2.0

    def _is_convex(self, vertices: List[Vec2]) -> bool:
        """Checks if a CCW polygon is convex.

        Args:
            vertices (List[Vec2]): A list of Vec2 vertices defining the polygon's shape.

        Returns:
            bool: True if the polygon is convex, False otherwise.
        """
        # A CCW polygon is convex if all turns are to the left (or straight)
        # although the code is very similar to the one in _remove_colinear, we keep it seperate for better modularity
        for i in range(len(vertices)):  # pylint: disable=consider-using-enumerate
            p_prev = vertices[i - 1]
            p_curr = vertices[i]
            p_next = vertices[(i + 1) % len(vertices)]

            edge1 = p_curr - p_prev
            edge2 = p_next - p_curr

            # If the cross product is negative, it's a right turn (concave)
            if edge1.cross(edge2) < 0:
                return False
        return True

    def _center_vertices(self, vertices: List[Vec2]) -> List[Vec2]:
        """Calculates the true geometric centroid and translates the vertices so the
        centroid is at the origin (0,0). Assumes a valid, non-degenerate polygon.

        Args:
            vertices (List[Vec2]): A list of Vec2 vertices defining the polygon's shape.

        Returns:
            List[Vec2]: A list of Vec2 vertices defining the polygon's shape with the centroid at the origin.
        """
        # https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
        signed_area = self._get_signed_area(vertices)

        cx_sum = 0.0
        cy_sum = 0.0

        for i in range(len(vertices)):  # pylint: disable=consider-using-enumerate
            p1 = vertices[i]
            p2 = vertices[(i + 1) % len(vertices)]

            cross_product = p1.cross(p2)

            cx_sum += (p1.x + p2.x) * cross_product
            cy_sum += (p1.y + p2.y) * cross_product

        six_times_area = 6 * signed_area
        centroid = Vec2(cx_sum / six_times_area, cy_sum / six_times_area)

        # Translate vertices by subtracting the calculated centroid
        return [v - centroid for v in vertices]

    @classmethod
    def create_rectangle(cls, width: float, height: float) -> "PolygonShape":
        """
        Creates a rectangle shape with the given width and height.
        Note that the shapes origin will be in the center of the rectangle.

        Args:
            width: The width of the rectangle.
            height: The height of the rectangle.

        Returns:
            A PolygonShape representing the rectangle.
        """
        vertices = [
            Vec2(-width / 2, -height / 2),
            Vec2(width / 2, -height / 2),
            Vec2(width / 2, height / 2),
            Vec2(-width / 2, height / 2),
        ]
        return cls(vertices)

    @classmethod
    def create_random(
        cls,
        num_vertices_range: Tuple[int, int],
        sample_radius_range: Tuple[float, float],
    ):
        n_vertices = random.randint(num_vertices_range[0], num_vertices_range[1])
        angles = [random.uniform(0, 2 * math.pi) for _ in range(n_vertices)]
        angles = sorted(angles)
        radius = random.uniform(sample_radius_range[0], sample_radius_range[1])
        vertices = [
            Vec2(radius * math.cos(angle), radius * math.sin(angle)) for angle in angles
        ]
        return cls(vertices)

    def get_type(self) -> str:
        return "polygon"

    @functools.lru_cache
    def get_world_space_vertices(self, position: Vec2, angle: float) -> List[Vec2]:
        """
        Calculates the world-space vertices of the polygon, taking into account the position and rotation of the shape.

        Args:
            position (Vec2): The world-space position of the shape.
            angle (float): The world-space angle of the shape in radians.

        Returns:
            List[Vec2]: A list of world-space vertices defining the shape.
        """
        # this method is accessed with the same values multiple times per frame
        # therefore we use lru_cache
        # however the caching overhead through hasing might be too high to be worth it

        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        return [
            Vec2(
                v.x * cos_angle - v.y * sin_angle + position.x,
                v.x * sin_angle + v.y * cos_angle + position.y,
            )
            for v in self.vertices
        ]

    @functools.lru_cache
    def get_normals(self, position: Vec2, angle: float) -> List[Vec2]:
        """
        Calculates the world-space normals of the polygon, taking into account the position and rotation of the shape.

        Args:
            position (Vec2): The world-space position of the shape.
            angle (float): The world-space angle of the shape in radians.

        Returns:
            List[Vec2]: A list of world-space normals defining the shape.
        """
        world_space_vertices = self.get_world_space_vertices(position, angle)
        normals = []
        for i in range(  # pylint: disable=consider-using-enumerate
            len(world_space_vertices)
        ):
            v1 = world_space_vertices[i]
            v2 = world_space_vertices[(i + 1) % len(world_space_vertices)]
            edge = v2 - v1
            normals.append(
                edge.right_normal()
            )  # right normal is the outward normal for convex, counter-clockwise polygons
        return normals

    @functools.lru_cache
    def get_edges(self, position: Vec2, angle: float) -> List[Tuple[Vec2, Vec2]]:
        """
        Calculates the world-space edges of the polygon, taking into account the position and rotation of the shape.

        Args:
            position (Vec2): The world-space position of the shape.
            angle (float): The world-space angle of the shape in radians.

        Returns:
            List[Tuple[Vec2, Vec2]]: A list of world-space edges defining the shape, where each edge is represented as a tuple of two vertices.
        """
        world_space_vertices = self.get_world_space_vertices(position, angle)
        edges = []
        for i in range(  # pylint: disable=consider-using-enumerate
            len(world_space_vertices)
        ):
            v1 = world_space_vertices[i]
            v2 = world_space_vertices[(i + 1) % len(world_space_vertices)]
            edges.append((v1, v2))
        return edges

    @functools.lru_cache
    def calculate_inertia(self, mass: float) -> float:
        """Calculates the moment of inertia for this shape.

        The moment of inertia is a measure of how much mass is distributed around an axis.
        For a rectangle, the moment of inertia is I = (1/12) * m * (w^2 + h^2).

        Args:
            mass (float): The mass of the shape.

        Returns:
            float: The moment of inertia of the shape.
        """
        min_x = min(v.x for v in self.vertices)
        max_x = max(v.x for v in self.vertices)
        min_y = min(v.y for v in self.vertices)
        max_y = max(v.y for v in self.vertices)
        width = max_x - min_x
        height = max_y - min_y
        return (1.0 / 12.0) * mass * (width**2 + height**2)

    def get_aabb(self, position: Vec2, angle: float) -> Tuple[Vec2, Vec2]:
        """
        Calculates the Axis-Aligned Bounding Box (AABB) of the shape in world space.

        Args:
            position (Vec2): The world-space position of the shape's body.
            angle (float): The world-space angle of the shape's body.

        Returns:
            A tuple containing the min and max points of the AABB.
        """
        world_space_vertices = self.get_world_space_vertices(position, angle)

        min_x = min(v.x for v in world_space_vertices)
        max_x = max(v.x for v in world_space_vertices)
        min_y = min(v.y for v in world_space_vertices)
        max_y = max(v.y for v in world_space_vertices)

        return Vec2(min_x, min_y), Vec2(max_x, max_y)

    def is_point_inside(self, point: Vec2, position: Vec2, angle: float) -> bool:
        """
        Checks if a point is inside the polygon using the separating axis theorem.

        For a convex polygon, a point is inside if it's on the correct side of all edges.
        We use the dot product with edge normals to determine which side of each edge the point is on.

        Args:
            point: The point to check in world space.
            position: The world-space position of the polygon's body.
            angle: The world-space angle of the polygon's body.

        Returns:
            True if the point is inside the polygon, False otherwise.
        """
        # First, do a quick AABB test for early rejection
        aabb_min, aabb_max = self.get_aabb(position, angle)
        if (
            point.x < aabb_min.x
            or point.x > aabb_max.x
            or point.y < aabb_min.y
            or point.y > aabb_max.y
        ):
            return False

        # Get world-space vertices and normals
        world_vertices = self.get_world_space_vertices(position, angle)

        # For each edge of the polygon, check if the point is on the inside
        for i in range(len(world_vertices)):  # pylint: disable=consider-using-enumerate
            v1 = world_vertices[i]
            v2 = world_vertices[(i + 1) % len(world_vertices)]

            # Calculate edge vector and outward normal
            edge = v2 - v1
            outward_normal = (
                edge.right_normal()
            )  # right normal is outward for CCW vertices

            # Vector from edge start to the test point
            to_point = point - v1

            # If the dot product is positive, the point is outside this edge
            if to_point.dot(outward_normal) > 0:
                return False

        # Point is inside all edges, so it's inside the polygon
        return True

    def get_area(self) -> float:
        """
        Calculates the area of the polygon using the shoelace formula.

        The shoelace formula (also known as the surveyor's formula) calculates the area
        of a simple polygon given its vertices. For a polygon with vertices (x₀,y₀), (x₁,y₁), ..., (xₙ₋₁,yₙ₋₁),
        the area is:

        Area = ½|∑ᵢ₌₀ⁿ⁻¹(xᵢyᵢ₊₁ - xᵢ₊₁yᵢ)|

        where indices are taken modulo n (so xₙ = x₀, yₙ = y₀).

        This formula works for any simple polygon (convex or concave) as long as the vertices
        are ordered consistently (either clockwise or counter-clockwise).

        Returns:
            The area of the polygon in square units.
        """
        if len(self.vertices) < 3:
            return 0.0

        # Apply the shoelace formula
        area = 0.0
        n = len(self.vertices)

        for i in range(n):
            j = (i + 1) % n  # Next vertex (wraps around to 0 for the last vertex)
            area += self.vertices[i].x * self.vertices[j].y
            area -= self.vertices[j].x * self.vertices[i].y

        return abs(area) / 2.0


# class CompoundShape(Shape):
#     def __init__(self, sub_shapes: List[Tuple[Shape, Vec2, float]]):
#         """
#         Initializes a compound shape with a list of shapes.

#         Args:
#             sub_shapes: A list of tuples, each containing a shape, its position relative to the compound shape's origin,
#                         and its rotation angle.
#         """
#         # TODO implement
#         raise NotImplementedError("CompoundShape is not implemented yet.")

#     def get_type(self) -> str:
#         return "compound"

#     def get_aabb(self, position, angle) -> Tuple[Vec2, Vec2]:
#         raise NotImplementedError("CompoundShape is not implemented yet.")
