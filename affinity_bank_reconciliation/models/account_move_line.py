from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    statement_date = fields.Date(string='Bank.St Date', copy=False)
    info_reference = fields.Char(string='Info Reference')
    bank_statement_id = fields.Many2one(comodel_name='bank.statement', string='Bank Statement', copy=False,
                                        ondelete='set null')

    def write(self, vals):
        protected_fields = {'debit', 'credit', 'balance', 'account_id', 'move_id'}
        updating_fields = set(vals.keys())

        # if protected_fields & updating_fields:
        #     raise UserError(_("You cannot modify accounting data of posted journal entries."))

        for record in self:
            if record.move_id.state == 'posted' and (protected_fields & updating_fields):
                raise UserError(_("You cannot modify accounting data of posted journal entries."))

        for record in self:
            if 'statement_date' in vals:
                if vals.get('statement_date'):
                    vals.update({'reconciled': True})
                    if record.payment_id:
                        record.payment_id.state = 'paid'
                else:
                    vals.update({'reconciled': False})
                    if record.payment_id:
                        record.payment_id.state = 'in_process'

        return super(AccountMoveLineInherit, self).write(vals)

    @api.onchange('statement_date')
    def _onchange_statement_date(self):
        if self.statement_date and self.move_id:
            self.move_id.status = 'reconciled'
        elif not self.statement_date and self.move_id:
            self.move_id.status = 'unreconciled'
