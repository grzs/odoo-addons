# coding: utf-8

# Copyright 2021 Janos Gerzson (grzs)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from types import LambdaType
import re
import graphene

from psycopg2 import ProgrammingError

from odoo import registry, api, SUPERUSER_ID, _, http
from odoo.exceptions import UserError
from odoo.addons.graphql_base import OdooObjectType

from .odoo_orm_regex import p as pattern_orm


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


class OobjectInput(graphene.InputObjectType):
    k = graphene.String()  # optional key
    otype = graphene.Field(Otype, default_value=Otype.STR)
    v = graphene.String()
    v_int = graphene.Int()
    v_float = graphene.Float()
    v_bool = graphene.Boolean()
    v_list_str = graphene.List(graphene.String)
    v_list_int = graphene.List(graphene.Int)
    v_list_float = graphene.List(graphene.Float)


class Oobject(graphene.ObjectType):
    k = graphene.String()
    otype = graphene.Field(Otype)
    v = graphene.String()
    v_int = graphene.Int()
    v_float = graphene.Float()
    v_bool = graphene.Boolean()
    v_list_str = graphene.List(graphene.String)
    v_list_int = graphene.List(graphene.Int)
    v_list_float = graphene.List(graphene.Float)


class DomainItemInput(graphene.InputObjectType):
    logical = graphene.String()
    f = graphene.String(required=True)
    o = graphene.String(required=True)
    v = graphene.Field(OobjectInput, required=True)


def _eval_domain(domain):
    domain_odoo = []
    if not domain:
        return domain_odoo
    for d in domain:
        value = _eval_oobject(d.v)
        if value is None:
            continue
        criterion = (d.f, d.o, value)
        if d.logical in ['&', '|', '!']:
            domain_odoo.append(d.logical)
        domain_odoo.append(criterion)
    return domain_odoo


def _eval_context(context):
    context_odoo = {}
    for o in context:
        if not o.k:
            continue
        value = _eval_oobject(o)
        if value is not None:
            context_odoo.update({o.k: value})
    return context_odoo


def _eval_oobject(o):
    if o.v is not None:
        if o.otype == Otype.STR:
            return o.v
        elif o.otype == Otype.INT:
            return int(o.v)
        elif o.otype == Otype.FLOAT:
            return float(o.v)
        elif o.otype == Otype.BOOL:
            return bool(o.v)
        elif o.otype == Otype.LAMBDA:
            pattern = r"^lambda (?P<var>[a-z]):.*(?P=var).*$"
            if re.match(pattern, o.v):
                return eval(o.v)
            else:
                raise UserError(
                    _(f"'{o.v}' is not a valid lambda expression!"))
        elif o.otype == Otype.ORM:
            match = pattern_orm.match(o.v)
            if match:
                model_name = match.group('model')
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

    # if o.v not set
    for v in [o.v, o.v_int, o.v_float, o.v_bool,
              o.v_list_str, o.v_list_int, o.v_list_float]:
        if v is not None:
            return v
    return None


def _create_oobject(o, key=None):
    oobject = Oobject()
    if isinstance(key, str):
        oobject.k = key

    if isinstance(o, str):
        oobject.otype = Otype.STR
        oobject.v = o
    elif isinstance(o, int):
        oobject.otype = Otype.INT
        oobject.v = str(o)
        oobject.v_int = o
    elif isinstance(o, float):
        oobject.otype = Otype.FLOAT
        oobject.v = str(o)
        oobject.v_float = o
    elif isinstance(o, bool):
        oobject.otype = Otype.BOOL
        oobject.v = str(o)
        oobject.v_bool = o
    elif isinstance(o, list):
        if len(o) == 0:
            return None
        elif isinstance(o[0], str):
            lst = [i for i in o if isinstance(i, str)]
            oobject.otype = Otype.LST_STR
            oobject.v = str(lst)
            oobject.v_list_str = lst
        elif isinstance(o[0], int):
            lst = [i for i in o if isinstance(i, int)]
            oobject.otype = Otype.LST_INT
            oobject.v = str(lst)
            oobject.v_list_int = lst
        elif isinstance(o[0], float):
            lst = [i for i in o if isinstance(i, float)]
            oobject.otype = Otype.LST_FLOAT
            oobject.v = str(lst)
            oobject.v_list_float = lst
    elif isinstance(o, LambdaType):
        oobject.otype = Otype.LAMBDA
        oobject.v = str(o)
    elif hasattr(o, '_model_classes'):
        oobject.otype = Otype.ORM
        ids_str = str(list(o.ids))
        oobject.v = f"env['{o._name}'].search(['id','in',{ids_str}])"
    else:
        return None
    return oobject


def _create_context_list(context):
    context_list = []
    for key, value in context.items():
        item = _create_oobject(value, key=key)
        if item.v:
            context_list.append(item)
    return context_list


class OdooSession(graphene.ObjectType):
    sid = graphene.String(required=True)
    uid = graphene.Int()
    login = graphene.String()
    db = graphene.String()
    context = graphene.List(Oobject)
    status = graphene.String()


class OdooSessionMutation(graphene.Mutation):
    class Arguments:
        login = graphene.String()
        password = graphene.String()
        terminate = graphene.Boolean()
        db = graphene.String()
        context = graphene.List(OobjectInput)

    Output = OdooSession

    def mutate(root, info,
               login=None, password=None, terminate=None, db=None, context=None):
        session = http.request.session
        res = OdooSession()
        res.sid = session.sid
        res.uid = session['uid']
        res.db = db if db else session['db']
        res.login = session['login']
        if res.login:
            res.status = "authenticated"
        else:
            res.status = "anonymus"
            session.modified = True
        if context:
            ctx = _eval_context(context)
            session['context'].update(ctx)
            session.modified = True
        res.context = _create_context_list(session['context'])

        if terminate:
            if session.new:
                raise UserError(_("Session expired!"))
            if res.uid:
                session.logout()
            http.root.session_store.delete(session)
            session.modified = False
            res.status = "terminated"
        elif login and password:
            if res.status == "authenticated":
                raise UserError(_("Already logged in!"))
            res.uid = session.authenticate(res.db, login=login, password=password)
            if not res.uid:
                raise UserError(_("Invalid credentials!"))
            res.login = login
            res.status = "authenticated"

        session.rotate = False
        return res


class GraphqlFactory():
    relation_ttypes = [
        'many2one', 'many2one_reference', 'reference',
        'one2many', 'many2many',
    ]
    query_types = {}

    @classmethod
    def _query_db_fields(cls, where_clause):
        field_tuples = []
        fields = [
            'model',
            'name',
            'ttype',
            'relation',
            'required'
        ]
        query = f"SELECT {','.join(fields)} FROM ir_model_fields {where_clause}"
        reg = registry()
        try:
            with reg.cursor() as cr:
                cr.execute(query)
                field_tuples = cr.fetchall()
                cr.rollback()
        except ProgrammingError as e:
            msg = e.args[0]
            if re.match('column .[a-z_]+. does not exist', msg):
                return {}
            else:
                raise e

        model_fields = {}
        for t in field_tuples:
            if t[0] not in model_fields.keys():
                model_fields.update({t[0]: []})
            model_fields[t[0]].append(t[1:])
        return model_fields

    # factory methods
    @classmethod
    def _make_field_type(cls, odoo_type, required=False):
        '''Map scalar odoo types to graphql types
        Mapping:
          String: char, html, selection, text, date, datetime
          Int: integer
          Float: float, monetary
          Boolean: boolean
          ?: binary, reference
        '''
        if odoo_type in ['char', 'text', 'html', 'selection']:
            return graphene.String(required=required)
        elif odoo_type == 'integer':
            return graphene.Int(required=required)
        elif odoo_type in ['float', 'monetary']:
            return graphene.Float(required=required)
        elif odoo_type == 'boolean':
            return graphene.Boolean(required=required)
        elif odoo_type == 'date':
            return graphene.Date(required=required)
        elif odoo_type == 'datetime':
            return graphene.DateTime(required=required)
        elif odoo_type in ['reference']:
            return graphene.String(required=required)
        elif odoo_type in ['many2one', 'many2one_reference']:
            return graphene.Int(required=required)
        elif odoo_type in ['one2many', 'many2many']:
            return graphene.List(graphene.Int, required=required)
        else:
            return None

    @classmethod
    def _make_relation_field_type(cls, odoo_type, comodel_name, required=False):
        '''Map relation odoo types to graphql types
        Mapping:
          Field/Int: many2one, many2one_reference, reference
          List(Field/Int): one2many, many2many
        '''
        if odoo_type in ['reference']:
            return graphene.String(required=required)
        elif odoo_type in ['many2one_reference']:
            return graphene.Int(required=required)
        else:
            return graphene.List(
                graphene.NonNull(cls.query_types[comodel_name]),
                required=True)

    @classmethod
    def _make_query_type(cls, model_name, fields):
        type_params = {'id': graphene.ID()}
        for t in fields:
            f_name, f_ttype, f_relation, f_required = t
            # if f_name == 'id':
            if f_name == 'id' or f_ttype in cls.relation_ttypes:
                continue
            field = cls._make_field_type(f_ttype)
            if field:
                type_params.update({f_name: field})

        type_name = ''.join([s.capitalize() for s in model_name.split('.')])
        return type(type_name, (OdooObjectType, ), type_params)

    @classmethod
    def _make_mutation_type(cls, model_name, fields, update=False):
        class Arguments:
            apikey = graphene.String()
            company = graphene.Int()
            context = graphene.List(graphene.NonNull(OobjectInput))
            id = graphene.ID(required=update)

        if update:
            setattr(Arguments, 'delete', graphene.Boolean())

        for t in fields:
            f_name, f_ttype, f_relation, f_required = t
            if f_name == 'id':
                continue
            required = False if update else f_required
            field = cls._make_field_type(f_ttype, required=required)
            if field:
                setattr(Arguments, f_name, field)

        @staticmethod
        def mutate(self, info,
                   model_name=model_name, model_getter=cls._get_model,
                   update=update, delete=False, **kw):

            env = info.context['env']
            model = model_getter(env, model_name, **kw)
            if update:
                record = model.browse(int(kw.pop('id')))
                if delete:
                    if record.unlink():
                        return model
                else:
                    record.write(kw)
                    # record.flush(kw.keys())
                return record
            return model.create(kw)

        type_params = {
            'Arguments': Arguments,
            'Output': cls.query_types[model_name],
            'mutate': mutate,
        }
        mode = 'Update' if update else 'Create'
        type_name = mode + ''.join([s.capitalize() for s in model_name.split('.')])
        return type(type_name, (graphene.Mutation, ), type_params)

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
            context.update(_eval_context(kw['context']))
        return _create_context_list(context)

    @staticmethod
    def resolve_session(parent, info):
        session = http.request.session
        res = OdooSession()
        res.sid = session.sid
        res.uid = session['uid']
        res.login = session['login']
        res.context = _create_context_list(session['context'])
        if res.login:
            res.status = "authenticated"
        else:
            res.status = "anonymus"
        # if session.new:
        #     return res

        res.db = session['db']
        session.modified = False
        return res

    # producer helper methods
    @classmethod
    def _get_model(cls, env, model_name, **kw):
        try:
            model = env[model_name]
        except KeyError:
            raise UserError(_(f"No such model: '{model_name}'"))

        context = env.context.copy()
        if kw.get('apikey'):
            user_id = env['res.users.apikeys']._check_credentials(
                scope='graphql', key=kw.pop('apikey'))
            context.update(uid=user_id)
            model = model.with_user(user_id)
        if kw.get('company'):
            model = model.with_company(kw.pop('company'))
        if kw.get('context'):
            context.update(_eval_context(kw.pop('context')))

        return model.with_context(context)

    @classmethod
    def _field_params(cls, model_name, query_type):
        def resolver(parent, info, model_name=model_name, **kw):
            env = info.context['env']
            model = cls._get_model(env, model_name, **kw)

            if kw.get('ids'):
                return model.browse(kw['ids'])
            else:
                domain = _eval_domain(kw.get('domain'))
                limit = kw.get('limit')
                offset = kw.get('offset')
                return model.search(domain, limit=limit, offset=offset)

        field_name = '_'.join(model_name.split('.'))
        resolver_name = f'resolve_{field_name}'
        return {
            field_name: graphene.List(
                graphene.NonNull(query_type),
                required=True,
                apikey=graphene.String(),
                company=graphene.Int(),
                context=graphene.List(graphene.NonNull(OobjectInput)),
                ids=graphene.List(graphene.Int),
                domain=graphene.List(graphene.NonNull(DomainItemInput)),
                limit=graphene.Int(),
                offset=graphene.Int(),
            ),
            resolver_name: resolver,
        }

    # producer methods
    @classmethod
    def _make_query(cls):
        subquery_models = "SELECT model FROM ir_model WHERE graphql = 't'"
        where_clause = f"WHERE model IN ({subquery_models})"
        query_model_fields = cls._query_db_fields(where_clause)

        if len(query_model_fields) == 0:
            return None

        # make types
        for model_name, fields in query_model_fields.items():
            cls.query_types.update({
                model_name: cls._make_query_type(model_name, fields)
            })

        # make relations
        for model_name, fields in query_model_fields.items():
            type_updated = False
            for t in fields:
                f_name, f_ttype, f_relation, f_required = t
                if f_ttype not in cls.relation_ttypes:
                    continue

                if f_relation and f_relation in cls.query_types.keys():
                    field_type = cls._make_relation_field_type(f_ttype, f_relation)
                else:
                    field_type = cls._make_field_type(f_ttype)
                setattr(cls.query_types[model_name], f_name, field_type)
                type_updated = True

            # reinit type
            if type_updated:
                delattr(cls.query_types[model_name], '_meta')
                cls.query_types[model_name].__init_subclass__()

        query_params = {
            'context': graphene.List(
                Oobject,
                apikey=graphene.String(),
                company=graphene.Int(),
                context=graphene.List(graphene.NonNull(OobjectInput)),
            ),
            'session': graphene.Field(OdooSession),
            'company_ids': graphene.List(graphene.Int),
            'resolve_context': cls.resolve_context,
            'resolve_company_ids': cls.resolve_company_ids,
            'resolve_session': cls.resolve_session,
        }
        for model_name, query_type in cls.query_types.items():
            query_params.update(cls._field_params(model_name, query_type))

        return type('QueryORM', (graphene.ObjectType, ), query_params)

    @classmethod
    def _make_mutation(cls):
        subquery_models = "SELECT model FROM ir_model WHERE graphql = 't'"
        subquery_models_writable = f"{subquery_models} AND graphql_write = 't'"
        where_clause = f"WHERE model IN ({subquery_models_writable})"
        mutation_model_fields = cls._query_db_fields(where_clause)
        mutation_params = {
            'session': OdooSessionMutation.Field()
        }
        if len(mutation_model_fields):
            for model_name, fields in mutation_model_fields.items():
                field_name = '_'.join(model_name.split('.'))
                mutation_type = cls._make_mutation_type(model_name, fields)
                mutation_update_type = cls._make_mutation_type(
                    model_name, fields, update=True)
                mutation_params.update({
                    f'create_{field_name}': mutation_type.Field(),
                    field_name: mutation_update_type.Field(),
                })
        return type('MutationORM', (graphene.ObjectType, ), mutation_params)

    @classmethod
    def make(cls):
        return cls._make_query(), cls._make_mutation()


Query, Mutation = GraphqlFactory.make()
schema = graphene.Schema(query=Query, mutation=Mutation)
