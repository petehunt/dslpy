from dslpy import macros
from dslpy.lang.repr import parser

class ShMacro(parser.ReprMacro):
    MACRO_TYPE = 'sh'

mgr = macros.MacroManager.get_instance()
mgr.register(ShMacro)
