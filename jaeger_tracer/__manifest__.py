# -*- coding: utf-8 -*-
{
    'name': "Jaeger Tracer Client",
    'summary': "Simple module to initialize the global tracer object.",
    'author': "János Gerzson (@grzs)",
    'website': "https://github.com/grzs/odoo-addons/tree/14.0/jaeger_tracer",
    'license': 'LGPL-3',
    'category': 'Technical',
    'version': '0.1',
    'depends': ['base'],
    'data': [],
    'external_dependencies': {
        'python': [
            'jaeger_client',
            'yaml'
        ]
    },
}
