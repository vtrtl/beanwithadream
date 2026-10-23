"""Things you collect, trigger or ride: coins, pads, lucky blocks and moving platforms."""
import math
import pygame
import visuals


class Coin:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.rect = pygame.Rect(0, 0, 30, 30)
        self.rect.center = (x, y)
        self.phase = (x * 0.013 + y * 0.007) % 6.28  # so neighbouring coins don't spin in sync


class Pad:
    """A spring or a buff pad. (x, y) is the middle of its base, standing on the ground."""
    SIZES = {"spring": (56, 22), "speed": (64, 10), "jump": (64, 10)}
    RECHARGE = 8.0  # seconds before a buff pad works again

    def __init__(self, kind, x, y):
        if kind not in self.SIZES:
            raise ValueError(f"Unknown pad type: {kind!r}")
        w, h = self.SIZES[kind]
        self.kind = kind
        self.rect = pygame.Rect(int(x - w // 2), int(y - h), w, h)
        self.cooldown = 0.0
        self.squash = 0.0

    @property
    def ready(self):
        return self.cooldown <= 0

    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt
        if self.squash > 0:
            self.squash = max(0.0, self.squash - dt * 4)

    def trigger(self):
        self.cooldown = 0.25 if self.kind == "spring" else self.RECHARGE
        self.squash = 1.0


class LuckyBlock:
    SIZE = 50

    def __init__(self, x, y):
        self.rect = pygame.Rect(int(x), int(y), self.SIZE, self.SIZE)
        self.used = False
        self.bump = 0.0

    def hit(self):
        """Returns True the first time only."""
        if self.used:
            return False
        self.used = True
        self.bump = 1.0
        return True

    def update(self, dt):
        if self.bump > 0:
            self.bump = max(0.0, self.bump - dt * 6)


class MovingPlatform:
    """Slides between two points (top-left corners), pausing briefly at each end."""

    def __init__(self, rect, start, end, speed=80):
        self.rect = pygame.Rect(rect)
        self.start = tuple(start)
        self.end = tuple(end)
        self.rect.topleft = self.start
        self.speed = speed
        self.length = max(1.0, math.hypot(self.end[0] - self.start[0], self.end[1] - self.start[1]))
        self.progress = 0.0
        self.direction = 1
        self.pause = 0.0
        self.delta = (0, 0)  # how far it moved this frame, used to carry the player
        self.surface = visuals.make_mover_surface(self.rect.width, self.rect.height)

    def update(self, dt):
        before = self.rect.topleft
        if self.pause > 0:
            self.pause -= dt
        else:
            self.progress += self.direction * self.speed * dt / self.length
            if self.progress >= 1.0:
                self.progress, self.direction, self.pause = 1.0, -1, 0.4
            elif self.progress <= 0.0:
                self.progress, self.direction, self.pause = 0.0, 1, 0.4
        s = self.progress * self.progress * (3 - 2 * self.progress)  # eases in and out
        self.rect.x = round(self.start[0] + (self.end[0] - self.start[0]) * s)
        self.rect.y = round(self.start[1] + (self.end[1] - self.start[1]) * s)
        self.delta = (self.rect.x - before[0], self.rect.y - before[1])