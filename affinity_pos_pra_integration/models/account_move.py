from odoo import models, fields


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    pra_invoice_number = fields.Char(string='PRA Invoice Number', readonly=True)
