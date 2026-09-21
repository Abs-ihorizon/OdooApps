from odoo import models, fields


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    invoice_currency_rate = fields.Float(string='Invoice Currency Rate', digits=(16, 12))
