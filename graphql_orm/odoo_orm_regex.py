import re

pattern = (
    r"^(env\['(?P<model>\w+(\.\w+)*?)'\])"
    r"((\.with_(?P<userco>((user)|(company))\(\d+\)))|"
    r"(\.with_context\("
    r"(?P<context>((\{(('\w+': ?'?\w+'?)(, ?'\w+': ?'?\w+'?)*)?\})|"  # context provided
    r"(\w+='?\w+'?))(, ?\w+='?\w+'?)*)\)))*"  # context overrides
    r"(?P<browse>(\.browse\((?P<ids>\d(, ?\d+)*)\))|"
    r"(?P<search>\.search\(\[(?P<domain>"  # search begin
    r"(('[!&|]')|"  # search domain logical
    r"(\('\w+', ?"  # search domain field
    r"'(([<>!]?=?\??)|((=|(not )?i?like))|((not )?in)|((parent)|(child)_of))', ?"  # search domain operator
    r"'?[a-zA-Z0-9_.]+'?\)))"  # search domain value
    r"(, ?(('[!&|]')|"  # search domain multi begin
    r"(\('\w+', ?"
    r"'(([<>!]?=?\??)|((=|(not )?i?like))|((not )?in)|((parent)|(child)_of))', ?"
    r"'?[a-zA-Z0-9_.]+'?\))))*"  # search domain multi end
    r")\](, ?limit=\d+)?(, ?offset=\d+)?\)))?"  # search end
    r"(\.filtered\((?P<ffilter>lambda (?P<var>[a-z]):.*(?P=var).*)\))?"
    r"(?P<fields>(\.\w+)*)$"
)
print(pattern, '\n')

# tests
examples = [
    "env['res.partner']",
    "env['res.partner'].with_user(13)",
    "env['res.partner'].with_company(2)",
    "env['res.partner'].with_user(2).with_context({})",
    "env['res.partner'].with_context({'uid': 2})",
    "env['res.partner'].with_context({'lang': 'en_US', 'uid': 2})",
    "env['res.partner'].with_context({}, lang='en_US', uid=4)",
    "env['res.partner'].with_context(lang='en_US', uid=4)",
    "env['res.partner'].with_context({}, lang='en_US', uid=4).browse(1,2,5)",
    "env['res.partner'].search([('name','=','foo')])",
    "env['res.partner'].search([('active','=',True),('name','=','foo')])",
    "env['res.partner'].search(['|',('active','=',True)])",
    "env['res.partner'].search(['|',('active','=',True),('name','=','foo')])",
    "env['res.partner'].browse(1,4, 7)",
    "env['res.partner'].browse(1,4, 7).filtered(lambda r: r.name[0] == 'A')",
    "env['res.partner'].browse(1,2,3).name",
    "env['res.partner'].search([('company_id','=',2)]).company_id.name",
]

p = re.compile(pattern, flags=re.ASCII)
for e in examples:
    match = p.match(e)
    if match:
        model, userco, context, ids, domain, ffilter, fields = match.group(
            'model', 'userco', 'context', 'ids', 'domain', 'ffilter', 'fields')
        if context:
            print(f"{e:75}{context}")
        if domain:
            print(f"{e:75}{domain}")
        if ffilter:
            print(f"{e:75}{ffilter}")
