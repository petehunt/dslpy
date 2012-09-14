from dslpy import macros
from dslpy.lang.repr import parser

class SqlMacro(parser.ReprMacro):
    MACRO_TYPE = 'sql'

mgr = macros.MacroManager.get_instance()
mgr.register(SqlMacro)
