import morepath
from morepath import setup
from morepath.request import Response
from werkzeug.test import Client
from morepath import generic
from morepath.security import (Identity, BasicAuthIdentityPolicy,
                               NO_IDENTITY)
from .fixtures import identity_policy
from werkzeug.datastructures import Headers
import base64
import json


def test_no_permission():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    class Permission(object):
        pass

    @app.path(model=Model, path='{id}',
              variables=lambda model: {'id': model.id})
    def get_model(id):
        return Model(id)

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    config.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.status == '401 UNAUTHORIZED'


def test_permission_directive():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    class Permission(object):
        pass

    @app.path(model=Model, path='{id}',
              variables=lambda model: {'id': model.id})
    def get_model(id):
        return Model(id)

    @app.permission(model=Model, permission=Permission)
    def get_permission(identity, model, permission):
        if model.id == 'foo':
            return True
        else:
            return False

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    @app.identity_policy()
    class IdentityPolicy(object):
        def identify(self, request):
            return Identity('testidentity')

        def remember(self, response, request, identity):
            pass

        def forget(self, response, request):
            pass

    config.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'Model: foo'
    response = c.get('/bar')
    assert response.status == '401 UNAUTHORIZED'


def test_policy_action():
    config = setup()
    config.scan(identity_policy)
    config.commit()

    c = Client(identity_policy.app, Response)

    response = c.get('/foo')
    assert response.data == 'Model: foo'
    response = c.get('/bar')
    assert response.status == '401 UNAUTHORIZED'


def test_basic_auth_identity_policy():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    class Permission(object):
        pass

    @app.path(model=Model, path='{id}',
              variables=lambda model: {'id': model.id})
    def get_model(id):
        return Model(id)

    @app.permission(model=Model, permission=Permission)
    def get_permission(identity, model, permission):
        return identity.userid == 'user' and identity.password == 'secret'

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    @app.identity_policy()
    def policy():
        return BasicAuthIdentityPolicy()

    config.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.status == '401 UNAUTHORIZED'

    headers = Headers()
    headers.add('Authorization', 'Basic ' + base64.b64encode('user:wrong'))
    response = c.get('/foo', headers=headers)
    assert response.status == '401 UNAUTHORIZED'

    headers = Headers()
    headers.add('Authorization', 'Basic ' + base64.b64encode('user:secret'))
    response = c.get('/foo', headers=headers)
    assert response.data == 'Model: foo'


def test_basic_auth_remember():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.path(path='{id}',
              variables=lambda model: {'id': model.id})
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.view(model=Model)
    def default(self, request):
        # will not actually do anything as it's a no-op for basic
        # auth, but at least won't crash
        response = Response()
        generic.remember(response, request, Identity('foo'),
                         lookup=request.lookup)
        return response

    @app.identity_policy()
    def policy():
        return BasicAuthIdentityPolicy()

    config.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.status == '200 OK'
    assert response.data == ''


def test_basic_auth_forget():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.path(path='{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.view(model=Model)
    def default(self, request):
        # will not actually do anything as it's a no-op for basic
        # auth, but at least won't crash
        response = Response()
        generic.forget(response, request, lookup=request.lookup)
        return response

    @app.identity_policy()
    def policy():
        return BasicAuthIdentityPolicy()

    config.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.status == '200 OK'
    assert response.data == ''
    assert sorted(response.headers.items()) == [
        ('Content-Length', '0'),
        ('Content-Type', 'text/plain; charset=utf-8'),
        ('WWW-Authenticate', 'Basic realm="Realm"'),
        ]


class DumbCookieIdentityPolicy(object):
    """A very insecure cookie-based policy.

    Only for testing. Don't use in practice!
    """
    def identify(self, request):
        data = request.cookies.get('dumb_id', None)
        if data is None:
            return NO_IDENTITY
        data = json.loads(base64.b64decode(data))
        return Identity(**data)

    def remember(self, response, request, identity):
        data = base64.b64encode(json.dumps(identity.as_dict()))
        response.set_cookie('dumb_id', data)

    def forget(self, response, request):
        response.delete_cookie('dumb_id')


def test_cookie_identity_policy():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.path(path='{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    class Permission(object):
        pass

    @app.permission(model=Model, permission=Permission)
    def get_permission(identity, model, permission):
        return identity.userid == 'user'

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    @app.view(model=Model, name='log_in')
    def log_in(self, request):
        response = Response()
        generic.remember(response, request, Identity(userid='user',
                                                     payload='Amazing'),
                         lookup=request.lookup)
        return response

    @app.view(model=Model, name='log_out')
    def log_out(self, request):
        response = Response()
        generic.forget(response, request, lookup=request.lookup)
        return response

    @app.identity_policy()
    def policy():
        return DumbCookieIdentityPolicy()

    config.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.status == '401 UNAUTHORIZED'

    response = c.get('/foo/log_in')

    response = c.get('/foo')
    assert response.status == '200 OK'
    assert response.data == 'Model: foo'

    response = c.get('/foo/log_out')

    response = c.get('/foo')
    assert response.status == '401 UNAUTHORIZED'
