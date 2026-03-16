# Copyright 2018 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# Copyright 2018 Rafis Bikbov <https://it-projects.info/team/bikbov>
# Copyright 2021 Denis Mudarisov <https://github.com/trojikman>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import json
import logging

import werkzeug

from odoo import http
from odoo.tools import json as ojson

from odoo.addons.web.controllers.utils import ensure_db

_logger = logging.getLogger(__name__)


class OAS(http.Controller):
    @http.route(
        "/api/v1/<namespace_name>/swagger.json",
        type="http",
        auth="none",
        csrf=False,
    )
    def OAS_json_spec_download(self, namespace_name, **kwargs):
        ensure_db()
        namespace = (
            http.request.env["openapi.namespace"]
            .sudo()
            .search([("name", "=", namespace_name)])
        )
        if not namespace:
            raise werkzeug.exceptions.NotFound()
        if namespace.token != kwargs.get("token"):
            raise werkzeug.exceptions.Forbidden()

        response_params = {"headers": [("Content-Type", "application/json")]}
        if "download" in kwargs:
            response_params = {
                "headers": [
                    ("Content-Type", "application/octet-stream; charset=binary"),
                    ("Content-Disposition", http.content_disposition("swagger.json")),
                ],
                "direct_passthrough": True,
            }

        return werkzeug.wrappers.Response(
            json.dumps(namespace.get_OAS(), default=ojson.json_default),
            status=200,
            **response_params
        )

    @http.route(
        "/api/v1/<namespace_name>/swagger-ui",
        type="http",
        auth="none",
        csrf=False,
    )
    def OAS_swagger_ui(self, namespace_name, **kwargs):
        ensure_db()
        namespace = (
            http.request.env["openapi.namespace"]
            .sudo()
            .search([("name", "=", namespace_name)])
        )
        if not namespace:
            raise werkzeug.exceptions.NotFound()
        if namespace.token != kwargs.get("token"):
            raise werkzeug.exceptions.Forbidden()

        token_param = ""
        if kwargs.get("token"):
            token_param = "?token=%s" % kwargs["token"]

        spec_url = "/api/v1/%s/swagger.json%s" % (namespace_name, token_param)

        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%(title)s - Swagger UI</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({
            url: "%(spec_url)s",
            dom_id: "#swagger-ui",
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
            layout: "BaseLayout",
            deepLinking: true,
        });
    </script>
</body>
</html>""" % {
            "title": namespace_name,
            "spec_url": spec_url,
        }

        return werkzeug.wrappers.Response(
            html,
            status=200,
            headers=[("Content-Type", "text/html; charset=utf-8")],
        )
