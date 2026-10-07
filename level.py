import json
import pygame


class Level:
    def __init__(self, filename):
        with open(filename, "r") as file:
            self.data = json.load(file)
        self.platforms = []
        for platform in self.data["platforms"]:
            self.platforms.append(pygame.Rect(platform))
        self.ground_colour = (90, 90, 90)
    def draw(self, screen):
        for platform in self.platforms:
            pygame.draw.rect(screen, self.ground_colour, platform)