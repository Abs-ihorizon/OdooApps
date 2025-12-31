from odoo import api, fields, models


class BankStatement(models.Model):
    _name = 'bank.statement'

    journal_id = fields.Many2one(comodel_name='account.journal', string='Bank', domain=[('type', '=', 'bank')])
    account_id = fields.Many2one(comodel_name='account.account', string='Bank Account')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    statement_lines = fields.One2many(comodel_name='account.move.line', inverse_name='bank_statement_id',
                                      string="Statement Lines")
    gl_balance = fields.Monetary(string='Balance as per Company Books', readonly=True, compute='_compute_amount')
    bank_balance = fields.Monetary(string='Balance as per Bank', readonly=True, compute='_compute_amount')
    balance_difference = fields.Monetary(string='Amounts not Reflected in Bank', readonly=True,
                                         compute='_compute_amount')
    current_update = fields.Monetary(string='Balance of entries updated now')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency')
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('bank.statement'))

    @api.onchange('journal_id', 'date_from', 'date_to')
    def _get_lines(self):
        self.statement_lines = [(5, 0, 0)]

        if not (self.journal_id and self.date_from and self.date_to):
            return

        self.account_id = self.journal_id.default_account_id.id
        self.currency_id = (
                self.journal_id.currency_id
                or self.journal_id.company_id.currency_id
                or self.env.user.company_id.currency_id
        )

        domain = [
            ('account_id', '=', self.account_id.id),
            ('statement_date', '=', False),
            ('parent_state', '=', 'posted'),
            ('full_reconcile_id', '=', False),
        ('display_type', 'not in', ('line_section', 'line_note')),
        ]

        # domain = [
        #     ('account_id', '=', self.account_id.id),
        #     ('display_type', 'not in', ('line_section', 'line_note')),
        #     ('account_id.reconcile', '=', True),
        #     ('parent_state', '=', 'posted'),
        #     ('full_reconcile_id', '=', False)]


        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))

        if self.journal_id and (self.date_from or self.date_to):
            lines = self.env['account.move.line'].search(domain)
            self.update({'statement_lines': [(6, 0, lines.ids)]})

    @api.depends('statement_lines.statement_date')
    def _compute_amount(self):
        gl_balance = 0
        bank_balance = 0
        current_update = 0
        # domain = [('account_id', '=', self.account_id.id), ('parent_state', '=', 'posted'),
        #           ('account_id.reconcile', '=', True)]
        if len(self.statement_lines.ids) >0:
            domain = [('display_type', 'not in', ('line_section', 'line_note')), ('account_id.reconcile', '=', True),
                      ('parent_state', '=', 'posted'), ('full_reconcile_id', '=', False)]
            lines = self.env['account.move.line'].search(domain)
            gl_balance += sum([line.debit - line.credit for line in lines])
            domain += [('id', 'not in', self.statement_lines.ids), ('statement_date', '!=', False)]
            lines = self.env['account.move.line'].search(domain)
            bank_balance += sum([line.balance for line in lines])
            current_update += sum([line.debit - line.credit if line.statement_date else 0 for line in self.statement_lines])

        self.gl_balance = gl_balance
        self.bank_balance = bank_balance + current_update
        self.balance_difference = self.gl_balance - self.bank_balance
