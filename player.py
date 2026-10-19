import pygame


class Player:

    SPAWN_Y_IS_FEET = True

    def __init__(self, x, y):
        self.width = 100
        self.height = 100
        self.collision_inset = 5
        self.speed = 300
        self.jump_strength = 600
        self.gravity = 1500
        self.max_fall_speed = 900
        self.deaths = 0
        self.respawn_lock = 0.0

        self.image = pygame.image.load("assets/bean.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

        self.rect = pygame.Rect(
            0, 0,
            self.width - (self.collision_inset * 2),
            self.height,
        )
        self._place_at_spawn(x, y)
        self.velocity_y = 0.0
        self.on_ground = False

    def _place_at_spawn(self, x, y):
        """Put the player at the spawn point and keep float positions in sync."""
        self.rect.x = int(x) + self.collision_inset
        self.rect.y = int(y) - self.height if self.SPAWN_Y_IS_FEET else int(y)
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

    def move(self, platforms, dt, world_width=None):
        # freeze everything first so gravity can't build up while locked
        if self.respawn_lock > 0:
            self.respawn_lock -= dt
            return

        keys = pygame.key.get_pressed()
        movement_x = 0
        if keys[pygame.K_a]:
            movement_x -= 1
        if keys[pygame.K_d]:
            movement_x += 1

        # ---- horizontal movement ----
        self.pos_x += movement_x * self.speed * dt
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

        # ---- jump (uses on_ground from the previous frame) ----
        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity_y = -self.jump_strength
            self.on_ground = False

        # ---- vertical movement ----
        self.velocity_y += self.gravity * dt
        self.velocity_y = min(self.velocity_y, self.max_fall_speed)
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

        # ground probe: resting exactly on a platform counts as grounded,
        # which stops the sink-and-pop-up cycle
        if not self.on_ground and self.velocity_y >= 0:
            probe = self.rect.move(0, 1)
            if any(probe.colliderect(p) for p in platforms):
                self.on_ground = True
                self.velocity_y = 0.0
                self.pos_y = float(self.rect.y)

    def draw(self, screen, camera):
        image_rect = pygame.Rect(
            self.rect.x - self.collision_inset,
            self.rect.y,
            self.width,
            self.height,
        )
        screen.blit(self.image, camera.apply(image_rect))
        screen_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, (255, 0, 0), screen_rect, 2)

    # respawn the player (falling off the world, hitting a hazard, etc.)
    def respawn(self, x, y):
        self.respawn_lock = 0.2
        self._place_at_spawn(x, y)
        self.velocity_y = 0.0
        self.on_ground = False