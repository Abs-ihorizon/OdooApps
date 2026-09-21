from odoo import fields, models


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    cheque_no = fields.Char(string='Cheque No')
    wht_lines = fields.One2many(comodel_name='withholding.lines', inverse_name='payment_id', string='Withholding Lines')
