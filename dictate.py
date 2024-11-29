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


def remove_tags(text):
    '''Remove HTML tags from a string'''
    '''Example: 
    input: if<00:00:00.240><c> you</c><00:00:00.399><c> can</c><00:00:00.560><c> give</c><00:00:00.719><c> me</c><00:00:00.919><c> 10</c><00:00:01.160><c> minutes</c><00:00:01.400><c> of</c><00:00:01.520><c> your</c>
    output: if you can give me 10 minutes of your
    '''
    removed_text = ' '.join([word.split('>')[-1] for word in text.split('<') if word])
    # reduce multi spaces
    return ' '.join(removed_text.split())


def parse_time_to_seconds(time):
    time = time.split(" align")[0]
    try:
        h, m, s = time.split(':')
    except ValueError:
        print(f"Error parsing time: {time}")
        raise ValueError
    # if s starts with 0, remove it
    if s.startswith('0'):
        s = s[1:]
    return int(h) * 3600.0 + int(m) * 60.0 + float(s)

class Dictation():
    def __init__(self, audio_file, subtitle_file, log_dir=None, pause_time=2.5, char_per_sent=150, offset=0.4):
        self.player = Player(audio_file, pause_time=pause_time)
        self.audio_name = audio_file
        self.offset = offset
        video_id = audio_file.split('/')[-1].split('.')[0]
        self.begin = 0
        if log_dir is not None:
            log_file = os.path.join(log_dir, f"{video_id}.char{char_per_sent}.log")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            if not os.path.exists(log_file):
                self.log_file = open(log_file, 'w')
                self.log_file.write("Time\tAudio\tNumber\tAccuracy\tWords/ListenIter\tHypothesis\tTarget\n")
                self.log_file.flush()
            else:
                # retrieve the current number of sentences
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        last_line = lines[-1].strip()
                        self.begin = int(last_line.split('\t')[2]) + 1
                self.log_file = open(log_file, 'a')
        else:
            self.log_file = None
        self.remove_words = "&[]:;—,“”"
        self.char_per_sent = char_per_sent
        self.sents = self.segment(subtitle_file)

    def segment(self, subtitle_path):
        # If the video is already downloaded, but not segmented
        with open(subtitle_path, 'r') as f:
            subtitles_content = f.readlines()
            sentences = []
            prev_text = 'none'
            curr_block = ''
            curr_start_time = 0
            curr_end_time = 0
            idx = 0
            while idx < len(subtitles_content):
                line = subtitles_content[idx]
                if '-->' in line:
                    start_time, end_time = line.strip().split(' --> ')
                    start_time = parse_time_to_seconds(start_time)
                    end_time = parse_time_to_seconds(end_time)
                    text = subtitles_content[idx + 2].strip()
                    text = remove_tags(text)
                    if curr_start_time == 0:
                        curr_start_time = start_time
                        curr_end_time = end_time
                    if prev_text == text:
                        curr_end_time = end_time
                    elif len(curr_block) + len(text) < self.char_per_sent:
                        curr_block += ' ' + text
                        curr_end_time = end_time
                    else:
                        if curr_block:
                            # reduce multi spaces
                            curr_block = re.sub(' +', ' ', curr_block).strip()
                            # if the last sentence's end time is in 2 seconds of the current start time, update the last sentence end time to the current start time
                            if sentences:
                                if curr_end_time - curr_start_time < 2:
                                    sentences[-1]['end_time'] = curr_start_time
                                else: # add a offset to the previous sentence end time
                                    sentences[-1]['end_time'] = sentences[-1]['end_time'] + self.offset
                            sentences.append({'text': curr_block, 'start_time': curr_start_time, 'end_time': curr_end_time})
                        curr_block = text
                        curr_start_time = start_time
                        curr_end_time = end_time
                    prev_text = text
                    idx += 2
                else:
                    idx += 1

        # Load audio file
        # split the audio file into sentences, save each sentence as a separate audio file, as well as the sentences as separate text files
        segmentations = []
        for i, sentence in enumerate(sentences):
            start_time, end_time = sentence['start_time'], sentence['end_time']
            segmentations.append((start_time, end_time, sentence['text']))
        return segmentations


    def play(self):
        for start, end, sent in self.sents:
            print(sent)
            self.player.play_seg(start, end)

    def run(self):
        t = None
        emoji_acc_stats = {'💯': 0, '👏': 0, '👍': 0, '👌': 0, '👀': 0, '🤔': 0, '🤨': 0, '😒': 0, '😞': 0, '😭': 0, '🤬': 0}
        emoji_wordrate_stats = {'🚀': 0, '💨': 0, '🏃‍♂️': 0, '🐇': 0, '🐢': 0, '🐌': 0}
        for i, (start, end, sent) in enumerate(self.sents):
            if i < self.begin:
                continue
            try:
                _ = input("+------------\n| Start Sentence [%d/%d] (👉 ⌨️🔜 )"%(i+1, len(self.sents)))
                if t is not None:
                    t.join()
                    t = None
            except:
                print("\n| *** Exit program ***")
                self.player.stop_sign = 1
                if self.log_file is not None:
                    self.log_file.close()
                print("+------------\n| Emoji Acc Stats:")
                for key, value in emoji_acc_stats.items():
                    print(f"| {key}  : {'#' * value}")
                print("+------------\n| Emoji Wordrate Stats:")
                for key, value in emoji_wordrate_stats.items():
                    print(f"| {key}  : {'#' * value}")
                sys.exit()
            t = threading.Thread(target=self.player.play_seg, args=[start, end, 1000]).start()
            try:
                text = input("| Enter Your Answer >>> ")
                text = re.sub(' +', ' ', text).strip()
            except:
                print("\n*** Exit program ***")
                self.player.stop_sign = 1
                print("+------------\n| Emoji Acc Stats:")
                for key, value in emoji_acc_stats.items():
                    print(f"| {key}  : {'#' * value}")
                print("+------------\n| Emoji Wordrate Stats:")
                for key, value in emoji_wordrate_stats.items():
                    print(f"| {key}  : {'#' * value}")
                sys.exit()
            acc = diff(text.lower(), sent.lower())
            n_iter = self.player.n_iter if self.player.n_iter > 0 else 1
            words = len(text.split(' '))
            wordrate = words/n_iter
            if self.log_file is not None:
                timestamp = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(time.time()))
                self.log_file.write("%s\t%s\t%d\t%.6f\t%.6f\t%s\t%s\n"%(timestamp, self.audio_name, i, acc, wordrate, text.lower(), sent.lower()))
                self.log_file.flush()
            
            emoji_acc = ''
            if acc > 0.95:
                emoji_acc = '💯'
            elif acc > 0.9:
                emoji_acc = '👏'
            elif acc > 0.8:
                emoji_acc = '👍'
            elif acc > 0.7:
                emoji_acc = '👌'
            elif acc > 0.6:
                emoji_acc = '👀'
            elif acc > 0.5:
                emoji_acc = '🤔'
            elif acc > 0.4:
                emoji_acc = '🤨'
            elif acc > 0.3:
                emoji_acc = '😒'
            elif acc > 0.2:
                emoji_acc = '😞'
            elif acc > 0.1:
                emoji_acc = '😭'
            else:
                emoji_acc = '🤬'

            emoji_acc_stats[emoji_acc] += 1

            emoji_wordrate = ''
            if wordrate > 4.5:
                emoji_wordrate = '🚀'
            elif wordrate > 4.0:
                emoji_wordrate = '💨'
            elif wordrate > 3.5:
                emoji_wordrate = '🏃‍♂️'
            elif wordrate > 3.0:
                emoji_wordrate = '🐇'
            elif wordrate > 2.0:
                emoji_wordrate = '🐢'
            else:
                emoji_wordrate = '🐌'

            emoji_wordrate_stats[emoji_wordrate] += 1

            try:
                _ = input("| Acc: {}  {:.2f} % Words/ListenIter: {}  {:.4f} (👉 ⌨️🔜 )".format(emoji_acc, acc*100, emoji_wordrate, wordrate))

            except:
                print("\n| *** Exit program ***")
                # print the statistics of emoji in bar chart
                print("+------------\n| Emoji Acc Stats:")
                for key, value in emoji_acc_stats.items():
                    print(f"| {key}  : {'#' * value}")
                print("+------------\n| Emoji Wordrate Stats:")
                for key, value in emoji_wordrate_stats.items():
                    print(f"| {key}  : {'#' * value}")

                self.player.stop_sign = 1
                sys.exit()
            self.player.stop_sign = 1
