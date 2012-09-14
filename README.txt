== dslpy overview ==

This framework was extracted from best practices at Facebook and has been thouroughly
thought out and used in production in a mobile/www geolocation app.

dslpy provides the following capabilities:
  * Domain-specific language syntax: using <?lang ... ?>, you can insert arbitrary languages inline
    with Python and treat them as expressions. This can be extended with plugins known as macros.
  * A complete implementation of HTML syntax and generation that allows for modular code reuse
  * Partial implementations of other languages (js, css, shell, sql)
  * A dependency-management system for including files (dslpy.rez)

I chose to use the <?html ?> syntax because it's arguably cleaner and, more importantly,
forbids string concatenation. With a function call one could still override the escaping
using raw string concatenation; not so with the custom syntax. I understand that this is
controversial; with a simple script we can convert this to use strings or external files.

=== dslpy DSL syntax ===

To enable the import hook to allow this syntax, you must call dslpy.macros.install().

You can create your own macros, too. See a simple example at dslpy.lang.repr.

=== dslpy HTML tutorial ===
Use the <?html ... ?> to insert dslpy markup. When inserting a tag, dslpy will look at the
current environment to see if there is a *Node class that exists. i.e. this piece of
code:
{{{
<?html
  <html>
    <body>
      <MyComponent name="test" />
    </body>
  </html> ?>
}}}

is equivalent to this in Python:
{{{
root = htmlNode()
body = bodyNode()
body.add_child(MyComponentNode(name="test"))
root.add_child(body)
return root
}}}

Additionally, you can insert arbitrary Python expressions that will be evaluated,
converted to HTML tree via escaping and inserted into the tree. For example:
{{{
name = "<b>pete</b>"
adjective = <?html <b>cool</b> ?>
<?html <p>My name is ${name} and I am ${adjective}</p> ?>
}}}
Emits:
{{{
<p>My name is &lt;b&gt;pete&lt;/b&gt; and I am <b>cool</b></p>
}}}

=== dslpy internals ===

Let's dive into the specifics of how dslpy HTML works. You don't need to know the details
in order to work with dslpy; skip to the next section for more hands-on examples.

All custom components extend dslpy.lang.html.BaseNode. This class has a constructor
that takes arbitrary keyword arguments (i.e. <MyComponent x="test" /> will pass x as a
keyword argument). You must call the superclass constructor if you override it. The base
class has the following fun stuff:
  * add_child(): add a child
  * __children__: list of all children added to the node.

When you render an dslpy tree, you first need to compose each node. Each node has a
__compose__() method that returns a new dslpy node. This return value will effectively
replace this node in the document. You can imagine writing a custom component that returns
the basic HTML to render itself using this method.

However, if your custom component includes another custom component, it needs to compose
itself too. So dslpy will keep calling __compose__() on the tree until all that is left
is basic HTML. It knows when to stop because each dslpy node can be composed only once, and
since all the basic HTML nodes just return self from __compose__(), it knows to stop when
all the nodes have already been composed.

Most of the time when writing a custom component, you'll want to compose your children.
Just call dslpy.lang.html.BaseNode.__compose__() and it will replace __children__ with
their fully composed versions.

=== A super basic example ===

{{{
from dslpy.lang import html
class HeaderNode(html.BaseNode):
  def __init__(self, title):
    html.BaseNode.__init__(self) # must call parent constructor always
    self.title = title # do whatever implementation-specific stuff you want here.
  def __compose__(self, request):
    # compose the children by calling superclass
    html.BaseNode.__compose__(self, request)
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

class PageNode(html.BaseNode):
  def __compose__(self, request):
    return <?html
<HeaderNode title="This is a test">
  <p>Hello, world!</p>
</HeaderNode> ?>

print html.render(PageNode())
}}}

This prints:
{{{
<html>
  <head>
    <title>This is a test</title>
  </head>
  <body>
    <h1>This is a test</h1>
    <p>Hello, world!</p>
  </body>
</html>
}}}

Cool. Now you can be more advanced by constructing loops and if statements and stuff by
using add_child() and add_attribute() on HTML nodes to modify the tree easily.

=== rez: static resource management ===

Different subcomponents will require different css and js files to work. We only want to
include them once, sometimes we want to use cache busting, and we don't want to have to
centrally manage the dependencies at the top-level. dslpy.rez takes care of this.

You noticed the request argument to __compose__(). You can call require_static('file.css')
to require a static file be referenced in the head. You can override how this path is
resolved and it automatically determines how to insert the node (script tag or link tag)
based on file extension.

Additionally, your JavaScript or CSS may have dependencies on other JS or CSS files as
well. You can include a comment in your file of the form @require_static(path) to require
a resource be listed in the head as well.

If you pass require_static() a True second argument, it will automatically do cachebusting
for you.

Example based on above:
{{{
from dslpy.lang import html
from dslpy import rez
class HeaderNode(html.BaseNode):
  def __init__(self, title):
    html.BaseNode.__init__(self) # must call parent constructor always
    self.title = title # do whatever implementation-specific stuff you want here.
  def __compose__(self, request):
    # compose the children by calling superclass
    html.BaseNode.__compose__(self, request)
    request.require_static('test.js')
    request.require_static('style.css')
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

class PageNode(html.BaseNode):
  def __compose__(self, request):
    return <?html
<HeaderNode title="This is a test">
  <p>Hello, world!</p>
</HeaderNode> ?>

print rez.render(PageNode(), rez.Request())
}}}

This prints:
{{{
<html>
  <head>
    <title>This is a test</title>
    <script src='test.js' type='text/javascript'></script>
    <link rel='stylesheet' href='style.css' type='text/css' />
  </head>
  <body>
    <h1>This is a test</h1>
    <p>Hello, world!</p>
  </body>
</html>
}}}

Note that you can call require_static() in ANY subelement and it will still propagate to
the head element of the document.

=== (eye)spy rez extensions ===

eyespy.client.request adds some extra capabilities, like require_coffee() and
require_sass(). It not only adds the required files to the head, it compiles them if
needed and copies them to the build directory.
