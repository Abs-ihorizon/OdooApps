from odoo import fields, models


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    journal_type = fields.Selection(related='journal_id.type', string='Journal Type')
    status = fields.Selection(selection=[
        ('unreconciled', 'Un Reconciled'),
        ('reconciled', 'Reconciled'),
    ])
