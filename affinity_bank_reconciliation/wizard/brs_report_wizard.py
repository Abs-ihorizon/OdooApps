from odoo import fields, models


class BrsReportWizard(models.TransientModel):
    _name = 'brs.report.wizard'
    _description = 'BRS Report'

    ending_date = fields.Date(string="Bank Statement Ending Date")
    bank = fields.Many2one(comodel_name='account.account', string="Bank")
    ending_balance = fields.Float(string="Statement Ending Balance")

    def print_report(self):
        data = {
            'date': self.ending_date,
            'bank_name': self.bank.name,
            'bank': self.bank.id,
            'balance': self.ending_balance,
        }

        return self.env.ref('affinity_bank_reconciliation.brs_report_pdf').with_context(landscape=False).report_action(self, data=data)
