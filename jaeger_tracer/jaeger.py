# coding: utf-8

import functools
import opentracing.tracer


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
            _tags = tags
            _log_kv = log_kv
            _operation = func.__name__ if not operation else operation

            if 'module' not in _tags.keys():
                _tags['odoo.module'] = func.__module__
            if 'event' not in _log_kv.keys() and func.__doc__:
                _log_kv['event'] = func.__doc__

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