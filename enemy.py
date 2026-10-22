import math
import pygame
from visuals import make_enemy_surface


class Enemy(pygame.sprite.Sprite):
    """A simple patrolling enemy. Walks back and forth along a flat stretch.

    x is the left edge, y is where the enemy's FEET go (same as the player).
    patrol = (left_limit, right_limit) is the span the enemy's body stays inside.
    All the numbers below are plain attributes so the adaptive difficulty
    system can scale them when a level loads.
    """

    def __init__(self, x, y, patrol=None, image=None, colour=(150, 60, 180)):
        super().__init__()
        self.custom_image = image is not None
        if image is not None:
            self.image_right = image
            self.image_left = pygame.transform.flip(image, True, False)
        else:
            self.image_right = make_enemy_surface(60, 60, 1, colour)
            self.image_left = make_enemy_surface(60, 60, -1, colour)
        self.image = self.image_right

        self.rect = self.image.get_rect()
        self.rect.x = int(x)
        self.rect.bottom = int(y)
        self.pos_x = float(self.rect.x)

        # patrol limits (left edge can't go below min, right edge can't pass max)
        if patrol:
            self.left_limit = float(patrol[0])
            self.right_limit = max(float(patrol[1]) - self.rect.width, self.left_limit)
        else:
            self.left_limit = self.right_limit = self.pos_x

        self.direction = 1
        self.speed = 100   # pixels per second
        self.damage = 20   # taken off the player's health on contact
        self.health = 1    # one stomp kills
        self.anim = 0.0

    @property
    def alive(self):
        return self.health > 0

    def update(self, dt):
        if not self.alive:
            return
        self.anim += dt
        self.pos_x += self.direction * self.speed * dt
        if self.pos_x >= self.right_limit:
            self.pos_x = self.right_limit
            self.direction = -1
        elif self.pos_x <= self.left_limit:
            self.pos_x = self.left_limit
            self.direction = 1
        self.rect.x = round(self.pos_x)
        self.image = self.image_right if self.direction > 0 else self.image_left

    def set_colour(self, colour):
        """Recolour the built-in blob (does nothing if you gave it your own image)."""
        if self.custom_image:
            return
        self.image_right = make_enemy_surface(60, 60, 1, colour)
        self.image_left = make_enemy_surface(60, 60, -1, colour)
        self.image = self.image_right if self.direction > 0 else self.image_left

    def take_damage(self, amount=1):
        """Returns True if this hit killed the enemy."""
        self.health -= amount
        return self.health <= 0

    def check_collision(self, rect):
        return self.rect.colliderect(rect)

    def draw(self, screen, camera):
        bob = int(abs(math.sin(self.anim * 9)) * 4)  # little walking hop
        screen.blit(self.image, camera.apply(self.rect).move(0, -bob))