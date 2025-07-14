import pytest
import math

# Import all the classes from your core module
from ppe.engine.common import (
    Vec2,
    Body,
    Shape,
    CircleShape,
    PolygonShape,
    CompoundShape,
    Contact,
    DistanceJoint,
)

# --- Vec2 Tests ---


def test_vec2_operations():
    """Tests basic vector arithmetic."""
    v1 = Vec2(10, 20)
    v2 = Vec2(5, -10)

    # Addition
    v_add = v1 + v2
    assert v_add.x == 15
    assert v_add.y == 10

    # Subtraction
    v_sub = v1 - v2
    assert v_sub.x == 5
    assert v_sub.y == 30

    # Scalar Multiplication
    v_mul = v1 * 2
    assert v_mul.x == 20
    assert v_mul.y == 40

    # Scalar Division
    v_div = v1 / 10
    assert v_div.x == 1.0
    assert v_div.y == 2.0


def test_vec2_methods():
    """Tests vector utility methods."""
    v1 = Vec2(3, 4)
    v2 = Vec2(5, 0)

    assert v1.length_squared() == 25
    assert v1.length() == pytest.approx(5.0)
    assert v1.dot(v2) == 15

    # Normalization
    v_norm = v1.normalize()
    assert v_norm.x == pytest.approx(0.6)
    assert v_norm.y == pytest.approx(0.8)
    assert v_norm.length() == pytest.approx(1.0)

    # Normalizing a zero vector
    zero_vec = Vec2(0, 0)
    assert zero_vec.normalize().length() == 0


# --- Body Tests ---


def test_body_dynamic_initialization():
    """Tests initialization of a standard dynamic body."""
    shape = CircleShape(radius=10)
    body = Body(shape=shape, position=Vec2(0, 0), mass=10)

    assert body.mass == 10
    assert body.inverse_mass == 0.1
    # Inertia for a circle of radius 10 and mass 10 is 0.5 * 10 * 100 = 500
    assert body.inverse_inertia == 1.0 / 500


def test_body_static_initialization():
    """Tests that a body with mass=None is correctly set as static."""
    shape = CircleShape(radius=10)
    body = Body(shape=shape, position=Vec2(0, 0), mass=None)

    assert body.mass is None
    assert body.inverse_mass == 0.0
    assert body.inverse_inertia == 0.0


def test_body_invalid_mass():
    """Tests that creating a body with non-positive mass raises an error."""
    shape = CircleShape(radius=10)
    with pytest.raises(ValueError):
        Body(shape=shape, position=Vec2(0, 0), mass=0)
    with pytest.raises(ValueError):
        Body(shape=shape, position=Vec2(0, 0), mass=-10)


def test_body_clear_forces():
    """Tests the clear_forces method."""
    shape = CircleShape(radius=10)
    body = Body(shape=shape, position=Vec2(0, 0), mass=10)
    body.force_accumulator = Vec2(100, 200)
    body.torque_accumulator = 50

    body.clear_forces()

    assert body.force_accumulator.x == 0
    assert body.force_accumulator.y == 0
    assert body.torque_accumulator == 0


# --- Shape Tests ---


def test_circle_shape():
    """Tests methods of the CircleShape class."""
    shape = CircleShape(radius=10)
    assert shape.get_type() == "circle"
    # Inertia for a circle of radius 10 and mass 10 is 500
    assert shape.calculate_inertia(mass=10) == pytest.approx(500)

    min_p, max_p = shape.get_aabb(position=Vec2(100, 200), angle=0)
    assert min_p.x == 90 and min_p.y == 190
    assert max_p.x == 110 and max_p.y == 210


def test_polygon_shape():
    """Tests methods of the PolygonShape class."""
    # A 20x10 box centered at the origin
    verts = [Vec2(-10, -5), Vec2(10, -5), Vec2(10, 5), Vec2(-10, 5)]
    shape = PolygonShape(vertices=verts)

    assert shape.get_type() == "polygon"

    # Unrotated AABB at (100, 200)
    min_p, max_p = shape.get_aabb(position=Vec2(100, 200), angle=0)
    assert min_p.x == 90 and min_p.y == 195
    assert max_p.x == 110 and max_p.y == 205

    # 90-degree rotated AABB (should now be 10 wide and 20 high)
    min_p_rot, max_p_rot = shape.get_aabb(position=Vec2(100, 200), angle=math.pi / 2)
    assert min_p_rot.x == pytest.approx(95)
    assert min_p_rot.y == pytest.approx(190)
    assert max_p_rot.x == pytest.approx(105)
    assert max_p_rot.y == pytest.approx(210)

# --- Data Class Tests ---


def test_data_classes_initialization():
    """Tests initialization of simple data container classes."""
    shape = CircleShape(1)
    b1 = Body(shape, Vec2(0, 0), 10)
    b2 = Body(shape, Vec2(0, 0), 10)

    # Contact
    contact = Contact(b1, b2, Vec2(1, 0), 5.0)
    assert contact.body_a == b1
    assert contact.normal.x == 1
    assert contact.penetration_depth == 5.0

    # DistanceJoint
    joint = DistanceJoint(b1, b2, Vec2(0, 0), Vec2(10, 0), 10.0)
    assert joint.body_b == b2
    assert joint.anchor_b.x == 10
    assert joint.distance == 10.0
