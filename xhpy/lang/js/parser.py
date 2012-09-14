from xhpy import macros
import re
import json

class JSMacro(object):
    MACRO_TYPE = 'js'

    @staticmethod
    def evaluate(env, code):
        def _sub(match):
            try:
                return json.dumps(env[match.group("id")])
            except KeyError:
                raise KeyError, "Invalid token: %s" % match.group("id")
        return macros.RE_INLINE.sub(_sub, code)
        
macros.MacroManager.get_instance().register(JSMacro)
