import pygame

SURFACES = {
    "ground": {"colour": (102, 196, 48), "solid": True,  "deadly": False, "water": False},
    "lava":   {"colour": (220, 50, 50),  "solid": False, "deadly": True,  "water": False},
    "water":  {"colour": (60, 120, 220), "solid": False, "deadly": False, "water": True},
}

class Tile:
    def __init__(self, rect, kind="ground"):
        if kind not in SURFACES:
            raise ValueError(f"Unknown surface type: {kind!r}")
        props = SURFACES[kind]
        self.rect = pygame.Rect(rect)
        self.kind = kind
        self.colour = props["colour"]
        self.solid = props["solid"]
        self.deadly = props["deadly"]
        self.water = props["water"]