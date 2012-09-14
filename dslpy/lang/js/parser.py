from dslpy import macros
import re
import json

class JSMacro(object):
    MACRO_TYPE = 'js'

    @staticmethod
    def evaluate(env, code):
        def _sub(match):
            return json.dumps(eval(match.group("id"), env))
        return macros.RE_INLINE.sub(_sub, code)

macros.MacroManager.get_instance().register(JSMacro)
