import pygame
import math
import array

class SoundManager:
    def __init__(self):
        self.move_sound = self._generate_rumble_sound()
        self.move_sound.set_volume(0.3)
        self.laser_sound = self._generate_laser_sound()
        self.laser_sound.set_volume(0.5)
        self.move_sound_channel = None

    def play_move(self, active):
        if active:
            if self.move_sound_channel is None or not self.move_sound_channel.get_busy():
                self.move_sound_channel = self.move_sound.play(loops=-1)
        else:
            if self.move_sound_channel is not None and self.move_sound_channel.get_busy():
                self.move_sound_channel.fadeout(200)

    def play_laser(self):
        self.laser_sound.play()

    def _generate_rumble_sound(self):
        sample_rate = 22050
        duration = 0.5
        freq1 = 28
        freq2 = 54
        n_samples = int(sample_rate * duration)
        arr = array.array("h")
        for i in range(n_samples):
            t = i / sample_rate
            val = 0.38 * math.sin(2 * math.pi * freq1 * t)
            val += 0.22 * math.sin(2 * math.pi * freq2 * t)
            val *= 0.8 + 0.2 * math.sin(2 * math.pi * 2 * t)
            arr.append(int(32767 * max(-1, min(1, val))))
        return pygame.mixer.Sound(buffer=arr)

    def _generate_laser_sound(self):
        sample_rate = 22050
        duration = 0.13
        n_samples = int(sample_rate * duration)
        arr = array.array("h")
        for i in range(n_samples):
            t = i / sample_rate
            freq = 1800 - 1400 * (t / duration)
            square = 1 if math.sin(2 * math.pi * freq * t) > 0 else -1
            sine = math.sin(2 * math.pi * freq * t)
            noise = (2 * (math.sin(2 * math.pi * 60 * t + math.sin(2 * math.pi * 120 * t))) - 1) * (1 - t / duration)
            val = 0.19 * square + 0.13 * sine + 0.09 * noise
            if i < 10:
                val += 0.25 * (1 - i / 10)
            arr.append(int(32767 * max(-1, min(1, val))))
        return pygame.mixer.Sound(buffer=arr)
