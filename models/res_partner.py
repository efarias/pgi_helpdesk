from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_school = fields.Boolean(
        string='Es unidad educativa',
        help='Marcar si este contacto corresponde a una unidad educativa del SLEP.'
    )
