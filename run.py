import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__),'libs'))

import kso_site , koslab_site
import morepath
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.serving import run_simple
import wfront

HOST='127.0.0.1'
PORT=5000

config = morepath.setup()
config.scan(package=kso_site)
config.scan(package=koslab_site)
config.commit()
kso_app = SharedDataMiddleware(
        kso_site.app, {
            '/static': os.path.join(os.path.dirname(__file__), 'wsgi/static')
        }
)

koslab_app = SharedDataMiddleware(
        koslab_site.app, {
            '/static': os.path.join(os.path.dirname(__file__), 'wsgi/static')
        }
)

mapping = [('kso.local', kso_app, None), ('koslab.local', koslab_app, None)]

router = wfront.route(mapping)

run_simple(HOST, PORT, router)
