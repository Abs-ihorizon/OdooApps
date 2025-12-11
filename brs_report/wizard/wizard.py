from odoo import _, api, fields, models


class BrsReportWizard(models.TransientModel):
    _name = 'brs.report'
    _description = 'BRS Report'
    
    ending_date = fields.Date(string="Bank Statement Ending Date")  
    bank = fields.Many2one('account.account',string="Bank")
    ending_balance = fields.Float(string="Statement Ending Balance")
  
    def print_report(self):
        data = {'date':self.ending_date,'bank_name':self.bank.name,'bank':self.bank.id,'balance':self.ending_balance }
        return self.env.ref('brs_report.brs_report_pdf').with_context(landscape=False).report_action(self,data=data)