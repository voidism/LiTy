import os
import argparse
from dictate import Dictation

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=str, required=True, help="The input audio file name.")
    parser.add_argument("--trans", type=str, default="", required=False, help="The input transcript file name.")
    parser.add_argument("--align", type=str, default="", required=False, help="The input align file name.")
    parser.add_argument("--begin", type=int, default=0, required=False, help="The begining sentence number.")
    parser.add_argument("--log", type=str, default=None, required=False, help="The log file name.")
    parser.add_argument("--gentle_root", type=str, default='gentle', required=False, help="The log file name.")
    parser.add_argument("--pause_time", type=float, default=2.5, required=False, help="The pause time between each mp3 replay. (sec)")
    args = parser.parse_args()
    if args.align == "":
        args.align = args.audio.replace(".mp3", ".align")
    if args.trans == "":
        args.trans = args.audio.replace(".mp3", ".txt")
    if not os.path.exists(args.align):
        print("Forced alignment results not found in {} => Execute aligner specified  in `--gentle_root`".format(args.align))
        print(os.popen("python {} {} {} -o {}".format(os.path.join(args.gentle_root, 'align.py'), args.audio, args.trans, args.align)).read())
    print(open('logo').read())
    dic = Dictation(args.audio, args.align, args.log, args.pause_time)
    dic.run(args.begin)
