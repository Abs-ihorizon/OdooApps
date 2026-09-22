from odoo import fields, models, _
from odoo.exceptions import UserError


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    gate_pass_in_id = fields.Many2one(comodel_name='gate.pass.in', string='Gate Pass In', copy=False, readonly=True)
    gate_pass_out_id = fields.Many2one(comodel_name='gate.pass.out', string='Gate Pass Out', copy=False, readonly=True)

    def _prepare_gate_pass_out_vals(self, lines):
        self.ensure_one()
        sale_id = self.sale_id.id if self.sale_id else False
        purchase_id = self.purchase_id.id if self.purchase_id else False
        return {
            'partner_id': self.partner_id.id,
            'location_id': self.location_id.id,
            'company_id': self.company_id.id,
            'reference': self.sale_id.name if self.sale_id else '',
            'line_ids': lines,
            'picking_id': self.id,
            'sale_id': sale_id,
            'purchase_id': purchase_id,
        }

    def _auto_create_gate_pass_out(self):
        for picking in self:
            if picking.picking_type_code == 'outgoing' and not picking.gate_pass_out_id:
                lines = []
                moves = picking.move_ids_without_package or picking.move_ids
                for move in moves:
                    qty_done = move.quantity
                    if qty_done > 0:
                        lines.append((0, 0, {
                            'product_id': move.product_id.id,
                            'description': move.name or move.product_id.display_name,
                            'quantity': move.product_uom_qty,
                            'dispatched_qty': qty_done,
                            'uom_id': move.product_uom.id,
                        }))
                if lines:
                    vals = picking._prepare_gate_pass_out_vals(lines)
                    gate_out = self.env['gate.pass.out'].create(vals)
                    picking.gate_pass_out_id = gate_out.id

    def _action_done(self):
        for picking in self:
            code = picking.picking_type_code
            if code == 'incoming':
                if not picking.gate_pass_in_id or picking.gate_pass_in_id.state != 'in':
                    raise UserError(
                        _('You cannot validate this receipt until the associated Gate Pass In (%s) is confirmed (marked as In).') % (
                            picking.gate_pass_in_id.name if picking.gate_pass_in_id else _('Not Found')))

        res = super(StockPickingInherit, self)._action_done()

        for picking in self:
            if picking.picking_type_code == 'outgoing' and picking.state == 'done':
                picking._auto_create_gate_pass_out()

        return res

    def action_view_gate_pass_in(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gate.pass.in',
            'res_id': self.gate_pass_in_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_gate_pass_out(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gate.pass.out',
            'res_id': self.gate_pass_out_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
