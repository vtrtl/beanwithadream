import pygame
from button import Button


class MainMenu:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        cx = width // 2
        self.play_button = Button("Play", (cx, 330))
        self.quit_button = Button("Quit", (cx, 410))
        self.title_font = pygame.font.Font(None, 110)
        self.sub_font = pygame.font.Font(None, 34)

    def handle(self, events):
        """Returns "play", "quit" or None."""
        for event in events:
            if self.play_button.clicked(event):
                return "play"
            if self.quit_button.clicked(event):
                return "quit"
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return "play"
        return None

    def _text(self, screen, font, text, colour, center):
        shadow = font.render(text, True, (25, 30, 70))
        label = font.render(text, True, colour)
        rect = label.get_rect(center=center)
        screen.blit(shadow, rect.move(3, 3))
        screen.blit(label, rect)

    def draw(self, screen, background=None, t=0.0):
        if background is not None:
            background.draw(screen, t * 60, 0, t)  # the scenery slowly drifts by
        else:
            screen.fill((30, 35, 70))
        self._text(screen, self.title_font, "Bean With A Dream", (255, 255, 255), (self.width // 2, 170))
        self._text(screen, self.sub_font, "A platformer that adapts to you", (255, 255, 255), (self.width // 2, 240))
        self.play_button.draw(screen)
        self.quit_button.draw(screen)
        self._text(screen, self.sub_font, "Enter to play  |  A / D move  |  Space jump",
                   (255, 255, 255), (self.width // 2, self.height - 40))