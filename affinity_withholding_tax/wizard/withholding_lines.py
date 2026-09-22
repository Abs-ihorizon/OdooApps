from odoo import models, fields, api


class WithholdingLines(models.Model):
    _name = 'withholding.lines'
    _description = 'Withholding Tax Lines'

    name = fields.Char(string='Description')

    wizard_id = fields.Many2one(comodel_name='account.payment.register', string='Payment Wizard')
    payment_id = fields.Many2one(comodel_name='account.payment', string='Payment')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', compute='_compute_currency_id',
                                  store=True)
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    tax_id = fields.Many2one(comodel_name='account.tax', string='Tax')
    account_id = fields.Many2one(comodel_name='account.account', string='Account')

    @api.depends('wizard_id', 'payment_id')
    def _compute_currency_id(self):
        for rec in self:
            if rec.wizard_id and rec.wizard_id.currency_id:
                rec.currency_id = rec.wizard_id.currency_id
            elif rec.payment_id and rec.payment_id.currency_id:
                rec.currency_id = rec.payment_id.currency_id
            else:
                rec.currency_id = rec.env.company.currency_id

    def _get_base_amount(self):
        if self.wizard_id:
            return self.wizard_id.amount
        elif self.payment_id:
            return self.payment_id.amount
        return 0.0

    def _get_move_type(self):
        self.ensure_one()

        if self.wizard_id and self.wizard_id.communication:
            move = self.env['account.move'].search([('name', '=', self.wizard_id.communication)], limit=1)
            return move.move_type if move else False
        if self.payment_id:
            return 'out_invoice' if self.payment_id.payment_type == 'outbound' else 'in_invoice'
        return False

    def _get_default_account_id(self, move_type):
        self.ensure_one()
        repartition_lines = self.tax_id.invoice_repartition_line_ids.filtered(lambda l: l.account_id)
        return repartition_lines[:1].account_id if repartition_lines else False

    @api.onchange('tax_id')
    def _onchange_tax_id(self):
        for rec in self:
            if not rec.tax_id:
                rec.amount = 0.0
                rec.account_id = False
                continue

            base_amount = rec._get_base_amount()
            rec.amount = (base_amount * rec.tax_id.amount) / 100

            move_type = rec._get_move_type()
            rec.account_id = rec._get_default_account_id(move_type)

    @api.onchange('name', 'amount', 'wizard_id', 'payment_id')
    def _onchange_context(self):
        for rec in self:
            if not rec.tax_id:
                continue

            move_type = rec._get_move_type()
            rec.account_id = rec._get_default_account_id(move_type)
