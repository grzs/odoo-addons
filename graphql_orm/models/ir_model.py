# coding: utf-8

from odoo import models, fields


class IrModel(models.Model):
    _inherit = 'ir.model'

    graphql = fields.Boolean()
