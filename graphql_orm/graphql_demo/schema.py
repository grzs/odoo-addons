# coding: utf-8

# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# disable undefined variable error, which erroneously triggers
# on forward declarations of classes in lambdas
# pylint: disable=E0602

import graphene
import re
import os
import json

# from odoo import SUPERUSER_ID
# from odoo import registry as odoo_registry
# from odoo.api import Environment
from odoo import _
from odoo.exceptions import UserError

from odoo.addons.graphql_base import OdooObjectType

# baked in data
fields_file = os.path.expanduser('~/.config/graphql_fields.json')
with open(fields_file, 'r') as f:
    fields_json = json.loads(f.read())

model_names = [
    'product.template',
    'product.product',
    'res.partner',
]

domain_operators = [
    '=',
    '!=',
    '>',
    '>=',
    '<',
    '<=',
    '=?',
    '=like',
    'like',
    'not like',
    'ilike',
    'not ilike',
    '=ilike',
    'in',
    'not in',
    # 'child_of',
    # 'parent_of',
]


def _serialize_domain(domain):
    domain_odoo = []
    if not domain:
        return domain_odoo

    for d in domain:
        if d.o not in domain_operators:
            continue

        value = None
        for v in [d.v, d.v_int, d.v_float, d.v_bool,
                  d.v_list_str, d.v_list_int, d.v_list_float]:
            if v is not None:
                value = v
                break

        if value is None:
            continue

        criterion = (d.f, d.o, value)

        if d.logical in ['&', '|', '!']:
            domain_odoo.append(d.logical)

        domain_odoo.append(criterion)

    return domain_odoo


def _serialize_context(context):
    context_odoo = {}
    for c in context:
        if c.type == OdooType.STR:
            value = c.value
        elif c.type == OdooType.INT:
            value = int(c.value)
        elif c.type == OdooType.FLOAT:
            value = float(c.value)
        elif c.type == OdooType.BOOL:
            value = bool(c.value)
        elif c.type == OdooType.LAMBDA:
            pattern = '^lambda [a-z]+[a-z0-9]*:'
            if re.match(pattern, c.value):
                value = eval(c.value)
            else:
                raise UserError(
                    _(f"'{c.value}' is not a valid lambda expression!"))

        context_odoo.update({c.key: value})
    return context_odoo


class OdooType(graphene.Enum):
    STR = 1
    INT = 2
    FLOAT = 3
    BOOL = 4
    LST_STR = 5
    LST_INT = 6
    LST_FLOAT = 7
    RECORDSET = 8
    LAMBDA = 9


class DomainItem(graphene.InputObjectType):
    f = graphene.String(required=True)
    o = graphene.String(required=True)
    v = graphene.String()
    v_int = graphene.Int()
    v_float = graphene.Float()
    v_bool = graphene.Boolean()
    v_list_str = graphene.List(graphene.String)
    v_list_int = graphene.List(graphene.Int)
    v_list_float = graphene.List(graphene.Float)
    logical = graphene.String()


class ContextItem(graphene.InputObjectType):
    key = graphene.String(required=True)
    value = graphene.String(required=True)
    type = graphene.Field(OdooType, required=True)


# resolvers
def resolve_context(parent, info, **kw):
    env = info.context['env']
    context = env.context.copy()
    if kw.get('apikey'):
        user_id = env['res.users.apikeys']._check_credentials(
            scope='graphql', key=kw['apikey'])
        context.update({'uid': user_id})

    if kw.get('context'):
        context.update(_serialize_context(kw['context']))

    return str(context)


def resolve_company_ids(root, info):
    return [c.id for c in info.context['env'].companies]


# type factory
def _get_recordset(env, name=None, limit=None, offset=None, **kw):
    context = env.context.copy()

    try:
        model = env[name]
    except KeyError:
        raise UserError(_(f"No such model: '{name}'"))

    if kw.get('apikey'):
        user_id = env['res.users.apikeys']._check_credentials(
            scope='graphql', key=kw['apikey'])
        context.update({'uid': user_id})
        model = model.with_user(user_id)

    if kw.get('company'):
        model = model.with_company(kw['company'])

    if kw.get('context'):
        context.update(_serialize_context(kw['context']))

    model = model.with_context(context)
    if kw.get('ids'):
        return model.browse(kw['ids'])
    else:
        domain_odoo = _serialize_domain(kw.get('domain'))
        return model.search(domain_odoo, limit=limit, offset=offset)


def _get_model_fields(model_name):
    fields = fields_json.get(model_name)
    # fields = None
    # registry = odoo_registry()
    # if model_name in registry.keys():
    #     with registry.cursor() as cr:
    #         uid = SUPERUSER_ID
    #         model = Environment(cr, uid, {})[model_name]
    #         fields = model.fields_get(attributes=['type'])
    #         cr.rollback()
    return fields


def _get_common_fields(model_name):
    fields = {}
    fields.update({
        'id': graphene.ID(),
        'name': graphene.String(),
    })
    return fields


def _graphql_field_factory(odoo_type):
    if odoo_type in ['char', 'text']:
        return graphene.String()
    elif odoo_type == 'integer':
        return graphene.Int()
    elif odoo_type == 'float':
        return graphene.Float()
    elif odoo_type == 'boolean':
        return graphene.Boolean()
    else:
        return None


def _graphql_type_factory(model_names):
    global odoo_types
    query_params = {}
    for m in model_names:
        type_fields = _get_common_fields(m)
        for k, v in _get_model_fields(m).items():
            if k == 'id':
                continue
            field = _graphql_field_factory(v.get('type'))
            if field:
                type_fields.update({k: field})
        classname = ''.join([sm.capitalize() for sm in m.split('.')])
        odoo_types[m] = type(classname, (OdooObjectType, ), type_fields)

        # query parameters
        field_name = '_'.join(m.split('.'))
        resolver_name = f'resolve_{field_name}'

        def resolver(parent, info, name=m, limit=None, offset=None, **kw):
            env = info.context['env']
            return _get_recordset(
                env, name=name, limit=limit, offset=offset, **kw)

        query_params.update({
            field_name: graphene.List(
                graphene.NonNull(odoo_types[m]),
                required=True,
                apikey=graphene.String(),
                company=graphene.Int(),
                context=graphene.List(graphene.NonNull(ContextItem)),
                ids=graphene.List(graphene.Int),
                domain=graphene.List(graphene.NonNull(DomainItem)),
                limit=graphene.Int(),
                offset=graphene.Int(),
            ),
            resolver_name: resolver,
        })
    return query_params


# query opject
query_params = {
    # fields
    'context': graphene.Field(
        graphene.String,
        apikey=graphene.String(),
        context=graphene.List(graphene.NonNull(ContextItem))),
    'company_ids': graphene.List(graphene.Int),

    # resolvers
    'resolve_context': resolve_context,
    'resolve_company_ids': resolve_company_ids,
}

odoo_types = {}
query_params.update(_graphql_type_factory(model_names))

Query = type('Query', (graphene.ObjectType, ), query_params)
schema = graphene.Schema(query=Query)


def update_schema():
    params_extra = _graphql_type_factory(model_names)
    if len(params_extra):
        global query_params
        global Query
        global schema
        query_params.update(params_extra)
        Query = type('Query', (graphene.ObjectType, ), query_params)
        schema = graphene.Schema(query=Query)
