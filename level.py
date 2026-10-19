import json
import pygame
from tile import Tile


class Level:
    def __init__(self, filename):
        with open(filename, "r") as file:
            self.data = json.load(file)

        self.tiles = []

        # new format: {"rect": [x, y, w, h], "type": "ground"}
        for t in self.data.get("tiles", []):
            self.tiles.append(Tile(t["rect"], t.get("type", "ground")))
        for rect in self.data.get("platforms", []):
            self.tiles.append(Tile(rect, "ground"))
        for rect in self.data.get("hazards", []):
            self.tiles.append(Tile(rect, "lava"))

        self.platforms = [t.rect for t in self.tiles if t.solid]
        self.hazards = [t.rect for t in self.tiles if t.deadly]
        self.water = [t.rect for t in self.tiles if t.water]

    def draw(self, screen, camera):
        screen_rect = screen.get_rect()
        for tile in self.tiles:
            if tile.water:
                continue
            r = camera.apply(tile.rect)
            if r.colliderect(screen_rect):
                pygame.draw.rect(screen, tile.colour, r)

    def draw_water(self, screen, camera):
        screen_rect = screen.get_rect()
        for tile in self.tiles:
            if not tile.water:
                continue
            r = camera.apply(tile.rect)
            if r.colliderect(screen_rect):
                overlay = pygame.Surface(r.size, pygame.SRCALPHA)
                overlay.fill((*tile.colour, 110))
                screen.blit(overlay, r.topleft)