import sublime
import sublime_plugin
import re

from mathsymbols import maths, inverse_maths, synonims, inverse_synonims

def log(message):
    print(u'UnicodeMath: {0}'.format(message))

def get_line_contents(view, location):
    """
    Returns the contents of the line at the given location
    """
    return view.substr(sublime.Region(view.line(location).a, location))

UNICODE_RE = re.compile(r'.*\\([^\s]+)$')

def get_unicode_prefix(view, location):
    """
    Returns unicode prefix at given location and it's region
    or None if there is no unicode prefix
    """
    cts = get_line_contents(view, location)
    res = UNICODE_RE.match(cts)
    if res:
        (pref_,) = res.groups()
        return (pref_, sublime.Region(location - len(pref_) - 1, location))
    else:
        return None

class UnicodeMathComplete(sublime_plugin.EventListener):
    supress_replace = False
        
    def on_query_completions(self, view, prefix, locations):
        # is prefix starts with '\\'
        is_unicode = get_unicode_prefix(view, locations[0])
        if not is_unicode:
            return

        # returns completions
        return [(k, k) for k in filter(lambda s: s.startswith(prefix), maths)]

    def on_modified(self, view):
        if UnicodeMathComplete.supress_replace:
            UnicodeMathComplete.supress_replace = False
            return
        edit = view.begin_edit()
        try:
            for r in view.sel():
                if r.a == r.b:
                    p = get_unicode_prefix(view, r.a)
                    if p:
                        if p[0] in maths:
                            view.replace(edit, p[1], maths[p[0]])
                        elif p[0] in synonims:
                            view.replace(edit, p[1], maths[synonims[p[0]]])
        finally:
            view.end_edit(edit)

class UnicodeMathSwap(sublime_plugin.TextCommand):
    def run(self, edit):
        for r in self.view.sel():
            w = self.view.word(r)
            usym = self.view.substr(w)
            if usym in inverse_maths:
                UnicodeMathComplete.supress_replace = True
                self.view.replace(edit, w, u'\\' + inverse_maths[usym])
            else:
                upref = get_unicode_prefix(self.view, w.b)
                if upref and upref[0] in maths:
                    self.view.replace(edit, upref[1], maths[upref[0]])

class UnicodeMathInsert(sublime_plugin.WindowCommand):
    def run(self):
        self.menu_items = []
        self.symbols = []
        for k, v in maths.items():
            value = v + ' ' + k
            if k in inverse_synonims:
                value += ' ' + ' '.join(inverse_synonims[k])
            self.menu_items.append(value)
            self.symbols.append(v)

        self.window.show_quick_panel(self.menu_items, self.on_done)

    def on_done(self, idx):
        if idx == -1:
            return
        view = self.window.active_view()
        if not view:
            return
        edit = view.begin_edit()
        for r in view.sel():
            view.replace(edit, r, self.symbols[idx])
        view.end_edit(edit)
