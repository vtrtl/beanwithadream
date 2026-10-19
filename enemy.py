import pygame

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.speed = 2

    def update(self):
        # Move the enemy down the screen
        self.rect.y += self.speed