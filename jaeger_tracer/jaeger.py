# coding: utf-8

import functools
import opentracing
from jaeger_client.tracer import Tracer
from .utils import init_tracer


def span(_func=None, *,
         operation='', tags={}, log_kv={}):
    '''Decorator jaeger.span accepts the following arguments:
    operation (str) - operation name,
    tags (dict) - tag key/value pairs,
    log_kv (dict) - structured log, forwarded to the span
    '''

    def decorator_span(func):
        @functools.wraps(func)
        def _span(*args, **kwargs):
            # filling span properties
            _operation = func.__name__ if not operation else operation
            _tags, _log_kv = {}, {}
            _tags.update(tags)
            _log_kv.update(log_kv)

            if 'module' not in tags.keys():
                _tags['odoo.module'] = func.__module__
            if 'event' not in log_kv.keys() and func.__doc__:
                _log_kv['event'] = func.__doc__

            # initialize tracer object if needed
            if not isinstance(opentracing.tracer, Tracer):
                init_tracer()

            tracer = opentracing.tracer

            with tracer.start_active_span(_operation) as scope:
                # set tags for span
                for _ in _tags.items():
                    scope.span.set_tag(_[0], _[1])
                # set log for span
                scope.span.log_kv(_log_kv)

                ret = func(*args, **kwargs)

            return ret
        return _span

    # this is needed if no arguments passed
    if _func is None:
        return decorator_span
    else:
        return decorator_span(_func)
