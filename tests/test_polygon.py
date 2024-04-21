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

    def test_normals(self):
        polygon = ConvexPolygon(VERTICES_CLOCKWISE)
        # even though the __equal__ method of the vector class allows for a tolerance of
        # 1e-5 hashes of vector with floating point inaccuracies have different hashes
        # therefore we can not directly compare the sets as the __hash__ method is used
        # and not the __equal__ method
        # instead we order the normals by x and y and compare them one by one

        sorted_normals = sorted(polygon.normals, key=lambda x: x.x)
        sorted_normals = sorted(sorted_normals, key=lambda x: x.y)
        sorted_normals_expected = sorted(NORMALS_EXSPECETED, key=lambda x: x.x)
        sorted_normals_expected = sorted(sorted_normals_expected, key=lambda x: x.y)

        for normal, normal_expected in zip(sorted_normals, sorted_normals_expected):
            assert normal == normal_expected
