import morepath
import os
from chameleon import PageTemplateLoader

path = os.path.dirname(__file__)
templates = PageTemplateLoader(os.path.join(path, "templates"))
app = morepath.App()

class BaseModel(object):

    def template_vars(self, request=None):
        output =  {
            'main_template': templates['main_template.pt'],
            'context': self,
            'static_url': '/static/',
            'application_url': request.application_url,
        }
        if request:
            output['static_url'] = os.path.join(request.application_url,'static')
        return output

class template(object):

    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        def render(context, request):
            result = func(context, request) or {}
            return templates[self.name](options=result,
                    **context.template_vars(request))
        render.__name__ = func.__name__
        return render
