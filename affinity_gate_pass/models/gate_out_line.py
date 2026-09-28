from odoo import api, fields, models


class GatePassOutLine(models.Model):
    _name = 'gate.pass.out.line'
    _description = 'Gate Pass Out Line'

    gate_pass_id = fields.Many2one(comodel_name='gate.pass.out', string='Gate Pass', ondelete='cascade')
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    description = fields.Char(string='Description')
    quantity = fields.Float(string='Qty.', default=1.0)
    dispatched_qty = fields.Float(string='Dispatched', default=1.0)
    uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM')
    note = fields.Char(string='Notes')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.description = line.product_id.display_name
                line.uom_id = line.product_id.uom_id
