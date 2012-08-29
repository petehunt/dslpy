from xhpy import macros
from xhpy.lang.repr import parser

class SqlMacro(parser.ReprMacro):
    MACRO_TYPE = 'sql'

mgr = macros.MacroManager.get_instance()
mgr.register(SqlMacro)
