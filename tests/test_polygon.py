import pytest

from ppe.objects import ConvexPolygon
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
    def test_init_clockwise(self):
        polygon = ConvexPolygon(VERTICES_CLOCKWISE)
        assert polygon.vertices == VERTICES_ANTICLOCKWISE

    def test_init_anticlockwise(self):
        polygon = ConvexPolygon(VERTICES_ANTICLOCKWISE)
        assert polygon.vertices == VERTICES_ANTICLOCKWISE

    def test_init_concave(self):
        with pytest.raises(ValueError):
            ConvexPolygon(VERTICES_CONCAVE)

    def test_is_convex(self):
        polygon = ConvexPolygon(VERTICES_CLOCKWISE)
        assert polygon._is_convex()

    def test_compute_area(self):
        polygon = ConvexPolygon(VERTICES_CLOCKWISE)
        assert polygon._compute_area() == 0.5

    def test_get_normal(self):
        polygon = ConvexPolygon(VERTICES_CLOCKWISE)

        normals = set(polygon.get_normals())

        assert normals == NORMALS_EXSPECETED
