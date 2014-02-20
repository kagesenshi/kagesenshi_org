from .path import Mount
from .request import Request
from .traject import Traject
from .config import Configurable
from .converter import ConverterRegistry
from .error import MountError
from reg import ClassRegistry, Lookup, CachingClassLookup
import venusian
from werkzeug.serving import run_simple


class AppBase(Configurable, ClassRegistry, ConverterRegistry):
    """Base for application objects.

    Extends :class:`morepath.config.Configurable`,
    :class:`reg.ClassRegistry` and
    :class:`morepath.converter.ConverterRegistry`.

    The application base is split from the :class:`App`
    class so that we can have an :class:`App` class that automatically
    extends from ``global_app``, which defines the Morepath framework
    itself.  Normally you would use :class:`App` instead this one.

    AppBase can be used as a WSGI application, i.e. it can be called
    with ``environ`` and ``start_response`` arguments.
    """
    def __init__(self, name='', extends=None, variables=None,
                 testing_config=None):
        """
        :param name: A name for this application. This is used in
          error reporting.
        :type name: str
        :param extends: :class:`App` objects that this
          app extends/overrides.
        :type extends: list, :class:`App` or ``None``
        :param variables: variable names that
          this application expects when mounted. Optional.
        :type variables: list or set
        :param testing_config: a :class:`morepath.Config` that actions
          are added to directly, instead of waiting for
          a scanning phase. This is handy during testing. If you want to
          use decorators inline in a test function, supply a ``testing_config``.
          It's not useful outside of tests. Optional.
        """
        ClassRegistry.__init__(self)
        Configurable.__init__(self, extends, testing_config)
        ConverterRegistry.__init__(self)
        self.name = name
        if variables is None:
            variables = set()
        self._variables = set(variables)
        self.traject = Traject()
        self._mounted = {}
        root_mount = None
        self._variables = variables or set()
        if not variables:
            self._app_mount = self.mounted()
        else:
            self._app_mount = FailingWsgi(self)
        self._cached_lookup = None
        # allow being scanned by venusian
        venusian.attach(self, callback)

    def __repr__(self):
        return '<morepath.App %r>' % self.name

    def clear(self):
        """Clear all registrations in this application.
        """
        ClassRegistry.clear(self)
        Configurable.clear(self)
        self.traject = Traject()
        self._cached_lookup = None
        self._mounted = {}

    def lookup(self):
        """Get the :class:`reg.Lookup` for this application.

        :returns: a :class:`reg.Lookup` instance.
        """
        # XXX use cached property instead?
        if self._cached_lookup is not None:
            return self._cached_lookup
        self._cached_lookup = result = Lookup(CachingClassLookup(self))
        return result

    def request(self, environ):
        """Create a :class:`Request` given WSGI environment.

        :param environ: WSGI environment
        :returns: :class:`morepath.Request` instance
        """
        request = Request(environ)
        request.lookup = self.lookup()
        return request

    def mounted(self, **context):
        """Create :class:`morepath.path.Mount` for application.

        :param kw: the arguments with which to mount the app.
        :returns: :class:`morepath.path.Mount` instance. This is
          a WSGI application.
        """
        for name in self._variables:
            if name not in context:
                raise MountError(
                    "Cannot mount app without context variable: %s" % name)
        return Mount(self, lambda: context, {})

    def __call__(self, environ, start_response):
        """This app as a WSGI application.

        This is only possible when the app expects no variables; if it
        does, use ``mount()`` to create a WSGI app first.
        """
        return self._app_mount(environ, start_response)

    def run(self, host=None, port=None, **options):
        """Use Werkzeug WSGI server to run application.

        :param host: hostname
        :param port: port
        :param options: options as for :func:`werkzeug.serving.run_simple`
        """
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 5000
        run_simple(host, port, self, **options)

    def mount_variables(self):
        return self._variables


class FailingWsgi(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        raise MountError("Cannot run WSGI app as this app requires "
                         "mount variables: %s" % ', '.join(
                self.app.mount_variables()))

class App(AppBase):
    """A Morepath-based application object.

    Extends :class:`AppBase` and through it
    :class:`morepath.config.Configurable`, :class:`reg.ClassRegistry`
    and :class:`morepath.converter.ConverterRegistry`.

    You can configure an application using Morepath decorator directives.

    An application can extend one or more other applications, if
    desired.  All morepath App's descend from ``global_app`` however,
    which contains the base configuration of the Morepath framework.

    Conflicting configuration within an app is automatically
    rejected. An extended app cannot conflict with the apps it is
    extending however; instead configuration is overridden.
    """
    def __init__(self, name='', extends=None, variables=None,
                 testing_config=None):
        """
        :param name: A name for this application. This is used in
          error reporting.
        :type name: str
        :param extends: :class:`App` objects that this
          app extends/overrides.
        :type extends: list, :class:`App` or ``None``
        :param variables: variable names that
          this application expects when mounted. Optional.
        :type variables: list or set
        :param testing_config: a :class:`morepath.Config` that actions
          are added to directly, instead of waiting for
          a scanning phase. This is handy during testing. If you want to
          use decorators inline in a test function, supply a ``testing_config``.
          It's not useful outside of tests. Optional.
        """
        if not extends:
            extends = [global_app]
        super(App, self).__init__(name, extends, variables, testing_config)
        # XXX why does this need to be repeated?
        venusian.attach(self, callback)


def callback(scanner, name, obj):
    scanner.config.configurable(obj)


global_app = AppBase('global_app')
"""The global app object.

Instance of :class:`AppBase`.

This is the application object that the Morepath framework is
registered on. It's automatically included in the extends of any
:class:`App`` object.

You could add configuration to ``global_app`` but it is recommended
you don't do so. Instead to extend or override the framework you can
create your own :class:`App` with this additional configuration.
"""
