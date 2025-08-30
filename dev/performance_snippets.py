import timeit

class Vec2:
    """A minimal Vec2 class for the benchmark."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

# A sample polygon
SQUARE_VERTS = [Vec2(0,0), Vec2(10,0), Vec2(10,10), Vec2(0,10)]

def recompute_edges(verts):
    """Calculates edges on the fly, twice."""
    total = 0
    # First pass
    for i in range(len(verts)):
        p1 = verts[i]
        p2 = verts[(i + 1) % len(verts)]
        edge = p2 - p1
        total += edge.x # Use the value to prevent optimization

    # Second pass (re-computing)
    for i in range(len(verts)):
        p1 = verts[i]
        p2 = verts[(i + 1) % len(verts)]
        edge = p2 - p1
        total += edge.x
    return total

def store_edges(verts):
    """Stores edges in a list, then accesses the list twice."""
    total = 0
    # Create and populate the list
    edges = []
    for i in range(len(verts)):
        p1 = verts[i]
        p2 = verts[(i + 1) % len(verts)]
        edges.append(p2 - p1)
    
    # First pass (accessing)
    for edge in edges:
        total += edge.x

    # Second pass (accessing)
    for edge in edges:
        total += edge.x
    return total

# Time the operation
iterations = 1_000_000
time_taken = timeit.timeit(lambda: store_edges(SQUARE_VERTS), number=iterations)
print(f"Storing in a list:       {time_taken:.4f} seconds for {iterations:,} iterations.")