import pygame
import math
import random
import pygame.gfxdraw

class Saucer:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Spawn just outside the visible area, aimed inward
        self._spawn_near_screen(center=(screen_width//2, screen_height//2))
        self.radius = 32
        self.charge = 0
        self.charge_max = 90  # frames to charge
        self.laser_cooldown = 0
        self.laser = None
        self.target_pos = None
        self.exploding = False
        self.explosion_timer = 0
        self.explosion_duration = 40
        self.explosion_sound = None
        try:
            self.explosion_sound = pygame.mixer.Sound("assets/explosion.wav")
        except Exception:
            self.explosion_sound = None

    def _spawn_near_screen(self, center):
        # Pick a random side and spawn just outside the visible area, aimed inward
        margin = 80
        cx, cy = center
        side = random.choice(['left', 'right', 'top', 'bottom'])
        if side == 'left':
            self.pos = [cx - self.screen_width//2 - margin, cy + random.randint(-self.screen_height//2, self.screen_height//2)]
            self.vel = [random.uniform(2, 3), random.uniform(-1, 1)]
        elif side == 'right':
            self.pos = [cx + self.screen_width//2 + margin, cy + random.randint(-self.screen_height//2, self.screen_height//2)]
            self.vel = [-random.uniform(2, 3), random.uniform(-1, 1)]
        elif side == 'top':
            self.pos = [cx + random.randint(-self.screen_width//2, self.screen_width//2), cy - self.screen_height//2 - margin]
            self.vel = [random.uniform(-1, 1), random.uniform(2, 3)]
        else:  # bottom
            self.pos = [cx + random.randint(-self.screen_width//2, self.screen_width//2), cy + self.screen_height//2 + margin]
            self.vel = [random.uniform(-1, 1), -random.uniform(2, 3)]

    def update(self, player_pos):
        if self.exploding:
            self.explosion_timer -= 1
            if self.explosion_timer <= 0:
                self.exploding = False
                # Respawn saucer just outside the visible area, aimed inward
                self._spawn_near_screen(center=player_pos)
                self.charge = 0
                self.laser_cooldown = 0
                self.laser = None
                self.target_pos = None
            return

        # Move saucer in world space
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

        # Keep saucer within visible range or fly back in
        visible_margin = 600
        cam_x, cam_y = player_pos
        min_x = cam_x - self.screen_width // 2 - visible_margin
        max_x = cam_x + self.screen_width // 2 + visible_margin
        min_y = cam_y - self.screen_height // 2 - visible_margin
        max_y = cam_y + self.screen_height // 2 + visible_margin

        if self.pos[0] < min_x:
            self.vel[0] = abs(self.vel[0])
        elif self.pos[0] > max_x:
            self.vel[0] = -abs(self.vel[0])
        if self.pos[1] < min_y:
            self.vel[1] = abs(self.vel[1])
        elif self.pos[1] > max_y:
            self.vel[1] = -abs(self.vel[1])

        # Keep distance from player
        dx = player_pos[0] - self.pos[0]
        dy = player_pos[1] - self.pos[1]
        dist = math.hypot(dx, dy)
        preferred_min = 350
        preferred_max = 700
        if dist < preferred_min:
            # Move away from player
            angle = math.atan2(-dx, -dy)
            speed = 3.5
            self.vel[0] = math.sin(angle) * speed
            self.vel[1] = -math.cos(angle) * speed
        elif dist > preferred_max:
            # Move toward player
            angle = math.atan2(dx, dy)
            speed = 2.5
            self.vel[0] = math.sin(angle) * speed
            self.vel[1] = math.cos(angle) * speed

        # Aim at player
        dx = player_pos[0] - self.pos[0]
        dy = player_pos[1] - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist < 800:
            # Build up charge to fire
            if self.laser is None and self.laser_cooldown == 0:
                self.charge += 1
                self.target_pos = (player_pos[0], player_pos[1])
                if self.charge >= self.charge_max:
                    self._fire_laser()
                    self.charge = 0
                    self.laser_cooldown = 60  # cooldown before next charge
            elif self.laser_cooldown > 0:
                self.laser_cooldown -= 1
        else:
            self.charge = 0
            self.laser_cooldown = 0
            self.laser = None
        # Update laser
        if self.laser:
            self.laser['life'] -= 1
            if self.laser['life'] <= 0:
                self.laser = None

    def hit(self):
        if not self.exploding:
            self.exploding = True
            self.explosion_timer = self.explosion_duration
            if self.explosion_sound:
                self.explosion_sound.play()
            self.laser = None
            self.charge = 0

    def _fire_laser(self):
        # Fire a laser at the last known player position
        if not self.target_pos:
            return
        dx = self.target_pos[0] - self.pos[0]
        dy = self.target_pos[1] - self.pos[1]
        angle = math.atan2(dx, -dy)
        self.laser = {
            'angle': angle,
            'life': 30,
        }

    def draw(self, screen, player_pos):
        if self.exploding:
            # Draw explosion effect
            sx = self.pos[0] - player_pos[0] + screen.get_width() // 2
            sy = self.pos[1] - player_pos[1] + screen.get_height() // 2
            t = self.explosion_timer / self.explosion_duration
            radius = int(self.radius * (2.5 - t))
            color = (255, int(200 * t), 0)
            pygame.draw.circle(screen, color, (int(sx), int(sy)), radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(sx), int(sy)), int(radius * 0.6))
            return

        # Draw saucer relative to player (camera)
        sx = self.pos[0] - player_pos[0] + screen.get_width() // 2
        sy = self.pos[1] - player_pos[1] + screen.get_height() // 2
        # Saucer body
        pygame.draw.ellipse(screen, (180, 220, 255), (sx - 32, sy - 16, 64, 32))
        pygame.draw.ellipse(screen, (80, 120, 180), (sx - 32, sy - 16, 64, 32), 2)
        pygame.draw.ellipse(screen, (200, 255, 255), (sx - 18, sy - 12, 36, 18))
        # Dome
        pygame.draw.ellipse(screen, (255, 255, 255), (sx - 12, sy - 18, 24, 18))
        pygame.draw.ellipse(screen, (120, 200, 255), (sx - 12, sy - 18, 24, 18), 2)
        # Charge indicator
        if self.charge > 0:
            charge_frac = min(1.0, self.charge / self.charge_max)
            pygame.draw.arc(screen, (255, 255, 0), (sx - 36, sy - 20, 72, 40), math.pi, math.pi + math.pi * charge_frac, 4)
        # Laser
        if self.laser:
            angle = self.laser['angle']
            lx = sx + math.sin(angle) * 32
            ly = sy - math.cos(angle) * 32
            end_x = sx + math.sin(angle) * 900
            end_y = sy - math.cos(angle) * 900
            pygame.draw.line(screen, (255, 0, 255), (lx, ly), (end_x, end_y), 4)
            # Glow
            for i in range(6):
                alpha = 80 - i * 12
                color = (255, 0, 255, alpha)
                # Use pygame.gfxdraw.line for glow effect
                pygame.gfxdraw.line(screen, int(lx), int(ly), int(end_x), int(end_y), color)

    def collides_with_point(self, point):
        """Check if a point (x, y) collides with the saucer's body."""
        if self.exploding:
            return False
        dx = point[0] - self.pos[0]
        dy = point[1] - self.pos[1]
        return dx * dx + dy * dy <= self.radius * self.radius

    def collides_with_line(self, line_start, line_end):
        """
        Check if a line segment (laser beam) intersects the saucer's circle.
        line_start, line_end: (x, y) world coordinates of the laser beam.
        """
        if self.exploding:
            return False
        # Vector from start to end
        x1, y1 = line_start
        x2, y2 = line_end
        cx, cy = self.pos
        # Compute the closest point on the line segment to the saucer center
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            # Line is a point
            closest_x, closest_y = x1, y1
        else:
            t = ((cx - x1) * dx + (cy - y1) * dy) / (dx * dx + dy * dy)
            t = max(0, min(1, t))
            closest_x = x1 + t * dx
            closest_y = y1 + t * dy
        # Distance from closest point to saucer center
        dist_sq = (closest_x - cx) ** 2 + (closest_y - cy) ** 2
        return dist_sq <= self.radius * self.radius
