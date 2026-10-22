import pygame
from button import Button


class LevelCompleteScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        cx = width // 2
        self.next_button = Button("Next Level", (cx, 420))
        self.again_button = Button("Retry", (cx, 485))
        self.menu_button = Button("Main Menu", (cx, 550))
        self.title_font = pygame.font.Font(None, 84)
        self.font = pygame.font.Font(None, 38)
        self.results = {}
        self.has_next = True

    @staticmethod
    def _fmt(seconds):
        return f"{int(seconds // 60)}:{seconds % 60:04.1f}"

    def set_results(self, results, has_next=True):
        self.results = results
        self.has_next = has_next

    def handle(self, events):
        """Returns "next", "again", "menu" or None."""
        for event in events:
            if self.has_next and self.next_button.clicked(event):
                return "next"
            if self.again_button.clicked(event):
                return "again"
            if self.menu_button.clicked(event):
                return "menu"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return "next" if self.has_next else "again"
        return None

    def draw(self, screen):
        screen.fill((30, 60, 50))
        heading = "Level Complete!" if self.has_next else "You finished every level!"
        title = self.title_font.render(heading, True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(self.width // 2, 110)))

        r = self.results
        time_line = f"Time: {self._fmt(r.get('time', 0.0))}"
        if r.get("par_time"):
            time_line += f"   (par {self._fmt(r['par_time'])})"
        lines = [
            time_line,
            f"Deaths: {r.get('deaths', 0)}",
            f"Damage taken: {r.get('damage_taken', 0)}",
            f"Enemies defeated: {r.get('total_defeats', 0)}",
            f"Objectives: {r.get('objectives_done', 0)} / {r.get('objectives_total', 0)}",
        ]
        y = 190
        for line in lines:
            text = self.font.render(line, True, (220, 255, 230))
            screen.blit(text, text.get_rect(center=(self.width // 2, y)))
            y += 42

        if self.has_next:
            self.next_button.draw(screen)
        self.again_button.draw(screen)
        self.menu_button.draw(screen)