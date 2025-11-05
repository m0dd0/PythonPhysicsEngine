## Constraint Solver
- iterative vs direct solvers
## Iterative Impulse-based Solver
https://en.wikipedia.org/wiki/Collision_response
https://www.chrishecker.com/images/e/e7/Gdmphys3.pdf
- derive impulse without rotational effects
- mathematically its often referred to as projected Gauss Seidel
### Positional Correction with Baumgarte Stabilization
- better than "teleporting" workaround
### Why do we need multiple iterations?
- solving stacks...
### Accounting for Rotation
- derive impulse with rotational effects
### Limitations of the Iterative Impulse-based Solver
## Iterative Position-based Solver