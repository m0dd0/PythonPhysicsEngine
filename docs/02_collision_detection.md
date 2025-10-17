# Collision Detection
- https://timallanwheeler.com/blog/2024/08/01/2d-collision-detection-and-resolution/
## Handling Different Shape Types with a Dispatch System
## Circle vs Circle
## Circle vs Polygon
## Separating Axis Theorem (SAT)
The Separating Axis Theorem (SAT) is a fundamental algorithm to detect the collision between two convex shapes.
The concrete implementation in this engine (`SatPolygonHandler`) can be found in `ppe.engine.collision_handlers.polygon_vs_polygon`.
I will approach the explanation by starting with the most basic version of the algorithm and then gradually add more details and optimizations.

### Basic Algorithm
The core idea is that if there exists an axis along which the projections of the two shapes do not overlap, then the shapes are not colliding.
Conversely, if no such axis exists, the shapes are colliding.
Instead of checking all possible axes (which would be computationally impossible ;)), it's sufficient to check all the axes that are perpendicular to the edges of the shapes.
This results in the following pseudocode for the basic version of the SAT algorithm:

```
for each edge in both shapes:
    axis = perpendicular_vector(edge)
    
    projection_values_1 = project_shape_onto_axis(shape1.vertices, axis)
    projection_values_2 = project_shape_onto_axis(shape2.vertices, axis)

    if not projections_overlap(projection_values_1, projection_values_2):
        return False  # Found a separating axis, no collision

return True  # No separating axis found, shapes are colliding
```

### Finding Collision Normal and Penetration Depth
However, this simple version has a key limitation: For correct collision response, we need more information than just whether a collision occurred. 
We also need to know the collision normal (the axis along which the shapes are colliding) and the penetration depth (how much the shapes overlap along that axis).
If theres a collision, the projections usually overlap on multiple axes.
We define the collision normal as the axis with the smallest overlap, and the penetration depth as the amount of that overlap.
To find the collision normal and penetration depth, we can keep track of the axis with the smallest overlap:

```
func project_shape_onto_axis(shape, axis):
    min_proj = infinity
    max_proj = -infinity
    for vertex in shape.vertices:
        projection = dot(vertex, axis)
        min_proj = min(min_proj, projection)
        max_proj = max(max_proj, projection)
    return (min_proj, max_proj)

min_overlap = infinity
collision_normal = None

for each edge in both shapes:
    axis = perpendicular_vector(edge)
    
    projection1 = project_shape_onto_axis(shape1, axis)
    projection2 = project_shape_onto_axis(shape2, axis)
    
    if not projections_overlap(projection1, projection2):
        return False  # Found a separating axis, no collision
    
    overlap = calculate_overlap(projection1, projection2)
    if overlap < min_overlap:
        min_overlap = overlap
        collision_normal = axis
```

### Finding the Contact Points
In order to compute the rotation induced by the collision, we also need to find the contact points.
The contact points are the points on the shapes that are in contact during the collision.
Since in the simulation, the collision is always a tiny overlap of the shapes, the contact points are the intersection points of the edges of the two shapes.
Finding these intersection points is easier said than done.
Before continuing, lets introduce some terminology:
- Reference Edge: The edge that is being penetrated into. Or more formally, the edge along whose normal the collision normal is aligned (the edge that produced the minimum overlap).
- Incident Edge: The edge that is penetrating into the reference edge. Formally, we define the incident edge as the edge whose normal is most opposite to the reference edge normal. Note that in an concave polygon, this edge always corresponds to one of the edges adjacent to the vertex that is deepest in the reference edge.
One option would be to check the for intersections of all edges of the incident shape with the reference edge.

### Computational Optimizations
Checking for overlapping projections can be simplified computationally:
Instead of projecting all the vertices from both shapes onto the axis, its more efficient if we calculate just the distance of all points from the other shape to the currently analyzed edge.
The distance of a point to an edge can be calculated using the dot product between the edge normal and the vector from a point on the edge to the point in question.
If all the distances have the same sign, then the shapes are not colliding along that axis.
Furthermore, if we can assume that all normals are pointing outwards of the shape, we can reuse the computed distances to determine the collision depth as well.
Note that to allow the assumption that all normals point outwards, we need to ensure that the vertices of each polygon are defined in a consistent winding order (clockwise or counter-clockwise).

Assuming our polygons have N and M edges respectively, the new version of the SAT algorithm has a time complexity of O(N + M) instead of O(N * M) in the naive version.
<!-- While in theory, this is a significant improvement, in practice, the difference is often negligible since the number of edges in typical polygons used in physics simulations is usually quite small. -->
```
min_overlap = infinity
collision_normal = None
for each edge in shape_1:
    axis = perpendicular_vector(edge) # assume outward pointing normals
    
    distances_to_edge = [dot(axis, vertex - edge.start_vertex) for vertex in shape2.vertices]

    if all(distance > 0 for distance in distances_to_edge):
        return False  # Found a separating axis, no collision

    overlap = abs(min(distances_to_edge))

for each edge in shape_2:
    axis = perpendicular_vector(edge) # assume outward pointing normals
    
    distances_to_edge = [dot(axis, vertex - edge.start_vertex) for vertex in shape1.vertices]

    if all(distance > 0 for distance in distances_to_edge):
        return False  # Found a separating axis, no collision

    overlap = abs(min(distances_to_edge))
```

This version will not work correctly 

## Broad Phase Collision Detection
## AABB Broad Phase
## Spatial Partitioning Broad Phase