# -*- coding: utf-8 -*-

from sys import version_info
import os
from odoo import models, fields, api, addons
from odoo.exceptions import UserError


class PdbLauncher(models.Model):
    _name = 'pdb.launcher'
    _description = 'pdb.launcher'

    name = fields.Char()
    module = fields.Selection(
        string="Debugger Python module",
        selection=[('pdb', 'Pdb'), ('pudb', 'PuDB')],
        default='pdb',
        required=True)
    description = fields.Text()
    breakpoints = fields.One2many('pdb.breakpoint', 'launcher')

    def write_rcfile(self):
        '''writes breakpoint definitions to the debugger rc file'''
        if len(self) > 0:
            record = self[0]
            breakpoint_lines = record.breakpoints.get_lines()
            if breakpoint_lines:
                if record.module == 'pdb':
                    rcfile = os.path.expanduser('~/.pdbrc')
                elif record.module == 'pudb':
                    confdir = os.path.join(
                        os.environ['HOME'], '.config', 'pudb')
                    if not os.path.isdir(confdir):
                        os.makedirs(confdir, exist_ok=True)
                    rcfile = os.path.join(
                        confdir, 'saved-breakpoints-{}.{}'.format(
                            version_info.major, version_info.minor))
                else:
                    return False

                with open(rcfile, 'w') as f:
                    f.writelines(breakpoint_lines)
            else:
                return False
        else:
            return False

    def launch(self):
        '''calls the rc file writer method and launches python debugger'''
        if len(self) > 0:
            record = self[0]
            record.write_rcfile()
            if record.module == 'pdb':
                import pdb
                pdb.set_trace()
            elif record.module == 'pudb':
                try:
                    import pudb
                    pudb.set_trace()
                except ImportError:
                    raise(UserError(
                        "PuDB is not installed!"))
        else:
            return False


class PdbBreakpoint(models.Model):
    _name = 'pdb.breakpoint'
    _description = 'pdb.breakpoint'

    launcher = fields.Many2one(
        'pdb.launcher',
        ondelete='cascade',
        required=True)
    module = fields.Many2one(
        'ir.module.module',
        domain='[("state","=","installed")]',
        string='Odoo Module',
        ondelete='cascade',
        required=True)
    filename = fields.Char(
        string='Relative File Path',
        required=True)
    line_nr = fields.Integer('Line Number', required=True)
    description = fields.Text()

    def get_lines(self):
        '''returns a list of breakpoint directives'''
        breakpoints = []
        for record in self:
            if record.launcher.module == 'pdb':
                cmd = 'tbreak'
            else:
                cmd = 'b'

            module_path = eval(
                'addons.' + record.module.name + '.__path__')[0]
            breakpoints.append(
                '{} {}/{}:{}\n'.format(
                    cmd, module_path, record.filename, record.line_nr)
            )
        return breakpoints
