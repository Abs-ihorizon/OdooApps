from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    currency_rate = fields.Float(string='Currency Rate', digits=(16, 12), default=1.0)
    currency_rate_visible = fields.Boolean(compute='_compute_currency_rate_visible')

    @api.depends('group_payment', 'line_ids', 'line_ids.move_id.currency_id')
    def _compute_currency_rate_visible(self):
        for wizard in self:
            moves = wizard.line_ids.mapped('move_id')

            foreign_moves = moves.filtered(lambda m: m.currency_id and m.currency_id != m.company_currency_id)
            currencies = foreign_moves.mapped('currency_id')

            if not foreign_moves:
                wizard.currency_rate_visible = False
                continue

            if len(currencies) == 1:
                wizard.currency_rate_visible = True
            else:
                wizard.currency_rate_visible = False

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])

        if active_model == 'account.move.line' and active_ids:
            lines = self.env['account.move.line'].browse(active_ids)
            moves = lines.mapped('move_id')
            move = moves[:1]

            if move and move.invoice_currency_rate:
                res['currency_rate'] = move.invoice_currency_rate

        return res

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        vals.update({
            'currency_rate': self.currency_rate,
        })
        return vals

    def _create_payment_vals_from_batch(self, batch_result):
        vals = super()._create_payment_vals_from_batch(batch_result)

        lines = batch_result.get('lines')
        move = lines.mapped('move_id')[:1] if lines else False

        if move and hasattr(move, 'invoice_currency_rate') and move.invoice_currency_rate:
            vals['currency_rate'] = move.invoice_currency_rate
        else:
            vals['currency_rate'] = self.currency_rate

        return vals
