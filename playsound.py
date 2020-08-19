import pygame.mixer
import time


class Player():
    def __init__(self, filename):
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        self.stop_sign = 0
        self.n_iter = 0

    def reload(filename):
        pygame.mixer.music.load(filename)

    def play_seg(self, start, end, times=1):
        self.n_iter = 0
        for i in range(times):
            now = time.time()
            pygame.mixer.music.play(start=start)
            time.sleep(end - start)
            pygame.mixer.music.stop()
            self.n_iter += 1
            time.sleep(2.5)
            if self.stop_sign:
                self.stop_sign = 0
                break
