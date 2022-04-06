# -*- coding: utf-8 -*-
{
    'name': "Module Stats",

    'summary': """
        Display installed apps statistics (dependencies, models, fields, views, etc.)
        and export them to spreadsheet document.""",

    'description': """
        Display installed apps statistics (dependencies, models, fields, views, etc.)
        and export them to spreadsheet document.
    """,

    'author': "grzs",
    'category': 'Base',
    'version': '0.1',
    'depends': ['portal'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        'views/templates.xml',
    ],
}
