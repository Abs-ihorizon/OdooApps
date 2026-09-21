from odoo import models


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    def create(self, vals):
        res = super(AccountMoveInherit, self).create(vals)

        if res.origin_payment_id:
            debit_line = next(filter(lambda line: line.credit == 0, res.line_ids), None)
            credit_line = next(filter(lambda line: line.debit == 0, res.line_ids), None)
            lines = []

            for i in res.origin_payment_id.wht_lines:
                if res.origin_payment_id.payment_type == 'outbound':
                    lines.append((0, 0, {
                        'account_id': i.account_id.id,
                        'debit': 0,
                        'credit': i.amount,
                        'display_type': 'product',
                        'name': i.name,
                    }))
                    credit_line.with_context(check_move_validity=False).credit -= i.amount
                if res.origin_payment_id.payment_type == 'inbound':
                    lines.append((0, 0, {
                        'account_id': i.account_id.id,
                        'debit': i.amount,
                        'credit': 0,
                        'display_type': 'product',
                        'name': i.name,
                    }))
                    debit_line.with_context(check_move_validity=False).debit -= i.amount

            res.with_context(check_move_validity=False).write({
                'line_ids': lines,
            })

        return res
