# PythonPhysicsEngine
## Assumptions
- no deformable objects
- no fluids
- constant density of objects (over time and space) --> center of mass is constant in the bodies relative coordinate system
- only convex polygons and circles (but manual combination of them into a composed object is possible)

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
