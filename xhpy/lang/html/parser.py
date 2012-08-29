import HTMLParser
import re
import htmlentitydefs
from xhpy.lang.html import ast
from xhpy import macros

RE_STARTTAG = re.compile(r"^<([^\s>]+)")

htmlentitydefs.name2codepoint["apos"] = 39
htmlentitydefs.codepoint2name[39] = "apos"

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

class HTMLEvaluator(HTMLParser.HTMLParser):
    MACRO_TYPE = 'html'

    def __init__(self, env, code, node_factory=None):
        HTMLParser.HTMLParser.__init__(self)
        self.env = env
        self.stack = [(None, {}, [])]
        if node_factory:
            self.node_factory = node_factory
        self.feed(code)

    def name_to_classname(self, name):
        return name + "Node"

    def node_factory(self, name):
        if ":" not in name:
            # fallback to regular HTML
            return self.env.get(self.name_to_classname(name), getattr(ast.HTML, name))
        else:
            names = name.split(":")
            names[-1] = self.name_to_classname(names[-1])
            try:
                root = self.env[names[0]]
                while len(names) > 1:
                    names = names[1:]
                    root = getattr(root, names[0])
                return root
            except AttributeError:
                raise KeyError, "Could not find XHP node %s" % name
            except KeyError:
                raise KeyError, "Could not find XHP node %s" % name

    def handle_starttag(self, tag, attrs):
        # fetch the correct case
        tag = RE_STARTTAG.match(self.get_starttag_text()).group(1)
        self.stack.append((tag, attrs, []))

    def handle_data(self, data):
        self.stack[-1][2].append(self.evaluate_expr(data))

    def handle_endtag(self, tag):
        new_tag, attrs, children = self.stack.pop()
        assert tag == new_tag.lower(), "Unmatched start/end tags: %s %s" % (tag, new_tag)
        tag = new_tag
        attrs = self.evaluate_attrs(attrs)
        self.stack[-1][2].append(self.node_factory(tag)(**attrs)[tuple(children)])

    def handle_charref(self, name):
        return self.handle_data(unescape('&#' + name + ';'))

    def handle_entityref(self, name):
        return self.handle_data(unescape('&' + name + ';'))

    def handle_comment(self, data):
        self.stack[-1][2].append(ast.HTMLCommentNode(data))

    def handle_decl(self, decl):
        self.stack[-1][2].append(ast.HTMLDeclNode(decl))

    unknown_decl = handle_decl

    def handle_pi(self, data):
        self.stack[-1][2].append(ast.HTMLPINode(data))

    def evaluate_attrs(self, attrs):
        return dict([(k, self.flatten_attr(self.evaluate_expr(v, True))) for (k, v) in attrs])

    def flatten_attr(self, attr):
        """ attrs should be passed as primitives whenever possible """
        if not isinstance(attr, ast.BaseNode):
            return attr
        if len(attr.__children__) == 1:
            return self.flatten_attr(attr.__children__[0])
        if isinstance(attr, ast.StringNode):
            return attr.value

    def evaluate_expr(self, expr, allow_native=False):
        # preparse the text
        tokens = macros.RE_INLINE.split(expr)
        children = []
        for i, token in enumerate(tokens):
            if i % 2 == 0:
                # static text
                children.append(token)
            else:
                # variable
                # TODO: we could make the language more powerful by doing a full python eval()
                # here, but that might be considered bad practice.
                try:
                    children.append(eval(token, self.env))
                except KeyError:
                    line, col = self.getpos()
                    raise KeyError, "Invalid token at line %d, character %d of HTML fragment: %s" % (line, col, token)

        if len(children) == 3 and children[0] == '' and children[2] == '' and allow_native:
            # this allows us to pass through attributes without converting them to xhp
            return children[1]
        return ast.BaseNode()[children]

    @classmethod
    def evaluate(cls, env, code):
        e = cls(env, code.strip())
        r = e.stack[0][2]
        if len(r) > 1:
            return ast.BaseNode()[r]
        return r[0]

    @classmethod
    def xss(cls, s):
        return ast.XSSNode(s)

    @classmethod
    def string(cls, s):
        return ast.StringNode(s)

macros.MacroManager.get_instance().register(HTMLEvaluator)

