# coding: utf-8

import functools

from odoo.http import route as odoo_http_route
from odoo import http, models

import opentracing
from jaeger_client.tracer import Tracer
from odoo.addons.jaeger_tracer.utils import init_tracer


def route_patched(route=None, **kw):
    def decorator(f):
        @functools.wraps(f)
        @odoo_http_route(route, **kw)
        def route_wrapper(*args, **kwargs):
            # initialize tracer object if needed
            if not isinstance(opentracing.tracer, Tracer):
                init_tracer()

            tracer = opentracing.tracer
            with tracer.start_active_span(f.__name__) as scope:
                scope.span.set_tag('odoo.module', f.__module__)
                if f.__doc__:
                    scope.span.log_kv({'event': f.__doc__})
                # get handler result
                res = f(*args, **kwargs)

                # add qcontext items to trace tags
                if hasattr(res, 'qcontext'):
                    for key, value in res.qcontext.items():
                        if isinstance(value, models.AbstractModel) and len(value) == 1:
                            scope.span.set_tag(
                                'odoo.response.qcontext.{}.name'.format(key), value.name)

                        value_str = str(value)
                        scope.span.set_tag(
                            'odoo.response.qcontext.{}'.format(key), value_str)

            return res
        return route_wrapper
    return decorator


def monkey_patch_odoo_http_route():
    # extend the docstring
    doc_template = "-- Monkey patched version of decorator 'odoo.http.route' --\n\n{}"
    route_patched.__doc__ = doc_template.format(http.route.__doc__)

    # replace the function
    http.route = route_patched
