import abc
from typing import Tuple, List, Dict, Any
import random
import math

from ppe.vector import Vector


class Shape(abc.ABC):
    """A Shape class represents a geometric shape in 2D space. It includes also the position of the shape in space.
    It is defined by a set of vertices and provides methods to compute properties like the center of mass, area, and bounding box.
    """

    def __init__(self, vertices: List[Vector]):
        """Initializes the Shape with the given list of vertices.

        Args:
            vertices (List[Vector]): A list of vertices that define the shape.
        """
        self._vertices = vertices

        self._com = self._compute_com()
        self._area = self._compute_area()

        self._bbox = None

    @property
    def vertices(self):
        return self._vertices

    @property
    def com(self):
        return self._com

    @property
    def area(self):
        return self._area

    @property
    def bbox(self):
        if self._bbox is None:
            self._bbox = self._compute_bbox()
        return self._bbox

    @abc.abstractmethod
    def _compute_com(self) -> Vector:
        """Computes the center of mass of the shape.

        Returns:
            Vector: The center of mass of the shape.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _compute_area(self) -> float:
        """Computes the area of the shape.

        Returns:
            float: The area of the shape.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _compute_bbox(self) -> Tuple[Vector, Vector]:
        """Computes the bounding box of the shape.

        Returns:
            Tuple[Vector, Vector]: The minimum and maximum coordinates of the bounding box.
        """
        raise NotImplementedError

    def rotate(self, angle: float):
        """Rotates the shape by the given angle around its center of mass by updating the vertices.

        Args:
            angle (float): The angle in radians by which to rotate the shape.
        """
        # updates the vertices and sets the bbox to None
        rotated_vertices = []
        for vertex in self._vertices:
            # there might be a tiny bit more efficient way to do this by using numpy or keeping the relative position of the vertices
            vertex_rel = vertex - self._com
            vertex_rotated = self._com + vertex_rel.rotate(angle)
            rotated_vertices.append(vertex_rotated)
        self._vertices = rotated_vertices

    def translate(self, delta: Vector):
        """Translates the shape by the given delta vector by updating the vertices.

        Args:
            delta (Vector): The delta vector by which to translate the shape.
        """
        # updates the vertices, com and sets the bbox to None
        # there might be a tiny bit more efficient way to do this by using numpy
        self._vertices = [v + delta for v in self._vertices]
        self._com += delta
        self._bbox = None


class Ball(Shape):
    def __init__(self, com: Vector, radius: float):
        """Initializes the Ball with the given position and radius. The intersction of a horizontal line with the ball are the vertices.

        Args:
            pos (Vector): The position of the center of the ball.
            radius (float): The radius of the ball.
        """
        self._radius = radius
        super().__init__([com - Vector(radius, 0), com + Vector(radius, 0)])

    @classmethod
    def create_random(
        cls,
        com_bounds: Tuple[Vector, Vector],
        radius_bounds: Tuple[float, float],
    ) -> "Ball":
        """Creates a random Ball with a random position and radius within the given bounds.

        Args:
            pos_bounds (Tuple[Vector, Vector]): The minimum and maximum position of the center of the ball.
            radius_bounds (Tuple[float, float]): The minimum and maximum radius of the ball.

        Returns:
            Ball: The created random Ball.
        """
        radius = random.uniform(*radius_bounds)
        pos = Vector(
            random.uniform(com_bounds[0].x, com_bounds[1].x),
            random.uniform(com_bounds[0].y, com_bounds[1].y),
        )
        return cls(pos, radius)

    @property
    def radius(self):
        return self._radius

    def _compute_bbox(self):
        return (
            self.com - Vector(self._radius, self._radius),
            self.com + Vector(self._radius, self._radius),
        )

    def _compute_com(self):
        return self.vertices[0] + Vector(self._radius, 0)

    def _compute_area(self):
        return math.pi * self._radius**2


class ConvexPolygon(Shape):
    """A ConvexPolygon class represents a convex polygon in 2D space. It is defined by a set of vertices in counter-clockwise order."""

    @staticmethod
    def vertices_are_convex(vertices: List[Vector]) -> bool:
        """Checks if the given vertices define a convex polygon.

        Args:
            vertices (List[Vector]): A list of vertices that define the polygon.

        Returns:
            bool: True if the polygon is convex, False otherwise.
        """
        n = len(vertices)
        vertex_signs = []
        for i in range(n):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % n]
            p3 = vertices[(i + 2) % n]
            edge1 = p2 - p1
            edge2 = p3 - p2

            vertex_signs.append(edge1.cross(edge2) > 0)

        return all(vertex_signs) or not any(vertex_signs)

    @staticmethod
    def vertices_are_anticlockwise(vertices: List[Vector]) -> bool:
        """Checks if the given vertices are in counter-clockwise order.

        Args:
            vertices (List[Vector]): A list of vertices.

        Returns:
            bool: True if the vertices are in counter-clockwise order, False otherwise.
        """
        n = len(vertices)
        total = 0
        for i in range(n):
            j = (i + 1) % n
            total += (vertices[j].x - vertices[i].x) * (vertices[j].y + vertices[i].y)
        return total < 0

    def __init__(self, vertices: List[Vector]):
        """Initializes the ConvexPolygon with the given list of vertices. The vertices must be in counter-clockwise order.

        Args:
            vertices (List[Vector]):

        Raises:
            ValueError: If the vertices do not define a convex polygon or are not in counter-clockwise order.
        """
        assert len(vertices) >= 3

        if not ConvexPolygon.vertices_are_convex(vertices):
            raise ValueError("Polygon is not convex")

        if not ConvexPolygon.vertices_are_anticlockwise(vertices):
            vertices = list(reversed(vertices))

        super().__init__(vertices)

        self._normals = None

    @classmethod
    def create_rectangle(
        cls,
        com: Vector,
        width: float,
        height: float,
        angle: float = 0,
    ) -> "ConvexPolygon":
        """Creates a rectangle with the given center of mass, width, height, and rotation angle.

        Args:
            com (Vector): The center of mass of the rectangle.
            width (float): The width of the rectangle.
            height (float): The height of the rectangle.
            angle (float, optional): The rotation angle of the rectangle in radians. Defaults to 0.

        Returns:
            ConvexPolygon: The created rectangle.
        """
        vertices = [
            Vector(-width / 2, -height / 2) + com,
            Vector(-width / 2, height / 2) + com,
            Vector(width / 2, height / 2) + com,
            Vector(width / 2, -height / 2) + com,
        ]
        polygon = cls(vertices)
        polygon.rotate(angle)

        return polygon

    @classmethod
    def create_random(
        cls,
        com_bounds: Tuple[Vector, Vector],
        extend_bounds: Tuple[float, float],
        n_vertices_bounds: Tuple[int, int],
    ) -> "ConvexPolygon":
        """Creates a random ConvexPolygon with a random center of mass, extends, and number of vertices within the given bounds.
        The vertices are distributed on an ellipse and then randomly perturbed.

        Args:
            com_bounds (Tuple[Vector, Vector]): The minimum and maximum center of mass of the polygon.
            extend_bounds (Tuple[float, float]): The minimum and maximum extends of the ellipse.
            n_vertices_bounds (Tuple[int, int]): The minimum and maximum number of vertices.

        Returns:
            ConvexPolygon: The created random ConvexPolygon.
        """
        n_vertices = random.randint(*n_vertices_bounds)

        # the extends of the ellipse
        ellpise_a = random.uniform(*extend_bounds) / 2
        ellipse_b = random.uniform(*extend_bounds) / 2

        # distribute the vertices first uniformly on the ellipse and then add a small random perturbation
        # the pertubation is limited to half the distance between two vertices
        delta_t = 2 * math.pi / n_vertices
        ts = [i * delta_t for i in range(n_vertices)]
        max_offset = delta_t / 2
        ts = [t + random.uniform(-max_offset, max_offset) for t in ts]

        vertices = [
            Vector(ellpise_a * math.cos(t), ellipse_b * math.sin(t)) for t in ts
        ]

        pos = Vector(
            random.uniform(com_bounds[0].x, com_bounds[1].x),
            random.uniform(com_bounds[0].y, com_bounds[1].y),
        )
        vertices = [v + pos for v in vertices]

        polygon = cls(vertices)

        # rotate the polygon randomly for extra randomness
        angle = random.uniform(0, 2 * math.pi)
        polygon.rotate(angle)

        return polygon

    @property
    def normals(self):
        if self._normals is None:
            self._normals = self._compute_normals()
        return self._normals

    def _compute_bbox(self) -> Tuple[Vector]:
        xs = [v.x for v in self._vertices]
        ys = [v.y for v in self._vertices]
        return (Vector(min(xs), min(ys)), Vector(max(xs), max(ys)))

    def _compute_com(self) -> Vector:
        # https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
        n = len(self._vertices)
        cx = 0
        cy = 0
        area = 0
        for i in range(n):
            j = (i + 1) % n
            factor = self._vertices[i].cross(self._vertices[j])
            cx += (self._vertices[i].x + self._vertices[j].x) * factor
            cy += (self._vertices[i].y + self._vertices[j].y) * factor
            area += factor
        return Vector(cx, cy) / (3 * area)

    def _compute_area(self) -> float:
        # https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
        n = len(self._vertices)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += self._vertices[i].cross(self._vertices[j])
        area = area / 2

        return area

    def _compute_normals(self):
        normals = []
        for i in range(len(self._vertices)):
            j = (i + 1) % len(self._vertices)
            edge = self._vertices[j] - self._vertices[i]
            normal = edge.rotate(math.pi * 0.5).normalize()
            normals.append(normal)
        return normals

    def rotate(self, angle: float):
        self._normals = None
        super().rotate(angle)


class Body:
    """A Body class represents a physical body in 2D space. It includes the shape of the
    body, mass, velocity, acceleration, angular velocity, angular acceleration, and other physical properties.
    """

    def __init__(
        self,
        shape: Shape,
        mass: float = 1,  # in kilogram
        vel: Vector = Vector(0, 0),  # in meter per second
        acc: Vector = Vector(0, 0),  # in meter per second squared
        angular_vel: float = 0,  # in radian per second
        angular_acc: float = 0,  # in radian per second squared
        kinematic: bool = False,
        bounciness: float = 1,
        friction_coefficient: float = 0,
        visual_attributes: Dict[Any, Any] = None,
        name: str = None,
    ):
        """Initializes the Body with the given shape, mass, velocity, acceleration, angular velocity, angular acceleration, and other physical properties.

        Args:
            shape (Shape): The shape of the body.
            mass (float, optional): The mass of the body in kilogram. Defaults to 1.
            vel (Vector, optional): The velocity of the body in meter per second. Defaults to Vector(0, 0).
            acc (Vector, optional): The acceleration of the body in meter per second squared. Defaults to Vector(0, 0).
            angular_vel (float, optional): The angular velocity of the body in radian per second. Defaults to 0.
            angular_acc (float, optional): The angular acceleration of the body in radian per second squared. Defaults to 0.
            kinematic (bool, optional): If True, the body is kinematic and does not move. Defaults to False.
            bounciness (float, optional): The bounciness of the body. Defaults to 1.
            friction_coefficient (float, optional): The friction coefficient of the body. Defaults to 0.
            visual_attributes (Dict[Any, Any], optional): The visual attributes of the body. Defaults to None.
            name (str, optional): The name of the body. Defaults to None.
        """
        self.shape = shape
        self.mass = mass
        self.vel = vel
        self.angular_vel = angular_vel
        self.acc = acc
        self.angular_acc = angular_acc
        self.kinematic = kinematic
        self.bounciness = bounciness
        self.friction_coefficient = friction_coefficient
        self.visual_attributes = visual_attributes or {}
        self.name = name or str(id(self))

        # all properties can be set and get and we do not do input validation

    def __repr__(self) -> str:
        return f"Body({self.name})"
