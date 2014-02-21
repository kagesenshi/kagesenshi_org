from kso_site import app, BaseModel, template

@app.path(path='')
class Root(BaseModel):
    pass


@app.html(model=Root)
@template('index.pt')
def index(context, request):
    pass


@app.html(model=Root, name='about')
@template('about.pt')
def about(context, request):
    pass
