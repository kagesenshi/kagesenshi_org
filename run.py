import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__),'libs'))

import kso_site 
import morepath
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.serving import run_simple

HOST='127.0.0.1'
PORT=5000

config = morepath.setup()
config.scan(package=kso_site)
config.commit()
app = SharedDataMiddleware(
        kso_site.app, {
            '/static': os.path.join(os.path.dirname(__file__), 'wsgi/static')
        }
)

run_simple(HOST, PORT, app)
