import pyaudio
from pydub import AudioSegment
import time


class Player():
    def __init__(self, filename, pause_time=2.5):
        self.mp3 = AudioSegment.from_mp3(filename)
        self.player = pyaudio.PyAudio()
        self.stop_sign = 0
        self.n_iter = 0
        self.pause_time = pause_time

    def reload(filename):
        self.mp3 = AudioSegment.from_mp3(filename)

    def play_seg(self, start, end, times=1):
        self.n_iter = 0
        for i in range(times):
            now = time.time()
            mp3_seg = self.mp3[int(start * 1000):int(end * 1000)]
            stream = self.player.open(format = self.player.get_format_from_width(mp3_seg.sample_width),
                        channels = mp3_seg.channels,
                        rate = mp3_seg.frame_rate,
                        output = True)
            data = mp3_seg.raw_data
            while data:
                stream.write(data)
                data=0

            stream.close()
            self.n_iter += 1
            if self.stop_sign:
                self.stop_sign = 0
                break
            time.sleep(self.pause_time)
            if self.stop_sign:
                self.stop_sign = 0
                break
