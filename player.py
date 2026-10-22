import pygame


class Player:
    # True: player_start's y is where the bean's FEET go (stands on the platform).
    # False: player_start's y is the TOP of the bean (old behaviour).
    SPAWN_Y_IS_FEET = True

    # draw the red collision box (handy when debugging collisions)
    SHOW_HITBOX = True

    # Shrink the hitbox inside the visible bean, in pixels.
    # X is taken off BOTH the left and the right; TOP is taken off the head.
    # The feet stay put so the bean still stands exactly on the ground.
    HITBOX_SHRINK_X = 20
    HITBOX_SHRINK_TOP = 5

    def __init__(self, x, y):
        self.width = 100
        self.height = 100
        self.speed = 300
        self.jump_strength = 600
        self.gravity = 1500
        self.max_fall_speed = 900
        self.deaths = 0
        self.respawn_lock = 0.0

        # health
        self.max_health = 100
        self.health = self.max_health
        self.invincible_time = 1.0     # seconds of immunity after a hit
        self.invincible_timer = 0.0
        self.flash_timer = 0.0         # blink only after taking damage
        self.stomp_bounce = 400

        # water / drowning
        self.max_breath = 5.0        # seconds the head can stay underwater
        self.breath = self.max_breath
        self.breath_refill_rate = 3.0  # breath regained per second out of water
        self.in_water = False
        self.submerged = False
        self.water_speed_mult = 0.6
        self.water_gravity_mult = 0.4
        self.water_max_fall = 200
        self.swim_speed = 220

        self.image = pygame.image.load("assets/bean.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.image_left = pygame.transform.flip(self.image, True, False)
        self.facing = 1

        # Size the hitbox from the artwork itself: the tight box around the
        # non-transparent pixels, so what you see is what collides.
        self.bounds_right = self.image.get_bounding_rect()
        self.bounds_left = self.image_left.get_bounding_rect()
        hit_w = max(1, self.bounds_right.width - 2 * self.HITBOX_SHRINK_X)
        hit_h = max(1, self.bounds_right.height - self.HITBOX_SHRINK_TOP)
        self.rect = pygame.Rect(0, 0, hit_w, hit_h)
        self._place_at_spawn(x, y)
        self.velocity_y = 0.0
        self.on_ground = False

    def _place_at_spawn(self, x, y):
        """Put the player at the spawn point and keep float positions in sync."""
        self.rect.centerx = int(x) + self.width // 2
        if self.SPAWN_Y_IS_FEET:
            self.rect.bottom = int(y)
        else:
            self.rect.top = int(y)
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

    def take_damage(self, amount):
        """Returns True if the hit landed (False while invincible)."""
        if self.invincible_timer > 0:
            return False
        self.health = max(0, self.health - amount)
        self.invincible_timer = self.invincible_time
        self.flash_timer = self.invincible_time
        return True

    def bounce(self):
        """Hop up after stomping an enemy."""
        self.velocity_y = -self.stomp_bounce
        self.on_ground = False
        self.invincible_timer = max(self.invincible_timer, 0.3)

    def update_water(self, water_rects, dt):
        """Work out if we're in water, drain/refill breath. Returns True if drowned."""
        head = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 20)
        self.in_water = any(self.rect.colliderect(w) for w in water_rects)
        self.submerged = any(head.colliderect(w) for w in water_rects)

        if self.submerged:
            self.breath = max(0.0, self.breath - dt)
        else:
            self.breath = min(self.max_breath, self.breath + self.breath_refill_rate * dt)
        return self.breath <= 0

    def move(self, platforms, dt, world_width=None):
        # freeze everything first so gravity can't build up while locked
        if self.respawn_lock > 0:
            self.respawn_lock -= dt
            return

        if self.invincible_timer > 0:
            self.invincible_timer -= dt
        if self.flash_timer > 0:
            self.flash_timer -= dt

        keys = pygame.key.get_pressed()
        movement_x = 0
        if keys[pygame.K_a]:
            movement_x -= 1
        if keys[pygame.K_d]:
            movement_x += 1
        if movement_x != 0:
            self.facing = 1 if movement_x > 0 else -1

        speed = self.speed * (self.water_speed_mult if self.in_water else 1.0)

        # ---- horizontal movement ----
        self.pos_x += movement_x * speed * dt
        self.rect.x = round(self.pos_x)
        for platform in platforms:
            if not self.rect.colliderect(platform):
                continue
            if movement_x > 0:
                self.rect.right = platform.left
            elif movement_x < 0:
                self.rect.left = platform.right
            self.pos_x = float(self.rect.x)

        # world edges
        if self.rect.left < 0:
            self.rect.left = 0
            self.pos_x = float(self.rect.x)
        if world_width is not None and self.rect.right > world_width:
            self.rect.right = world_width
            self.pos_x = float(self.rect.x)

        # ---- jump / swim (uses on_ground from the previous frame) ----
        if keys[pygame.K_SPACE]:
            if self.on_ground:
                self.velocity_y = -self.jump_strength
                self.on_ground = False
            elif self.in_water:
                self.velocity_y = -self.swim_speed

        # ---- vertical movement ----
        gravity = self.gravity * (self.water_gravity_mult if self.in_water else 1.0)
        max_fall = self.water_max_fall if self.in_water else self.max_fall_speed
        self.velocity_y += gravity * dt
        self.velocity_y = min(self.velocity_y, max_fall)
        self.pos_y += self.velocity_y * dt
        self.rect.y = round(self.pos_y)

        self.on_ground = False
        for platform in platforms:
            if not self.rect.colliderect(platform):
                continue
            if self.velocity_y >= 0:
                self.rect.bottom = platform.top
                self.on_ground = True
            else:
                self.rect.top = platform.bottom
            self.pos_y = float(self.rect.y)
            self.velocity_y = 0.0
            break

        # ground probe: resting exactly on a platform counts as grounded
        if not self.on_ground and self.velocity_y >= 0:
            probe = self.rect.move(0, 1)
            if any(probe.colliderect(p) for p in platforms):
                self.on_ground = True
                self.velocity_y = 0.0
                self.pos_y = float(self.rect.y)

    def draw(self, screen, camera):
        # blink while invincible
        if self.flash_timer > 0 and int(self.flash_timer * 10) % 2 == 0:
            return
        flipped = self.facing < 0
        img = self.image_left if flipped else self.image
        bounds = self.bounds_left if flipped else self.bounds_right

        # squash and stretch with vertical speed
        sx = sy = 1.0
        stretch = min(abs(self.velocity_y) / 900, 1.0) * 0.15
        if stretch > 0.01:
            new_w = int(self.width * (1 - stretch * 0.6))
            new_h = int(self.height * (1 + stretch))
            img = pygame.transform.scale(img, (new_w, new_h))
            sx, sy = new_w / self.width, new_h / self.height

        # line up the artwork's visible bottom-centre with the hitbox's bottom-centre
        x = self.rect.centerx - bounds.centerx * sx
        y = self.rect.bottom - bounds.bottom * sy
        screen.blit(img, camera.apply(pygame.Rect(round(x), round(y), *img.get_size())))

        if self.SHOW_HITBOX:
            pygame.draw.rect(screen, (255, 0, 0), camera.apply(self.rect), 2)

    # respawn the player (falling off the world, hazards, drowning, etc.)
    def respawn(self, x, y):
        self.respawn_lock = 0.2
        self._place_at_spawn(x, y)
        self.velocity_y = 0.0
        self.on_ground = False
        self.breath = self.max_breath
        self.in_water = False
        self.submerged = False
        self.health = self.max_health
        self.invincible_timer = 0.0
        self.flash_timer = 0.0