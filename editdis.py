from visedit import StringEdit
import Levenshtein

def diff(src, trg):
    # if Levenshtein.distance(src, trg) > 100:
    #     print("difference too much!")
    #     print("Your:", src)
    #     print("Gold:", trg)
    #     return
    se = StringEdit(src, trg)
    text = se.generate_text(truncate=True)
    print(text)
    total = len(trg)
    error = 0
    for ed in se._edit_list:
        if ed[0] != 'equal':
            error += 1
    return error/total
