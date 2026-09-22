from odoo import models, fields


class AccountPaymentRegisterInherit(models.TransientModel):
    _inherit = 'account.payment.register'

    wht_lines = fields.One2many(comodel_name='withholding.lines', inverse_name='wizard_id', string='Withholding Lines')
    account_id = fields.Many2one(comodel_name='account.account', string='Withholding Account',
                                  default=lambda self: self._get_default_account_id())

    def _get_default_account_id(self):
        communication = self.env.context.get('default_communication')
        if not communication:
            return False

        move = self.env['account.move'].search([('name', '=', communication)], limit=1)

        if not move:
            return False

        if move.move_type == 'out_invoice':
            return 8
        elif move.move_type == 'in_invoice':
            return 1157

        return False

    def _create_payment_vals_from_wizard(self, batch_result):
        self.ensure_one()
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        payment_vals['wht_lines'] = [(6, 0, self.wht_lines.ids)]
        return payment_vals
