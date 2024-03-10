import abc


class Solver(abc.ABC):
    @abc.abstractmethod
    def solve(self, collisions, joints, forces, dt):
        raise NotImplementedError
