import pygame
from .player import Player
from .network import NetworkManager
import socket
import random

class Starfield:
    def __init__(self, width, height, num_layers=3, stars_per_layer=60):
        self.width = width
        self.height = height
        self.layers = []
        self.speeds = []
        for i in range(num_layers):
            stars = [
                [random.randint(0, width), random.randint(0, height)]
                for _ in range(stars_per_layer)
            ]
            self.layers.append(stars)
            self.speeds.append(0.2 + 0.4 * (i / (num_layers - 1)))
        self.colors = [(180, 180, 180), (220, 220, 255), (255, 255, 255)]

    def update(self, player_vel):
        # Move stars in the opposite direction of player velocity, scaled by layer speed
        for idx, stars in enumerate(self.layers):
            speed = self.speeds[idx]
            for star in stars:
                star[0] -= player_vel[0] * speed
                star[1] -= player_vel[1] * speed
                # Wrap around screen
                if star[0] < 0:
                    star[0] += self.width
                elif star[0] > self.width:
                    star[0] -= self.width
                if star[1] < 0:
                    star[1] += self.height
                elif star[1] > self.height:
                    star[1] -= self.height

    def draw(self, screen):
        for idx, stars in enumerate(self.layers):
            color = self.colors[idx % len(self.colors)]
            for star in stars:
                pygame.draw.circle(screen, color, (int(star[0]), int(star[1])), 2 - idx // 2)

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.player = Player(self.screen_width, self.screen_height)
        # Use hostname:port as a simple unique id
        self.player_id = f"{socket.gethostname()}_{socket.gethostbyname(socket.gethostname())}"
        self.network = NetworkManager(self.player_id)
        self.network.start()
        self.remote_players = {}  # key: peer_id, value: Player
        self.starfield = Starfield(self.screen_width, self.screen_height)

    def run(self):
        font = pygame.font.Font(None, 36)
        while self.running:
            self._handle_events()
            self._update()
            self._draw(font)
            self.clock.tick(60)
        self.network.stop()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                self.running = False
            else:
                self.player.handle_event(event)

    def _update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        # Starfield parallax update
        self.starfield.update(self.player.vel)
        self._update_peers()

    def _update_peers(self):
        # Check for new peers and add them as remote players if not already present
        peers = self.network.get_peers()
        for peer_id, _ in peers:
            if peer_id not in self.remote_players:
                self.remote_players[peer_id] = Player(self.screen_width, self.screen_height)

    def _draw(self, font):
        self.screen.fill((0, 0, 0))
        self.starfield.draw(self.screen)
        self.player.draw(self.screen)

        # Draw remote players
        for remote in self.remote_players.values():
            remote.draw(self.screen)

        # Show detected peers
        y = 10
        self.screen.blit(font.render("Peers on LAN:", True, (255,255,0)), (10, y))
        y += 30
        for peer_id, ip in self.network.get_peers():
            self.screen.blit(font.render(f"{peer_id} ({ip})", True, (180,180,180)), (10, y))
            y += 25

        pygame.display.flip()
