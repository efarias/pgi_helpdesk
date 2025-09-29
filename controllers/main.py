import base64
import logging

import werkzeug
from odoo import http
from odoo.addons.helpdesk_mgmt.controllers.main import HelpdeskTicketController as BaseController
from odoo.http import request

_logger = logging.getLogger(__name__)


class PGIHelpdeskTicketController(BaseController):
    """Extiende el controlador de OCA para:
       - Render: /new/ticket
       - Submit: /pgi/submitted/ticket
       - Guardar tanto category_id (subcategoría) como category_parent_id (si existe)
    """

    @http.route("/new/ticket", type="http", auth="user", website=True)
    def create_new_ticket(self, **kw):
        # (sin cambios relevantes) -> render del formulario con categorías padre y subcategorías
        _logger.info(">> [PGI] Entrando a controlador personalizado /new/ticket")
        team_id = int(kw.get("team") or 0)
        category_parent_id = int(kw.get("category_parent") or 0)
        category_id = int(kw.get("category") or 0)

        company = request.env.company
        category_model = request.env["helpdesk.ticket.category"].sudo()
        email = request.env.user.email
        name = request.env.user.name
        session_info = request.env["ir.http"].session_info()

        if team_id:
            parent_categories = category_model.search([
                ("active", "=", True),
                ("parent_id", "=", False),
                ("team_ids", "in", [team_id]),
            ])
            subcategories = category_model.search([
                ("active", "=", True),
                ("parent_id", "in", parent_categories.ids),
            ])
        else:
            parent_categories = category_model.search([
                ("active", "=", True),
                ("parent_id", "=", False),
            ])
            subcategories = category_model.search([
                ("active", "=", True),
                ("parent_id", "!=", False),
            ])

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

    # --- NUEVO: preparamos los valores a crear tomando categoría y subcategoría ---
    def _prepare_submit_ticket_vals_pgi(self, **kw):
        """
        Igual que el _prepare_submit_ticket_vals de OCA pero:
        - Lee 'category_parent' (padre) y 'category' (subcat).
        - Valida consistencia entre ambos.
        - Setea category_id = subcategoría.
        - Si el ticket tiene el campo category_parent_id, también lo setea.
        - Acepta HTML del portal para 'description' (WYSIWYG).
        """
        # Subcategoría (obligatoria por el form)
        subcat = request.env["helpdesk.ticket.category"].browse(int(kw.get("category") or 0)).sudo()
        if not subcat or not subcat.exists():
            raise http.ValidationError("Debe seleccionar una subcategoría válida.")

        # Padre seleccionado por el usuario
        parent_from_kw = request.env["helpdesk.ticket.category"].browse(int(kw.get("category_parent") or 0)).sudo()
        # Si no llegó padre, usamos el padre real de la subcategoría
        parent_final = parent_from_kw if parent_from_kw and parent_from_kw.exists() else subcat.parent_id

        # Validación de consistencia: si el usuario eligió un padre distinto al real, corregimos al real
        if parent_from_kw and parent_from_kw != subcat.parent_id:
            _logger.warning(
                ">> [PGI] Mismatch padre-subcategoría: padre elegido (%s) != padre real (%s). Se tomará el padre real.",
                parent_from_kw.id, subcat.parent_id.id if subcat.parent_id else None
            )
            parent_final = subcat.parent_id

        # Base: aprovechamos la lógica de equipos y stage del BaseController
        vals = super(PGIHelpdeskTicketController, self)._prepare_submit_ticket_vals(**kw)

        # Forzamos la empresa desde la categoría (si tiene) o desde el entorno
        company = (subcat.company_id or request.env.company).sudo()
        vals.update({
            "company_id": company.id,
            "category_id": subcat.id,  # subcategoría
            # ACEPTAMOS HTML DEL PORTAL (WYSIWYG). Si quieres forzar texto plano, usa plaintext2html.
            "description": kw.get("description") or "",
            "name": kw.get("subject"),
            "attachment_ids": False,
        })

        # Si el modelo tiene 'category_parent_id', lo seteamos.
        ticket_model = request.env["helpdesk.ticket"]
        if "category_parent_id" in ticket_model._fields and parent_final:
            vals["category_parent_id"] = parent_final.id

        return vals

    # --- NUEVO: ruta de envío que calza con tu <form action="/pgi/submitted/ticket"> ---
    @http.route("/pgi/submitted/ticket", type="http", auth="user", website=True, csrf=True)
    def submit_ticket_pgi(self, **kw):
        """
        Ruta de submit usada por el template PGI.
        Crea el ticket con categoría + subcategoría y adjuntos.
        """
        vals = self._prepare_submit_ticket_vals_pgi(**kw)
        ticket = request.env["helpdesk.ticket"].sudo().create(vals)
        ticket.message_subscribe(partner_ids=request.env.user.partner_id.ids)

        # Adjuntos (igual que OCA)
        if kw.get("attachment"):
            for c_file in request.httprequest.files.getlist("attachment"):
                data = c_file.read()
                if c_file.filename:
                    request.env["ir.attachment"].sudo().create({
                        "name": c_file.filename,
                        "datas": base64.b64encode(data),
                        "res_model": "helpdesk.ticket",
                        "res_id": ticket.id,
                    })

        return werkzeug.utils.redirect(f"/my/ticket/{ticket.id}")
