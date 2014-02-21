from kso_site import app

@app.path(path='')
class Root(object):
    pass

@app.html(model=Root)
def hello_root(self, request):
    return u'<h1>Hello World</h1>'

