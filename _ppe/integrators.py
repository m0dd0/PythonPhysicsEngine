import abc
from _ppe.bodies import Body


class IntegratorBase(abc.ABC):
    """The IntegratorBase class is an abstract class for integrators.
    Integrators are used to integrate the state of a body over time.
    """

    @abc.abstractmethod
    def integrate(self, body: Body, dt: float):
        """Integrates the state of the given body over the time step dt.

        Args:
            body (Body): The body to integrate.
            dt (float): The time step for the integration.
        """
        raise NotImplementedError


class Euler(IntegratorBase):
    """The Euler class is an integrator that uses the Euler method to integrate the state of a body over time.
    The Euler method is a simple and fast method that is easy to implement.
    It is a first-order method that is not very accurate, but it is often used as a baseline for comparison with more advanced integrators.
    """

    def integrate(self, body: Body, dt: float):
        delta_com = body.vel * dt
        body.shape.translate(delta_com)
        body.vel += body.acc * dt


# TODO implement the following integrators and check the correctness of AI suggestions
# class Verlet(Integrator):
#     def integrate(self, body, dt):
#         body.pos += body.vel * dt + 0.5 * body.acc * dt ** 2
#         body.acc = body.force / body.mass
#         body.vel += 0.5 * (body.acc + body.prev_acc) * dt
#         body.prev_acc = body.acc

# class RK4(Integrator):
#     def integrate(self, body, dt):
#         k1v = body.acc * dt
#         k1x = body.vel * dt
#         k1a = body.force / body.mass

#         k2v = (body.acc + k1a / 2) * dt
#         k2x = (body.vel + k1v / 2) * dt
#         body.pos += k2x
#         k2a = body.force / body.mass

#         k3v = (body.acc + k2a / 2) * dt
#         k3x = (body.vel + k2v / 2) * dt
#         k3a = body.force / body.mass

#         k4v = (body.acc + k3a) * dt
#         k4x = (body.vel + k3v) * dt
#         body.pos += k4x
#         k4a = body.force / body.mass

#         body.vel += (k1v + 2 * k2v + 2 * k3v + k4v) / 6
#         body.acc = (k1a + 2 * k2a + 2 * k3a + k4a) / 6

# class SymplecticEuler(Integrator):
#     def integrate(self, body, dt):
#         body.vel += body.acc * dt
#         body.pos += body.vel * dt
#         body.acc = body.force / body.mass
