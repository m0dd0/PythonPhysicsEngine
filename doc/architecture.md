# Architecture

## Simulation step Psuedo Code
```python
objects = [Object1, Object2, ...]
joints = [Joint1, Joint2, ...]
external_forces = [Force1, Force2, ...]

collision_detector = CollisionDetector(
    narrow_phase=SeparatingAxisTheorem(),
    broad_phase=Grid()
)
solver = Solver()
integrator = SemiImplicitEulerIntegrator()

while True:
    collisions = collision_detector.detect_collisions(objects)
    solver.solve(collisions, objects, joints, external_forces, dt) # updates velocities (and positions)
    integrator.integrate(objects, dt) # updates positions
```

## Where to put the calculation of Polygon Normals?
- In the Polygon class
    - pro: we can easily cache the normals
- In the CollisionDetector class
- In a helper class/function