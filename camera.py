
class Camera:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset_x = 0
        self.offset_y = 0
    def update(self, player, world_width, world_height):
        self.offset_x = player.rect.centerx - self.screen_width // 2
        self.offset_y = player.rect.centery - self.screen_height // 2
        max_x = max(0, world_width - self.screen_width)
        max_y = max(0, world_height - self.screen_height)

        self.offset_x = max(0, min(self.offset_x, max_x))
        self.offset_y = max(0, min(self.offset_y, max_y))

    def apply(self, rect):
        return rect.move(-self.offset_x, -self.offset_y)