from morepath.app import App
from morepath import setup
from morepath.request import Response
from werkzeug.test import Client


def test_view_predicates():
    config = setup()
    app = App(testing_config=config)

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root, name='foo', request_method='GET')
    def get(self, request):
        return 'GET'

    @app.view(model=Root, name='foo', request_method='POST')
    def post(self, request):
        return 'POST'

    config.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'GET'
    response = c.post('/foo')
    assert response.data == 'POST'


def test_extra_predicates():
    config = setup()
    app = App(testing_config=config)

    @app.path(path='{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.view(model=Model, name='foo', id='a')
    def get_a(self, request):
        return 'a'

    @app.view(model=Model, name='foo', id='b')
    def get_b(self, request):
        return 'b'

    @app.predicate(name='id', order=2, default='')
    def get_id(self, request):
        return self.id
    config.commit()

    c = Client(app, Response)

    response = c.get('/a/foo')
    assert response.data == 'a'
    response = c.get('/b/foo')
    assert response.data == 'b'
