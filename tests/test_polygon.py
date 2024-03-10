import pytest

from ppe.bodies import ConvexPolygon
from ppe.vector import Vector

VERTICES_CLOCKWISE = [
    Vector(0, 0),
    Vector(0, 1),
    Vector(1, 0),
]
VERTICES_ANTICLOCKWISE = list(reversed(VERTICES_CLOCKWISE))
VERTICES_CONCAVE = [
    Vector(0, 0),
    Vector(0, 1),
    Vector(0.5, 0.5),
    Vector(1, 1),
    Vector(1, 0),
]
NORMALS_EXSPECETED = {
    Vector(0, -1).normalize(),
    Vector(1, 1).normalize(),
    Vector(-1, 0).normalize(),
}


class TestPolygon:
    def test_init_anticlockwise(self):
        polygon = ConvexPolygon(VERTICES_ANTICLOCKWISE)
        assert polygon.vertices == VERTICES_ANTICLOCKWISE

    def test_init_clockwise(self):
        polygon = ConvexPolygon(VERTICES_CLOCKWISE)
        assert polygon.vertices == VERTICES_ANTICLOCKWISE

    def test_init_concave(self):
        with pytest.raises(ValueError):
            ConvexPolygon(VERTICES_CONCAVE)

    def test_is_convex(self):
        assert ConvexPolygon.vertices_are_convex(VERTICES_CLOCKWISE)

    def test_area(self):
        polygon = ConvexPolygon(VERTICES_CLOCKWISE)
        assert polygon.area == 0.5

    def test_pos(self):
        polygon = ConvexPolygon(VERTICES_CLOCKWISE)
        assert polygon.com == Vector(1 / 3, 1 / 3)

    def test_bounding_box(self):
        polygon = ConvexPolygon(VERTICES_CLOCKWISE)
        assert polygon.bbox == (Vector(0, 0), Vector(1, 1))
