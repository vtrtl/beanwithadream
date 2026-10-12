import pygame
import time
from player import Player
from level import Level
from camera import Camera
class Game:

    def __init__(self):
        self.width = 1200
        self.height = 600
        self.fps = 120
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Bean With A Dream")
        self.clock = pygame.time.Clock()
        self.background_color = (173, 216, 230)
        self.level = None
        self.player = None
        self.camera = Camera(self.width, self.height)
    def loading_screen(self):
        self.screen.fill((20, 20, 30))
        font = pygame.font.Font(None, 60)
        text = font.render("Loading...", True,(255, 255, 255))
        text_rect = text.get_rect(
            center=(self.width // 2, self.height // 2))
        self.screen.blit(text, text_rect)
        pygame.display.flip()
        time.sleep(1)
    def load_game(self):
        self.level = Level("levels/level1.json")
        start_x, start_y = self.level.data["player_start"]
        self.player = Player(start_x, start_y)
    def run(self):
        self.loading_screen()
        self.load_game()
        running = True
        while running:
            dt = self.clock.tick(self.fps) / 1000
            dt = min(dt, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.player.move(self.level.platforms, dt)
            self.screen.fill(self.background_color)
            self.level.draw(self.screen, self.camera)
            self.player.draw(self.screen, self.camera)
            pygame.display.flip()
            self.camera.update(self.player, self.level.data["world_width"],self.level.data["world_height"])
        pygame.quit()