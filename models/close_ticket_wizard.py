from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

class CloseTicketWizard(models.TransientModel):
    _name = 'close.ticket.wizard'
    _description = 'Asistente para Cierre de Ticket Helpdesk'

    close_note = fields.Text(string='Nota de Cierre', required=True)
    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket', required=True)

    @staticmethod
    def clean_html_for_chatter(html_content):
        """
        Convierte contenido HTML a texto plano, preservando saltos de línea.
        Útil para publicar contenido HTML en el chatter sin etiquetas.
        """
        if not html_content:
            return ""
        # html2plaintext convierte <br>, <p> y otros elementos en saltos de línea
        return html2plaintext(html_content).strip()

    def action_close_ticket(self):
        self.ensure_one()

        # Verificar si hay OT asociadas y filtrar las que no están cerradas
        ot_abiertas = self.ticket_id.workorder_ids.filtered(
            lambda r: r.stage_id and r.stage_id.state not in ('done', 'cancelled')
        )

        if ot_abiertas:
            nombres_ot = ', '.join(ot_abiertas.mapped('name'))
            raise UserError(
                f"No se puede cerrar el ticket porque existen órdenes de trabajo abiertas:\n{nombres_ot}"
            )

        # Guardar la nota de cierre
        self.ticket_id.closing_notes = self.close_note

        # Publicar en el chatter
        texto_plano = self.clean_html_for_chatter(self.ticket_id.closing_notes)

        self.ticket_id.message_post(
            body=f"📝 Nota de Cierre:\n{texto_plano}",
            message_type="comment",
            subtype_id=self.env.ref("mail.mt_note").id
        )

        # Buscar etapa de cierre definitivo
        stage_cierre = self.env['helpdesk.ticket.stage'].search([
            ('team_ids', 'in', self.ticket_id.team_id.id),
            ('ticket_close', '=', True)
        ], limit=1)

        if not stage_cierre:
            raise UserError("No se ha definido una etapa de cierre definitivo para este equipo.")

        # Asignar la etapa al ticket
        self.ticket_id.stage_id = stage_cierre.id

