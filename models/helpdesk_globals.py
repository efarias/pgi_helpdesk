from odoo import api, fields, models

# Equipos
class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.ticket.team"
    company_id = fields.Many2one("res.company", default=False)

    @api.model
    def create(self, vals):
        vals.setdefault("company_id", False)
        return super().create(vals)

# Categorías
class HelpdeskCategory(models.Model):
    _inherit = "helpdesk.ticket.category"
    company_id = fields.Many2one("res.company", default=False)

    @api.model
    def create(self, vals):
        vals.setdefault("company_id", False)
        return super().create(vals)

# Etapas
class HelpdeskStage(models.Model):
    _inherit = "helpdesk.ticket.stage"
    company_id = fields.Many2one("res.company", default=False)

    @api.model
    def create(self, vals):
        vals.setdefault("company_id", False)
        return super().create(vals)

# Tags
class HelpdeskTag(models.Model):
    _inherit = "helpdesk.ticket.tag"
    company_id = fields.Many2one("res.company", default=False)

    @api.model
    def create(self, vals):
        vals.setdefault("company_id", False)
        return super().create(vals)
