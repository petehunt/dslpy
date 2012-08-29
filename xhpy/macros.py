# TODO: URLs, SQL, CSS, shell commands and simple JavaScript (just json encode for now)
# TODO: omg this is epic: Python. This allows for silly macros.

import re
import imp
import sys
import os

class MacroManager(object):
    _instance = None

    def __init__(self):
        self.types = {}

    def evaluate(self, l, g, type, code):
        macro_type = self.types.get(type, None)
        if not macro_type:
            raise ValueError, "Bad macro type %r" % type
        env = g.copy()
        env.update(l)
        return macro_type.evaluate(env, code)

    def evaluate_file(self, type, env, file):
        return self.evaluate(env, {}, type, file.read())

    def register(self, type):
        self.types[type.MACRO_TYPE] = type

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

RE_EXPRESSION = re.compile(r'<\?(?P<type>\w+)(?P<body>.*?)\?>', re.DOTALL)
RE_INLINE = re.compile(r'\$\{(?P<id>.*?)\}', re.DOTALL) # used externally

def quote(s):
    # TODO: not unicode-safe
    return repr(unicode(s).encode("utf8"))

def _sub(match):
    type = match.group("type")
    body = match.group("body")
    # in order to keep the line numbers consistent, we need to insert the string
    # exactly as-is and manually escape the quotes.
    body = '"""' + body.replace('"""', r'\"\"\"') + '"""'
    return "MacroManager.get_instance().evaluate(locals(), globals(), %r, %s)" % (type, body)

def preprocess(src):
    return RE_EXPRESSION.sub(_sub, src)

class Importer(object):
    def _find_dotted(self, fullname):
        parts = fullname.split(".")
        path = None
        result = None
        for part in parts:
            if not path:
                result = imp.find_module(part)
            else:
                result = imp.find_module(part, [path])
            _,path,_ = result
        return result
    def find_module(self, fullname, path=None):
        try:
            _,name,_ = self._find_dotted(fullname)
            if name.endswith(".py"):
                return self
        except ImportError:
            pass
    def load_module(self, fullname):
        file,filename,_ = self._find_dotted(fullname)
        data = file.read()
        mod = imp.new_module(fullname)
        mod.__loader__ = self
        mod.__file__ = filename
        sys.modules[fullname] = mod
        processed_data = preprocess(data)
        mod.MacroManager = MacroManager
        try:
          data = compile(processed_data, filename, "exec")
        except SyntaxError:
          data = compile(data, filename, "exec")
        exec data in mod.__dict__
        return mod

INSTALLED = False

def install():
    global INSTALLED
    if INSTALLED:
        return
    INSTALLED = True
    sys.meta_path = [Importer()]
