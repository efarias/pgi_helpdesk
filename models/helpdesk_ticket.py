from odoo import models, fields, api
from datetime import timedelta


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    urgency = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ], string='Urgencia', required=True, default='medium')

    impact = fields.Selection([
        ('individual', 'A un funcionario'),
        ('group', 'A un grupo o unidad'),
        ('institutional', 'A toda la institución'),
    ], string='Impacto', required=True, default='individual')

    expected_resolution_date = fields.Datetime(
        string='Fecha esperada de resolución',
        readonly=True,
    )

    visibility = fields.Selection([
        ('internal', 'Solo equipo TI'),
        ('shared', 'Visible para usuario solicitante'),
        ('public', 'Visible en portal público'),
    ], string='Visibilidad', default='shared')

    closing_notes = fields.Html('Notas de Cierre')

    @api.onchange('urgency', 'impact')
    def _onchange_urgency_impact(self):
        self._compute_priority_and_resolution()

    def _compute_priority_and_resolution(self):
        priority_matrix = {
            'individual': {
                'low': '0',
                'medium': '1',
                'high': '1',
                'critical': '2',
            },
            'group': {
                'low': '1',
                'medium': '1',
                'high': '2',
                'critical': '3',
            },
            'institutional': {
                'low': '1',
                'medium': '2',
                'high': '3',
                'critical': '3',
            },
        }

        resolution_times = {
            '3': timedelta(hours=4),  # Very High
            '2': timedelta(hours=8),  # High
            '1': timedelta(days=1),  # Medium
            '0': timedelta(days=2),  # Low
        }

        now = fields.Datetime.now()

        for ticket in self:
            urgency = ticket.urgency
            impact = ticket.impact

            if urgency and impact:
                priority = priority_matrix.get(impact, {}).get(urgency, '0')
                ticket.priority = priority
                ticket.expected_resolution_date = now + resolution_times[priority]

    priority_badge_html = fields.Html(string="Prioridad (visual)", compute='_compute_priority_badge')

    @api.depends('priority')
    def _compute_priority_badge(self):
        for rec in self:
            color_map = {
                '3': 'danger',  # Muy Alta
                '2': 'warning',  # Alta
                '1': 'info',  # Media
                '0': 'secondary'  # Baja
            }
            label_map = {
                '3': '🔴 Muy Alta',
                '2': '🟠 Alta',
                '1': '🔵 Media',
                '0': '⚪ Baja'
            }
            color = color_map.get(rec.priority or '1', 'secondary')
            label = label_map.get(rec.priority or '1', 'Desconocida')
            rec.priority_badge_html = f"<span class='badge bg-{color}'>{label}</span>"

    priority_color = fields.Char(compute='_compute_priority_color')

    @api.depends('priority')
    def _compute_priority_color(self):
        for rec in self:
            colors = {
                '3': 'bg-danger',
                '2': 'bg-warning',
                '1': 'bg-info',
                '0': 'bg-secondary'
            }
            rec.priority_color = colors.get(rec.priority or '1', 'bg-secondary')

    def write(self, vals):
        res = super().write(vals)
        if 'urgency' in vals or 'impact' in vals:
            self._compute_priority_and_resolution()
        return res

    @api.model
    def create(self, vals):
        ticket = super().create(vals)
        if 'urgency' in vals or 'impact' in vals:
            ticket._compute_priority_and_resolution()
        return ticket

    category_parent_id = fields.Many2one('helpdesk.ticket.category', string='Categoría',
                                         domain="[('parent_id', '=', False)]")
    category_id = fields.Many2one('helpdesk.ticket.category', string='Subcategoría',
                                  domain="[('parent_id', '=', category_parent_id)]")

    is_incident = fields.Boolean(string='Es incidente', compute='_compute_is_incident', store=True)

    @api.depends('category_id')
    def _compute_is_incident(self):
        for ticket in self:
            ticket.is_incident = ticket.category_id.is_incident if ticket.category_id else False


    ticket_company_id = fields.Many2one(
        'res.company',
        string='Compañía relacionada',
        compute='_compute_ticket_company_id',
        store=True,
        readonly=False  # para permitir override manual por técnicos
    )

    @api.depends('partner_id', 'user_id', 'create_uid')
    def _compute_ticket_company_id(self):
        for ticket in self:
            if ticket.partner_id and ticket.partner_id.user_ids:
                ticket.ticket_company_id = ticket.partner_id.user_ids[0].company_id
            elif ticket.user_id:
                ticket.ticket_company_id = ticket.user_id.company_id
            elif ticket.create_uid:
                ticket.ticket_company_id = ticket.create_uid.company_id

    def action_assign_technician(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asignar Técnico',
            'res_model': 'assign.technician.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
            }
        }

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override message_new to set ticket name from sequence instead of email subject."""
        if custom_values is None:
            custom_values = {}

        defaults = {
            # Asignar nombre desde secuencia personalizada
            "number": self._prepare_ticket_number(self.company_id),
            "name": msg.get("subject") or self.env._("Sin Asunto"),
            "description": msg.get("body"),
            "partner_email": msg.get("from"),
            "partner_id": msg.get("author_id"),
        }
        defaults.update(custom_values)

        ticket = super().message_new(msg, custom_values=defaults)

        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=ticket, force_create=False
            )
            if p
        ]
        ticket.message_subscribe(partner_ids)

        return ticket

