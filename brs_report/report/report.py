from odoo.exceptions import UserError, AccessError
from odoo import _, api, fields, models



class CustomReport(models.AbstractModel):
    _name = "report.brs_report.brs_reports"
    _description = "BRS Report"

    def _get_report_values(self, docids, data=None):
        
        bank = data['bank']       
        bank_name = data['bank_name']       
        balance = data['balance']       
        date = data['date']       
        cr = self._cr

        
        headerdata = ("""select aa.name,
                    coalesce(sum(aml.balance),0.00) as Balance,
                    (select coalesce(sum(amlp.credit),0.00) from account_move_line amlp inner join account_move amp on amp.id = amlp.move_id where amlp.account_id=%s and amlp.date <='%s' and amlp.statement_date is null and amp.state = 'posted')Un_Payment,
                    (select coalesce(sum(amlp.debit),0.00) from account_move_line amlp inner join account_move amp on amp.id = amlp.move_id where amlp.account_id=%s and amlp.date <='%s' and amlp.statement_date is null and amp.state = 'posted') as un_Receipt
                    from account_move_line aml 
                    inner join account_account aa on aml.account_id=aa.id 
                    
                    where account_id=%s and aml.date <= '%s' group by aa.name,aml.account_id
                     """
                      % (bank,date,bank,date,bank,date) 
                        ) 
     
        cr.execute(headerdata)
        header = cr.dictfetchall()


        unpaiddata = ("""
                    select am.name,am.date,am.cheque_number,am.id,aml.ref,aml.debit,aml.credit from account_move_line aml
                    left join account_move am on aml.move_id = am.id
                    where am.state = 'posted' and aml.statement_date is null and account_id=%s and aml.date <= '%s'
                    """
                            % (bank,date) 
            
            )
        cr.execute(unpaiddata)
        unpaid = cr.dictfetchall()

        paiddata = ("""
                    select am.name,am.date,am.cheque_number,am.id,aml.ref,aml.debit,aml.credit from account_move_line aml
                    left join account_move am on aml.move_id = am.id
                    where am.state = 'posted' and aml.statement_date is not null and account_id=%s and aml.date <= '%s'
                    """
                            % (bank,date) 
            
            )

        cr.execute(paiddata)
        paid = cr.dictfetchall()
        
        
        return {
            'header': header,
            'paid': paid,
            'unpaid': unpaid,
            'bank_name': bank_name,
            'date': date,
            'balance': balance,
        }
