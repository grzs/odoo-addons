# coding: utf-8

from ..schema import GraphqlFactory as cls


def _get_field_type(name, ttype, required=False):
    '''Map scalar odoo types to typescript types
    Mapping:
      String: char, html, selection, text, date, datetime
      Number: integer, float, monetary
      Boolean: boolean
      ?: binary, reference
    '''
    if ttype in ['char', 'text', 'html', 'selection']:
        ts_type = 'string'
    elif ttype in ['integer', 'float', 'monetary']:
        ts_type = 'number'
    elif ttype == 'boolean':
        ts_type = 'boolean'
    elif ttype == 'date':
        ts_type = 'string'
    elif ttype == 'datetime':
        ts_type = 'string'
    elif ttype in ['reference']:
        ts_type = 'string'
    elif ttype in ['many2one', 'many2one_reference']:
        ts_type = 'number'
    elif ttype in ['one2many', 'many2many']:
        ts_type = 'Array<number>'
    else:
        ts_type = 'any'

    req = '' if required else '?'

    name_parts = name.split('_')
    ts_name = name_parts[0] + ''.join([n.capitalize() for n in name_parts[1:]])

    return f'{ts_name}{req}: {ts_type}'


def write_ts_file(filename, indent=2):
    '''Generates typescript interfaces from odoo model definitions exported to
    GraphQL and writes to file.
    Parameters:
    :filename - file to write;
    :indent=<integer, default=2> - number of spaces to indent by'''
    indent = indent * ' '

    subquery_models = "SELECT model FROM ir_model WHERE graphql = 't'"
    where_clause = f"WHERE model IN ({subquery_models})"
    query_model_fields = cls._query_db_fields(where_clause)

    ts_lines = ['// Odoo model types\n']
    ts_export_lines = ['export {\n']
    for model_name, fields in query_model_fields.items():
        ts_name = ''.join([n.capitalize() for n in model_name.split('.')])
        ts_export_lines.append(f'{indent}{ts_name},\n')

        ts_lines.append('\n')
        ts_lines.append(f'interface {ts_name} {{\n')
        for t in fields:
            f_name, f_ttype, f_relation, f_required = t
            if f_ttype != 'binary':
                field = _get_field_type(f_name, f_ttype, f_required)
                ts_lines.append(f'{indent}{field};\n')
        ts_lines.append('}\n')

    ts_lines.append('\n')
    ts_export_lines.append('}\n')

    with open(filename, 'w') as f:
        f.writelines(ts_lines + ts_export_lines)
