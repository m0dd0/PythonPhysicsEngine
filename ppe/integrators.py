import abc


class IntegratorBase(abc.ABC):
    @abc.abstractmethod
    def integrate(self, body, dt):
        raise NotImplementedError


class Euler(IntegratorBase):
    def integrate(self, body, dt):
        delta_com = body.vel * dt
        body.shape.translate(delta_com)
        body.vel += body.acc * dt
        # body.acc = body.force / body.mass


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
