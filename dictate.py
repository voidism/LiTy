import re
import sys
import json
import tqdm
import threading
from playsound import Player
from editdis import diff

class Dictation():
    def __init__(self, audio_file, align_file):
        self.player = Player(audio_file)
        self.align = json.load(open(align_file))
        self.remove_words = "&[]:;—,“”"
        self.sents = []
        w_index = 0
        for sent in tqdm.tqdm(re.split(r'\. |\! |\? |\.\n|\n\n', self.align['transcript'])):
            sent = sent.strip()
            for s in self.remove_words:
                sent = sent.replace(s, '')
            sent = sent.replace('\n', ' ')
            if len(sent) == 0:
                continue
            if sent[-1] == '.':
                sent = sent[:-1]
            times = []
            for word in sent.split(' '):
                if self.align['words'][w_index]['word'] == word:
                    #print(self.align['words'][w_index]['word'], "<+>", word)
                    if 'start' in self.align['words'][w_index]:
                        times.append([self.align['words'][w_index]['start'], self.align['words'][w_index]['end']])
                    elif len(times)>0:
                        times.append([times[-1][-1], times[-1][-1]])
                    elif len(self.sents)>0:
                        times.append([self.sents[-1][1], self.sents[-1][1]])
                    else:
                        times.append([0.0, 0.0])
                    w_index += 1
                else:
                    for n in range(5):
                        if w_index+n >= len(self.align['words']):
                            break
                        if self.align['words'][w_index+n]['word'] == word:
                            #print(self.align['words'][w_index+n]['word'], "<+>", word)
                            w_index += n
                            if 'start' in self.align['words'][w_index]:
                                times.append([self.align['words'][w_index]['start'], self.align['words'][w_index]['end']])
                            elif len(times)>0:
                                times.append([times[-1][-1], times[-1][-1]])
                            elif len(self.sents)>0:
                                times.append([self.sents[-1][1], self.sents[-1][1]])
                            else:
                                times.append([0.0, 0.0])
                            w_index += 1
                            break
            self.sents.append([times[0][0], times[-1][-1], sent])
    def play(self):
        for start, end, sent in self.sents:
            print(sent)
            self.player.play_seg(start, end)
    def dictate(self, begin=0):
        for i, (start, end, sent) in enumerate(self.sents):
            if i < begin:
                continue
            _ = input("\nStart Sentence [%d] (press to continue)"%(i+1))
            t = threading.Thread(target=self.player.play_seg, args=[start, end, 1000]).start()
            text = input("Type Your Answer >>> ")
            diff(text, sent)
            _ = input("(press to continue)")
            self.player.stop_sign = 1
