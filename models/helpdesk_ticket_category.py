from odoo import models, fields

class HelpdeskTicketCategory(models.Model):
    _inherit = 'helpdesk.ticket.category'

    parent_id = fields.Many2one('helpdesk.ticket.category', string='Categoría padre')
    child_ids = fields.One2many('helpdesk.ticket.category', 'parent_id', string='Subcategorías')
    team_ids = fields.Many2many('helpdesk.ticket.team', string='Equipos asociados')
    is_incident = fields.Boolean(string='Es incidente', default=True)
