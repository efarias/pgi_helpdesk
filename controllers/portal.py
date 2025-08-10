# pgi_helpdesk/controllers/portal.py
# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.tools import html_sanitize
from html import unescape
import base64

class PGIHelpdeskPortal(http.Controller):

    @http.route('/pgi/submitted/ticket', type='http', auth='user', website=True, methods=['POST'])
    def pgi_submitted_ticket(self, **post):
        partner = request.env.user.partner_id

        team_id = int(post.get('team') or 0) or False
        category_id = int(post.get('category') or 0) or False
        subject = (post.get('subject') or '').strip() or _('Sin asunto')

        # Descripción en HTML (desde el editor) → des-escapar y SANITIZAR
        raw_html = unescape(post.get('description') or '')
        safe_html = html_sanitize(raw_html, sanitize_attributes=True, sanitize_style=True)

        Ticket = request.env['helpdesk.ticket'].sudo()
        Attach = request.env['ir.attachment'].sudo()

        ticket = Ticket.create({
            'name': subject,
            'description': safe_html,
            'team_id': team_id,
            'category_id': category_id,
            'partner_id': partner.id,
        })

        for f in request.httprequest.files.getlist('attachment') or []:
            if not f:
                continue
            Attach.create({
                'name': f.filename,
                'res_model': 'helpdesk.ticket',
                'res_id': ticket.id,
                'type': 'binary',
                'datas': base64.b64encode(f.read()),
            })

        return request.redirect(f"/my/ticket/{ticket.id}")
