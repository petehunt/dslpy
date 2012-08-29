from xhpy import macros

class ReprMacro(object):
    @staticmethod
    def evaluate(env, code):
        def _sub(match):
            try:
                return macros.quote(eval(match.group("id"), env))
            except KeyError:
                raise KeyError, "Invalid token: %s" % match.group("id")
        return macros.RE_INLINE.sub(_sub, code)
        
