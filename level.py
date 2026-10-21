import json
import pygame
from tile import Tile
from enemy import Enemy


class Level:
    def __init__(self, filename):
        with open(filename, "r") as file:
            self.data = json.load(file)

        self.tiles = []

        # new format: {"rect": [x, y, w, h], "type": "ground"}
        for t in self.data.get("tiles", []):
            self.tiles.append(Tile(t["rect"], t.get("type", "ground")))

        # old format still works while you migrate levels
        for rect in self.data.get("platforms", []):
            self.tiles.append(Tile(rect, "ground"))
        for rect in self.data.get("hazards", []):
            self.tiles.append(Tile(rect, "lava"))

        # rect lists used by game.py and player.py
        self.platforms = [t.rect for t in self.tiles if t.solid]
        self.hazards = [t.rect for t in self.tiles if t.deadly]
        self.water = [t.rect for t in self.tiles if t.water]

        # enemies: {"x": 900, "y": 550, "patrol": [850, 1350], "type": "walker"}
        self.enemies = []
        for e in self.data.get("enemies", []):
            self.enemies.append(Enemy(e["x"], e["y"], e.get("patrol")))

    def draw(self, screen, camera):
        """Draw everything except water (water is drawn after the player)."""
        screen_rect = screen.get_rect()
        for tile in self.tiles:
            if tile.water:
                continue
            r = camera.apply(tile.rect)
            if r.colliderect(screen_rect):
                pygame.draw.rect(screen, tile.colour, r)

    def draw_water(self, screen, camera):
        """Translucent water, drawn on top of the player so they look submerged."""
        screen_rect = screen.get_rect()
        for tile in self.tiles:
            if not tile.water:
                continue
            r = camera.apply(tile.rect)
            if r.colliderect(screen_rect):
                overlay = pygame.Surface(r.size, pygame.SRCALPHA)
                overlay.fill((*tile.colour, 110))
                screen.blit(overlay, r.topleft)