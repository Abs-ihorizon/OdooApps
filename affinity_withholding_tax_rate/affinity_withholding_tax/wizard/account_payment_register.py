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

        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'destination_account_id': self.line_ids[:1].account_id.id,
            'write_off_line_vals': [],
            'wht_lines': [(6, 0, self.wht_lines.ids)],
        }

        return payment_vals
