# TODO: typed/required attributes/children?
# TODO: find child node by type
# BIG TODO: unicode support
import cgi
import gettext

from xhpy import macros

class AlreadyComposedException(Exception):
    ''' you can only compose once '''

class NotComposedException(Exception):
    ''' you must compose before rendering. this is an internal bug '''

def compose(node, request):
    node = ProtoNode.convert_to_node(node)
    while not node.__composed__:
        node = node.__compose__(request)
    return node

class ProtoNode(object):
    def __init__(self):
        self.__children__ = []
        self.__composed__ = False
    def __compose__(self, request):
        if self.__composed__:
            raise AlreadyComposedException
        self.__children__ = [compose(child, request) for child in self.__children__]
        self.__composed__ = True
        return self
    def __render__(self):
        """ Return proper xhp markup. Don't implement this and return non-self from __compose__() """
        raise NotImplementedError

    BUILT_IN_TYPES = set((type(None), int, float, basestring, bool, str, unicode))
    @classmethod
    def convert_to_node(cls, value):
        if hasattr(value, 'to_node'):
            value = value.to_node()
        elif hasattr(value, 'to_xss_html'):
            value = XSSNode(value.to_xss_html())
        elif hasattr(value, 'to_html_string'):
            value = StringNode(value.to_html_string())
        elif isinstance(value, list) or isinstance(value, tuple):
            g = BaseNode()
            for c in value:
                g.add_child(c)
            value = g
        elif type(value) in cls.BUILT_IN_TYPES:
            if value is None:
                value = ""
            value = StringNode(unicode(value))
        elif not isinstance(value, ProtoNode):
            raise ValueError("Could not insert %r into tree" % value)
        return value
    def __getitem__(self, children):
        """ Syntactic sugar to add children """
        return self.add_child(children)
    def add_child(self, children):
        if not isinstance(children, tuple) and not isinstance(children, list):
            children = (children,)
        # need to convert children
        for child in children:
            self.__children__.append(self.convert_to_node(child))
        return self
    @classmethod
    def render(cls, node, request):
        node = cls.convert_to_node(node)
        node = compose(node, request)
        return node.__render__()

class BaseNode(ProtoNode):
    # aka group
    def __render__(self):
        """ Group node only renders its children """
        if not self.__composed__:
            raise NotComposedException
        # TODO: does it make sense to use __render__() and not __compose__()?
        # TODO: does it make sense to pass the request thru here and not just in __compose__()?
        return "".join(child.__render__() for child in self.__children__)

class StringNode(BaseNode):
    def __init__(self, value):
        BaseNode.__init__(self)
        self.value = value
    def __str__(self):
        return "<StringNode %r>" % self.value
    def __render__(self):
        return cgi.escape(gettext.gettext(self.value))
    def __getitem__(self, children):
        raise ValueError, "Can't add children to a string"

class XSSNode(StringNode):
    """ If you want an XSS vulnerability, use this. """
    def __str__(self):
        return '<XSSNode %r>' % self.value
    def __render__(self):
        return self.value

class HTMLNode(BaseNode):
    def __init__(self, tag, **attrs):
        BaseNode.__init__(self)
        self.tag = tag
        self.attrs = attrs
    def add_attribute(self, key, value):
        self.attrs[key] = value
        return self
    def __str__(self):
        return "<HTMLNode %s %r>" % (self.tag, self.attrs)
    def __compose__(self, request):
        BaseNode.__compose__(self, request)
        # compose attributes too
        self.attrs = dict([(k, compose(ProtoNode.convert_to_node(v), request)) for (k, v) in self.attrs.items()])
        return self
    def __render__(self):
        node = self
        if node.attrs:
            # TODO: use real quoting
            attrs = " " + " ".join("%s=%s" % (k, macros.quote(v.__render__())) for (k, v) in node.attrs.items())
        else:
            attrs = ""
        if not node.__children__:
            # render single tag
            return "<%s%s />" % (node.tag, attrs)
        else:
            # render close/open
            return "<%s%s>%s</%s>" % (node.tag, attrs, BaseNode.__render__(self), node.tag)

class HTMLCommentNode(BaseNode):
    def __init__(self, value=None):
        BaseNode.__init__(self)
        if value:
            self.add_child(value)
    def __str__(self):
        return "<HTMLCommentNode>"
    def __render__(self):
        return "<!--%s-->" % BaseNode.__render__(self)

class HTMLDeclNode(ProtoNode):
    def __init__(self, data):
        ProtoNode.__init__(self)
        self.data = data
    def __str__(self):
        return "<HTMLDeclNode %r>" % self.data
    def __render__(self):
        return "<!%s>" % self.data

class HTMLPINode(ProtoNode):
    def __init__(self,  data):
        ProtoNode.__init__(self)
        self.data = data
    def __str__(self):
        return "<HTMLPINode %r>" % self.data
    def __render__(self):
        return "<?%s>" % self.data

class HTMLNodeFactory(object):
    def __init__(self):
        self._types = {}
    def __getattribute__(self, tag):
        try:
            return object.__getattribute__(self, tag)
        except:
            pass
        tag = tag.lower()
        if isinstance(tag, tuple):
            tag = ":".join(tag)

        class ClosureNode(HTMLNode):
            def __init__(self, **attrs):
                HTMLNode.__init__(self, tag, **attrs)
        self._types[tag] = ClosureNode
        return self._types[tag]

HTML = HTMLNodeFactory()

# a few browsers get confused when you do the short-close syntax. WHY? i don't know!
# i.e. <script />
class HTMLNoShortNode(HTMLNode):
    def __init__(self, *args, **kwargs): 
        HTMLNode.__init__(self, *args, **kwargs)
    def __compose__(self, request):
        if not self.__children__:
            # force tag to have a close tag
            self.add_child("")
        return HTMLNode.__compose__(self, request)

class HTMLScriptNode(HTMLNoShortNode):
    ''' dont do <script /> '''
    def __init__(self, **attrs):
        HTMLNode.__init__(self, 'script', **attrs)

class HTMLDivNode(HTMLNoShortNode):
    ''' dont do <div /> '''
    def __init__(self, **attrs):
        HTMLNode.__init__(self, 'div', **attrs)

class HTMLTextareaNode(HTMLNoShortNode):
    ''' dont do <textarea /> '''
    def __init__(self, **attrs):
        HTMLNoShortNode.__init__(self, 'textarea', **attrs)

HTML.script = HTMLScriptNode
HTML.div = HTMLDivNode
HTML.textarea = HTMLTextareaNode

def pprint(node, nesting=""):
    print nesting + unicode(node)
    for child in node.__children__:
        pprint(child, nesting + "  ")

def render(node, request=None):
    return ProtoNode.render(node, request)
