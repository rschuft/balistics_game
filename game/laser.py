import pygame
import math

class Laser:
    def __init__(self, pos, vel, angle):
        self.pos = list(pos)
        self.vel = list(vel)
        self.angle = angle

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

    def draw(self, screen):
        x, y = self.pos
        rad = math.radians(self.angle)
        length = 20
        dx = math.sin(rad) * length
        dy = -math.cos(rad) * length
        end_x = x + dx
        end_y = y + dy
        pygame.draw.line(screen, (255, 0, 0), (x, y), (end_x, end_y), 2)
