import pygame


class Button:
    def __init__(self, text, center, size=(260, 56)):
        self.text = text
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center
        self.font = pygame.font.Font(None, 38)

    def draw(self, screen):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        colour = (95, 115, 210) if hover else (60, 75, 150)
        pygame.draw.rect(screen, colour, self.rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=10)
        label = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )