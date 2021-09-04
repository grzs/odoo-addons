# coding: utf-8

import functools
import opentracing.tracer


def span(_func=None, *,
         _operation='', _tags={}, _log_kv={}):
    '''Decorator jaeger.span accepts the following arguments:
    _operation (str) - operation name,
    _tags (dict) - tag key/value pairs,
    _log_kv (dict) - structured log, forwarded to the span
    '''

    def decorator_span(func):
        @functools.wraps(func)
        def _span(*args, **kwargs):
            # filling span properties
            tags = _tags
            log_kv = _log_kv
            operation = func.__name__ if not _operation else _operation

            if 'module' not in tags.keys():
                tags['module'] = func.__module__
            if 'event' not in log_kv.keys() and func.__doc__:
                log_kv['event'] = func.__doc__

            tracer = opentracing.tracer
            with tracer.start_active_span(operation) as scope:
                # set tags for span
                for _ in tags.items():
                    scope.span.set_tag(_[0], _[1])
                # set log for span
                scope.span.log_kv(log_kv)

                ret = func(*args, **kwargs)

            return ret
        return _span

    # this is needed if no arguments passed
    if _func is None:
        return decorator_span
    else:
        return decorator_span(_func)
