from xhpy.lang import html, js
from xhpy import rez

class HeaderNode(html.BaseNode):
  def __init__(self, title):
    html.BaseNode.__init__(self) # must call parent constructor always
    self.title = title # do whatever implementation-specific stuff you want here.
  def __compose__(self, request):
    # compose the children by calling superclass
    html.BaseNode.__compose__(self, request)
    request.require_script(<?js alert("My name is " + ${self.title}); ?>)
    return <?html
<html>
  <head>
    <title>${self.title}</title>
  </head>
  <body>
    <h1>${self.title}</h1>
    ${self.__children__}
  </body>
</html> ?>

name = "<b>Pete</b>" # XSS

page = <?html
<Header title="This is a test">
  <p>Hello, world! My name is ${name}!</p>
</Header> ?>

print rez.render(page)
