import pygame
import math
import array

from .sound import SoundManager
from .laser import Laser

class Player:
    def __init__(self, screen_width, screen_height, sound_manager=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.pos = [0.0, 0.0]
        self.vel = [0.0, 0.0]
        self.angle = 0  # 0 is up, in degrees
        self.thrust = 0.3
        self.friction = 0.98
        self.lasers = []
        self.tilt = 0
        self._tilt_target = 0
        self._tilt_speed = 2  # degrees per frame
        self._thruster_geom = []
        self._sound = sound_manager or SoundManager()
        self._init_ship_surface()

    def _init_ship_surface(self):
        # Draw the entire ship as a single surface, facing up (angle 0)
        scale = 2
        surf_size = 80 * scale
        self.ship_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        cx, cy = surf_size // 2, surf_size // 2

        # Body
        body_points = [
            (0, -24), (-8, -10), (-18, 0), (-10, 6), (-6, 18), (0, 14),
            (6, 18), (10, 6), (18, 0), (8, -10)
        ]
        body_points = [(cx + x * scale, cy + y * scale) for (x, y) in body_points]
        pygame.draw.polygon(self.ship_surf, (80, 200, 255), body_points)
        pygame.draw.polygon(self.ship_surf, (40, 80, 180), body_points, 2)

        # Cockpit
        cockpit_rect = pygame.Rect(cx - 7*scale, cy - 8*scale - 12*scale, 14*scale, 14*scale)
        pygame.draw.ellipse(self.ship_surf, (120, 240, 255), cockpit_rect)
        pygame.draw.ellipse(self.ship_surf, (180, 240, 255), cockpit_rect, 2)
        highlight_rect = cockpit_rect.inflate(-6*scale, -8*scale)
        pygame.draw.arc(self.ship_surf, (255, 255, 255), highlight_rect, math.radians(200), math.radians(320), 2)

        # Tiny pilot helmet
        helmet_radius = int(2.2 * scale)
        helmet_center = (cx, cy - 12*scale)
        pygame.draw.circle(self.ship_surf, (220, 220, 230), helmet_center, helmet_radius)
        visor_rect = pygame.Rect(
            helmet_center[0] - helmet_radius, helmet_center[1] - helmet_radius, helmet_radius*2, helmet_radius*2
        )
        pygame.draw.arc(self.ship_surf, (100, 180, 255), visor_rect, math.radians(210), math.radians(330), max(1, scale))

        # Thrusters
        for tx in [-7, 7]:
            thruster_center = (cx + tx*scale, cy + 18*scale)
            thruster_rect = pygame.Rect(0, 0, 7*scale, 14*scale)
            thruster_rect.center = thruster_center
            pygame.draw.ellipse(self.ship_surf, (180, 180, 180), thruster_rect)
            pygame.draw.ellipse(self.ship_surf, (80, 80, 80), thruster_rect, 2)
            for bolt_angle in [0, 120, 240]:
                bolt_rad = math.radians(bolt_angle)
                bolt_x = thruster_center[0] + 3*scale * math.cos(bolt_rad)
                bolt_y = thruster_center[1] + 6*scale * math.sin(bolt_rad)
                pygame.draw.circle(self.ship_surf, (60, 60, 60), (int(bolt_x), int(bolt_y)), scale)
            # Save local thruster center for glow calculation
            self._thruster_geom.append((tx * scale, 18 * scale, 14 * scale))  # (local_x, local_y, length)

        # Laser cannons: fused, skinnier, embedded, and shorter
        barrel_length = 5 * scale  # shorter
        barrel_width = 3 * scale
        base_center = (cx, cy - 18*scale)
        tip_center = (cx, cy - (18 + barrel_length)*scale)
        barrel_vec = (tip_center[0] - base_center[0], tip_center[1] - base_center[1])
        mag = math.hypot(*barrel_vec)
        if mag != 0:
            perp = (-barrel_vec[1]/mag * (barrel_width//2), barrel_vec[0]/mag * (barrel_width//2))
        else:
            perp = (0, 0)
        # Embedded section (first third)
        embed_frac = 0.33
        embed_tip = (
            base_center[0] + barrel_vec[0] * embed_frac,
            base_center[1] + barrel_vec[1] * embed_frac
        )
        embed_poly = [
            (base_center[0] + perp[0], base_center[1] + perp[1]),
            (base_center[0] - perp[0], base_center[1] - perp[1]),
            (embed_tip[0] - perp[0], embed_tip[1] - perp[1]),
            (embed_tip[0] + perp[0], embed_tip[1] + perp[1]),
        ]
        pygame.draw.polygon(self.ship_surf, (60, 100, 140), embed_poly)
        pygame.draw.polygon(self.ship_surf, (100, 140, 180), embed_poly, 1)
        # Exposed section (rest of barrel)
        exposed_poly = [
            (embed_tip[0] + perp[0], embed_tip[1] + perp[1]),
            (embed_tip[0] - perp[0], embed_tip[1] - perp[1]),
            (tip_center[0] - perp[0], tip_center[1] - perp[1]),
            (tip_center[0] + perp[0], tip_center[1] + perp[1]),
        ]
        pygame.draw.polygon(self.ship_surf, (120, 120, 120), exposed_poly)
        pygame.draw.polygon(self.ship_surf, (180, 180, 180), exposed_poly, 1)
        pygame.draw.circle(self.ship_surf, (120, 120, 120), (int(embed_tip[0]), int(embed_tip[1])), int(barrel_width // 2), 1)
        pygame.draw.circle(self.ship_surf, (255, 220, 180), (int(tip_center[0]), int(tip_center[1])), int(2*scale))
        # Store the laser tip position for firing
        self._laser_tip_offset = (0, -(18 + barrel_length)*scale)

    def update(self, keys):
        self._update_tilt(keys)
        thrusting = (keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_s] or keys[pygame.K_DOWN])
        self._sound.play_move(thrusting)
        self._apply_controls(keys)
        self._apply_friction()
        self._update_position()
        self._update_lasers()

    def _update_tilt(self, keys):
        turning_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        turning_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        if turning_left and not turning_right:
            self._tilt_target = 18
        elif turning_right and not turning_left:
            self._tilt_target = -18
        else:
            self._tilt_target = 0
        if self.tilt < self._tilt_target:
            self.tilt = min(self.tilt + self._tilt_speed, self._tilt_target)
        elif self.tilt > self._tilt_target:
            self.tilt = max(self.tilt - self._tilt_speed, self._tilt_target)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self._fire_laser()

    def draw(self, screen):
        surf = pygame.transform.rotate(self.ship_surf, -self.angle + self.tilt)
        rect = surf.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        screen.blit(surf, rect)
        self._draw_thruster_glow(screen, rect, self._last_thrusting)
        for laser in self.lasers:
            laser.draw(screen)

    def _draw_thruster_glow(self, screen, rect, show_glow):
        if not show_glow:
            return
        scale = 2
        cx, cy = self.screen_width // 2, self.screen_height // 2
        angle_rad = math.radians(self.angle - self.tilt)
        glow_length = 18 * scale
        for local_x, local_y, thruster_length in self._thruster_geom:
            tip_x, tip_y = self._get_thruster_tip(cx, cy, local_x, local_y, thruster_length, angle_rad)
            self._draw_thruster_glow_lines(screen, tip_x, tip_y, angle_rad, glow_length, scale)

    def _get_thruster_tip(self, cx, cy, local_x, local_y, thruster_length, angle_rad):
        base_x = cx + local_x * math.cos(angle_rad) - local_y * math.sin(angle_rad)
        base_y = cy + local_x * math.sin(angle_rad) + local_y * math.cos(angle_rad)
        back_angle = angle_rad + math.pi
        tip_x = base_x + math.sin(back_angle) * (thruster_length // 2)
        tip_y = base_y - math.cos(back_angle) * (thruster_length // 2)
        return tip_x, tip_y

    def _draw_thruster_glow_lines(self, screen, tip_x, tip_y, angle_rad, glow_length, scale):
        back_angle = angle_rad + math.pi
        for i in range(8):
            frac = i / 8.0
            start = (
                tip_x + math.sin(back_angle) * glow_length * frac,
                tip_y - math.cos(back_angle) * glow_length * frac
            )
            end = (
                tip_x + math.sin(back_angle) * glow_length * (frac + 0.13),
                tip_y - math.cos(back_angle) * glow_length * (frac + 0.13)
            )
            alpha1 = int(180 * (1 - frac))
            alpha2 = int(90 * (1 - frac))
            try:
                import pygame.gfxdraw
                pygame.gfxdraw.line(screen, int(start[0]), int(start[1]), int(end[0]), int(end[1]), (100, 200, 255, alpha1))
                pygame.gfxdraw.line(screen, int(start[0]), int(start[1]), int(end[0]), int(end[1]), (180, 240, 255, alpha2))
            except ImportError:
                glow_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
                pygame.draw.line(glow_surf, (100, 200, 255, alpha1), start, end, 6*scale//2)
                pygame.draw.line(glow_surf, (180, 240, 255, alpha2), start, end, 2*scale)
                screen.blit(glow_surf, (0, 0))

    def _apply_controls(self, keys):
        # Thrust forward/backward, rotate left/right
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.angle -= 4
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.angle += 4
        thrust = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            thrust += 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            thrust -= 1
        # Only set _last_thrusting for the glow, not for motion
        self._last_thrusting = (thrust != 0)
        if thrust != 0:
            rad = math.radians(self.angle)
            self.vel[0] += math.sin(rad) * self.thrust * thrust
            self.vel[1] -= math.cos(rad) * self.thrust * thrust

    def _apply_friction(self):
        self.vel[0] *= self.friction
        self.vel[1] *= self.friction

    def _update_position(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

    def _update_lasers(self):
        for laser in self.lasers:
            laser.update()
        self.lasers = [
            l for l in self.lasers
            if 0 <= l.pos[0] <= self.screen_width and 0 <= l.pos[1] <= self.screen_height
        ]

    def _fire_laser(self):
        laser_speed = 10
        # Fire from the end of the gun, in the direction the ship is facing (self.angle + self.tilt for visual alignment)
        rad = math.radians(self.angle - self.tilt)
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        tip_dx, tip_dy = self._laser_tip_offset
        # Rotate the tip offset by the ship's angle and tilt
        laser_x = cx + tip_dx * math.cos(rad) - tip_dy * math.sin(rad)
        laser_y = cy + tip_dx * math.sin(rad) + tip_dy * math.cos(rad)
        vx = math.sin(rad) * laser_speed
        vy = -math.cos(rad) * laser_speed
        laser = Laser([laser_x, laser_y], [vx, vy], self.angle - self.tilt)
        self.lasers.append(laser)
        self._sound.play_laser()
