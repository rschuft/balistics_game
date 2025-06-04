import socket
import threading
import time

BROADCAST_PORT = 54545
BROADCAST_INTERVAL = 1.0  # seconds
DISCOVERY_MESSAGE = b"PYGAME_PEER_DISCOVERY"

class NetworkManager:
    def __init__(self, player_id):
        self.player_id = player_id
        self.peers = set()
        self.running = False
        self.lock = threading.Lock()
        self._broadcast_thread = None
        self._listen_thread = None

    def start(self):
        self.running = True
        self._broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._broadcast_thread.start()
        self._listen_thread.start()

    def stop(self):
        self.running = False

    def _broadcast_loop(self):
        sock = self._create_broadcast_socket()
        message = self._make_discovery_message()
        while self.running:
            self._broadcast_message(sock, message)
            time.sleep(BROADCAST_INTERVAL)
        sock.close()

    def _listen_loop(self):
        sock = self._create_listen_socket()
        while self.running:
            self._receive_and_process(sock)
        sock.close()

    def _create_broadcast_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return sock

    def _create_listen_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', BROADCAST_PORT))
        return sock

    def _make_discovery_message(self):
        return DISCOVERY_MESSAGE + b":" + self.player_id.encode()

    def _broadcast_message(self, sock, message):
        sock.sendto(message, ('<broadcast>', BROADCAST_PORT))

    def _receive_and_process(self, sock):
        try:
            data, addr = sock.recvfrom(1024)
            self._process_incoming(data, addr)
        except Exception:
            pass

    def _process_incoming(self, data, addr):
        if data.startswith(DISCOVERY_MESSAGE):
            parts = data.split(b":", 1)
            if len(parts) == 2:
                peer_id = parts[1].decode(errors="ignore")
                if peer_id != self.player_id:
                    with self.lock:
                        self.peers.add((peer_id, addr[0]))

    def get_peers(self):
        with self.lock:
            return list(self.peers)
