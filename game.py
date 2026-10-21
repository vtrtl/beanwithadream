import pygame
import time
from player import Player
from level import Level
from camera import Camera


class Game:
    DEBUG = False  # set True to print player state every frame

    def __init__(self):
        pygame.init()
        self.width = 1200
        self.height = 600
        self.fps = 60
        self.death_count = 0
        self.frame_count = 0
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.SCALED)
        pygame.display.set_caption("Bean With A Dream")
        self.clock = pygame.time.Clock()
        self.background_color = (196, 207, 255)
        self.hud_font = pygame.font.Font(None, 32)
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
        text = self.hud_font.render(f"Deaths: {self.death_count}", True, (255, 255, 255))
        self.screen.blit(text, (20, 20))

        p = self.player

        # health bar
        bar_w, bar_h = 200, 16
        pygame.draw.rect(self.screen, (60, 20, 20), (20, 55, bar_w, bar_h))
        fill = int(bar_w * p.health / p.max_health)
        pygame.draw.rect(self.screen, (220, 60, 60), (20, 55, fill, bar_h))
        pygame.draw.rect(self.screen, (255, 255, 255), (20, 55, bar_w, bar_h), 2)

        # breath bar: only shown once the player has started running out of air
        if p.breath < p.max_breath:
            bar_w, bar_h = 200, 14
            x, y = 20, 80
            pygame.draw.rect(self.screen, (30, 30, 50), (x, y, bar_w, bar_h))
            fill = int(bar_w * p.breath / p.max_breath)
            colour = (90, 200, 255) if p.breath > 1.5 else (255, 120, 80)
            pygame.draw.rect(self.screen, colour, (x, y, fill, bar_h))
            pygame.draw.rect(self.screen, (255, 255, 255), (x, y, bar_w, bar_h), 2)

    def run(self):
        self.loading_screen()
        print("Loading game...")
        self.load_game()
        print("Game loaded. Starting main loop.")

        # discard the long delay caused by the loading screen's sleep
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

            dead = False
            reason = None

            if self.player.respawn_lock <= 0:
                # water / breath first, so move() knows if we're swimming
                if self.player.update_water(self.level.water, dt):
                    dead = True
                    reason = "drowned"

            self.player.move(self.level.platforms, dt, self.level.data["world_width"])

            if self.DEBUG:
                p = self.player
                print(
                    f"x={p.rect.x} y={p.rect.y} vy={p.velocity_y:.0f} "
                    f"breath={p.breath:.1f} water={p.in_water} deaths={self.death_count}"
                )

            if not dead and self.player.respawn_lock <= 0:
                if self.player.rect.top > self.level.data["world_height"]:
                    dead = True
                    reason = "fell into the abyss"
                else:
                    for hazard in self.level.hazards:
                        if self.player.rect.colliderect(hazard):
                            dead = True
                            reason = f"touched lava {hazard}"
                            break

            # enemies: patrol, then contact (stomp from above, otherwise take damage)
            for enemy in list(self.level.enemies):
                enemy.update(dt)
                if dead or self.player.respawn_lock > 0:
                    continue
                if not self.player.rect.colliderect(enemy.rect):
                    continue
                stomping = (
                    self.player.velocity_y > 0
                    and self.player.rect.bottom - enemy.rect.top <= 30
                )
                if stomping:
                    if enemy.take_damage(1):
                        self.level.enemies.remove(enemy)
                    self.player.bounce()
                elif self.player.take_damage(enemy.damage):
                    if self.player.health <= 0:
                        dead = True
                        reason = "killed by an enemy"

            if dead:
                if self.DEBUG:
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
            for enemy in self.level.enemies:
                enemy.draw(self.screen, self.camera)
            self.player.draw(self.screen, self.camera)
            self.level.draw_water(self.screen, self.camera)
            self.draw_hud()
            pygame.display.flip()
            self.frame_count += 1
            if self.frame_count % 30 == 0:
                pygame.display.set_caption(
                    f"Bean With A Dream - {self.clock.get_fps():.0f} fps"
                )
        pygame.quit()