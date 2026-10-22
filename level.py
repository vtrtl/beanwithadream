import json
import math
import pygame
from tile import Tile
from enemy import Enemy
from themes import THEMES, DEFAULT_THEME
import visuals


class Level:
    def __init__(self, filename):
        with open(filename, "r") as file:
            self.data = json.load(file)

        # which visual theme to use: "theme": "night" in the JSON (default forest)
        name = self.data.get("theme", DEFAULT_THEME)
        self.theme_name = name if name in THEMES else DEFAULT_THEME
        self.theme = THEMES[self.theme_name]

        self.tiles = []

        # new format: {"rect": [x, y, w, h], "type": "ground"}
        for t in self.data.get("tiles", []):
            self.tiles.append(Tile(t["rect"], t.get("type", "ground")))

        # old format still works while you migrate levels
        for rect in self.data.get("platforms", []):
            self.tiles.append(Tile(rect, "ground"))
        for rect in self.data.get("hazards", []):
            self.tiles.append(Tile(rect, "lava"))

        self._build_surfaces()

        # rect lists used by game.py and player.py
        self.platforms = [t.rect for t in self.tiles if t.solid]
        self.hazards = [t.rect for t in self.tiles if t.deadly]
        self.water = [t.rect for t in self.tiles if t.water]

        # enemies: {"x": 900, "y": 550, "patrol": [850, 1350], "type": "walker"}
        self.enemies = []
        for e in self.data.get("enemies", []):
            self.enemies.append(Enemy(e["x"], e["y"], e.get("patrol"), colour=self.theme["enemy"]))

        # exit door: "exit": [x, y, w, h]
        exit_data = self.data.get("exit")
        self.exit_rect = pygame.Rect(exit_data) if exit_data else None

    def _build_surfaces(self):
        """Pre-render the textures once so drawing stays cheap."""
        for tile in self.tiles:
            tile.surface = None
            r = tile.rect
            if tile.kind == "ground":
                tile.surface = visuals.make_ground_surface(r.width, r.height, r.x * 7919 + r.y, self.theme)
            elif tile.water:
                tile.surface = visuals.make_water_surface(r.width, r.height, self.theme)

    def set_theme(self, name):
        """Switch theme on the fly (used by the preview key in game.py)."""
        self.theme_name = name if name in THEMES else DEFAULT_THEME
        self.theme = THEMES[self.theme_name]
        self._build_surfaces()
        for enemy in self.enemies:
            enemy.set_colour(self.theme["enemy"])

    def draw_exit(self, screen, camera, unlocked, t=0.0):
        if self.exit_rect:
            visuals.draw_exit(screen, camera.apply(self.exit_rect), unlocked, t)

    def draw(self, screen, camera, t=0.0):
        """Draw everything except water (water is drawn after the player)."""
        screen_rect = screen.get_rect()
        for tile in self.tiles:
            if tile.water:
                continue
            r = camera.apply(tile.rect)
            if not r.colliderect(screen_rect):
                continue
            if tile.deadly:
                visuals.draw_lava(screen, r, tile.rect.x, t)
            elif tile.surface is not None:
                screen.blit(tile.surface, r.topleft)
            else:
                pygame.draw.rect(screen, tile.colour, r)

    def draw_water(self, screen, camera, t=0.0):
        """Translucent water, drawn on top of the player so they look submerged."""
        screen_rect = screen.get_rect()
        line_colour = self.theme["water_line"]
        for tile in self.tiles:
            if not tile.water:
                continue
            r = camera.apply(tile.rect)
            if not r.colliderect(screen_rect):
                continue
            screen.blit(tile.surface, r.topleft)
            points = [
                (r.x + x, r.y + 2 + 2 * math.sin(t * 2.5 + (tile.rect.x + x) * 0.05))
                for x in range(0, r.width + 1, 8)
            ]
            pygame.draw.lines(screen, line_colour, False, points, 3)