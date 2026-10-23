"""Visual themes. A level picks one with  "theme": "night"  in its JSON.

To make a new theme, copy one of these, change the colours, and add it to THEMES.
Anything you leave out falls back to the forest theme.
"""

FOREST = {
    "sky": ((110, 165, 255), (225, 240, 255)),          # top colour, bottom colour
    "hills": [(150, 190, 235), (120, 175, 150), (95, 160, 105)],   # far to near
    "cloud": (255, 255, 255),
    "dirt": (134, 96, 67),
    "top": (92, 178, 54),                               # grass / snow / sand on top
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
    "stars": False,                                     # stars and a moon behind the hills
    "ambient": None,                                    # "snow" for falling snow
}

NIGHT = {
    **FOREST,
    "sky": ((8, 10, 38), (52, 62, 115)),
    "hills": [(32, 40, 84), (26, 52, 74), (20, 46, 58)],
    "cloud": (95, 105, 160),
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
    "stars": True,
}

DESERT = {
    **FOREST,
    "sky": ((255, 188, 120), (255, 236, 192)),
    "hills": [(238, 190, 146), (222, 164, 114), (202, 142, 92)],
    "cloud": (255, 246, 232),
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
}

SNOW = {
    **FOREST,
    "sky": ((148, 174, 216), (226, 236, 250)),
    "hills": [(204, 218, 238), (174, 198, 228), (144, 172, 208)],
    "cloud": (255, 255, 255),
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