from odoo import models, fields


class PosOrderInherit(models.Model):
    _inherit = 'pos.order'

    pra_status_code = fields.Integer(string='PRA Status Code')
    pra_last_response = fields.Text(string='PRA Last Response')
    pra_push_failed = fields.Boolean(string='PRA Push Failed', default=False)
    pra_invoice_number = fields.Char(string="PRA Invoice Number", readonly=True)
