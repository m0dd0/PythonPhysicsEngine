import math
from abc import ABC, abstractmethod
from typing import List, Tuple, Union
import random


class Vec2:
    """A 2D vector class for all position, velocity, and force calculations."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> "Vec2":
        return Vec2(self.x / scalar, self.y / scalar)

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    def length(self) -> float:
        return math.sqrt(self.length_squared())

    def left_normal(self) -> "Vec2":
        """Returns the left normal of the vector."""
        return Vec2(-self.y, self.x).normalize()

    def right_normal(self) -> "Vec2":
        """Returns the right normal of the vector."""
        return Vec2(self.y, -self.x).normalize()

    def normalize(self) -> "Vec2":
        l = self.length()
        if l == 0:
            return Vec2(0, 0)
        return self / l
    
    def to_tuple(self) -> Tuple[float, float]:
        """Returns the vector as a tuple."""
        return (self.x, self.y)
    
    def to_int_tuple(self) -> Tuple[int, int]:
        """Returns the vector as a tuple of integers."""
        return (int(self.x), int(self.y))

    def __repr__(self) -> str:
        return f"Vec2({self.x:.2f}, {self.y:.2f})"


class Body:
    """Represents a single physical object in the world."""

    def __init__(
        self,
        shape: "Shape",
        position: Vec2,
        mass: Union[float, None],
        restitution: float = 0.2,
        user_data: dict = None,
    ):
        if mass is not None and mass <= 0:
            raise ValueError("Mass must be positive or None for static bodies.")

        self.shape = shape
        self.position = position
        self.angle: float = 0.0

        self.previous_position: Vec2 = (
            self.position
        )  # used by some integrators like Verlet
        self.previous_angle: float = self.angle  # used by some integrators like Verlet

        self.velocity: Vec2 = Vec2(0, 0)
        self.angular_velocity: float = 0.0

        self.force_accumulator: Vec2 = Vec2(0, 0)
        self.torque_accumulator: float = 0.0

        self.mass = mass
        self.restitution = restitution

        if self.mass is None:
            self.inverse_mass: float = 0.0
            self.inverse_inertia: float = 0.0
        else:
            self.inverse_mass: float = 1.0 / mass
            self.inverse_inertia: float = 1.0 / self.shape.calculate_inertia(mass)

        self.user_data = user_data if user_data is not None else dict()

    def clear_forces(self) -> None:
        self.force_accumulator = Vec2(0, 0)
        self.torque_accumulator = 0.0

    def get_aabb(self) -> Tuple[Vec2, Vec2]:
        """
        Calculates the Axis-Aligned Bounding Box (AABB) of the body in world space.

        Returns:
            A tuple containing the min and max points of the AABB.
        """
        return self.shape.get_aabb(self.position, self.angle)

    def is_point_inside(self, point: Vec2) -> bool:
        """
        Checks if a point is inside the body in world space.

        Args:
            point: The point to check.

        Returns:
            True if the point is inside the body, False otherwise.
        """
        return self.shape.is_point_inside(point, self.position, self.angle)

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
        self.radius = radius

        # TODO check if caching of aabb and interatia improves performance and by how much. try lru cache util and custom caching implemenation where we do not need to hash the inputs

        # TODO add constructors for random circles

    @classmethod
    def create_random_circle(cls, min_radius: float = 0.05, max_radius: float = 1.0) -> "CircleShape":
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
        radius = self.radius
        return (
            Vec2(position.x - radius, position.y - radius),
            Vec2(position.x + radius, position.y + radius),
        )

    def is_point_inside(self, point: Vec2, position: Vec2, angle: float) -> bool:
        """Checks if a point is inside the circle in world space."""
        # No need to consider angle for circles, as they are symmetric
        distance_squared = (point.x - position.x) ** 2 + (point.y - position.y) ** 2
        return distance_squared <= self.radius**2

    def get_area(self) -> float:
        """Calculates the area of the circle."""
        return math.pi * self.radius**2

class PolygonShape(Shape):
    def __init__(self, vertices: List[Vec2]):
        self.vertices = vertices
        # TODO check that the vertices are in counter-clockwise order and form a convex polygon

        # TODO check if caching of aabb and interatia improves performance and by how much. try lru cache util and custom caching implemenation where we do not need to hash the inputs

        # TODO adapt the vertices coordinats so that the geometric center is at the origin

        # TODO add different constructors for regular polygons, rectangles, etc.

    @classmethod
    def create_rectangle(cls, width: float, height: float) -> "PolygonShape":
        """
        Creates a rectangle shape with the given width and height.

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
    def create_random_rectangle(cls, min_size: float = 0.05, max_size: float = 1.0) -> "PolygonShape":
        """
        Creates a random rectangle shape with width and height between min_size and max_size.

        Args:
            min_size: The minimum size for width and height.
            max_size: The maximum size for width and height.

        Returns:
            A PolygonShape representing the random rectangle.
        """
        width = random.uniform(min_size, max_size)
        height = random.uniform(min_size, max_size)
        return cls.create_rectangle(width, height)

    def get_type(self) -> str:
        return "polygon"

    def get_world_space_vertices(self, position: Vec2, angle: float) -> List[Vec2]:
        """Calculates the world-space vertices of the polygon."""
        # TODO check if caching rotated vertices improves performance
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        return [
            Vec2(
                v.x * cos_angle - v.y * sin_angle + position.x,
                v.x * sin_angle + v.y * cos_angle + position.y,
            )
            for v in self.vertices
        ]

    def get_normals(self, position: Vec2, angle: float) -> List[Vec2]:
        """Calculates the world-space normals of the polygon."""
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

    def calculate_inertia(self, mass: float) -> float:
        min_x = min(v.x for v in self.vertices)
        max_x = max(v.x for v in self.vertices)
        min_y = min(v.y for v in self.vertices)
        max_y = max(v.y for v in self.vertices)
        width = max_x - min_x
        height = max_y - min_y
        return (1.0 / 12.0) * mass * (width**2 + height**2)

    def get_aabb(self, position: Vec2, angle: float) -> Tuple[Vec2, Vec2]:
        """Calculates the AABB of the polygon shape in world space."""
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
        if (point.x < aabb_min.x or point.x > aabb_max.x or 
            point.y < aabb_min.y or point.y > aabb_max.y):
            return False
        
        # Get world-space vertices and normals
        world_vertices = self.get_world_space_vertices(position, angle)
        
        # For each edge of the polygon, check if the point is on the inside
        for i in range(len(world_vertices)): # pylint: disable=consider-using-enumerate
            v1 = world_vertices[i]
            v2 = world_vertices[(i + 1) % len(world_vertices)]
            
            # Calculate edge vector and outward normal
            edge = v2 - v1
            outward_normal = edge.right_normal()  # right normal is outward for CCW vertices
            
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
#         # TODO
#         raise NotImplementedError("CompoundShape is not implemented yet.")

#     def get_type(self) -> str:
#         return "compound"

#     def get_type_id(self) -> int:
#         return 3

#     def get_aabb(self, position, angle) -> Tuple[Vec2, Vec2]:
#         raise NotImplementedError("CompoundShape is not implemented yet.")


class Contact:
    """Holds information about a collision between two bodies."""

    def __init__(
        self,
        body_a: Body,
        body_b: Body,
        normal: Vec2,
        penetration_depth: float,
        contact_points: List[Vec2],
    ):
        self.body_a = body_a
        self.body_b = body_b
        self.normal = normal
        self.penetration_depth = penetration_depth
        self.contact_points = contact_points


class Joint(ABC):
    pass


class DistanceJoint(Joint):
    """A constraint that keeps two bodies at a fixed distance."""

    def __init__(
        self,
        body_a: Body,
        body_b: Body,
        anchor_a: Vec2,
        anchor_b: Vec2,
        distance: float,
    ):
        self.body_a = body_a
        self.body_b = body_b
        self.anchor_a = anchor_a
        self.anchor_b = anchor_b
        self.distance = distance

# TODO more joints
