# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import http

from odoo.addons.graphql_base import GraphQLControllerMixin

from ..schema import schema


class GraphQLController(http.Controller, GraphQLControllerMixin):

    # The GraphiQL route, providing an IDE for developers
    @http.route("/graphiql/orm", auth="public")
    def graphiql(self, **kwargs):
        return self._handle_graphiql_request(schema)

    # The graphql route, for applications.
    # Note csrf=False: you may want to apply extra security
    # (such as origin restrictions) to this route.
    @http.route("/graphql/orm", auth="public", csrf=False)
    def graphql(self, **kwargs):
        return self._handle_graphql_request(schema)
