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
class Layer:
    """One piece of scenery. Layers with front=True draw over the level (fog, fireflies)."""
    front = False

    def draw(self, screen, cam_x, cam_y, t):
        raise NotImplementedError


class TiledLayer(Layer):
    """A strip of scenery that repeats sideways and scrolls slower than the camera (parallax)."""

    def __init__(self, surface, speed):
        self.surface = surface
        self.speed = speed

    def draw(self, screen, cam_x, cam_y, t):
        tile_w = self.surface.get_width()
        off = int(cam_x * self.speed) % tile_w
        y = -int(cam_y * self.speed)
        screen.blit(self.surface, (-off, y))
        if tile_w - off < screen.get_width():
            screen.blit(self.surface, (tile_w - off, y))


def _strip(tile_w, height):
    return pygame.Surface((tile_w, height + 120), pygame.SRCALPHA)


def build_hills(spec, width, height, seed):
    """Smooth rolling hills (or big dunes, depending on the colour and size)."""
    rnd = random.Random(seed)
    tile_w = spec.get("tile", 1500)
    base, amp = spec.get("base", 420), spec.get("amp", 45)
    surf = _strip(tile_w, height)
    p1, p2, p3 = (rnd.uniform(0, 6.28) for _ in range(3))
    points = []
    for x in range(0, tile_w + 1, 10):
        a = 2 * math.pi * x / tile_w  # whole numbers of waves, so the strip loops seamlessly
        y = base + amp * (0.6 * math.sin(a + p1) + 0.3 * math.sin(3 * a + p2) + 0.1 * math.sin(7 * a + p3))
        points.append((x, y))
    points += [(tile_w, surf.get_height()), (0, surf.get_height())]
    pygame.draw.polygon(surf, spec["colour"], points)
    return TiledLayer(surf, spec.get("speed", 0.25))


def build_mountains(spec, width, height, seed):
    """Jagged peaks. Add "snow": (r, g, b) for snow caps."""
    rnd = random.Random(seed)
    step = spec.get("step", 150)
    n = max(4, (spec.get("tile", 1800) // step) // 2 * 2)  # an even number of points: peak, valley, peak ...
    tile_w = n * step
    base, amp = spec.get("base", 330), spec.get("amp", 120)
    surf = _strip(tile_w, height)
    ys = [base - amp * (rnd.uniform(0.6, 1.0) if i % 2 == 0 else rnd.uniform(0.0, 0.3)) for i in range(n)]

    points = []
    for i in range(n):
        x0, y0 = i * step, ys[i]
        x1, y1 = (i + 1) * step, ys[(i + 1) % n]
        points.append((x0, y0))
        points.append(((x0 + x1) / 2, (y0 + y1) / 2 + rnd.uniform(-10, 10)))  # a kink so slopes look rocky
    points.append((tile_w, ys[0]))
    points += [(tile_w, surf.get_height()), (0, surf.get_height())]
    pygame.draw.polygon(surf, spec["colour"], points)

    snow = spec.get("snow")
    if snow:
        for i in range(0, n, 2):  # the even points are the peaks
            px, py = i * step, ys[i]
            lx, ly = px - step, ys[(i - 1) % n]
            rx, ry = px + step, ys[(i + 1) % n]
            lp = (px + (lx - px) * 0.3, py + (ly - py) * 0.3)
            rp = (px + (rx - px) * 0.3, py + (ry - py) * 0.3)
            cap = [
                (px, py), rp, ((px + rp[0]) / 2, (py + rp[1]) / 2 + 12),
                (px, (lp[1] + rp[1]) / 2 + 18), ((px + lp[0]) / 2, (py + lp[1]) / 2 + 12), lp,
            ]
            for shift in ((0, tile_w) if i == 0 else (0,)):  # the first peak sits on the seam
                pygame.draw.polygon(surf, snow, [(x + shift, y) for x, y in cap])
    return TiledLayer(surf, spec.get("speed", 0.1))


def _draw_tree(surf, kind, x, base_y, size, colour, snow):
    if kind == "round":
        trunk = _shade(colour, 0.7)
        pygame.draw.rect(surf, trunk, (int(x - 4), int(base_y - size * 0.32), 8, int(size * 0.32)))
        for dx, dy, r in ((0, 0.58, 0.28), (-0.2, 0.44, 0.22), (0.2, 0.44, 0.22)):
            pygame.draw.circle(surf, _shade(colour, 1.05), (int(x + dx * size), int(base_y - dy * size)), int(r * size))
        return
    pygame.draw.rect(surf, _shade(colour, 0.7), (int(x - 3), int(base_y - size * 0.2), 6, int(size * 0.2)))
    for i in range(3):  # three stacked tiers
        tw = size * (0.55 - 0.13 * i)
        th = size * 0.36
        bottom = base_y - size * 0.12 - i * size * 0.27
        tier = _shade(colour, 0.9 if i % 2 else 1.0)
        pygame.draw.polygon(surf, tier, [(x, bottom - th), (x - tw / 2, bottom), (x + tw / 2, bottom)])
        if snow:
            pygame.draw.polygon(surf, snow, [(x, bottom - th), (x - tw * 0.22, bottom - th * 0.55),
                                             (x + tw * 0.22, bottom - th * 0.55)])


def build_trees(spec, width, height, seed):
    """A row of tree silhouettes: "kind": "pine" or "round", optional "snow" dusting."""
    rnd = random.Random(seed)
    tile_w, base, colour = spec.get("tile", 1500), spec.get("base", 470), spec["colour"]
    surf = _strip(tile_w, height)
    pygame.draw.rect(surf, colour, (0, base, tile_w, surf.get_height() - base))
    x = rnd.randint(10, 40)
    while x < tile_w + 40:
        size = rnd.randint(70, 130)
        for shift in (0, -tile_w):  # a wrapped copy so the strip loops cleanly
            _draw_tree(surf, spec.get("kind", "pine"), x + shift, base + 6, size, colour, spec.get("snow"))
        x += rnd.randint(40, 85)
    return TiledLayer(surf, spec.get("speed", 0.3))


def build_ruins(spec, width, height, seed):
    """Castle towers and broken walls on the horizon, with a few lit windows."""
    rnd = random.Random(seed)
    tile_w, base, colour = spec.get("tile", 2000), spec.get("base", 455), spec["colour"]
    lit = spec.get("windows", (255, 214, 120))
    surf = _strip(tile_w, height)
    pygame.draw.rect(surf, colour, (0, base, tile_w, surf.get_height() - base))
    clear = (0, 0, 0, 0)
    x = rnd.randint(80, 200)
    while x < tile_w - 420:
        tw, th = rnd.randint(46, 72), rnd.randint(130, 230)
        pygame.draw.rect(surf, colour, (x, base - th, tw, th + 10))
        if rnd.random() < 0.5:  # pointed roof
            pygame.draw.polygon(surf, colour, [(x - 6, base - th), (x + tw + 6, base - th),
                                               (x + tw // 2, base - th - rnd.randint(50, 80))])
        else:  # battlements
            for cx in range(x, x + tw - 6, 14):
                pygame.draw.rect(surf, colour, (cx, base - th - 10, 8, 10))
        for wy in (45, 95):  # arched windows
            if wy < th - 20:
                window = lit if rnd.random() < 0.6 else _shade(colour, 0.6)
                wx = x + tw // 2 - 4
                pygame.draw.rect(surf, window, (wx, base - th + wy, 8, 14))
                pygame.draw.circle(surf, window, (wx + 4, base - th + wy), 4)
        gap, wall_h = rnd.randint(110, 200), rnd.randint(55, 95)
        pygame.draw.rect(surf, colour, (x + tw, base - wall_h, gap, wall_h + 10))
        for cx in range(x + tw, x + tw + gap - 8, 20):
            pygame.draw.rect(surf, colour, (cx, base - wall_h - 8, 10, 8))
        if rnd.random() < 0.7:  # a chunk knocked out of the wall
            bx = x + tw + rnd.randint(20, max(21, gap - 50))
            pygame.draw.rect(surf, clear, (bx, base - wall_h - 10, rnd.randint(18, 34), rnd.randint(14, 30)))
        x += tw + gap + rnd.randint(150, 320)
    return TiledLayer(surf, spec.get("speed", 0.2))


def build_pyramids(spec, width, height, seed):
    rnd = random.Random(seed)
    tile_w, base, colour = spec.get("tile", 1800), spec.get("base", 425), spec["colour"]
    surf = _strip(tile_w, height)
    pygame.draw.rect(surf, spec.get("ground", colour), (0, base, tile_w, surf.get_height() - base))
    for i in range(3):
        x = i * (tile_w // 3) + rnd.randint(220, 320)
        half = rnd.randint(85, 130)
        peak = base - int(half * 1.25)
        pygame.draw.polygon(surf, _shade(colour, 1.08), [(x - half, base), (x, peak), (x, base)])  # lit side
        pygame.draw.polygon(surf, _shade(colour, 0.82), [(x, peak), (x + half, base), (x, base)])  # shaded side
    return TiledLayer(surf, spec.get("speed", 0.16))


def _make_cloud(colour, scale):
    w, h = int(180 * scale), int(70 * scale)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    fill = (*colour, 230)
    for fx, fy, fr in ((0.22, 0.62, 0.30), (0.42, 0.45, 0.38), (0.65, 0.55, 0.34), (0.82, 0.68, 0.24)):
        pygame.draw.circle(surf, fill, (int(w * fx), int(h * fy)), int(h * fr))
    pygame.draw.rect(surf, fill, (int(w * 0.15), int(h * 0.55), int(w * 0.7), int(h * 0.33)),
                     border_radius=int(h * 0.15))
    return surf


class CloudsLayer(Layer):
    def __init__(self, spec, width, seed):
        rnd = random.Random(seed)
        self.width = width
        self.surfs = [_make_cloud(spec["colour"], s) for s in (1.0, 1.4, 0.8)]
        self.clouds = [
            (rnd.randint(0, width + 400), rnd.randint(30, 230), rnd.randrange(3), rnd.uniform(4, 12))
            for _ in range(spec.get("count", 12))
        ]

    def draw(self, screen, cam_x, cam_y, t):
        span = self.width + 400
        for x, y, variant, speed in self.clouds:
            sx = (x + t * speed - cam_x * 0.08) % span - 200
            screen.blit(self.surfs[variant], (sx, y - cam_y * 0.05))


class SunLayer(Layer):
    def __init__(self, spec, width):
        r, colour = spec.get("radius", 46), spec["colour"]
        size = r * 6
        c = size // 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        for ring in range(r * 3, r, -4):  # soft glow, brighter towards the middle
            alpha = max(0, int(55 * (1 - (ring - r) / (r * 2))))
            pygame.draw.circle(surf, (*colour, alpha), (c, c), ring)
        for i in range(14):  # rays
            ang = 2 * math.pi * i / 14
            p1 = (c + math.cos(ang - 0.07) * r * 1.15, c + math.sin(ang - 0.07) * r * 1.15)
            p2 = (c + math.cos(ang + 0.07) * r * 1.15, c + math.sin(ang + 0.07) * r * 1.15)
            tip = (c + math.cos(ang) * r * 2.4, c + math.sin(ang) * r * 2.4)
            pygame.draw.polygon(surf, (*colour, 90), [p1, tip, p2])
        pygame.draw.circle(surf, (*colour, 255), (c, c), r)
        pygame.draw.circle(surf, (255, 255, 255, 200), (c, c), int(r * 0.7))
        self.surface, self.size = surf, size
        self.x, self.y, self.speed = spec.get("x", 0.78) * width, spec.get("y", 110), spec.get("speed", 0.02)

    def draw(self, screen, cam_x, cam_y, t):
        self.surface.set_alpha(int(225 + 30 * math.sin(t * 1.5)))  # gentle pulse
        screen.blit(self.surface, (self.x - cam_x * self.speed - self.size / 2,
                                   self.y - cam_y * self.speed - self.size / 2))


class MoonLayer(Layer):
    def __init__(self, spec, width):
        r, colour = spec.get("radius", 40), spec["colour"]
        size = r * 4
        c = size // 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        for ring in range(int(r * 1.8), r, -3):
            pygame.draw.circle(surf, (*colour, max(0, int(45 * (1 - (ring - r) / (r * 0.8))))), (c, c), ring)
        pygame.draw.circle(surf, (*colour, 255), (c, c), r)
        pygame.draw.circle(surf, (0, 0, 0, 0), (c + int(r * 0.4), c - int(r * 0.15)), int(r * 0.88))  # crescent
        self.surface, self.size = surf, size
        self.x, self.y, self.speed = spec.get("x", 0.75) * width, spec.get("y", 100), spec.get("speed", 0.015)

    def draw(self, screen, cam_x, cam_y, t):
        screen.blit(self.surface, (self.x - cam_x * self.speed - self.size / 2,
                                   self.y - cam_y * self.speed - self.size / 2))


class StarsLayer(Layer):
    """Twinkling stars and the occasional shooting star."""

    def __init__(self, spec, width, height, seed):
        rnd = random.Random(seed)
        self.width = width
        self.stars = [
            (rnd.randint(0, width), rnd.randint(0, int(height * 0.7)), rnd.choice((1, 1, 2)), rnd.uniform(0, 6.28))
            for _ in range(spec.get("count", 120))
        ]

    def draw(self, screen, cam_x, cam_y, t):
        for x, y, size, phase in self.stars:
            level = int(170 + 85 * math.sin(t * 2 + phase))
            pygame.draw.rect(screen, (level, level, min(255, level + 20)),
                             ((x - cam_x * 0.01) % self.width, y, size, size))
        cycle, local = int(t // 9), t % 9  # one shooting star every 9 seconds
        if local < 0.7:
            rnd = random.Random(cycle)
            sx, sy = rnd.randint(100, self.width - 300), rnd.randint(20, 180)
            progress = local / 0.7
            head = (sx + progress * 260, sy + progress * 110)
            tail = (head[0] - 70 * (1 - progress * 0.3), head[1] - 30 * (1 - progress * 0.3))
            pygame.draw.line(screen, (255, 255, 240), tail, head, 2)
            pygame.draw.circle(screen, (255, 255, 255), (int(head[0]), int(head[1])), 2)


class AuroraLayer(Layer):
    """Rippling curtains of light. Pre-drawn once, then drifted and pulsed."""
    TILE_W = 1600

    def __init__(self, colours, seed, speed=0.04):
        rnd = random.Random(seed)
        self.speed = speed
        self.curtains = []
        for i, colour in enumerate(colours):
            self.curtains.append((self._make_curtain(colour, rnd), 12 + 6 * i, rnd.uniform(0, 6.28), 25 + 45 * i))

    def _make_curtain(self, colour, rnd):
        w, h = self.TILE_W, 320
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        p1, p2, p3 = (rnd.uniform(0, 6.28) for _ in range(3))
        for x in range(0, w, 4):
            a = 2 * math.pi * x / w  # whole numbers of waves, so the curtain loops
            top = 90 + 40 * math.sin(3 * a + p1) + 22 * math.sin(5 * a + p2)
            ray = 130 + 60 * math.sin(2 * a + p3)
            for j in range(0, int(ray), 8):
                alpha = int(170 * (1 - j / ray) ** 1.6)
                if alpha < 4:
                    break
                pygame.draw.rect(surf, (*colour, alpha), (x, int(top) + j, 4, 8))
        return surf

    def draw(self, screen, cam_x, cam_y, t):
        for surf, drift, phase, y in self.curtains:
            surf.set_alpha(int(170 + 70 * math.sin(t * 0.7 + phase)))  # shimmer
            off = int(cam_x * self.speed + t * drift) % self.TILE_W
            yy = y - cam_y * 0.02
            screen.blit(surf, (-off, yy))
            if self.TILE_W - off < screen.get_width():
                screen.blit(surf, (self.TILE_W - off, yy))


class FogLayer(Layer):
    """Soft drifting fog banks. Drawn in front of the level by default."""
    front = True
    TILE_W = 1400

    def __init__(self, spec, seed):
        rnd = random.Random(seed)
        height = 180
        surf = pygame.Surface((self.TILE_W, height), pygame.SRCALPHA)
        for _ in range(60):
            rx, ry = rnd.randint(120, 260), rnd.randint(18, 42)
            cx, cy = rnd.randint(0, self.TILE_W), rnd.randint(ry, height - ry)
            puff = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(puff, (*spec["colour"], spec.get("alpha", 12)), puff.get_rect())
            for shift in (0, -self.TILE_W, self.TILE_W):  # blit (not draw) so overlapping puffs build up
                surf.blit(puff, (cx - rx + shift, cy - ry))
        self.surface = surf
        self.y = spec.get("y", 400)
        self.speed = spec.get("speed", 0.5)
        self.drift = rnd.uniform(6, 12)

    def draw(self, screen, cam_x, cam_y, t):
        off = int(cam_x * self.speed + t * self.drift) % self.TILE_W
        yy = self.y - cam_y * 0.3
        screen.blit(self.surface, (-off, yy))
        if self.TILE_W - off < screen.get_width():
            screen.blit(self.surface, (self.TILE_W - off, yy))


class BirdsLayer(Layer):
    def __init__(self, spec, width, seed):
        rnd = random.Random(seed)
        self.width, self.colour = width, spec["colour"]
        self.birds = [
            (rnd.uniform(0, width + 300), rnd.uniform(90, 230), rnd.uniform(25, 45), rnd.uniform(0, 6.28))
            for _ in range(spec.get("count", 6))
        ]

    def draw(self, screen, cam_x, cam_y, t):
        span = self.width + 300
        for x0, y0, speed, phase in self.birds:
            x = (x0 + t * speed - cam_x * 0.06) % span - 150
            y = y0 + math.sin(t * 0.8 + phase) * 10 - cam_y * 0.04
            flap = math.sin(t * 8 + phase) * 6
            pygame.draw.lines(screen, self.colour, False, [(x - 10, y + flap), (x, y), (x + 10, y + flap)], 2)


class FirefliesLayer(Layer):
    """Glowing dots that wander and blink. Drawn in front of the level."""
    front = True

    def __init__(self, spec, width, height, seed):
        rnd = random.Random(seed)
        self.width = width
        self.flies = [
            (rnd.uniform(0, width + 200), rnd.uniform(height * 0.35, height * 0.85), rnd.uniform(0, 6.28))
            for _ in range(spec.get("count", 25))
        ]
        self.glows = [self._glow(spec["colour"], alpha) for alpha in (60, 110, 170, 230)]

    @staticmethod
    def _glow(colour, alpha):
        surf = pygame.Surface((24, 24), pygame.SRCALPHA)
        for r in range(12, 0, -2):
            pygame.draw.circle(surf, (*colour, int(alpha * (1 - r / 12) + 20)), (12, 12), r)
        pygame.draw.circle(surf, (255, 255, 255, min(255, alpha + 30)), (12, 12), 2)
        return surf

    def draw(self, screen, cam_x, cam_y, t):
        for bx, by, phase in self.flies:
            x = (bx - cam_x * 0.5 + math.sin(t * 0.7 + phase) * 30) % (self.width + 200) - 100
            y = by - cam_y * 0.3 + math.sin(t * 0.9 + phase * 1.3) * 20
            blink = int((math.sin(t * 2 + phase * 3) + 1) / 2 * 3.99)
            screen.blit(self.glows[blink], (x - 12, y - 12))


LAYER_BUILDERS = {
    "sun": lambda spec, w, h, seed: SunLayer(spec, w),
    "moon": lambda spec, w, h, seed: MoonLayer(spec, w),
    "stars": lambda spec, w, h, seed: StarsLayer(spec, w, h, seed),
    "clouds": lambda spec, w, h, seed: CloudsLayer(spec, w, seed),
    "mountains": build_mountains,
    "hills": build_hills,
    "trees": build_trees,
    "ruins": build_ruins,
    "pyramids": build_pyramids,
    "aurora": lambda spec, w, h, seed: AuroraLayer(spec["colours"], seed, spec.get("speed", 0.04)),
    "fog": lambda spec, w, h, seed: FogLayer(spec, seed),
    "birds": lambda spec, w, h, seed: BirdsLayer(spec, w, seed),
    "fireflies": lambda spec, w, h, seed: FirefliesLayer(spec, w, h, seed),
}


def make_layer(spec, width, height, seed):
    kind = spec["type"]
    if kind not in LAYER_BUILDERS:
        raise ValueError(f"Unknown background layer type: {kind!r} (try one of {sorted(LAYER_BUILDERS)})")
    layer = LAYER_BUILDERS[kind](spec, width, height, seed)
    if "front" in spec:
        layer.front = spec["front"]
    return layer


class Background:
    """A gradient sky plus the theme's scenery layers, back to front."""

    def __init__(self, width, height, theme=None):
        theme = theme or FOREST
        self.width = width
        self.height = height
        self.theme = theme
        self.sky = self._make_sky()
        self.layers = [make_layer(spec, width, height, 11 + i * 17) for i, spec in enumerate(theme["layers"])]

    def _make_sky(self):
        surf = pygame.Surface((self.width, self.height))
        top, bottom = self.theme["sky"]
        for y in range(self.height):
            t = y / self.height
            colour = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(surf, colour, (0, y), (self.width, y))
        return surf

    def draw(self, screen, cam_x, cam_y, t):
        """The sky and every layer that sits behind the level."""
        screen.blit(self.sky, (0, 0))
        for layer in self.layers:
            if not layer.front:
                layer.draw(screen, cam_x, cam_y, t)

    def draw_front(self, screen, cam_x, cam_y, t):
        """Layers that pass in front of the level (fog, fireflies)."""
        for layer in self.layers:
            if layer.front:
                layer.draw(screen, cam_x, cam_y, t)


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


def draw_checkpoint(screen, x, y, active, t):
    """A flag on a pole. (x, y) is where its base touches the ground, in screen coordinates."""
    pole = (205, 205, 215)
    pygame.draw.rect(screen, pole, (x - 3, y - 72, 6, 72))
    pygame.draw.circle(screen, pole, (x, y - 74), 5)
    colour = (90, 220, 120) if active else (150, 150, 162)
    wave = 3 * math.sin(t * 5) if active else 0
    points = [(x + 3, y - 70), (x + 38, y - 58 + wave), (x + 3, y - 46)]
    pygame.draw.polygon(screen, colour, points)
    pygame.draw.polygon(screen, _shade(colour, 0.6), points, 2)


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


# ---------------------------------------------------------------- items
_FONTS = {}


def _font(size):
    if size not in _FONTS:
        _FONTS[size] = pygame.font.Font(None, size)
    return _FONTS[size]


def draw_coin(screen, x, y, t, phase=0.0):
    """A spinning, bobbing gold coin centred on (x, y) in screen coordinates."""
    bob = 3 * math.sin(t * 3 + phase)
    w = max(4, int(abs(math.cos(t * 4 + phase)) * 22))
    rect = pygame.Rect(0, 0, w, 22)
    rect.center = (int(x), int(y + bob))
    pygame.draw.ellipse(screen, (170, 120, 20), rect.inflate(4, 4))
    pygame.draw.ellipse(screen, (255, 205, 60), rect)
    if w > 12:
        pygame.draw.ellipse(screen, (255, 238, 150), rect.inflate(-w // 2, -10))


def draw_pad(screen, r, kind, ready, squash, t):
    """Springs and buff pads. r is the pad's rect in screen coordinates."""
    if kind == "spring":
        drop = int(10 * squash)  # the plate squashes down after a bounce
        base = pygame.Rect(r.x + 8, r.bottom - 5, r.width - 16, 5)
        plate = pygame.Rect(r.x, r.y + drop, r.width, 6)
        pygame.draw.rect(screen, (90, 92, 105), base, border_radius=2)
        points = [(r.centerx, base.y)]
        for i in range(1, 5):
            yy = base.y + (plate.bottom - base.y) * i / 4
            points.append((r.centerx + (14 if i % 2 else -14), yy))
        pygame.draw.lines(screen, (200, 200, 215), False, points, 3)
        pygame.draw.rect(screen, (230, 70, 70), plate, border_radius=3)
        pygame.draw.rect(screen, (120, 25, 25), plate, 2, border_radius=3)
        return

    colour = {"speed": (255, 150, 40), "jump": (90, 220, 130)}.get(kind, (200, 200, 200))
    if not ready:
        colour = (105, 108, 120)  # recharging
    pygame.draw.rect(screen, colour, r, border_radius=4)
    pygame.draw.rect(screen, _shade(colour, 0.55), r, 2, border_radius=4)
    if ready:
        wave = int(3 * math.sin(t * 5))
        for i in (0, 1):
            if kind == "speed":
                cx = r.centerx - 14 + i * 24 + wave
                pts = [(cx, r.y - 22), (cx + 10, r.y - 14), (cx, r.y - 6)]
            else:
                cy = r.y - 6 - i * 11 - wave
                pts = [(r.centerx - 10, cy), (r.centerx, cy - 9), (r.centerx + 10, cy)]
            pygame.draw.lines(screen, colour, False, pts, 3)


def draw_lucky_block(screen, r, used, bump, t):
    """A gold ? block. bump (0 to 1) makes it jump up when hit."""
    r = r.move(0, -int(10 * bump))
    if used:
        fill, edge = (150, 130, 105), (80, 65, 50)
    else:
        pulse = 0.5 + 0.5 * math.sin(t * 4)
        fill, edge = (240, int(185 + 25 * pulse), 50), (125, 80, 10)
    pygame.draw.rect(screen, fill, r, border_radius=6)
    pygame.draw.rect(screen, _shade(fill, 1.2), (r.x + 5, r.y + 4, r.width - 10, 5), border_radius=2)
    pygame.draw.rect(screen, edge, r, 3, border_radius=6)
    for cx, cy in ((r.x + 7, r.y + 7), (r.right - 7, r.y + 7), (r.x + 7, r.bottom - 7), (r.right - 7, r.bottom - 7)):
        pygame.draw.circle(screen, edge, (cx, cy), 2)
    if not used:
        font = _font(46)
        pos = font.render("?", True, (255, 255, 255)).get_rect(center=r.center)
        screen.blit(font.render("?", True, (110, 70, 10)), pos.move(2, 2))
        screen.blit(font.render("?", True, (255, 255, 255)), pos)


def make_mover_surface(w, h):
    """A riveted metal plate for moving platforms."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (118, 126, 145), (0, 0, w, h), border_radius=6)
    pygame.draw.rect(surf, (170, 178, 198), (3, 2, w - 6, 4), border_radius=2)
    pygame.draw.rect(surf, (80, 86, 104), (3, h - 6, w - 6, 4), border_radius=2)
    for x in range(14, w - 8, 26):
        pygame.draw.circle(surf, (60, 64, 80), (x, h // 2), 3)
    pygame.draw.rect(surf, (45, 50, 66), (0, 0, w, h), 2, border_radius=6)
    return surf


def draw_buff_aura(screen, centre, buffs, t):
    """A pulsing glow around the player while a buff is active."""
    colours = {"speed": (255, 170, 60), "jump": (100, 230, 140)}
    for i, name in enumerate(buffs):
        colour = colours.get(name, (255, 255, 255))
        radius = int(58 + 4 * math.sin(t * 6 + i))
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*colour, 45), (radius, radius), radius)
        pygame.draw.circle(glow, (*colour, 120), (radius, radius), radius, 3)
        screen.blit(glow, (centre[0] - radius, centre[1] - radius))


# ---------------------------------------------------------------- more enemies
def make_flyer_surface(w, h, facing, frame, colour):
    """A winged flyer. frame 0 has its wings up, frame 1 has them down."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    dark, wing = _shade(colour, 0.55), _shade(colour, 1.15)
    if frame == 0:
        left = [(w * 0.30, h * 0.50), (w * 0.00, h * 0.05), (w * 0.42, h * 0.30)]
    else:
        left = [(w * 0.30, h * 0.50), (w * 0.00, h * 0.70), (w * 0.42, h * 0.62)]
    right = [(w - x, y) for x, y in left]
    for pts in (left, right):
        pts = [(int(x), int(y)) for x, y in pts]
        pygame.draw.polygon(surf, wing, pts)
        pygame.draw.polygon(surf, dark, pts, 2)
    body = pygame.Rect(int(w * 0.22), int(h * 0.26), int(w * 0.56), int(h * 0.66))
    pygame.draw.ellipse(surf, colour, body)
    pygame.draw.ellipse(surf, dark, body, 3)
    eye_y = int(h * 0.52)
    for ex in (int(w * 0.40), int(w * 0.60)):
        pygame.draw.circle(surf, (255, 255, 255), (ex, eye_y), 5)
        pygame.draw.circle(surf, (30, 20, 40), (ex + facing * 2, eye_y + 1), 2)
    pygame.draw.line(surf, dark, (int(w * 0.33), eye_y - 8), (int(w * 0.45), eye_y - 5), 2)
    pygame.draw.line(surf, dark, (int(w * 0.67), eye_y - 8), (int(w * 0.55), eye_y - 5), 2)
    return surf


def make_hopper_surface(w, h, facing, colour, pose):
    """A bouncy blob. pose is "idle", "crouch" (winding up) or "air" (stretched)."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if pose == "crouch":
        body = pygame.Rect(0, int(h * 0.38), w, int(h * 0.62))
    elif pose == "air":
        body = pygame.Rect(int(w * 0.10), int(h * 0.02), int(w * 0.80), int(h * 0.98))
    else:
        body = pygame.Rect(int(w * 0.04), int(h * 0.14), int(w * 0.92), int(h * 0.86))
    radius = int(min(body.width, body.height) * 0.38)
    pygame.draw.rect(surf, colour, body, border_radius=radius)
    pygame.draw.rect(surf, _shade(colour, 0.6), body, 3, border_radius=radius)
    pygame.draw.ellipse(surf, _shade(colour, 1.28),
                        (body.x + int(body.width * 0.15), body.y + int(body.height * 0.1),
                         int(body.width * 0.3), int(body.height * 0.14)))
    eye_y = body.y + int(body.height * 0.40)
    eye_r = max(4, int(body.width * 0.13))
    for ex in (body.x + int(body.width * 0.32), body.x + int(body.width * 0.68)):
        pygame.draw.circle(surf, (255, 255, 255), (ex, eye_y), eye_r)
        pygame.draw.circle(surf, (30, 20, 40), (ex + facing * 3, eye_y + 1), max(2, eye_r // 2))
    brow = _shade(colour, 0.35)
    pygame.draw.line(surf, brow, (body.x + int(body.width * 0.18), eye_y - eye_r - 3),
                     (body.x + int(body.width * 0.42), eye_y - eye_r + 2), 4)
    pygame.draw.line(surf, brow, (body.x + int(body.width * 0.82), eye_y - eye_r - 3),
                     (body.x + int(body.width * 0.58), eye_y - eye_r + 2), 4)
    return surf


# ---------------------------------------------------------------- ground props
def make_prop(spec, variant, theme):
    """A little decoration that stands on the ground (or hangs from a platform).

    spec is an entry from the theme's "props" list; variant picks one of a few looks.
    """
    kind = spec["kind"]
    rnd = random.Random(f"{kind}-{variant}")
    top = theme["top"]

    if kind == "grass":
        w, h = 26, 22
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for _ in range(rnd.randint(4, 7)):
            x, blade, lean = rnd.randint(3, w - 4), rnd.randint(9, h - 2), rnd.randint(-5, 5)
            pygame.draw.polygon(surf, _shade(top, rnd.uniform(0.7, 1.1)), [(x - 2, h), (x + 2, h), (x + lean, h - blade)])
        return surf

    if kind == "flower":
        w, h = 18, 30
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        stem = rnd.randint(16, 22)
        green = _shade(top, 0.7)
        pygame.draw.line(surf, green, (9, h), (9, h - stem), 2)
        pygame.draw.polygon(surf, green, [(9, h - 6), (15, h - 11), (9, h - 10)])
        colour = rnd.choice(spec.get("colours", [(255, 120, 140)]))
        pygame.draw.circle(surf, colour, (9, h - stem), 5)
        pygame.draw.circle(surf, (255, 230, 120), (9, h - stem), 2)
        return surf

    if kind == "bush":
        w, h = 64, 34
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        body = _shade(top, 0.62)
        for rect in ((0, 12, 34, 22), (20, 3, 34, 31), (34, 12, 30, 22)):
            pygame.draw.ellipse(surf, body, rect)
            pygame.draw.ellipse(surf, _shade(body, 0.7), rect, 2)
        for _ in range(5):
            pygame.draw.circle(surf, _shade(top, 0.95), (rnd.randint(14, 50), rnd.randint(8, 22)), 2)
        return surf

    if kind == "mushroom":
        w, h = 30, 28
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cap = rnd.choice(spec.get("colours", [(220, 80, 80)]))
        if spec.get("glow"):
            pygame.draw.circle(surf, (*cap, 45), (15, 12), 14)
        pygame.draw.rect(surf, (235, 230, 220), (12, 15, 6, 13), border_radius=2)
        pygame.draw.ellipse(surf, cap, (3, 4, 24, 16))
        pygame.draw.ellipse(surf, _shade(cap, 0.6), (3, 4, 24, 16), 2)
        for sx, sy in ((10, 9), (19, 11)):
            pygame.draw.circle(surf, (255, 255, 255), (sx, sy), 2)
        return surf

    if kind == "cactus":
        w, h = 44, 66
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        green = spec.get("colours", [(66, 138, 82)])[0]
        edge = _shade(green, 0.6)
        parts = [(16, 12, 12, 54)]                                # trunk
        if variant % 2 == 0:
            parts += [(4, 34, 14, 8), (4, 20, 8, 22)]             # left arm
        if variant % 3 != 1:
            parts += [(26, 40, 14, 8), (32, 28, 8, 20)]           # right arm
        for rect in parts:
            pygame.draw.rect(surf, green, rect, border_radius=4)
            pygame.draw.rect(surf, edge, rect, 2, border_radius=4)
        pygame.draw.rect(surf, green, (16, 12, 12, 54), border_radius=5)  # re-cover the trunk joins
        if variant == 3:
            pygame.draw.circle(surf, (255, 130, 160), (22, 11), 4)
        return surf

    if kind == "rock":
        w, h = 34, 16
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        x = 2
        for _ in range(rnd.randint(1, 3)):
            rw, rh = rnd.randint(10, 18), rnd.randint(7, 14)
            colour = _shade(theme["pebble"], rnd.uniform(0.85, 1.15))
            pygame.draw.ellipse(surf, colour, (x, h - rh, rw, rh))
            pygame.draw.ellipse(surf, _shade(colour, 0.6), (x, h - rh, rw, rh), 1)
            x += rnd.randint(8, 12)
        return surf

    if kind == "drift":
        w, h = rnd.randint(50, 90), rnd.randint(14, 22)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, theme["top_light"], (0, 0, w, h * 2))  # only the top half shows
        pygame.draw.ellipse(surf, _shade(theme["top"], 0.9), (0, 0, w, h * 2), 2)
        return surf

    if kind == "icicle":
        w, h = 34, 30
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(rnd.randint(2, 4)):
            x, length = 5 + i * 8 + rnd.randint(-2, 2), rnd.randint(10, 28)
            pygame.draw.polygon(surf, (205, 232, 252), [(x - 3, 0), (x + 3, 0), (x, length)])
            pygame.draw.line(surf, (255, 255, 255), (x - 1, 1), (x, max(2, length - 6)), 1)
        return surf

    raise ValueError(f"Unknown prop type: {kind!r}")


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


class LeafAmbient:
    """A few leaves drifting down and sideways."""

    COLOURS = [(96, 170, 70), (220, 165, 55), (200, 100, 50), (140, 190, 80)]

    def __init__(self, width, height, count=24):
        rnd = random.Random(5)
        self.width, self.height = width, height
        self.t = 0.0
        # [x, y, fall speed, sway phase, colour, size]
        self.leaves = [
            [rnd.uniform(0, width), rnd.uniform(0, height), rnd.uniform(35, 70),
             rnd.uniform(0, 6.28), rnd.choice(self.COLOURS), rnd.choice((7, 8, 10))]
            for _ in range(count)
        ]

    def update(self, dt):
        self.t += dt
        for leaf in self.leaves:
            leaf[1] += leaf[2] * dt
            leaf[0] += (math.sin(self.t * 1.5 + leaf[3]) * 30 + 15) * dt
            if leaf[1] > self.height:
                leaf[1] = -10
                leaf[0] = random.uniform(0, self.width)

    def draw(self, screen):
        for x, y, _, phase, colour, size in self.leaves:
            flutter = 2 + int(abs(math.sin(self.t * 3 + phase)) * (size // 2))
            pygame.draw.ellipse(screen, colour, (int(x % self.width), int(y), size, flutter))


class SandAmbient:
    """Streaks of sand blowing across the screen."""

    def __init__(self, width, height, count=60):
        rnd = random.Random(9)
        self.width, self.height = width, height
        self.t = 0.0
        # [x, y, speed, length]
        self.grains = [
            [rnd.uniform(0, width), rnd.uniform(0, height), rnd.uniform(350, 600), rnd.randint(10, 26)]
            for _ in range(count)
        ]

    def update(self, dt):
        self.t += dt
        for g in self.grains:
            g[0] += g[2] * dt
            if g[0] > self.width + 30:
                g[0] = -30
                g[1] = random.uniform(0, self.height)

    def draw(self, screen):
        for x, y, _, length in self.grains:
            yy = y + math.sin(self.t * 2 + x * 0.01) * 4
            pygame.draw.line(screen, (236, 208, 160), (x, yy), (x - length, yy - 1), 1)


def make_ambient(theme, width, height):
    """Returns an object with update(dt) and draw(screen), or None."""
    kind = theme.get("ambient")
    if kind == "snow":
        return SnowAmbient(width, height)
    if kind == "leaves":
        return LeafAmbient(width, height)
    if kind == "sand":
        return SandAmbient(width, height)
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