import urlparse
import urllib

def url(base, **kw):
  scheme,netloc,path,params,query,fragment = urlparse.urlparse(base)
  query = urllib.urlencode(urlparse.parse_qsl(query) + kw.items())
  return urlparse.urlunparse((scheme,netloc,path,params,query,fragment))

