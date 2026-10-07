import pygame

class Player:
    def __init__(self, x, y):
        self.width = 40
        self.height = 60
        self.speed = 300
        self.jump_strength = 650
        self.gravity = 1800
        self.rect = pygame.Rect(x, y, self.width, self.height)

        self.velocity_y = 0
        self.on_ground = False
    def move(self, platforms, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.rect.x -= int(self.speed * dt)

        if keys[pygame.K_d]:
            self.rect.x += int(self.speed * dt)

        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity_y = -self.jump_strength
            self.on_ground = False

        self.velocity_y = self.velocity_y + (self.gravity * dt)
        self.rect.y += int(self.velocity_y * dt)
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.velocity_y >= 0:
                    self.rect.bottom = platform.top
                    self.velocity_y = 0
                    self.on_ground = True
    def draw(self, screen):
        pygame.draw.rect(screen, (80, 180, 255), self.rect)