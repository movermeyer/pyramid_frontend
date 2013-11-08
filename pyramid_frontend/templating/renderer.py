from __future__ import absolute_import, print_function, division

import sys

from mako import exceptions
from pyramid.compat import reraise
from pyramid.mako_templating import MakoRenderingException


class MakoRenderer(object):

    def __init__(self, info, clear_default_filters=False):
        self.name = info.name
        self.clear_default_filters = clear_default_filters

    def __call__(self, value, system):
        """Find and render a template.

        This replaces the default Mako renderer to locate templates by theme.

        ``system`` will contain default renderer globals plus those added by
        by :func:`add_renderer_globals`.

        ``value`` will be either the dict returned from a view or the dict
        passed to one of Pyramid's render functions. These values will
        override the ``system`` values.

        :func:`add_renderer_globals` will be called to update ``system``
        before this method is called; it can access ``value`` via
        ``event.rendering_val``.

        """
        # Avoid conflict between Pyramid and Mako ``context``s
        system['_context'] = system.pop('context', None)

        try:
            system.update(value)
        except (TypeError, ValueError):
            raise ValueError('renderer was passed non-dictionary as value')

        request = system['request']

        theme = request.theme
        if self.clear_default_filters:
            lookup = theme.lookup_nofilters
        else:
            lookup = theme.lookup

        template = lookup.get_template(self.name)

        try:
            result = template.render_unicode(**system)
        except:
            try:
                exc_info = sys.exc_info()
                errtext = exceptions.text_error_template().render(
                    error=exc_info[1],
                    traceback=exc_info[2])
                reraise(MakoRenderingException(errtext), None, exc_info[2])
            finally:
                del exc_info

        return result


def mako_renderer_factory(info):
    return MakoRenderer(info)


def mako_renderer_factory_nofilters(info):
    return MakoRenderer(info, clear_default_filters=True)
