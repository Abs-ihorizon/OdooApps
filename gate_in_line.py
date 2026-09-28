from odoo import api, fields, models


class GatePassInLine(models.Model):
    _name = 'gate.pass.in.line'
    _description = 'Gate Pass In Line'

    gate_pass_id = fields.Many2one(comodel_name='gate.pass.in', string='Gate Pass', ondelete='cascade')
    product_id = fields.Many2one(comodel_name='product.product', string='Product', readonly=True)
    description = fields.Char(string='Description', readonly=True)
    quantity = fields.Float(string='Qty.', default=1.0, readonly=True)
    received_qty = fields.Float(string='Received', default=1.0)
    uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM', readonly=True)
    note = fields.Char(string='Notes')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.description = line.product_id.display_name
                line.uom_id = line.product_id.uom_id
