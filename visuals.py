"""All the procedural art for the game: backgrounds, tile textures, particles.

Nothing here needs image files, and every colour comes from a theme (see themes.py),
so a level can change its whole look with one line of JSON.
"""
import math
import random
import pygame
from themes import FOREST


def _shade(colour, factor):
    return tuple(max(0, min(255, int(v * factor))) for v in colour)


# ---------------------------------------------------------------- background
class Background:
    """Gradient sky, drifting clouds and three layers of parallax hills.

    Night themes also get twinkling stars and a moon.
    """

    def __init__(self, width, height, theme=None):
        theme = theme or FOREST
        self.width = width
        self.height = height
        self.theme = theme
        self.sky = self._make_sky()
        self.cloud_surfs = [self._make_cloud(s) for s in (1.0, 1.4, 0.8)]
        rnd = random.Random(7)
        self.clouds = [
            (rnd.randint(0, width + 400), rnd.randint(30, 230), rnd.randrange(3), rnd.uniform(4, 12))
            for _ in range(12)
        ]
        # (surface, parallax factor): far hills move least. Tile widths loop seamlessly.
        specs = [(1800, 360, 55, 1, 0.12), (1500, 420, 45, 2, 0.25), (1200, 470, 35, 3, 0.40)]
        self.layers = [
            (self._make_hills(tile_w, base, amp, colour, seed), factor)
            for (tile_w, base, amp, seed, factor), colour in zip(specs, theme["hills"])
        ]

        self.stars = []
        self.moon = None
        if theme.get("stars"):
            srnd = random.Random(11)
            self.stars = [
                (srnd.randint(0, width), srnd.randint(0, int(height * 0.7)), srnd.choice((1, 1, 2)),
                 srnd.uniform(0, 6.28))
                for _ in range(120)
            ]
            self.moon = self._make_moon()

    def _make_sky(self):
        surf = pygame.Surface((self.width, self.height))
        top, bottom = self.theme["sky"]
        for y in range(self.height):
            t = y / self.height
            colour = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(surf, colour, (0, y), (self.width, y))
        return surf

    def _make_cloud(self, scale):
        w, h = int(180 * scale), int(70 * scale)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        colour = (*self.theme["cloud"], 230)
        for fx, fy, fr in ((0.22, 0.62, 0.30), (0.42, 0.45, 0.38), (0.65, 0.55, 0.34), (0.82, 0.68, 0.24)):
            pygame.draw.circle(surf, colour, (int(w * fx), int(h * fy)), int(h * fr))
        pygame.draw.rect(surf, colour, (int(w * 0.15), int(h * 0.55), int(w * 0.7), int(h * 0.33)),
                         border_radius=int(h * 0.15))
        return surf

    def _make_moon(self):
        size = 100
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        centre = (size // 2, size // 2)
        pygame.draw.circle(surf, (240, 240, 215, 40), centre, 46)   # soft glow
        pygame.draw.circle(surf, (240, 240, 215, 255), centre, 34)
        pygame.draw.circle(surf, (0, 0, 0, 0), (centre[0] + 14, centre[1] - 6), 30)  # cut a crescent
        return surf

    def _make_hills(self, tile_w, base, amp, colour, seed):
        rnd = random.Random(seed)
        surf = pygame.Surface((tile_w, self.height + 120), pygame.SRCALPHA)
        p1, p2, p3 = (rnd.uniform(0, 6.28) for _ in range(3))
        points = []
        for x in range(0, tile_w + 1, 10):
            a = 2 * math.pi * x / tile_w
            h = base + amp * (0.6 * math.sin(a + p1) + 0.3 * math.sin(3 * a + p2) + 0.1 * math.sin(7 * a + p3))
            points.append((x, h))
        points += [(tile_w, surf.get_height()), (0, surf.get_height())]
        pygame.draw.polygon(surf, colour, points)
        return surf

    def draw(self, screen, cam_x, cam_y, t):
        screen.blit(self.sky, (0, 0))

        for x, y, size, phase in self.stars:  # twinkle
            level = int(170 + 85 * math.sin(t * 2 + phase))
            pygame.draw.rect(screen, (level, level, min(255, level + 20)), (x, y, size, size))
        if self.moon:
            screen.blit(self.moon, (self.width - 220 - cam_x * 0.02, 50 - cam_y * 0.02))

        span = self.width + 400
        for x, y, variant, speed in self.clouds:
            sx = (x + t * speed - cam_x * 0.08) % span - 200
            screen.blit(self.cloud_surfs[variant], (sx, y - cam_y * 0.05))
        for surf, factor in self.layers:
            tile_w = surf.get_width()
            off = int(cam_x * factor) % tile_w
            y = -int(cam_y * factor)
            screen.blit(surf, (-off, y))
            if tile_w - off < self.width:
                screen.blit(surf, (tile_w - off, y))


# ---------------------------------------------------------------- tiles
def _make_stone_texture(w, h, rnd, theme):
    """Rubble of stones in uneven rows. Used for the layer under the dirt."""
    tex = pygame.Surface((w, h))
    tex.fill(theme["gap"])  # dark gaps between the stones
    stone = theme["stone"]
    y = 0
    while y < h:
        row_h = rnd.randint(20, 28)
        x = -rnd.randint(0, 20)
        while x < w:
            sw = rnd.randint(28, 52)
            depth = 1 - 0.35 * (y / max(h, 1))
            base = _shade(stone, rnd.uniform(0.85, 1.1) * depth)
            r = pygame.Rect(x + 1, y + 1, sw - 2, row_h - 2)
            pygame.draw.rect(tex, base, r, border_radius=6)
            pygame.draw.line(tex, _shade(base, 1.2), (r.x + 5, r.y + 1), (r.right - 6, r.y + 1))
            pygame.draw.line(tex, _shade(base, 0.75), (r.x + 5, r.bottom - 1), (r.right - 6, r.bottom - 1))
            for _ in range(2):  # little speckles
                sx = rnd.randint(r.x + 4, r.right - 6)
                sy = rnd.randint(r.y + 3, r.bottom - 5)
                pygame.draw.rect(tex, _shade(base, rnd.choice((0.8, 1.15))), (sx, sy, 2, 2))
            x += sw
        y += row_h
    return tex


def make_ground_surface(w, h, seed, theme=None):
    """Dirt with a coloured top and a layer of stone underneath. Built once per tile.

    Thin platforms (under 80px tall) are dirt all the way down.
    """
    theme = theme or FOREST
    rnd = random.Random(seed)
    surf = pygame.Surface((w, h))
    has_stone = h >= 80
    dirt_h = int(h * 0.4) if has_stone else h

    # dirt, a little darker with depth
    dirt = theme["dirt"]
    for y in range(h):
        shade = max(0.7, 1 - 0.25 * (y / max(dirt_h, 1)))
        pygame.draw.line(surf, _shade(dirt, shade), (0, y), (w, y))
    speckles = (_shade(dirt, 0.8), _shade(dirt, 1.14), _shade(dirt, 0.71))
    for _ in range(max(1, w * dirt_h // 500)):
        x, y, size = rnd.randrange(w), rnd.randrange(12, max(13, dirt_h)), rnd.randint(2, 5)
        pygame.draw.rect(surf, rnd.choice(speckles), (x, y, size, size))

    if has_stone:
        # pebbles buried in the dirt, getting more common towards the stone
        for _ in range(max(2, w // 40)):
            px = rnd.randrange(w)
            py = int(14 + (dirt_h - 8) * rnd.random() ** 0.6)
            pw, ph = rnd.randint(5, 10), rnd.randint(4, 7)
            colour = _shade(theme["pebble"], rnd.uniform(0.8, 1.15))
            pygame.draw.ellipse(surf, colour, (px, py, pw, ph))
            pygame.draw.ellipse(surf, _shade(colour, 0.6), (px, py, pw, ph), 1)

        # the stone layer, with an uneven edge where it meets the dirt
        tex = _make_stone_texture(w, h, rnd, theme)
        phase = rnd.uniform(0, 6.28)
        edges = []
        for x in range(0, w, 4):
            by = dirt_h + int(5 * math.sin(x * 0.045 + phase) + 3 * math.sin(x * 0.13 + phase * 2))
            by = max(14, min(h - 10, by + rnd.randint(-2, 2)))
            edges.append((x, by))
            surf.set_clip(pygame.Rect(x, by, 4, h - by))
            surf.blit(tex, (0, 0))
        surf.set_clip(None)
        shadow = _shade(dirt, 0.75)
        for x, by in edges:  # soft shadow where the dirt sits on the stone
            pygame.draw.rect(surf, shadow, (x, by - 3, 4, 3))

    # grass / snow / sand on top
    top_colour, top_light = theme["top"], theme["top_light"]
    top = min(10, h)
    pygame.draw.rect(surf, top_colour, (0, 0, w, top))
    for x in range(0, w, 7):  # dripping down into the dirt
        pygame.draw.rect(surf, top_colour, (x, top - 2, rnd.randint(3, 5), rnd.randint(3, 8)))
    pygame.draw.rect(surf, top_light, (0, 0, w, min(3, h)))

    pygame.draw.rect(surf, theme["outline"], surf.get_rect(), 2)
    return surf


def make_water_surface(w, h, theme=None):
    """Translucent water that gets deeper and darker towards the bottom."""
    theme = theme or FOREST
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    shallow, deep = theme["water"]
    for y in range(h):
        t = y / max(h, 1)
        colour = tuple(int(shallow[i] + (deep[i] - shallow[i]) * t) for i in range(3))
        pygame.draw.line(surf, (*colour, int(80 + 90 * t)), (0, y), (w, y))
    return surf


def draw_lava(screen, r, world_x, t):
    """Animated lava: a glowing wavy top and drifting hot spots."""
    pygame.draw.rect(screen, (200, 45, 20), r)
    step = 6
    for x in range(0, r.width, step):
        wave = 4 + 2 * math.sin(t * 4 + (world_x + x) * 0.08)
        pygame.draw.rect(screen, (255, 160, 40), (r.x + x, r.y, step, min(int(wave) + 2, r.height)))
    for x in range(10, r.width, 28):
        yy = r.y + 9 + 3 * math.sin(t * 3 + (world_x + x))
        pygame.draw.circle(screen, (255, 215, 100), (r.x + x, int(yy)), 2)


def draw_exit(screen, r, unlocked, t):
    """An arched door: grey with a padlock when locked, golden and glowing when open."""
    if unlocked:
        glow_r = int(r.width * 1.3 + 4 * math.sin(t * 4))
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 230, 120, 70), (glow_r, glow_r), glow_r)
        screen.blit(glow, (r.centerx - glow_r, r.centery - glow_r))
    frame = (90, 60, 30)
    fill = (240, 200, 60) if unlocked else (110, 110, 125)
    pygame.draw.rect(screen, frame, r.inflate(10, 10),
                     border_top_left_radius=r.width // 2 + 5, border_top_right_radius=r.width // 2 + 5)
    pygame.draw.rect(screen, fill, r,
                     border_top_left_radius=r.width // 2, border_top_right_radius=r.width // 2)
    pygame.draw.circle(screen, frame, (r.right - 14, r.centery + 10), 5)
    if not unlocked:
        body = pygame.Rect(0, 0, 22, 18)
        body.center = (r.centerx, r.centery)
        pygame.draw.rect(screen, (60, 60, 70), body, border_radius=3)
        pygame.draw.arc(screen, (60, 60, 70), (body.x + 3, body.y - 14, 16, 20), 0, math.pi, 3)


# ---------------------------------------------------------------- enemy
def make_enemy_surface(w, h, facing, colour=(150, 60, 180)):
    """A grumpy blob in the theme's enemy colour. facing is 1 (right) or -1 (left)."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    body = pygame.Rect(0, int(h * 0.12), w, int(h * 0.88))
    radius = int(w * 0.3)
    pygame.draw.rect(surf, colour, body, border_radius=radius)
    pygame.draw.rect(surf, _shade(colour, 0.6), body, 3, border_radius=radius)
    pygame.draw.ellipse(surf, _shade(colour, 1.28), (int(w * 0.15), int(h * 0.2), int(w * 0.3), int(h * 0.14)))
    eye_y = int(h * 0.45)
    for ex in (int(w * 0.32), int(w * 0.68)):
        pygame.draw.circle(surf, (255, 255, 255), (ex, eye_y), int(w * 0.13))
        pygame.draw.circle(surf, (30, 20, 40), (ex + facing * 3, eye_y + 1), int(w * 0.06))
    brow = _shade(colour, 0.35)
    pygame.draw.line(surf, brow, (int(w * 0.18), eye_y - int(w * 0.15)), (int(w * 0.42), eye_y - int(w * 0.08)), 4)
    pygame.draw.line(surf, brow, (int(w * 0.82), eye_y - int(w * 0.15)), (int(w * 0.58), eye_y - int(w * 0.08)), 4)
    return surf


# ---------------------------------------------------------------- ambient effects
class SnowAmbient:
    """Gently falling snow, drawn over the whole screen."""

    def __init__(self, width, height, count=90):
        rnd = random.Random(3)
        self.width, self.height = width, height
        self.t = 0.0
        # [x, y, fall speed, sway phase, size]
        self.flakes = [
            [rnd.uniform(0, width), rnd.uniform(0, height), rnd.uniform(30, 80),
             rnd.uniform(0, 6.28), rnd.choice((2, 2, 3, 4))]
            for _ in range(count)
        ]

    def update(self, dt):
        self.t += dt
        for f in self.flakes:
            f[1] += f[2] * dt
            f[0] += math.sin(self.t + f[3]) * 20 * dt
            if f[1] > self.height:
                f[1] = -5
                f[0] = random.uniform(0, self.width)

    def draw(self, screen):
        for x, y, _, _, size in self.flakes:
            pygame.draw.circle(screen, (255, 255, 255), (int(x % self.width), int(y)), size // 2 + 1)


def make_ambient(theme, width, height):
    """Returns an object with update(dt) and draw(screen), or None."""
    if theme.get("ambient") == "snow":
        return SnowAmbient(width, height)
    return None


# ---------------------------------------------------------------- particles
class ParticleSystem:
    MAX_PARTICLES = 300

    def __init__(self):
        self.particles = []

    def emit(self, x, y, colours, count=10, speed=160, up=100, gravity=600, life=(0.3, 0.7), size=(2, 5)):
        for _ in range(count):
            if len(self.particles) >= self.MAX_PARTICLES:
                return
            angle = random.uniform(0, 2 * math.pi)
            sp = random.uniform(0.3, 1.0) * speed
            life_time = random.uniform(*life)
            # [x, y, vx, vy, time_left, life, colour, size, gravity]
            self.particles.append([
                x, y, math.cos(angle) * sp, math.sin(angle) * sp - up,
                life_time, life_time, random.choice(colours), random.uniform(*size), gravity,
            ])

    def update(self, dt):
        alive = []
        for p in self.particles:
            p[4] -= dt
            if p[4] <= 0:
                continue
            p[3] += p[8] * dt
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            alive.append(p)
        self.particles = alive

    def draw(self, screen, camera):
        for p in self.particles:
            size = max(1, int(p[7] * (p[4] / p[5]) + 1))
            pygame.draw.rect(screen, p[6], (int(p[0] - camera.offset_x), int(p[1] - camera.offset_y), size, size))