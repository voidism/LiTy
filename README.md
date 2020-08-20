# LiTy: Listen &amp; Type

An Efficient Dictation Training Tool for English Learners.

Train your "human brain speech recognition".

## Features
- Support any MP3 file with a transcript.
- Segment audio file automatically into sentences by **forced alignment**.
- Play segments again and again until you complete the whole sentence.
- Visualize the errors in your answer.
- Record statistics (error rate, speed) for personal reviewing.

## Example

![usage](https://i.imgur.com/nkijuMB.gif)

- To practice dictation, all you need are a mp3 file and its transcript. Your can find high quality audios and transcripts on [Scientific American 60-second science](https://www.scientificamerican.com/podcasts/) and download them for free.
- When typing sentences, the audio segment will be played repeatly with a 2.5-second pause time. Your can also specify the pause time.
- A visualization of edit distance will be shown after submit your answer. This feature are supported by [visedit](https://github.com/ukiuki-satoshi/visedit/). We used [python-Levenshtein](https://github.com/ztane/python-Levenshtein/) to speed up this module.
- The feedback information will be show and recorded in a log file, including **Character Error Rate (CER)**, **word speed per listen iteration**.

## Setup

### Install gentle:

Install submodule [gentle](https://github.com/lowerquality/gentle):

```
cd gentle
./install.sh
```

> If you have installed gentle before, skip this step. Just set `--gentle_root` to the existing directory of gentle when running `python main.py`.

### Install required packages:

- pydub
- pyaudio
- tqdm
- python-Levenshtein

```
pip install -r requirements.txt
```

## Usage

```
usage: main.py [-h] --audio AUDIO [--trans TRANS] [--align ALIGN]
               [--begin BEGIN] [--log LOG] [--gentle_root GENTLE_ROOT]
               [--pause_time PAUSE_TIME]

optional arguments:
  -h, --help            show this help message and exit
  --audio AUDIO         The input audio file name.
  --trans TRANS         The input transcript file name.
  --align ALIGN         The input align file name.
  --begin BEGIN         The begining sentence number.
  --log LOG             The log file name.
  --gentle_root GENTLE_ROOT
                        The installed gentle directory.
  --pause_time PAUSE_TIME
                        The pause time between each mp3 replay. (sec)
```
- When running on an audio file for the first time, gentle will be executed. Alignment file will be save and skip executing gentle when running the second time.
- If you want to begin in at the middle of the whole article, just set `--begin [sentence number]`.
- log file will be in tsv format to record `practice time, audio file name, sentence number, CER, word speed/iter, hypothesis, target`
