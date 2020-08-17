import argparse
from dictate import Dictation

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=str, required=True, help="The input audio file name.")
    parser.add_argument("--align", type=str, default="", required=False, help="The input align file name.")
    parser.add_argument("--begin", type=int, default=0, required=False, help="The begining sentence number.")
    parser.add_argument("--log", type=str, default=None, required=False, help="The log file name.")
    args = parser.parse_args()
    if args.align == "":
        args.align = args.audio.replace(".mp3", ".align")
    dic = Dictation(args.audio, args.align, args.log)
    dic.dictate(args.begin)
