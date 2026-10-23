import math
import pygame
from visuals import make_enemy_surface, make_flyer_surface, make_hopper_surface


class Enemy(pygame.sprite.Sprite):
    """The walker: patrols back and forth along a flat stretch. Other types build on it.

    x is the left edge, y is where the enemy's FEET go (same as the player).
    patrol = (left_limit, right_limit) is the span the enemy's body stays inside.
    speed, damage and health are plain attributes so the adaptive difficulty
    system can scale them when a level loads.
    """
    THEME_KEY = "enemy"
    DEFAULT_COLOUR = (150, 60, 180)
    DEFAULT_SPEED = 100   # pixels per second
    DEFAULT_DAMAGE = 20

    def __init__(self, x, y, patrol=None, image=None, colour=None):
        super().__init__()
        self.custom_image = image is not None
        self.colour = colour or self.DEFAULT_COLOUR
        self.build_images(image)
        self.rect = self.image.get_rect()
        self.place(x, y)
        self.pos_x = float(self.rect.x)

        # patrol limits (left edge can't go below min, right edge can't pass max)
        if patrol:
            self.left_limit = float(patrol[0])
            self.right_limit = max(float(patrol[1]) - self.rect.width, self.left_limit)
        else:
            self.left_limit = self.right_limit = self.pos_x

        self.direction = 1
        self.speed = self.DEFAULT_SPEED
        self.damage = self.DEFAULT_DAMAGE
        self.health = 1    # one stomp kills
        self.anim = 0.0

    # --- things subclasses change ---
    def build_images(self, image=None):
        if image is not None:
            self.image_right = image
            self.image_left = pygame.transform.flip(image, True, False)
        else:
            self.image_right = make_enemy_surface(60, 60, 1, self.colour)
            self.image_left = make_enemy_surface(60, 60, -1, self.colour)
        self.image = self.image_right

    def place(self, x, y):
        self.rect.x = int(x)
        self.rect.bottom = int(y)

    def refresh_image(self):
        self.image = self.image_right if self.direction > 0 else self.image_left

    def update(self, dt, player_rect=None):
        if not self.alive:
            return
        self.anim += dt
        self.patrol(dt)
        self.refresh_image()

    def draw(self, screen, camera):
        bob = int(abs(math.sin(self.anim * 9)) * 4)  # little walking hop
        screen.blit(self.image, camera.apply(self.rect).move(0, -bob))

    # --- shared ---
    @property
    def alive(self):
        return self.health > 0

    def patrol(self, dt):
        self.pos_x += self.direction * self.speed * dt
        if self.pos_x >= self.right_limit:
            self.pos_x = self.right_limit
            self.direction = -1
        elif self.pos_x <= self.left_limit:
            self.pos_x = self.left_limit
            self.direction = 1
        self.rect.x = round(self.pos_x)

    def set_colour(self, colour):
        """Recolour the built-in art (does nothing if you gave it your own image)."""
        if self.custom_image:
            return
        self.colour = colour
        self.build_images(None)
        self.refresh_image()

    def take_damage(self, amount=1):
        """Returns True if this hit killed the enemy."""
        self.health -= amount
        return self.health <= 0

    def check_collision(self, rect):
        return self.rect.colliderect(rect)


class Flyer(Enemy):
    """Hovers in a wave pattern while drifting along its patrol. y is the hover height."""
    THEME_KEY = "flyer"
    DEFAULT_COLOUR = (232, 172, 62)
    DEFAULT_SPEED = 80
    SIZE = (56, 44)
    AMPLITUDE = 38
    BOB_SPEED = 2.2

    def build_images(self, image=None):
        w, h = self.SIZE
        self.frames = {
            (facing, frame): make_flyer_surface(w, h, facing, frame, self.colour)
            for facing in (1, -1) for frame in (0, 1)
        }
        self.image = self.frames[(1, 0)]

    def place(self, x, y):
        self.rect.x = int(x)
        self.rect.centery = int(y)
        self.base_y = float(y)

    def refresh_image(self):
        self.image = self.frames[(1 if self.direction > 0 else -1, int(self.anim * 8) % 2)]

    def update(self, dt, player_rect=None):
        if not self.alive:
            return
        self.anim += dt
        self.patrol(dt)
        self.rect.centery = round(self.base_y + math.sin(self.anim * self.BOB_SPEED) * self.AMPLITUDE)
        self.refresh_image()

    def draw(self, screen, camera):
        screen.blit(self.image, camera.apply(self.rect))


class Hopper(Enemy):
    """Wanders slowly, then crouches and leaps at you when you get close."""
    THEME_KEY = "hopper"
    DEFAULT_COLOUR = (222, 92, 92)
    DEFAULT_SPEED = 40       # slow wander while the player is far away
    DEFAULT_DAMAGE = 25
    SIZE = (56, 56)
    SIGHT = 380              # how close you have to be to get noticed
    JUMP_SPEED = 520
    LEAP_SPEED = 170
    GRAVITY = 1500
    WINDUP = 0.3             # crouch time before a leap
    COOLDOWN = 1.5

    def build_images(self, image=None):
        w, h = self.SIZE
        self.images = {
            (pose, facing): make_hopper_surface(w, h, facing, self.colour, pose)
            for pose in ("idle", "crouch", "air") for facing in (1, -1)
        }
        self.image = self.images[("idle", 1)]

    def place(self, x, y):
        self.rect.x = int(x)
        self.rect.bottom = int(y)
        self.ground_y = int(y)
        self.feet = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True
        self.windup = 0.0
        self.cooldown = 1.0

    def refresh_image(self):
        if not self.on_ground:
            pose = "air"
        elif self.windup > 0:
            pose = "crouch"
        else:
            pose = "idle"
        self.image = self.images[(pose, 1 if self.direction > 0 else -1)]

    def update(self, dt, player_rect=None):
        if not self.alive:
            return
        self.anim += dt
        if self.on_ground:
            self.cooldown -= dt
            if self.windup > 0:
                self.windup -= dt
                if self.windup <= 0:  # leap!
                    self.vy = -self.JUMP_SPEED
                    self.vx = self.LEAP_SPEED * self.direction
                    self.on_ground = False
            else:
                near = (
                    player_rect is not None
                    and abs(player_rect.centerx - self.rect.centerx) < self.SIGHT
                    and abs(player_rect.bottom - self.ground_y) < 160
                )
                if near:
                    self.direction = 1 if player_rect.centerx > self.rect.centerx else -1
                    if self.cooldown <= 0:
                        self.windup = self.WINDUP
                        self.cooldown = self.COOLDOWN
                else:
                    self.patrol(dt)
        else:
            self.vy += self.GRAVITY * dt
            self.feet += self.vy * dt
            self.pos_x += self.vx * dt
            if self.pos_x <= self.left_limit:
                self.pos_x, self.vx = self.left_limit, 0.0
            elif self.pos_x >= self.right_limit:
                self.pos_x, self.vx = self.right_limit, 0.0
            if self.feet >= self.ground_y and self.vy > 0:
                self.feet = float(self.ground_y)
                self.vy = self.vx = 0.0
                self.on_ground = True

        self.rect.x = round(self.pos_x)
        self.rect.bottom = round(self.feet)
        self.refresh_image()

    def draw(self, screen, camera):
        screen.blit(self.image, camera.apply(self.rect))


ENEMY_TYPES = {"walker": Enemy, "flyer": Flyer, "hopper": Hopper}


def create_enemy(data, theme=None):
    """Build an enemy from a level-file entry: {"type": "flyer", "x": .., "y": .., "patrol": [..]}."""
    cls = ENEMY_TYPES.get(data.get("type", "walker"), Enemy)
    colour = theme.get(cls.THEME_KEY) if theme else None
    return cls(data["x"], data["y"], data.get("patrol"), colour=colour)