import pygame
import time
from player import Player
from level import Level
from camera import Camera
from objective import ObjectiveTracker
from performance import LevelPerformance, PerformanceHistory
from menu import MainMenu
from level_complete import LevelCompleteScreen
from visuals import Background, ParticleSystem, make_ambient
from themes import THEME_NAMES


class Game:
    DEBUG = False
    LEVELS = ["levels/level1.json", "levels/level2.json", "levels/level3.json"]
    THEME_PREVIEW = True  # press T while playing to cycle through the themes

    def __init__(self):
        pygame.init()
        self.width = 1200
        self.height = 600
        self.fps = 60
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.SCALED)
        pygame.display.set_caption("Bean With A Dream")
        self.clock = pygame.time.Clock()
        self.hud_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 26)

        self.menu_background = Background(self.width, self.height)  # menu always uses forest
        self.background = self.menu_background
        self.ambient = None
        self.particles = ParticleSystem()
        self.anim_time = 0.0  # drives all the animations

        # translucent panel behind the top-left HUD
        self.hud_panel = pygame.Surface((250, 100), pygame.SRCALPHA)
        pygame.draw.rect(self.hud_panel, (20, 20, 40, 120), self.hud_panel.get_rect(), border_radius=12)

        # states: "menu", "playing", "level_complete"
        self.state = "menu"
        self.running = True
        self.menu = MainMenu(self.width, self.height)
        self.complete_screen = LevelCompleteScreen(self.width, self.height)

        # per-level data (filled in by start_level)
        self.level = None
        self.player = None
        self.objectives = None
        self.camera = Camera(self.width, self.height)
        self.perf = LevelPerformance("")           # replaced by start_level
        self.history = PerformanceHistory()        # last few finished levels, saved to disk
        self.level_index = 0
        self.checkpoint = None                     # (x_centre, y_feet) of the last flag reached
        self.hint_text = ""
        self.hint_timer = 0.0

    # ------------------------------------------------------------ setup
    def loading_screen(self):
        self.screen.fill((20, 20, 30))
        font = pygame.font.Font(None, 60)
        text = font.render("Loading...", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=(self.width // 2, self.height // 2)))
        pygame.display.flip()
        pygame.event.pump()
        time.sleep(1)

    def start_level(self, index=None):
        if index is not None:
            self.level_index = index
        self.level = Level(self.LEVELS[self.level_index])
        self.apply_theme()
        start_x, start_y = self.level.data["player_start"]
        self.player = Player(start_x, start_y)
        self.camera = Camera(self.width, self.height)
        self.objectives = ObjectiveTracker(self.level.data.get("objectives", []))
        self.particles = ParticleSystem()
        self.perf = LevelPerformance(
            self.level.data.get("name", self.LEVELS[self.level_index]),
            self.level.data.get("par_time"),
        )
        self.checkpoint = None
        self.hint_text = self.level.data.get("name", "")  # level title banner
        self.hint_timer = 3.0
        self.state = "playing"

    def apply_theme(self):
        """Build the background and ambient effects for the level's current theme."""
        theme = self.level.theme
        self.background = Background(self.width, self.height, theme)
        self.ambient = make_ambient(theme, self.width, self.height)

    def finish_level(self):
        self.perf.finish(self.objectives.completed_count, self.objectives.total)
        self.history.add(self.perf)
        if self.DEBUG:
            print("Level complete:", self.perf.to_dict())
        has_next = self.level_index + 1 < len(self.LEVELS)
        self.complete_screen.set_results(self.perf.to_dict(), has_next)
        self.state = "level_complete"

    # ------------------------------------------------------------ main loop
    def run(self):
        self.loading_screen()
        self.clock.tick()  # discard the loading screen's long delay

        while self.running:
            dt = min(self.clock.tick(self.fps) / 1000, 0.05)
            self.anim_time += dt
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
            if not self.running:
                break

            if self.state == "menu":
                self.run_menu(events)
            elif self.state == "playing":
                self.run_playing(events, dt)
            elif self.state == "level_complete":
                self.run_level_complete(events)

            pygame.display.flip()

        pygame.quit()

    # ------------------------------------------------------------ menu
    def run_menu(self, events):
        action = self.menu.handle(events)
        if action == "play":
            self.start_level(0)
            return
        if action == "quit":
            self.running = False
            return
        self.menu.draw(self.screen, self.menu_background, self.anim_time)

    # ------------------------------------------------------------ level complete
    def run_level_complete(self, events):
        action = self.complete_screen.handle(events)
        if action == "next":
            self.start_level(self.level_index + 1)
            return
        if action == "again":
            self.start_level()
            return
        if action == "menu":
            self.state = "menu"
            return
        self.complete_screen.draw(self.screen)

    # ------------------------------------------------------------ playing
    def run_playing(self, events, dt):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = "menu"
                return
            if self.THEME_PREVIEW and event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                index = THEME_NAMES.index(self.level.theme_name)
                name = THEME_NAMES[(index + 1) % len(THEME_NAMES)]
                self.level.set_theme(name)
                self.apply_theme()
                self.hint_text = f"Theme: {name}"
                self.hint_timer = 1.5

        self.update_playing(dt)
        if self.state == "playing":
            self.draw_playing()

    def water_surface_y(self):
        """Top of the water the player is touching (for splashes)."""
        for w in self.level.water:
            if self.player.rect.colliderect(w):
                return w.top
        return self.player.rect.centery

    def update_playing(self, dt):
        self.perf.tick(dt)
        if self.hint_timer > 0:
            self.hint_timer -= dt
        self.particles.update(dt)
        if self.ambient:
            self.ambient.update(dt)

        p = self.player
        dead = False
        reason = None

        if p.respawn_lock <= 0:
            was_in_water = p.in_water
            # water / breath first, so move() knows if we're swimming
            if p.update_water(self.level.water, dt):
                dead = True
                reason = "drowned"
            if p.in_water != was_in_water and abs(p.velocity_y) > 100:
                self.particles.emit(
                    p.rect.centerx, self.water_surface_y(),
                    [(190, 225, 255), (120, 180, 245), (255, 255, 255)],
                    count=14, speed=170, up=160, gravity=700,
                )

        was_on_ground = p.on_ground
        prev_vy = p.velocity_y
        p.move(self.level.platforms, dt, self.level.data["world_width"])

        # landing dust
        if p.on_ground and not was_on_ground and prev_vy > 300:
            self.particles.emit(
                p.rect.centerx, p.rect.bottom,
                [(214, 190, 150), (180, 150, 110), (240, 225, 195)],
                count=8, speed=110, up=30, gravity=300, size=(3, 6),
            )

        if self.DEBUG:
            print(
                f"x={p.rect.x} y={p.rect.y} vy={p.velocity_y:.0f} "
                f"breath={p.breath:.1f} water={p.in_water} deaths={self.perf.deaths}"
            )

        if not dead and p.respawn_lock <= 0:
            if p.rect.top > self.level.data["world_height"]:
                dead = True
                reason = "abyss"
            else:
                for hazard in self.level.hazards:
                    if p.rect.colliderect(hazard):
                        dead = True
                        reason = "lava"
                        break

        # enemies: patrol, then contact (stomp from above, otherwise take damage)
        for enemy in list(self.level.enemies):
            enemy.update(dt)
            if dead or p.respawn_lock > 0:
                continue
            if not p.rect.colliderect(enemy.rect):
                continue
            stomping = p.velocity_y > 0 and p.rect.bottom - enemy.rect.top <= 30
            if stomping:
                if enemy.take_damage(1):
                    self.level.enemies.remove(enemy)
                    self.objectives.on_event("enemy_defeated")
                    self.perf.record_defeat("stomp")
                    self.particles.emit(
                        enemy.rect.centerx, enemy.rect.centery,
                        [(150, 60, 180), (190, 110, 215), (255, 255, 255)],
                        count=18, speed=220, up=120, size=(3, 7),
                    )
                p.bounce()
            elif p.take_damage(enemy.damage):
                self.perf.record_damage(enemy.damage)
                self.particles.emit(
                    p.rect.centerx, p.rect.centery,
                    [(255, 90, 90), (255, 200, 200)],
                    count=10, speed=180, up=80,
                )
                if p.health <= 0:
                    dead = True
                    reason = "enemy"

        if dead:
            if self.DEBUG:
                print(f"DIED: {reason} at x={p.rect.x} y={p.rect.y}")
            self.particles.emit(
                p.rect.centerx, p.rect.centery,
                [(255, 255, 255), (255, 120, 80), (255, 210, 90)],
                count=26, speed=260, up=140, size=(3, 7),
            )
            self.perf.record_death(reason)
            if self.checkpoint:
                p.respawn(self.checkpoint[0] - p.width // 2, self.checkpoint[1])
            else:
                start_x, start_y = self.level.data["player_start"]
                p.respawn(start_x, start_y)

        # checkpoints: reaching a flag makes it your new respawn point (forward only)
        for cx, cy in self.level.checkpoints:
            current_x = self.checkpoint[0] if self.checkpoint else -1
            if (not dead and cx > current_x and p.rect.centerx >= cx
                    and abs(p.rect.bottom - cy) < 200):
                self.checkpoint = (cx, cy)
                self.hint_text = "Checkpoint reached"
                self.hint_timer = 1.5
                self.particles.emit(
                    cx, cy - 40, [(120, 255, 150), (255, 255, 255), (255, 240, 150)],
                    count=14, speed=150, up=140,
                )

        # exit door: only opens once the required objectives are done
        if not dead and self.level.exit_rect and p.rect.colliderect(self.level.exit_rect):
            if self.objectives.required_done:
                self.finish_level()
                return
            self.hint_text = "The exit is locked - finish the objectives first"
            self.hint_timer = 2.0

        self.camera.update(
            p,
            self.level.data["world_width"],
            self.level.data["world_height"],
        )

    def draw_playing(self):
        t = self.anim_time
        self.background.draw(self.screen, self.camera.offset_x, self.camera.offset_y, t)
        self.level.draw(self.screen, self.camera, t)
        self.level.draw_exit(self.screen, self.camera, self.objectives.required_done, t)
        self.level.draw_checkpoints(self.screen, self.camera, self.checkpoint, t)
        for enemy in self.level.enemies:
            enemy.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)
        self.particles.draw(self.screen, self.camera)
        self.level.draw_water(self.screen, self.camera, t)
        if self.ambient:
            self.ambient.draw(self.screen)
        self.draw_hud()

    # ------------------------------------------------------------ HUD
    def draw_text(self, font, text, colour, pos):
        shadow = font.render(text, True, (20, 20, 40))
        self.screen.blit(shadow, (pos[0] + 1, pos[1] + 1))
        self.screen.blit(font.render(text, True, colour), pos)

    def draw_bar(self, x, y, w, h, frac, colour, label):
        frac = max(0.0, min(1.0, frac))
        pygame.draw.rect(self.screen, (25, 25, 45), (x, y, w, h), border_radius=h // 2)
        if frac > 0:
            pygame.draw.rect(self.screen, colour, (x, y, max(h, int(w * frac)), h), border_radius=h // 2)
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, w, h), 2, border_radius=h // 2)
        self.draw_text(self.small_font, label, (255, 255, 255), (x + w + 10, y - 3))

    def draw_hud(self):
        p = self.player
        self.screen.blit(self.hud_panel, (10, 10))
        self.draw_text(self.hud_font, f"Deaths: {self.perf.deaths}", (255, 255, 255), (22, 18))
        self.draw_bar(22, 52, 180, 16, p.health / p.max_health, (220, 60, 60), "HP")

        # breath bar: only shown once the player has started running out of air
        if p.breath < p.max_breath:
            colour = (90, 200, 255) if p.breath > 1.5 else (255, 120, 80)
            self.draw_bar(22, 78, 180, 14, p.breath / p.max_breath, colour, "AIR")

        # objectives, top right
        labels = []
        for obj in self.objectives.items:
            mark = "[x]" if obj.complete else "[ ]"
            text = f"{mark} {obj.text}"
            if obj.target > 1:
                text += f" {obj.progress}/{obj.target}"
            if not obj.required:
                text += " (bonus)"
            colour = (120, 255, 140) if obj.complete else (255, 255, 255)
            labels.append(self.small_font.render(text, True, colour))
        if labels:
            w = max(l.get_width() for l in labels) + 24
            h = len(labels) * 26 + 14
            panel = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(panel, (20, 20, 40, 120), panel.get_rect(), border_radius=12)
            self.screen.blit(panel, (self.width - w - 10, 10))
            y = 18
            for label in labels:
                self.screen.blit(label, (self.width - 22 - label.get_width(), y))
                y += 26

        # short message, e.g. when touching a locked exit
        if self.hint_timer > 0:
            width = self.hud_font.size(self.hint_text)[0]
            self.draw_text(self.hud_font, self.hint_text, (255, 230, 120), (self.width // 2 - width // 2, 120))