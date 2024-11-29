from visedit import StringEdit

def diff(src, trg):
    se = StringEdit(src, trg)
    text = se.generate_text(truncate=True)
    colored_src, colored_trg = text.split('\n')
    print("| Your:", colored_src)
    print("| Gold:", colored_trg)
    total = 0
    corre = 0
    for ed in se._edit_list:
        if ed[0] == 'equal':
            corre += ed[4] - ed[3]
        total += ed[4] - ed[3]
    return corre/total
