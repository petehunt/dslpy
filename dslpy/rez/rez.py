import orderedset
from dslpy.lang import html

import urlparse
import re

RE_REQUIRE = re.compile(r"@require_static\((?P<path>.*?)\)")

class HTMLHeadNode(html.HTMLNode):
    def __init__(self, **attrs):
        html.HTMLNode.__init__(self, 'head', **attrs)
        self.request = None
    def __compose__(self, request):
        html.HTMLNode.__compose__(self, request)
        self.request = request # we need this at render time
        return self
    def __render__(self):
        children = []
        for filename in self.request.get_statics():
            basename = urlparse.urlparse(filename).path
            # TODO: change this up; this is stupid.
            if basename.endswith(".js"):
                children.append(<?html <script type="text/javascript" src="${filename}"></script> ?>)
            elif basename.endswith(".css"):
                children.append(<?html <link rel="stylesheet" type="text/css" href="${filename}" /> ?>)
            else:
                assert False, "Got bad extension: " + basename
            children.append(html.StringNode("\n"))

        for script in self.request.get_scripts():
            children.append(<?html <script type="text/javascript">${script}</script> ?>)
        # since we are adding children at render time, they must be composed before rendering
        # the only reason we are doing this is that we need the entire tree to be traversed to populate request
        for child in children:
            self.add_child(html.compose(child, self.request))
        return html.HTMLNode.__render__(self)

html.HTML.head = HTMLHeadNode

class Request(object):
    def __init__(self):
        self.statics = orderedset.OrderedSet()
        self.scripts = []

    def _translate_path(self, path):
        return path

    def _preprocess_requires(self, path):
        with open(path, "r") as f:
            requires = RE_REQUIRE.findall(f.read())
        for filename, in requires:
            if filename[0] == '"' or filename[0] == "'":
                filename = filename[1:-1] # strip quotes
            self.require_static(path)

    def require_static(self, path):
        self._preprocess_requires(path)
        self.statics.add(self._translate_path(path))

    def require_script(self, script):
        self.scripts.append(script)

    def get_statics(self):
        return self.statics

    def get_scripts(self):
        return self.scripts

def render(node, translate_path=lambda path: path):
    request = Request()
    request._translate_path = translate_path
    return html.render(node, request)

