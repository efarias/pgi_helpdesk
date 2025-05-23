from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HelpdeskTicketStage(models.Model):
    _inherit = 'helpdesk.ticket.stage'

    ticket_close = fields.Boolean(
        string='Etapa de cierre definitivo',
        help='Marca esta etapa como el cierre formal del ciclo de vida del ticket. Solo puede haber una por equipo.'
    )

    @api.constrains('ticket_close', 'team_ids')
    def _check_unique_ticket_close_per_team(self):
        for stage in self:
            if stage.ticket_close:
                for team in stage.team_ids:
                    others = self.search([
                        ('ticket_close', '=', True),
                        ('team_ids', 'in', team.id),
                        ('id', '!=', stage.id)
                    ])
                    if others:
                        raise ValidationError(
                            f"Ya existe una etapa de cierre definitivo para el equipo '{team.name}'."
                        )
