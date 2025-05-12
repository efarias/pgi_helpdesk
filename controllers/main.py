import logging

from odoo import http
from odoo.http import request
from odoo.addons.helpdesk_mgmt.controllers.main import HelpdeskTicketController as BaseController

_logger = logging.getLogger(__name__)


class PGIHelpdeskTicketController(BaseController):

    @http.route("/new/ticket", type="http", auth="user", website=True)
    def create_new_ticket(self, **kw):
        _logger.info(">> [PGI] Entrando a controlador personalizado /new/ticket")

        team_id = int(kw.get("team") or 0)
        category_parent_id = int(kw.get("category_parent") or 0)
        category_id = int(kw.get("category") or 0)

        company = request.env.company
        category_model = request.env["helpdesk.ticket.category"].sudo()
        email = request.env.user.email
        name = request.env.user.name
        session_info = request.env["ir.http"].session_info()

        _logger.info(">> [PGI] Parámetros recibidos: team_id=%s, category_parent_id=%s, category_id=%s",
                     team_id, category_parent_id, category_id)

        if team_id:
            parent_categories = category_model.search([
                ("active", "=", True),
                ("parent_id", "=", False),
                ("team_ids", "in", [team_id])
            ])
            subcategories = category_model.search([
                ("active", "=", True),
                ("parent_id", "in", parent_categories.ids)
            ])
        else:
            parent_categories = category_model.search([
                ("active", "=", True),
                ("parent_id", "=", False)
            ])
            subcategories = category_model.search([
                ("active", "=", True),
                ("parent_id", "!=", False)
            ])

        _logger.info(">> [PGI] Categorías padre encontradas (%d): %s", len(parent_categories), parent_categories)
        _logger.info(">> [PGI] Subcategorías encontradas (%d): %s", len(subcategories), subcategories)

        return request.render("pgi_helpdesk.portal_create_ticket", {
            "teams": self._get_teams(),
            "categories": parent_categories,
            "subcategories": subcategories,
            "selected_team": team_id,
            "category_parent_id": category_parent_id,
            "category_id": category_id,
            "email": email,
            "name": name,
            "ticket_team_id_required": company.helpdesk_mgmt_portal_team_id_required,
            "ticket_category_id_required": company.helpdesk_mgmt_portal_category_id_required,
            "max_upload_size": session_info["max_file_upload_size"],
        })
