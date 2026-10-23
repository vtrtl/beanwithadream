import json
import math
import pygame
from tile import Tile
from enemy import create_enemy
from items import Coin, Pad, LuckyBlock, MovingPlatform
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

        # enemies: {"type": "walker" | "flyer" | "hopper", "x": 900, "y": 550, "patrol": [850, 1350]}
        self.enemies = [create_enemy(e, self.theme) for e in self.data.get("enemies", [])]

        # coins: [x, y]  or a row  {"x": 300, "y": 450, "count": 4, "dx": 45}
        self.coins = []
        for entry in self.data.get("coins", []):
            if isinstance(entry, dict):
                for i in range(entry.get("count", 1)):
                    self.coins.append(Coin(entry["x"] + i * entry.get("dx", 0),
                                           entry["y"] + i * entry.get("dy", 0)))
            else:
                self.coins.append(Coin(*entry))
        self.coin_total = len(self.coins)

        # pads: {"type": "spring" | "speed" | "jump", "x": centre, "y": ground height}
        self.pads = [Pad(p["type"], p["x"], p["y"]) for p in self.data.get("pads", [])]

        # lucky blocks: [x, y] (top-left corner), hit them from below
        self.lucky_blocks = [LuckyBlock(*b) for b in self.data.get("lucky_blocks", [])]

        # moving platforms: {"rect": [x, y, w, h], "from": [x, y], "to": [x, y], "speed": 80}
        self.movers = [
            MovingPlatform(m["rect"], m["from"], m["to"], m.get("speed", 80))
            for m in self.data.get("movers", [])
        ]

        # checkpoints: [[x_centre, y_feet], ...] in the order you reach them
        self.checkpoints = [tuple(c) for c in self.data.get("checkpoints", [])]

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
            enemy.set_colour(self.theme[enemy.THEME_KEY])

    # ------------------------------------------------------------ updating
    def solids(self):
        """Every rect the player can stand on or bump into, this frame."""
        return (
            self.platforms
            + [m.rect for m in self.movers]
            + [b.rect for b in self.lucky_blocks]
        )

    def update_movers(self, dt, player):
        """Move the platforms, carrying the player along if they're standing on one."""
        for mover in self.movers:
            riding = player.respawn_lock <= 0 and player.is_standing_on(mover.rect)
            mover.update(dt)
            if riding:
                player.shift(*mover.delta)

    def update_items(self, dt):
        for pad in self.pads:
            pad.update(dt)
        for block in self.lucky_blocks:
            block.update(dt)

    # ------------------------------------------------------------ drawing
    def draw_checkpoints(self, screen, camera, active, t=0.0):
        """active is the (x, y) of the checkpoint the player last reached, or None."""
        for cx, cy in self.checkpoints:
            sx, sy = cx - camera.offset_x, cy - camera.offset_y
            if -60 < sx < screen.get_width() + 60:
                visuals.draw_checkpoint(screen, int(sx), int(sy), (cx, cy) == active, t)

    def draw_exit(self, screen, camera, unlocked, t=0.0):
        if self.exit_rect:
            visuals.draw_exit(screen, camera.apply(self.exit_rect), unlocked, t)

    def draw_items(self, screen, camera, t=0.0):
        """Moving platforms, lucky blocks, pads and coins."""
        screen_rect = screen.get_rect().inflate(120, 120)
        for mover in self.movers:
            r = camera.apply(mover.rect)
            if r.colliderect(screen_rect):
                screen.blit(mover.surface, r.topleft)
        for block in self.lucky_blocks:
            r = camera.apply(block.rect)
            if r.colliderect(screen_rect):
                visuals.draw_lucky_block(screen, r, block.used, block.bump, t)
        for pad in self.pads:
            r = camera.apply(pad.rect)
            if r.colliderect(screen_rect):
                visuals.draw_pad(screen, r, pad.kind, pad.ready, pad.squash, t)
        for coin in self.coins:
            sx, sy = coin.x - camera.offset_x, coin.y - camera.offset_y
            if -40 < sx < screen.get_width() + 40:
                visuals.draw_coin(screen, sx, sy, t, coin.phase)

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