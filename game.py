import pygame
import time
from player import Player
from level import Level
from camera import Camera


class Game:
    DEBUG = False

    def __init__(self):
        pygame.init()
        self.width = 1200
        self.height = 600
        self.fps = 120
        self.death_count = 0
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.SCALED)
        pygame.display.set_caption("Bean With A Dream")
        self.clock = pygame.time.Clock()
        self.background_color = (196, 207, 255)
        self.level = None
        self.player = None
        self.camera = Camera(self.width, self.height)

    def loading_screen(self):
        self.screen.fill((20, 20, 30))
        font = pygame.font.Font(None, 60)
        text = font.render("Loading...", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.event.pump()
        time.sleep(1)

    def load_game(self):
        self.level = Level("levels/level1.json")
        start_x, start_y = self.level.data["player_start"]
        self.player = Player(start_x, start_y)

    def draw_hud(self):
        font = pygame.font.Font(None, 32)
        text = font.render(f"Deaths: {self.death_count}", True, (255, 255, 255))
        self.screen.blit(text, (20, 20))

    def run(self):
        self.loading_screen()
        print("Loading game...")
        self.load_game()
        print("Game loaded. Starting main loop.")
        self.clock.tick()

        running = True
        while running:
            dt = self.clock.tick(self.fps) / 1000
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            if not running:
                break

            self.player.move(self.level.platforms, dt)

            if self.DEBUG:
                p = self.player
                print(
                    f"x={p.rect.x} y={p.rect.y} vy={p.velocity_y:.0f} "
                    f"lock={p.respawn_lock:.2f} ground={p.on_ground} "
                    f"deaths={self.death_count}"
                )
            dead = False
            reason = None
            if self.player.respawn_lock <= 0:
                if self.player.rect.top > self.level.data["world_height"]:
                    dead = True
                    reason = "fell into the abyss"
                else:
                    for hazard in self.level.hazards:
                        if self.player.rect.colliderect(hazard):
                            dead = True
                            reason = f"touched lava {hazard}"
                            break


            if dead:
                print(f"DIED: {reason} at x={self.player.rect.x} y={self.player.rect.y}")
                self.death_count += 1
                start_x, start_y = self.level.data["player_start"]
                self.player.respawn(start_x, start_y)

            self.camera.update(
                self.player,
                self.level.data["world_width"],
                self.level.data["world_height"],
            )

            self.screen.fill(self.background_color)
            self.level.draw(self.screen, self.camera)
            self.player.draw(self.screen, self.camera)
            self.draw_hud()
            pygame.display.flip()

        pygame.quit()