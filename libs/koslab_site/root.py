from koslab_site import BaseModel, template
from koslab_site import app

@app.path(path='')
class Root(BaseModel):
    pass

@app.html(model=Root)
@template('index.pt')
def index(context, request):
    pass

