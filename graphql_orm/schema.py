# coding: utf-8

# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# disable undefined variable error, which erroneously triggers
# on forward declarations of classes in lambdas
# pylint: disable=E0602

import graphene
import re

from odoo import registry, api, SUPERUSER_ID
from odoo import _
from odoo.exceptions import UserError
from odoo.addons.graphql_base import OdooObjectType


class Otype(graphene.Enum):
    STR = 1
    INT = 2
    FLOAT = 3
    BOOL = 4
    LST_STR = 5
    LST_INT = 6
    LST_FLOAT = 7
    LAMBDA = 8
    ORM = 9


class Oobject(graphene.InputObjectType):
    otype = graphene.Field(Otype)
    v = graphene.String()
    v_int = graphene.Int()
    v_float = graphene.Float()
    v_bool = graphene.Boolean()
    v_list_str = graphene.List(graphene.String)
    v_list_int = graphene.List(graphene.Int)
    v_list_float = graphene.List(graphene.Float)


class DomainItem(graphene.InputObjectType):
    logical = graphene.String()
    f = graphene.String(required=True)
    o = graphene.String(required=True)
    v = graphene.Field(Oobject, required=True)


class ContextItem(graphene.InputObjectType):
    k = graphene.String(required=True)
    v = graphene.Field(Oobject, required=True)


class GraphqlFactory():
    record_types = {}
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
        'child_of',
        'parent_of',
    ]

    @classmethod
    def _query_db(cls):
        field_tuples = []
        fields_to_query = ','.join([
            'model',
            'name',
            'ttype',
            'relation',
            'required'
        ])
        query_models = "SELECT model FROM ir_model WHERE graphql = 't'"
        query_fields = f"SELECT {fields_to_query} FROM ir_model_fields WHERE model IN ({query_models})"
        reg = registry()
        with reg.cursor() as cr:
            cr.execute(query_fields)
            field_tuples = cr.fetchall()
            cr.rollback()

        model_fields = {}
        for t in field_tuples:
            if t[0] not in model_fields.keys():
                model_fields.update({t[0]: []})
            model_fields[t[0]].append(t[1:])
        return model_fields

    @classmethod
    def _eval_domain(cls, domain):
        domain_odoo = []
        if not domain:
            return domain_odoo
        for d in domain:
            value = cls._eval_oobject(d.v)
            if value is None:
                continue
            criterion = (d.f, d.o, value)
            if d.logical in ['&', '|', '!']:
                domain_odoo.append(d.logical)
            domain_odoo.append(criterion)
        return domain_odoo

    @classmethod
    def _eval_context(cls, context):
        context_odoo = {}
        for c in context:
            value = cls._eval_oobject(c.v)
            if value is not None:
                context_odoo.update({c.k: value})
        return context_odoo

    @classmethod
    def _eval_oobject(cls, o):
        if o.otype is not None:
            if not o.v:
                raise UserError(_("'v' is required when 'otype' is given!"))
            if o.otype == Otype.STR:
                return o.v
            elif o.otype == Otype.INT:
                return int(o.v)
            elif o.otype == Otype.FLOAT:
                return float(o.v)
            elif o.otype == Otype.BOOL:
                return bool(o.v)
            elif o.otype == Otype.LAMBDA:
                pattern = '^lambda [a-z]+[a-z0-9]*:'
                if re.match(pattern, o.v):
                    return eval(o.v)
                else:
                    raise UserError(
                        _(f"'{o.v}' is not a valid lambda expression!"))
            elif o.otype == Otype.ORM:
                # regex pattern
                p_model = r"(([a-z][a-z\.]*[a-z])|[a-z])"
                p_context = r"\{('': ?.*)(, ?'': ?.*)*\}"
                p_with = rf".with_((user)|(company)|(context))\(([0-9]+|({p_context}))\)"
                p_field = r"(([a-z][a-z_]*[a-z])|[a-z])"
                p_fields = rf"{p_field}(.{p_field})*"
                p_ops = "|".join([f"({do})" for do in cls.domain_operators])
                p_domain_item = rf"('(!|&|\|)'|(\('{p_fields}','({p_ops})',.*\)))"
                p_domain = rf"{p_domain_item}(,{p_domain_item})*"
                p_search = rf"search\(\[({p_domain})*\]\)"
                p_browse = r"browse\(([0-9]+,)*([0-9]+)\)"
                pattern = rf"^env\['{p_model}'\]({p_with})*\.(({p_search})|({p_browse}))(\.{p_fields})?$"
                if re.match(pattern, o.v):
                    model_name = re.findall(p_model, o.v)[1][0]
                    reg = registry()
                    if model_name in reg.keys():
                        with reg.cursor() as cr:
                            env = api.Environment(cr, SUPERUSER_ID, {})
                            recordset = eval(o.v)
                            cr.rollback()
                        return recordset
                    else:
                        raise UserError(_(f"No such model: '{model_name}'"))
                else:
                    raise UserError(
                        _(f"'{o.v}' is not a valid ORM expression!"))

        # if otype not set
        for v in [o.v, o.v_int, o.v_float, o.v_bool,
                  o.v_list_str, o.v_list_int, o.v_list_float]:
            if v is not None:
                return v
        return None

    # factory methods
    @classmethod
    def _make_field_type(cls, odoo_type):
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

    @classmethod
    def _make_record_type(cls, model_name, fields):
        type_params = {'id': graphene.ID()}
        for t in fields:
            f_name, f_ttype, f_relation, f_required = t
            if f_name == 'id':
                continue
            field = cls._make_field_type(f_ttype)
            if field:
                type_params.update({f_name: field})

        type_name = ''.join([s.capitalize() for s in model_name.split('.')])
        return type(type_name, (OdooObjectType, ), type_params)

    # resolvers
    @staticmethod
    def resolve_company_ids(parent, info):
        return [c.id for c in info.context['env'].companies]

    @staticmethod
    def resolve_context(parent, info, **kw):
        env = info.context['env']
        context = env.context.copy()
        if kw.get('apikey'):
            user_id = env['res.users.apikeys']._check_credentials(
                scope='graphql', key=kw['apikey'])
            context.update({'uid': user_id})
        if kw.get('context'):
            context.update(parent._eval_context(kw['context']))
        return str(context)

    @classmethod
    def query_orm(cls, env, model_name, **kw):
        try:
            model = env[model_name]
        except KeyError:
            raise UserError(_(f"No such model: '{model_name}'"))

        context = env.context.copy()
        if kw.get('apikey'):
            user_id = env['res.users.apikeys']._check_credentials(
                scope='graphql', key=kw['apikey'])
            context.update({'uid': user_id})
            model = model.with_user(user_id)
        if kw.get('company'):
            model = model.with_company(kw['company'])
        if kw.get('context'):
            context.update(cls._eval_context(kw['context']))
        model = model.with_context(context)
        if kw.get('ids'):
            return model.browse(kw['ids'])
        else:
            domain = cls._eval_domain(kw.get('domain'))
            limit = kw.get('limit')
            offset = kw.get('offset')
            return model.search(domain, limit=limit, offset=offset)

    @classmethod
    def _field_params(cls, model_name, record_type):
        def resolver(parent, info, model_name=model_name, **kw):
            env = info.context['env']
            return cls.query_orm(env, model_name, **kw)

        field_name = '_'.join(model_name.split('.'))
        resolver_name = f'resolve_{field_name}'
        return {
            field_name: graphene.List(
                graphene.NonNull(record_type),
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
        }

    # producer methods
    @classmethod
    def make_query(cls):
        model_fields = cls._query_db()
        for model_name, fields in model_fields.items():
            record_type = cls._make_record_type(model_name, fields)
            cls.record_types.update({model_name: record_type})

        query_params = {
            'context': graphene.Field(
                graphene.String,
                apikey=graphene.String(),
                company=graphene.Int(),
                context=graphene.List(graphene.NonNull(ContextItem)),
            ),
            'company_ids': graphene.List(graphene.Int),
            'resolve_context': cls.resolve_context,
            'resolve_company_ids': cls.resolve_company_ids,
        }
        for model_name, record_type in cls.record_types.items():
            query_params.update(model_name, record_type)

        return type('QueryORM', (graphene.ObjectType, ), query_params)


Query = GraphqlFactory.make_query()
schema = graphene.Schema(query=Query)
