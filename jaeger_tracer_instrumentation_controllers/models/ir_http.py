# coding: utf-8

from odoo import models
from odoo.http import request

import opentracing
from jaeger_client.tracer import Tracer
from odoo.addons.jaeger_tracer.utils import init_tracer


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls):

        # initialize tracer object if needed
        if not isinstance(opentracing.tracer, Tracer):
            init_tracer()

        tracer = opentracing.tracer
        with tracer.start_active_span(request.httprequest.path) as scope:
            # set tags for span
            scope.span.set_tag('odoo.model', 'ir.http')
            scope.span.set_tag('odoo.model.method', '_dispatch')

            response = super(IrHttp, cls)._dispatch()

            scope.span.set_tag('odoo.response.status_code', response.status_code)
            scope.span.set_tag('odoo.response.mimetype', response.mimetype)

            keys_notag = [
                'request',
                'session_info',
                'menu_data'
            ]
            for key, value in response.qcontext.items():
                if isinstance(value, models.AbstractModel):
                    scope.span.set_tag(f'odoo.response.qcontext.{key}.name', value.name)
                elif key in keys_notag:
                    continue

                value_str = str(value)
                scope.span.set_tag(f'odoo.response.qcontext.{key}', value_str)

        return response
