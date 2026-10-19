import pygame

import camera

class Player:
    def __init__(self, x, y):
        self.width = 100
        self.height = 80
        self.collision_inset = 10
        self.speed = 300
        self.jump_strength = 600
        self.gravity = 1500
        self.velocity_y = 100
        self.deaths = 0
        self.image = pygame.image.load("assets/bean.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.rect = pygame.Rect(int(x) + self.collision_inset,int(y),
        self.width - (self.collision_inset * 2), self.height)

    def move(self, platforms, dt):
        keys = pygame.key.get_pressed()
        movement_x = 0
        if keys[pygame.K_a]:
            movement_x -= 1
        if keys[pygame.K_d]:
            movement_x += 1
        self.rect.x += round(movement_x * self.speed * dt)
        for platform in platforms:
            if not self.rect.colliderect(platform):
                continue
            if movement_x > 0:
                self.rect.right = platform.left
            elif movement_x < 0:
                self.rect.left = platform.right
        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity_y = -self.jump_strength
            self.on_ground = False
        self.velocity_y += self.gravity * dt
        self.rect.y += round(self.velocity_y * dt)
        self.on_ground = False

        for platform in platforms:
            if not self.rect.colliderect(platform):
                continue
            if self.velocity_y >= 0 and self.rect.bottom >= platform.top:
                self.rect.bottom = platform.top
                self.velocity_y = 0
                self.on_ground = True
                break
            elif self.velocity_y < 0 and self.rect.top <= platform.bottom:
                self.rect.top = platform.bottom
                self.velocity_y = 0
                break

    def draw(self, screen, camera):
        image_rect = pygame.Rect(self.rect.x - self.collision_inset, self.rect.y,
            self.width, self.height)
        screen.blit(self.image, camera.apply(image_rect))
        screen_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, (255, 0, 0), screen_rect, 2)

    #class for respawning the player when they fall off the screen
    def respawn(self, x, y):
        self.deaths += 1
        self.rect.x = int(x) + self.collision_inset
        self.rect.y = int(y)
        self.velocity_y = 0
        self.on_ground = False
    