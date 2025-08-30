import pytest
import math

# Import all the classes from your core module
from ppe.engine.common import (
    Vec2,
    Body,
    Shape,
    CircleShape,
    PolygonShape,
    Contact,
    DistanceJoint,
)


class TestVec2:
    """Test class for Vec2 methods."""

    def test_initialization(self):
        """Tests Vec2 initialization."""
        v = Vec2(1.5, 2.7)
        assert v.x == 1.5
        assert v.y == 2.7

    def test_addition(self):
        """Tests vector addition."""
        v1 = Vec2(10, 20)
        v2 = Vec2(5, -10)
        v_add = v1 + v2
        assert v_add.x == 15
        assert v_add.y == 10

    def test_subtraction(self):
        """Tests vector subtraction."""
        v1 = Vec2(10, 20)
        v2 = Vec2(5, -10)
        v_sub = v1 - v2
        assert v_sub.x == 5
        assert v_sub.y == 30

    def test_scalar_multiplication(self):
        """Tests scalar multiplication."""
        v = Vec2(10, 20)
        v_mul = v * 2
        assert v_mul.x == 20
        assert v_mul.y == 40

    def test_scalar_division(self):
        """Tests scalar division."""
        v = Vec2(10, 20)
        v_div = v / 10
        assert v_div.x == 1.0
        assert v_div.y == 2.0

    def test_dot_product(self):
        """Tests dot product calculation."""
        v1 = Vec2(3, 4)
        v2 = Vec2(5, 0)
        assert v1.dot(v2) == 15

    def test_cross_product(self):
        """Tests cross product calculation."""
        v1 = Vec2(1, 0)
        v2 = Vec2(0, 1)
        assert v1.cross(v2) == 1
        assert v2.cross(v1) == -1

    def test_length_squared(self):
        """Tests length squared calculation."""
        v = Vec2(3, 4)
        assert v.length_squared() == 25

    def test_length(self):
        """Tests length calculation."""
        v = Vec2(3, 4)
        assert v.length() == pytest.approx(5.0)

    def test_left_normal(self):
        """Tests left normal calculation."""
        v = Vec2(1, 0)
        left_norm = v.left_normal()
        assert left_norm.x == pytest.approx(0)
        assert left_norm.y == pytest.approx(1)

    def test_right_normal(self):
        """Tests right normal calculation."""
        v = Vec2(1, 0)
        right_norm = v.right_normal()
        assert right_norm.x == pytest.approx(0)
        assert right_norm.y == pytest.approx(-1)

    def test_rotate(self):
        """Tests vector rotation."""
        v = Vec2(1, 0)
        v_rot = v.rotate(math.pi / 2)
        assert v_rot.x == pytest.approx(0, abs=1e-10)
        assert v_rot.y == pytest.approx(1)

    def test_normalize(self):
        """Tests vector normalization."""
        v = Vec2(3, 4)
        v_norm = v.normalize()
        assert v_norm.x == pytest.approx(0.6)
        assert v_norm.y == pytest.approx(0.8)
        assert v_norm.length() == pytest.approx(1.0)

    def test_normalize_zero_vector(self):
        """Tests normalization of zero vector."""
        zero_vec = Vec2(0, 0)
        normalized = zero_vec.normalize()
        assert normalized.length() == 0

    def test_to_tuple(self):
        """Tests conversion to tuple."""
        v = Vec2(1.5, 2.7)
        assert v.to_tuple() == (1.5, 2.7)

    def test_to_int_tuple(self):
        """Tests conversion to integer tuple."""
        v = Vec2(1.7, 2.3)
        assert v.to_int_tuple() == (1, 2)

    def test_repr(self):
        """Tests string representation."""
        v = Vec2(1.234, 5.678)
        assert repr(v) == "Vec2(1.23, 5.68)"


class TestBody:
    """Test class for Body methods."""

    def test_dynamic_initialization(self):
        """Tests initialization of a standard dynamic body."""
        shape = CircleShape(radius=10)
        body = Body(shape=shape, position=Vec2(0, 0), mass=10)

        assert body.mass == 10
        assert body.inverse_mass == 0.1
        # Inertia for a circle of radius 10 and mass 10 is 0.5 * 10 * 100 = 500
        assert body.inverse_inertia == 1.0 / 500
        assert body.velocity.x == 0 and body.velocity.y == 0
        assert body.angular_velocity == 0.0
        assert body.force_accumulator.x == 0 and body.force_accumulator.y == 0
        assert body.torque_accumulator == 0.0

    def test_static_initialization(self):
        """Tests that a body with mass=None is correctly set as static."""
        shape = CircleShape(radius=10)
        body = Body(shape=shape, position=Vec2(0, 0), mass=None)

        assert body.mass is None
        assert body.inverse_mass == 0.0
        assert body.inverse_inertia == 0.0

    def test_invalid_mass(self):
        """Tests that creating a body with non-positive mass raises an error."""
        shape = CircleShape(radius=10)
        with pytest.raises(ValueError):
            Body(shape=shape, position=Vec2(0, 0), mass=0)
        with pytest.raises(ValueError):
            Body(shape=shape, position=Vec2(0, 0), mass=-10)

    def test_clear_forces(self):
        """Tests the clear_forces method."""
        shape = CircleShape(radius=10)
        body = Body(shape=shape, position=Vec2(0, 0), mass=10)
        body.force_accumulator = Vec2(100, 200)
        body.torque_accumulator = 50

        body.clear_forces()

        assert body.force_accumulator.x == 0
        assert body.force_accumulator.y == 0
        assert body.torque_accumulator == 0

    def test_get_aabb(self):
        """Tests the get_aabb method."""
        shape = CircleShape(radius=5)
        body = Body(shape=shape, position=Vec2(10, 20), mass=1)

        min_p, max_p = body.get_aabb()
        assert min_p.x == 5 and min_p.y == 15
        assert max_p.x == 15 and max_p.y == 25

    def test_is_point_inside(self):
        """Tests the is_point_inside method."""
        shape = CircleShape(radius=5)
        body = Body(shape=shape, position=Vec2(10, 20), mass=1)

        assert body.is_point_inside(Vec2(10, 20))  # center
        assert body.is_point_inside(Vec2(13, 20))  # inside
        assert not body.is_point_inside(Vec2(16, 20))  # outside

    def test_user_data(self):
        """Tests user data functionality."""
        shape = CircleShape(radius=5)
        body = Body(
            shape=shape, position=Vec2(0, 0), mass=1, user_data={"name": "test_body"}
        )

        assert body.user_data["name"] == "test_body"

        # Test default empty dict
        body2 = Body(shape=shape, position=Vec2(0, 0), mass=1)
        assert isinstance(body2.user_data, dict)
        assert len(body2.user_data) == 0


class TestCircleShape:
    """Test class for CircleShape methods."""

    def test_initialization(self):
        """Tests CircleShape initialization."""
        shape = CircleShape(radius=10)
        assert shape.radius == 10

    def test_create_random_circle(self):
        """Tests random circle creation."""
        shape = CircleShape.create_random_circle(min_radius=5, max_radius=10)
        assert 5 <= shape.radius <= 10

    def test_get_type(self):
        """Tests get_type method."""
        shape = CircleShape(radius=10)
        assert shape.get_type() == "circle"

    def test_calculate_inertia(self):
        """Tests inertia calculation."""
        shape = CircleShape(radius=10)
        # Inertia for a circle of radius 10 and mass 10 is 500
        assert shape.calculate_inertia(mass=10) == pytest.approx(500)

    def test_get_aabb(self):
        """Tests AABB calculation."""
        shape = CircleShape(radius=10)
        min_p, max_p = shape.get_aabb(position=Vec2(100, 200), angle=0)
        assert min_p.x == 90 and min_p.y == 190
        assert max_p.x == 110 and max_p.y == 210

    def test_is_point_inside(self):
        """Tests point inside calculation."""
        shape = CircleShape(radius=5)

        # Point at center
        assert shape.is_point_inside(Vec2(0, 0), Vec2(0, 0), 0)

        # Point inside
        assert shape.is_point_inside(Vec2(3, 0), Vec2(0, 0), 0)

        # Point on boundary
        assert shape.is_point_inside(Vec2(5, 0), Vec2(0, 0), 0)

        # Point outside
        assert not shape.is_point_inside(Vec2(6, 0), Vec2(0, 0), 0)

        # Test with offset position
        assert shape.is_point_inside(Vec2(13, 20), Vec2(10, 20), 0)

    def test_get_area(self):
        """Tests area calculation."""
        shape = CircleShape(radius=5)
        expected_area = math.pi * 25
        assert shape.get_area() == pytest.approx(expected_area)


class TestPolygonShape:
    """Test class for PolygonShape methods."""

    def test_rectangle_creation(self):
        """Tests rectangle creation."""
        shape = PolygonShape.create_rectangle(width=10, height=6)
        assert shape.get_type() == "polygon"
        assert len(shape.vertices) == 4

    def test_create_random_rectangle(self):
        """Tests random rectangle creation."""
        shape = PolygonShape.create_random_rectangle(min_size=2, max_size=5)
        assert shape.get_type() == "polygon"
        assert len(shape.vertices) == 4

    def test_polygon_validation(self):
        """Tests polygon validation during construction."""
        # Valid polygon
        verts = [Vec2(-1, -1), Vec2(1, -1), Vec2(1, 1), Vec2(-1, 1)]
        shape = PolygonShape(vertices=verts)
        assert len(shape.vertices) == 4

        # Invalid polygon (less than 3 vertices)
        with pytest.raises(ValueError):
            PolygonShape(vertices=[Vec2(0, 0), Vec2(1, 0)])

    def test_get_type(self):
        """Tests get_type method."""
        shape = PolygonShape.create_rectangle(10, 6)
        assert shape.get_type() == "polygon"

    def test_get_world_space_vertices(self):
        """Tests world space vertex calculation."""
        shape = PolygonShape.create_rectangle(width=2, height=2)
        vertices = shape.get_world_space_vertices(position=Vec2(10, 20), angle=0)

        assert len(vertices) == 4
        # Check that vertices are properly translated
        for v in vertices:
            assert 9 <= v.x <= 11
            assert 19 <= v.y <= 21

    def test_get_normals(self):
        """Tests normal calculation."""
        shape = PolygonShape.create_rectangle(width=2, height=2)
        normals = shape.get_normals(position=Vec2(0, 0), angle=0)

        assert len(normals) == 4
        # For a rectangle, normals should be unit vectors
        for normal in normals:
            assert abs(normal.length() - 1.0) < 1e-10

    def test_get_edges(self):
        """Tests edge calculation."""
        shape = PolygonShape.create_rectangle(width=2, height=2)
        edges = shape.get_edges(position=Vec2(0, 0), angle=0)

        assert len(edges) == 4
        # Each edge should be a tuple of two Vec2 points
        for edge in edges:
            assert len(edge) == 2
            assert isinstance(edge[0], Vec2)
            assert isinstance(edge[1], Vec2)

    def test_calculate_inertia(self):
        """Tests inertia calculation."""
        shape = PolygonShape.create_rectangle(width=10, height=6)
        inertia = shape.calculate_inertia(mass=12)
        # For a rectangle: I = (1/12) * m * (w² + h²)
        expected = (1.0 / 12.0) * 12 * (100 + 36)
        assert inertia == pytest.approx(expected)

    def test_get_aabb(self):
        """Tests AABB calculation."""
        shape = PolygonShape.create_rectangle(width=20, height=10)

        # Unrotated AABB at (100, 200)
        min_p, max_p = shape.get_aabb(position=Vec2(100, 200), angle=0)
        assert min_p.x == 90 and min_p.y == 195
        assert max_p.x == 110 and max_p.y == 205

        # 90-degree rotated AABB (should now be 10 wide and 20 high)
        min_p_rot, max_p_rot = shape.get_aabb(
            position=Vec2(100, 200), angle=math.pi / 2
        )
        assert min_p_rot.x == pytest.approx(95)
        assert min_p_rot.y == pytest.approx(190)
        assert max_p_rot.x == pytest.approx(105)
        assert max_p_rot.y == pytest.approx(210)

    def test_is_point_inside(self):
        """Tests point inside calculation."""
        shape = PolygonShape.create_rectangle(width=10, height=6)

        # Point at center
        assert shape.is_point_inside(Vec2(0, 0), Vec2(0, 0), 0)

        # Point inside
        assert shape.is_point_inside(Vec2(2, 1), Vec2(0, 0), 0)

        # Point outside
        assert not shape.is_point_inside(Vec2(6, 4), Vec2(0, 0), 0)

        # Point on boundary (should be inside)
        assert shape.is_point_inside(Vec2(5, 0), Vec2(0, 0), 0)

    def test_get_area(self):
        """Tests area calculation."""
        shape = PolygonShape.create_rectangle(width=10, height=6)
        assert shape.get_area() == pytest.approx(60)

    def test_colinear_removal(self):
        """Tests removal of co-linear vertices."""
        # Create vertices with a co-linear point in the middle of an edge
        verts = [
            Vec2(-1, -1),
            Vec2(0, -1),
            Vec2(1, -1),  # Co-linear points on bottom edge
            Vec2(1, 1),
            Vec2(-1, 1),
        ]
        shape = PolygonShape(vertices=verts)
        # Should remove the middle co-linear point, leaving 4 vertices
        assert len(shape.vertices) == 4

    def test_convexity_validation(self):
        """Tests convexity validation."""
        # Create a non-convex (concave) polygon - this should raise an error
        concave_verts = [
            Vec2(-2, -1),
            Vec2(2, -1),
            Vec2(2, 1),
            Vec2(0, 0),  # This creates a concave shape
            Vec2(-2, 1),
        ]
        with pytest.raises(ValueError, match="convex polygon"):
            PolygonShape(vertices=concave_verts)

    def test_centering_validation(self):
        """Tests centering of vertices."""
        # Create a polygon with vertices that are not centered at the origin
        verts = [Vec2(1, 1), Vec2(3, 1), Vec2(3, 3), Vec2(1, 3)]
        shape = PolygonShape(vertices=verts)

        assert shape.vertices[0] == Vec2(-1.0, -1.0)  # Should be centered at origin
        assert shape.vertices[1] == Vec2(1.0, -1.0)
        assert shape.vertices[2] == Vec2(1.0, 1.0)
        assert shape.vertices[3] == Vec2(-1.0, 1.0)


class TestContact:
    """Test class for Contact data structure."""

    def test_initialization(self):
        """Tests Contact initialization."""
        shape = CircleShape(1)
        b1 = Body(shape, Vec2(0, 0), 10)
        b2 = Body(shape, Vec2(0, 0), 10)

        contact = Contact(b1, b2, Vec2(1, 0), 5.0, [Vec2(0, 0)])
        assert contact.body_a == b1
        assert contact.body_b == b2
        assert contact.normal.x == 1
        assert contact.penetration_depth == 5.0
        assert len(contact.contact_points) == 1


class TestDistanceJoint:
    """Test class for DistanceJoint."""

    def test_initialization(self):
        """Tests DistanceJoint initialization."""
        shape = CircleShape(1)
        b1 = Body(shape, Vec2(0, 0), 10)
        b2 = Body(shape, Vec2(0, 0), 10)

        joint = DistanceJoint(b1, b2, Vec2(0, 0), Vec2(10, 0), 10.0)
        assert joint.body_a == b1
        assert joint.body_b == b2
        assert joint.anchor_a.x == 0
        assert joint.anchor_b.x == 10
        assert joint.distance == 10.0
