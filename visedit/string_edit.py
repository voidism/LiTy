from .utils import HTMLFormatter, TextFormatter, color_settings
import Levenshtein

class StringEdit(object):

    def _generate_comparison(self, fm):
        s1 = self._source_str
        s2 = self._target_str

        i = 0
        j = 0
        result_source = ""
        result_target = ""
        for edit_type, ss, se, ts, te in self._edit_list:
            if edit_type == "equal":
                result_source += ''.join([fm.elem(fm.padding(s1[x])) for x in range(ss,se)])
                result_target += ''.join([fm.elem(fm.padding(s2[x])) for x in range(ts,te)])
            elif edit_type == "replace":
                result_source += ''.join([fm.elem(fm.wrong(fm.padding(s1[x]))) for x in range(ss,se)])
                result_target += ''.join([fm.elem(fm.correct(fm.padding(s2[x]))) for x in range(ts,te)])
            elif edit_type == "delete":
                result_source += ''.join([fm.elem(fm.wrong(fm.padding(s1[x]))) for x in range(ss,se)])
                result_target += ''.join([fm.elem(fm.padding(" ")) for x in range(ss,se)])
            elif edit_type == "insert":
                result_source += ''.join([fm.elem(fm.padding(" ")) for x in range(ts,te)])
                result_target += ''.join([fm.elem(fm.correct(fm.padding(s2[x]))) for x in range(ts,te)])
        #for edit_type in self._edit_list:
        '''    
            if edit_type == "noedit":
                if i < len(s1):
                    result_source += fm.elem(fm.padding(s1[i]))
                    i += 1
                if j < len(s2):
                    result_target += fm.elem(fm.padding(s2[j]))
                    j += 1
            elif edit_type == "replace":
                result_source += fm.elem(fm.wrong(fm.padding(s1[i])))
                result_target += fm.elem(fm.correct(fm.padding(s2[j])))
                i += 1
                j += 1
            elif edit_type == "delete":
                result_source += fm.elem(fm.wrong(fm.padding(s1[i])))
                result_target += fm.elem(fm.padding(" "))
                i += 1
            elif edit_type == "insert":
                result_source += fm.elem(fm.padding(" "))
                result_target += fm.elem(fm.correct(fm.padding(s2[j])))
                j += 1
        '''        
        return fm.output(result_source, result_target)

    def __init__(self,
        source_str,
        target_str,
        text_color_settings = color_settings.TEXT_COLOR_SETTINGS_PRESETS["default"],
        html_color_settings = color_settings.HTML_COLOR_SETTINGS_PRESETS["default"]):

        self._source_str = source_str
        self._target_str = target_str
        #self._cost_table = Levenshtein.leven(source_str, target_str)
        #self._edit_list = Levenshtein.find_path(self._cost_table, padding=True)
        #editopts = Levenshtein.editops(source_str, target_str)
        self._edit_list = Levenshtein.opcodes(source_str, target_str)
        #self._edit_list = ["noedit"]*(len(source_str)+len(target_str)) #max(len(source_str), len(target_str), max([x[1] for x in editopts])+1)
        #for opt in editopts:
        #    self._edit_list[opt[1]] = opt[0]
        self._text_color_settings = text_color_settings
        self._html_color_settings = html_color_settings

    def generate_html(self):
        return self._generate_comparison(HTMLFormatter(self._html_color_settings))

    def generate_text(self, truncate=False):
        return self._generate_comparison(TextFormatter(self._text_color_settings, truncate=truncate))

    def get_edit_distance(self):
        return len(list(filter(lambda s: s != "noedit", self._edit_list)))

