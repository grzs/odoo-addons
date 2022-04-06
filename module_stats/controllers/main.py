# coding: utf-8
import re
from odoo import modules, registry
from odoo.models import Model
from odoo.http import request, route, Controller


class ModuleStats(Controller):
    @route('/module_stats/stats', type='http', auth='user', website=True)
    def stats(self, **kwargs):
        return request.render('module_stats.stats')

    @route('/module_stats/json', type='json', auth='user')
    def fetch(
            self, pattern=None,
            get_models=False, get_fields=False, get_ids=False
    ):
        mods = request.env['ir.module.module'].sudo().search(
            [('state', '=', 'installed')])
        if pattern:
            mods = mods.filtered(
                lambda r: re.search(pattern, modules.get_module_path(r.name)))

        mod_map = {
            mod.name: {
                'path': modules.get_module_path(mod.name),
                'dependencies': mod.dependencies_id.mapped('name'),
                'menus': self.parse_recordstr(mod.menus_by_module),
                'reports': self.parse_recordstr(mod.reports_by_module),
                'views': self.parse_recordstr(mod.views_by_module),
                'models': {},
            } for mod in mods
        }

        if not get_models:
            return mod_map

        # get model stats for modules
        reg = registry()
        for model_name, model_class in reg.models.items():
            # get a map with model fields with list of related modules
            fields_modules = {}
            if get_fields:
                fields = request.env['ir.model.fields'].sudo().search(
                    [('model', '=', model_name)])
                fields_modules = {f.name: f.modules.split(', ') for f in fields}

            # iterating over the mro to find related modules
            for c in model_class.__mro__:
                # it has to be a subclass of odoo.models.Model,
                # but not Model itself nor the registry item
                if (issubclass(c, Model) and
                    not c._transient and
                    c not in [model_class, Model]):
                    # getting a list of inherited models
                    inherit = (c._inherit if isinstance(c._inherit, list)
                               else [c._inherit])
                    # collect data if found module
                    if c._module in mod_map.keys():
                        records = (
                            request.env[model_name].sudo().search([]).ids
                            if get_ids else
                            request.env[model_name].sudo().search_count([])
                        )
                        mod_map[c._module]['models'][model_name] = {
                            'is_extended':
                            not bool(c._name and c._name not in inherit),
                            'classname': c.__name__,
                            'inherits': inherit,
                            'fields':[
                                f for f, mods in fields_modules.items()
                                if c._module in mods
                            ],
                            'records': records,
                        }

        return mod_map

    def parse_recordstr(self, recordstr):
        if len(recordstr) <= 0:
            return []

        res = []
        p = re.compile(r'^(\* INHERIT )?([^()]*)( \((.*)\))?$')
        for r in recordstr.split('\n'):
            match = p.match(r)
            res.append({
                'is_extended': bool(p.match(r).group(1)),
                'name': p.match(r).group(2),
                'type': p.match(r).group(4),
            })

        return res
