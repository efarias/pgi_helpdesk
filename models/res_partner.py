from odoo import api, fields, models
from odoo.exceptions import ValidationError
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_school = fields.Boolean(
        string='Es unidad educativa',
        help='Marcar si este contacto corresponde a una unidad educativa del SLEP.'
    )

