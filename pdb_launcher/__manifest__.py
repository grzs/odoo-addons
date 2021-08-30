# -*- coding: utf-8 -*-
{
    'name': "Pdb Launcher",

    'summary': """Simple module to run a python debugger
    with a set of breakpoints.""",

    'description': """Simple module to run a python debugger.
    Several named launchers can be saved with different set of breakpoints.
    The module takes care about the installation path of the selected
    module, only a relative file path and a line number need to be added.""",

    'author': "János Gerzson (@grzs)",
    'website': "https://github.com/grzs/odoo-addons/tree/12.0/pdb_launcher",
    'license': 'LGPL-3',
    'category': 'Technical',
    'version': '0.3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/default.xml'
    ],
}
