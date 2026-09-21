from odoo import api, fields, models


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    currency_rate = fields.Float(string='Currency Rate', digits=(16, 12), default=1.0)
    is_foreign_currency = fields.Boolean(compute='_compute_is_foreign_currency', store=True)

    @api.depends('currency_id', 'company_currency_id')
    def _compute_is_foreign_currency(self):
        for rec in self:
            rec.is_foreign_currency = (
                    rec.currency_id
                    and rec.company_currency_id
                    and rec.currency_id != rec.company_currency_id
            )

    def _get_custom_rate(self):
        self.ensure_one()
        return self.currency_rate or 1.0

    @api.depends(
        'move_id.amount_total_signed',
        'amount',
        'payment_type',
        'currency_id',
        'date',
        'company_id',
        'company_currency_id',
        'currency_rate',
    )
    def _compute_amount_company_currency_signed(self):
        for payment in self:
            if payment.currency_id != payment.company_currency_id and payment.currency_rate:
                sign = -1 if payment.payment_type == 'outbound' else 1
                payment.amount_company_currency_signed = (payment.amount / payment._get_custom_rate()) * sign
            else:
                super(AccountPaymentInherit, payment)._compute_amount_company_currency_signed()

    def _prepare_move_lines_per_type(self, write_off_line_vals=None, force_balance=None):
        self.ensure_one()

        line_vals_per_type = super()._prepare_move_lines_per_type(
            write_off_line_vals=write_off_line_vals,
            force_balance=force_balance,
        )

        if self.currency_id != self.company_currency_id and self.currency_rate:
            rate = self._get_custom_rate()
            sign = -1 if self.payment_type == 'outbound' else 1

            liquidity_lines = line_vals_per_type.get('liquidity_lines', [])
            counterpart_lines = line_vals_per_type.get('counterpart_lines', [])

            liquidity_balance = sign * (self.amount / rate)
            liquidity_amount_currency = sign * self.amount

            counterpart_balance = -liquidity_balance
            counterpart_amount_currency = -liquidity_amount_currency

            for line in liquidity_lines:
                line['balance'] = liquidity_balance
                line['amount_currency'] = liquidity_amount_currency

            for line in counterpart_lines:
                line['balance'] = counterpart_balance
                line['amount_currency'] = counterpart_amount_currency

        return line_vals_per_type

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        if self.currency_id != self.company_currency_id and self.currency_rate:
            force_balance = self.amount / self._get_custom_rate()
            if self.payment_type == 'outbound':
                force_balance *= -1

        return super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals,
            force_balance=force_balance,
        )

    @api.model
    def _get_trigger_fields_to_synchronize(self):
        return super()._get_trigger_fields_to_synchronize() + (
            'currency_rate',
        )
