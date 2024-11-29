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

gpt4o_prompts = {
    'en': '''"Task: Explain the more difficult English expressions in the correct answer."
Below is a user's answer while transcribing an English audio recording. The user's answer is shown after "Your:", and the correct answer is shown after "Gold:".
If the correct answer contains more difficult English expressions, please help explain their meaning, even if the transcription is correct, as the user may not necessarily understand them. However, note that the user has been learning English for a long time, so there is no need to explain basic English expressions.
If the user's answer has errors in certain words or phrases, those words or phrases should be explained. However, if the errors are minor and can be ignored (e.g., "we're" written as "we are," or "there's" written as "there is"), there is no need to point them out.
Additionally, due to imperfect audio segmentation, the user's answer may sometimes miss a few words at the end of a sentence. These cases can also be ignored unless the missing words involve particularly difficult English expressions.
Keep your response concise and focus only on explaining the more difficult English expressions, typically phrases or complex usages of a few words together. There is no need to explain simple or basic vocabulary. Also, do not repeat Your: and Gold: in your response. Simply provide the explanations. Avoid adding unnecessary opening or closing remarks; just write the explanations directly.
''',
    'zh': '''「任務：用中文解釋正確答案中的比較困難的英文表達」
以下是一位使用者在聽寫一段英文語音時的答案。他的答案放在Your:之後，正確答案則是在Gold:之後。
如果正確答案裡面有比較困難的英文表達，請幫忙用中文解釋他們的意思，就算聽寫的結果是正確的，也還是可以解釋，因為使用者不一定清楚知道他們的意思。不過請注意，使用者已經學習英文很久，所以不需要解釋一些比較基本的英文表達。
如果使用者的答案在某些字詞上有誤，那就更應該解釋這些字詞的意思。不過請注意，如果錯誤的地方是一些可以忽略的，例如we're寫成we are，there's寫成there is，那就忽略，不需要特別解釋了。
另外由於語音切割不完美的問題，句子結尾的地方使用者的答案可能會有一些不完整，漏掉幾個字，這種情況也可以忽略，除非漏掉的幾個字是特別困難的英文表達。
回答要盡量簡潔，不需要解釋太多簡單的基礎單字，只需要解釋比較困難的英文表達即可，通常是一些片語或是幾個字合起來的複雜用法。也不需要重複寫**Your:**和**Gold:**了，只需要寫中文解釋就好。開頭結尾也不需要寫額外的廢話，只需要寫中文解釋就好。
''',
    'es': '''"Tarea: Explicar en español las expresiones inglesas más difíciles en la respuesta correcta"
A continuación se presenta la respuesta de un usuario al transcribir un audio en inglés. Su respuesta está después de Your:, mientras que la respuesta correcta está después de Gold:.  
Si en la respuesta correcta hay expresiones inglesas más complicadas, por favor ayude a explicarlas en español, incluso si la transcripción es correcta, ya que el usuario podría no comprender completamente su significado. Sin embargo, tenga en cuenta que el usuario ya lleva mucho tiempo aprendiendo inglés, por lo que no es necesario explicar expresiones básicas en inglés.  
Si la respuesta del usuario tiene errores en algunas palabras o frases, será aún más importante explicar el significado de esas palabras o frases. No obstante, si el error se debe a algo menor, como escribir "we're" en lugar de "we are" o "there's" en lugar de "there is", puede ignorarlo y no hace falta explicarlo.  
Además, debido a problemas de segmentación del audio, es posible que la respuesta del usuario esté incompleta al final de las frases y falten algunas palabras. En estos casos, también se puede ignorar, a menos que las palabras omitidas sean expresiones inglesas especialmente difíciles.  
La respuesta debe ser lo más concisa posible; no es necesario explicar demasiadas palabras básicas, solo enfocarse en las expresiones inglesas más complicadas, generalmente frases o combinaciones de palabras con un uso más complejo. Tampoco es necesario repetir "Your:" y "Gold:", simplemente escribe la explicación en español. No añadas introducciones o conclusiones innecesarias; solo escribe la explicación en español directamente.
''',
    'fr': '''"Tâche : Expliquer les expressions anglaises les plus difficiles dans la réponse correcte."
Voici la réponse d’un utilisateur lors d’une dictée audio en anglais. Sa réponse est indiquée après Your:, tandis que la réponse correcte est indiquée après Gold:.
Si la réponse correcte contient des expressions anglaises relativement complexes, veuillez les expliquer en français, même si le résultat de la dictée est correct, car l'utilisateur peut ne pas comprendre pleinement leur signification. Cependant, veuillez noter que l'utilisateur étudie l'anglais depuis longtemps, donc il n'est pas nécessaire d'expliquer des expressions anglaises de base.
Si la réponse de l'utilisateur comporte des erreurs sur certains mots ou expressions, vous devriez expliquer la signification de ces termes. Cependant, si les erreurs sont mineures et négligeables, comme écrire "we're" au lieu de "we are" ou "there's" au lieu de "there is", vous pouvez les ignorer et ne pas les expliquer.
De plus, en raison de problèmes d’imperfections dans le découpage audio, il se peut que la fin des phrases de l’utilisateur soit incomplète ou qu’il manque quelques mots. Ces cas peuvent également être ignorés, sauf si les mots manquants sont des expressions anglaises particulièrement complexes.
La réponse doit rester aussi concise que possible. Inutile d'expliquer des mots simples ou des bases élémentaires ; concentrez-vous uniquement sur les expressions plus complexes ou les usages combinés de plusieurs mots. Il n’est pas non plus nécessaire de répéter Your: et Gold:, il suffit d’écrire l’explication en français. De plus, n’ajoutez pas d’introduction ou de conclusion superflue ; écrivez uniquement l’explication en français.
'''
}

class Dictation():
    def __init__(self, audio_file, subtitle_file, log_dir=None, pause_time=2.5, char_per_sent=150, openai_key=None, lang='en'):
        self.player = Player(audio_file, pause_time=pause_time)
        self.audio_name = audio_file
        self.offset = 0.4
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
        self.openai_key = openai_key
        if self.openai_key is not None:
            import openai
            openai.api_key = self.openai_key
            if lang not in gpt4o_prompts:
                raise ValueError(f"Language {lang} is not supported.")
            self.gpt4o_prompt = gpt4o_prompts[lang]

    def segment(self, subtitle_path):
        # If the video is already downloaded, but not segmented
        auto_generated = False
        with open(subtitle_path, 'r') as f:
            subtitles_content = f.readlines()
            for line in subtitles_content[:10]:
                if '</c>' in line:
                    auto_generated = True
                    break
            sentences = []
            prev_text = 'none'
            curr_block = ''
            curr_start_time = -1
            curr_end_time = 0
            idx = 0
            while idx < len(subtitles_content):
                line = subtitles_content[idx]
                if '-->' in line:
                    start_time, end_time = line.strip().split(' --> ')
                    start_time = parse_time_to_seconds(start_time)
                    end_time = parse_time_to_seconds(end_time)
                    if auto_generated:
                        text = subtitles_content[idx + 2].strip()
                        text = remove_tags(text)
                    else:
                        text = subtitles_content[idx + 1].strip()
                    if curr_start_time == -1:
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
                    if auto_generated:
                        idx += 2
                    else:
                        idx += 1
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

    def gpt4o_feedback(self, text):
        import openai
        prompt = f"{self.gpt4o_prompt}\n{text}"
        response = openai.chat.completions.create(
            model='gpt-4o-2024-05-13',
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

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
                if self.openai_key is not None:
                    print("| Acc: {}  {:.2f} % Words/ListenIter: {}  {:.4f}".format(emoji_acc, acc*100, emoji_wordrate, wordrate))
                    feedback = self.gpt4o_feedback(f"Your: {text}\nGold: {sent}")
                    print("| Feedback:")
                    print('\n'.join([f"| {line}" for line in feedback.split('\n')[:-1] if line.strip() != '']))
                    _ = input("| {} (👉 ⌨️🔜 )".format(feedback.split('\n')[-1]))
                else:
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
