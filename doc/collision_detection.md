# Collision Detection

## Broad Phase

## Narrow Phase
### Separating Axis Theorem
```python	
min_penetration_depth = float('inf')
collision_normal = None

for each outward pointing normal of both objects:
    min1, max1 = project(object1, normal)
    min2, max2 = project(object2, normal)
    if max1 < min2 or max2 < min1:
        return False

    penetration_depth = min(max1, max2) - max(min1, min2)
    if penetration_depth < min_penetration_depth:
        min_penetration_depth = penetration_depth
        collision_normal = normal

return collision_normal, min_penetration_depth, obj1, obj2
```
    

