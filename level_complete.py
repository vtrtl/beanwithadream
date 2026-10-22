import pygame
from button import Button


class LevelCompleteScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        cx = width // 2
        self.again_button = Button("Play Again", (cx, 430))
        self.menu_button = Button("Main Menu", (cx, 500))
        self.title_font = pygame.font.Font(None, 84)
        self.font = pygame.font.Font(None, 38)
        self.results = {}

    def set_results(self, results):
        self.results = results

    def handle(self, events):
        """Returns "again", "menu" or None."""
        for event in events:
            if self.again_button.clicked(event):
                return "again"
            if self.menu_button.clicked(event):
                return "menu"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return "again"
        return None

    def draw(self, screen):
        screen.fill((30, 60, 50))
        title = self.title_font.render("Level Complete!", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(self.width // 2, 110)))

        r = self.results
        seconds = r.get("time", 0.0)
        lines = [
            f"Time: {int(seconds // 60)}:{seconds % 60:04.1f}",
            f"Deaths: {r.get('deaths', 0)}",
            f"Damage taken: {r.get('damage_taken', 0)}",
            f"Objectives: {r.get('objectives_done', 0)} / {r.get('objectives_total', 0)}",
        ]
        y = 200
        for line in lines:
            text = self.font.render(line, True, (220, 255, 230))
            screen.blit(text, text.get_rect(center=(self.width // 2, y)))
            y += 48

        self.again_button.draw(screen)
        self.menu_button.draw(screen)