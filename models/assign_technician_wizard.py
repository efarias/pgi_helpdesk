from odoo import models, fields, api

class AssignTechnicianWizard(models.TransientModel):
    _name = 'assign.technician.wizard'
    _description = 'Asignar Técnico al Ticket'

    technician_id = fields.Many2one('res.users', string="Técnico", required=True, domain=[('share', '=', False)])
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket", required=True)

    def action_confirm_assign(self):
        self.ensure_one()
        ticket = self.ticket_id
        ticket.user_id = self.technician_id

        # Buscar etapa "Asignado"
        assigned_stage = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Asignado')], limit=1)
        if assigned_stage:
            ticket.stage_id = assigned_stage.id

        ticket.message_post(body=f"Técnico asignado: {self.technician_id.name}")
