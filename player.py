import pygame
import os 
import camera

class Player:
    def __init__(self, x, y):
        self.width = 500
        self.height = 500
        self.speed = 300
        self.jump_strength = 600
        self.gravity = 1500
        # Load the bean sprite
        self.image = pygame.image.load("assets/bean.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

        self.rect = pygame.Rect(int(x), int(y), self.width, self.height)
        self.velocity_y = 0.0
        self.on_ground = False

    def move(self, platforms, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.rect.x -= int(self.speed * dt)
        if keys[pygame.K_d]:
            self.rect.x += int(self.speed * dt)
        for platform in platforms:
            if self.rect.colliderect(platform):
                if keys[pygame.K_d]:
                    self.rect.right = platform.left
                if keys[pygame.K_a]:
                    self.rect.left = platform.right
        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity_y = -self.jump_strength
            self.on_ground = False
        self.velocity_y += self.gravity * dt
        self.rect.y += int(self.velocity_y * dt)
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.top
                    self.on_ground = True
                elif self.velocity_y < 0: 
                    self.rect.top = platform.bottom
                self.velocity_y = 0
    def draw(self, screen, camera):
        screen_rect = camera.apply(self.rect)
        screen.blit(self.image, screen_rect)