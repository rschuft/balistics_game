import pygame
import math

class Player:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.pos = [0.0, 0.0]
        self.vel = [0.0, 0.0]
        self.angle = 0
        self.thrust = 0.3
        self.friction = 0.98
        self.lasers = []

    def update(self, keys):
        self._apply_thrust(keys)
        self._apply_friction()
        self._update_position()
        self._update_lasers()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self._fire_laser()

    def draw(self, screen):
        self._draw_ship(screen)
        self._draw_lasers(screen)

    # --- Internal methods ---

    def _apply_thrust(self, keys):
        thrust_x, thrust_y = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            thrust_y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            thrust_y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            thrust_x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            thrust_x += 1
        if thrust_x != 0 or thrust_y != 0:
            mag = math.hypot(thrust_x, thrust_y)
            thrust_x /= mag
            thrust_y /= mag
            self.vel[0] += thrust_x * self.thrust
            self.vel[1] += thrust_y * self.thrust

    def _apply_friction(self):
        self.vel[0] *= self.friction
        self.vel[1] *= self.friction

    def _update_position(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

    def _update_lasers(self):
        for laser in self.lasers:
            laser['pos'][0] += laser['vel'][0]
            laser['pos'][1] += laser['vel'][1]
        self.lasers = [
            l for l in self.lasers
            if 0 <= l['pos'][0] <= self.screen_width and 0 <= l['pos'][1] <= self.screen_height
        ]

    def _fire_laser(self):
        laser_speed = 10
        laser = {
            'pos': [self.screen_width // 2, self.screen_height // 2],
            'vel': [0, -laser_speed]
        }
        self.lasers.append(laser)

    def _draw_ship(self, screen):
        cx, cy = self.screen_width // 2, self.screen_height // 2
        points = [
            (cx, cy - 20),
            (cx - 12, cy + 12),
            (cx + 12, cy + 12)
        ]
        pygame.draw.polygon(screen, (0, 200, 255), points)

    def _draw_lasers(self, screen):
        for laser in self.lasers:
            pygame.draw.line(
                screen, (255, 0, 0),
                (laser['pos'][0], laser['pos'][1]),
                (laser['pos'][0], laser['pos'][1] - 10), 3
            )
