import re
import os
import sys
import json
import tqdm
import time
import readline
import threading

from playsound import Player
from editdis import diff

readline.parse_and_bind('tab: complete')
readline.parse_and_bind('set editing-mode vi')

class Dictation():
    def __init__(self, audio_file, align_file, log_file=None, pause_time=2.5):
        self.player = Player(audio_file, pause_time=pause_time)
        self.align = json.load(open(align_file))
        self.audio_name = audio_file
        if log_file is not None:
            if not os.path.exists(log_file):
                self.log_file = open(log_file, 'w')
                self.log_file.write("Time\tAudio\tNumber\tCER\tWords/ListenIter\tHypothesis\tTarget\n")
            else:
                self.log_file = open(log_file, 'a')
        else:
            self.log_file = None
        self.remove_words = "&[]:;—,“”"
        self.sents = []
        w_index = 0
        print("Parse transcript...")
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

    def run(self, begin=0):
        for i, (start, end, sent) in enumerate(self.sents):
            if i < begin:
                continue
            try:
                _ = input("\nStart Sentence [%d/%d] (press to continue)"%(i+1, len(self.sents)))
            except:
                print("\n*** Exit program ***")
                self.player.stop_sign = 1
                sys.exit()
            t = threading.Thread(target=self.player.play_seg, args=[start, end, 1000]).start()
            try:
                text = input("Type Your Answer >>> ")
            except:
                print("\n*** Exit program ***")
                self.player.stop_sign = 1
                sys.exit()
            wer = diff(text.lower(), sent.lower())
            n_iter = self.player.n_iter
            words = len(text.split(' '))
            wordrate = words/n_iter
            if self.log_file is not None:
                timestamp = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(time.time()))
                self.log_file.write("%s\t%s\t%d\t%.6f\t%.6f\t%s\t%s\n"%(timestamp, self.audio_name, i, wer, wordrate, text.lower(), sent.lower()))
            try:
                _ = input("CER: {:.2f} % Words/ListenIter: {:.4f} (press to continue)".format(wer*100, wordrate))
            except:
                print("\n*** Exit program ***")
                self.player.stop_sign = 1
                sys.exit()
            self.player.stop_sign = 1
