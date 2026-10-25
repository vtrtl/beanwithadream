"""Visual themes. A level picks one with  "theme": "night"  in its JSON.

A theme is mostly three things:
  "layers"  the scenery behind the level, drawn back to front (see visuals.LAYER_BUILDERS)
  "props"   decorations placed on top of the ground (grass, cacti, icicles ...)
  colours   for the sky, ground, water and enemies

To make a new theme, copy one of these, change it, and add it to THEMES.
Anything you leave out falls back to the forest theme.

Layer types
  sun, moon, stars, clouds, mountains (add "snow" for snow caps), hills, trees ("kind": "pine"
  or "round"), ruins, pyramids, aurora, birds, fog and fireflies. "speed" is how fast a layer
  scrolls compared with the camera, so small numbers look far away. fog and fireflies draw
  in FRONT of the level; any layer can be flipped with "front": True / False.

Prop types
  grass, flower, bush, mushroom, cactus, rock, drift, icicle. "density" is roughly how many
  per 100px of ground. "anchor": "bottom" hangs a prop from the underside of a platform.
"""

FOREST = {
    "sky": ((110, 165, 255), (225, 240, 255)),          # top colour, bottom colour
    "layers": [
        {"type": "sun", "colour": (255, 240, 170), "x": 0.8, "y": 105, "radius": 42, "speed": 0.02},
        {"type": "clouds", "colour": (255, 255, 255)},
        {"type": "mountains", "colour": (166, 200, 236), "base": 340, "amp": 130, "step": 170, "speed": 0.08},
        {"type": "birds", "colour": (55, 65, 95), "count": 7},
        {"type": "hills", "colour": (130, 182, 150), "base": 410, "amp": 42, "tile": 1700, "speed": 0.18},
        {"type": "trees", "colour": (84, 150, 98), "kind": "round", "base": 465, "tile": 1500, "speed": 0.32},
        {"type": "hills", "colour": (92, 158, 104), "base": 495, "amp": 28, "tile": 1300, "speed": 0.45},
    ],
    "props": [
        {"kind": "grass", "density": 4.5},
        {"kind": "flower", "density": 1.3,
         "colours": [(255, 120, 140), (255, 220, 90), (250, 250, 255), (170, 140, 255)]},
        {"kind": "bush", "density": 0.45},
    ],
    "dirt": (134, 96, 67),
    "top": (92, 178, 54),                               # grass / snow / sand on top of the ground
    "top_light": (140, 215, 80),
    "stone": (128, 131, 140),                           # the layer under the dirt
    "gap": (58, 61, 70),                                # dark gaps between stones
    "pebble": (122, 124, 132),
    "outline": (45, 38, 34),
    "water": ((70, 150, 235), (20, 60, 160)),           # shallow colour, deep colour
    "water_line": (190, 225, 255),
    "enemy": (150, 60, 180),
    "flyer": (232, 172, 62),
    "hopper": (222, 92, 92),
    "ambient": "leaves",                                # falling "leaves", "snow" or blowing "sand"
}

NIGHT = {
    **FOREST,
    "sky": ((8, 10, 38), (52, 62, 115)),
    "layers": [
        {"type": "stars", "count": 130},
        {"type": "moon", "colour": (240, 240, 215), "x": 0.74, "y": 100, "radius": 40, "speed": 0.015},
        {"type": "clouds", "colour": (80, 92, 150)},
        {"type": "mountains", "colour": (34, 42, 90), "base": 350, "amp": 120, "step": 170, "speed": 0.08},
        {"type": "ruins", "colour": (24, 30, 66), "base": 455, "tile": 2000, "speed": 0.22},
        {"type": "hills", "colour": (22, 52, 66), "base": 470, "amp": 34, "tile": 1400, "speed": 0.40},
        {"type": "fog", "colour": (120, 140, 200), "alpha": 12, "y": 380},
        {"type": "fireflies", "colour": (190, 255, 140), "count": 26},
    ],
    "props": [
        {"kind": "grass", "density": 4.0},
        {"kind": "mushroom", "density": 0.9, "glow": True,
         "colours": [(120, 220, 255), (190, 130, 255), (255, 140, 200)]},
    ],
    "dirt": (86, 64, 54),
    "top": (46, 112, 72),
    "top_light": (84, 164, 104),
    "stone": (88, 92, 112),
    "gap": (34, 36, 52),
    "pebble": (84, 86, 102),
    "outline": (18, 16, 26),
    "water": ((40, 92, 172), (10, 28, 100)),
    "water_line": (140, 182, 240),
    "enemy": (90, 170, 112),
    "flyer": (232, 232, 130),
    "hopper": (236, 122, 122),
    "ambient": None,
}

DESERT = {
    **FOREST,
    "sky": ((255, 188, 120), (255, 236, 192)),
    "layers": [
        {"type": "sun", "colour": (255, 226, 150), "x": 0.7, "y": 120, "radius": 58, "speed": 0.02},
        {"type": "clouds", "colour": (255, 246, 232), "count": 6},
        {"type": "birds", "colour": (95, 60, 40), "count": 4},
        {"type": "hills", "colour": (240, 196, 150), "base": 380, "amp": 50, "tile": 1900, "speed": 0.10},
        {"type": "pyramids", "colour": (224, 170, 118), "ground": (228, 180, 128), "base": 425,
         "tile": 1800, "speed": 0.16},
        {"type": "hills", "colour": (224, 172, 118), "base": 455, "amp": 45, "tile": 1500, "speed": 0.30},
        {"type": "hills", "colour": (206, 148, 94), "base": 495, "amp": 30, "tile": 1300, "speed": 0.45},
    ],
    "props": [
        {"kind": "cactus", "density": 0.55},
        {"kind": "rock", "density": 1.4},
        {"kind": "grass", "density": 1.2},
    ],
    "dirt": (214, 180, 120),
    "top": (238, 212, 148),
    "top_light": (252, 234, 182),
    "stone": (186, 148, 108),
    "gap": (118, 86, 60),
    "pebble": (168, 134, 100),
    "outline": (88, 60, 36),
    "water": ((72, 192, 202), (20, 112, 142)),
    "water_line": (204, 246, 246),
    "enemy": (206, 92, 52),
    "flyer": (126, 92, 200),
    "hopper": (84, 152, 92),
    "ambient": "sand",
}

SNOW = {
    **FOREST,
    "sky": ((72, 100, 164), (220, 232, 250)),
    "layers": [
        {"type": "aurora", "colours": [(90, 240, 170), (140, 150, 255)]},
        {"type": "clouds", "colour": (255, 255, 255), "count": 8},
        {"type": "mountains", "colour": (150, 172, 210), "snow": (244, 248, 255),
         "base": 350, "amp": 150, "step": 190, "speed": 0.08},
        {"type": "mountains", "colour": (120, 146, 190), "snow": (236, 243, 255),
         "base": 420, "amp": 110, "step": 150, "speed": 0.16},
        {"type": "trees", "colour": (60, 98, 96), "kind": "pine", "snow": (236, 244, 252),
         "base": 470, "tile": 1500, "speed": 0.32},
        {"type": "hills", "colour": (214, 226, 244), "base": 495, "amp": 26, "tile": 1300, "speed": 0.45},
        {"type": "fog", "colour": (235, 244, 255), "alpha": 10, "y": 400},
    ],
    "props": [
        {"kind": "drift", "density": 1.4},
        {"kind": "rock", "density": 0.7},
        {"kind": "icicle", "density": 1.6, "anchor": "bottom"},
    ],
    "dirt": (112, 86, 72),
    "top": (236, 242, 252),
    "top_light": (255, 255, 255),
    "stone": (118, 130, 152),
    "gap": (58, 66, 84),
    "pebble": (130, 138, 156),
    "outline": (38, 44, 60),
    "water": ((152, 212, 246), (60, 122, 192)),
    "water_line": (236, 250, 255),
    "enemy": (110, 170, 224),
    "flyer": (240, 150, 176),
    "hopper": (242, 134, 64),
    "ambient": "snow",
}

THEMES = {
    "forest": FOREST,
    "night": NIGHT,
    "desert": DESERT,
    "snow": SNOW,
}
THEME_NAMES = list(THEMES)
DEFAULT_THEME = "forest"


def get_theme(name):
    """Look a theme up by name, falling back to forest for unknown names."""
    return THEMES.get(name, THEMES[DEFAULT_THEME])