import json
import pygame


class Level:
    def __init__(self, filename):
        with open(filename, "r") as file:
            self.data = json.load(file)
        self.platforms = []
        for platform in self.data["platforms"]:
            self.platforms.append(pygame.Rect(platform))
        self.ground_colour = (0, 255, 0)
    def draw(self, screen, camera):
        for platform in self.platforms:
            screen_rect = camera.apply(platform)
            pygame.draw.rect(screen, self.ground_colour, screen_rect)