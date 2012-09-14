from dslpy import macros
import cssutils

class CSSMacro(object):
    MACRO_TYPE = 'css'
    @staticmethod
    def evaluate(env, code):
        def _sub(match):
            try:
                return str(env[match.group("id")])
            except KeyError:
                raise KeyError, "Invalid token: %s" % match.group("id")
        return cssutils.parseString(macros.RE_INLINE.sub(_sub, code))

macros.MacroManager.get_instance().register(CSSMacro)
