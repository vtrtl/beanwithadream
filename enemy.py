import pygame


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol=None, image=None):
        super().__init__()
        if image is not None:
            self.image = image
        else:
            self.image = pygame.Surface((60, 60))
            self.image.fill((150, 60, 180))  # purple placeholder until you have art

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

    @property
    def alive(self):
        return self.health > 0

    def update(self, dt):
        if not self.alive:
            return
        self.pos_x += self.direction * self.speed * dt
        if self.pos_x >= self.right_limit:
            self.pos_x = self.right_limit
            self.direction = -1
        elif self.pos_x <= self.left_limit:
            self.pos_x = self.left_limit
            self.direction = 1
        self.rect.x = round(self.pos_x)

    def take_damage(self, amount=1):
        """Returns True if this hit killed the enemy."""
        self.health -= amount
        return self.health <= 0

    def check_collision(self, rect):
        return self.rect.colliderect(rect)

    def draw(self, screen, camera):
        screen.blit(self.image, camera.apply(self.rect))