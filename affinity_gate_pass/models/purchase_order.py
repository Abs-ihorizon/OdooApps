from odoo import fields, models


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    gate_pass_in_ids = fields.One2many(comodel_name='gate.pass.in', inverse_name='purchase_id', string='Gate Pass In')
    gate_pass_in_count = fields.Integer(string='Gate Pass In Count', compute='_compute_gate_pass_counts')
    gate_pass_out_ids = fields.One2many(comodel_name='gate.pass.out', inverse_name='purchase_id',
                                        string='Gate Pass Out')
    gate_pass_out_count = fields.Integer(string='Gate Pass Out Count', compute='_compute_gate_pass_counts')

    def _compute_gate_pass_counts(self):
        for order in self:
            order.gate_pass_in_count = len(order.gate_pass_in_ids)
            order.gate_pass_out_count = len(order.gate_pass_out_ids)

    def button_confirm(self):
        res = super(PurchaseOrderInherit, self).button_confirm()
        for order in self:
            order._auto_create_gate_pass_in()
        return res

    def _prepare_gate_pass_in_vals(self, picking, lines):
        self.ensure_one()
        return {
            'partner_id': self.partner_id.id,
            'location_id': self.picking_type_id.default_location_dest_id.id,
            'company_id': self.company_id.id,
            'reference': self.name,
            'line_ids': lines,
            'picking_id': picking.id,
            'purchase_id': self.id,
        }

    def _auto_create_gate_pass_in(self):
        for order in self:
            picking = order.picking_ids.filtered(
                lambda p: p.picking_type_code == 'incoming' and p.state not in ('done', 'cancel')
            )[:1]
            if picking and not picking.gate_pass_in_id:
                lines = []
                for line in order.order_line:
                    if line.product_id.type != 'service' and line.product_qty > 0:
                        qty = line.product_qty
                        lines.append((0, 0, {
                            'product_id': line.product_id.id,
                            'description': line.name or line.product_id.display_name,
                            'quantity': qty,
                            'received_qty': qty,
                            'uom_id': line.product_uom.id,
                        }))

                if lines:
                    vals = order._prepare_gate_pass_in_vals(picking, lines)
                    gate_in = self.env['gate.pass.in'].create(vals)
                    picking.gate_pass_in_id = gate_in.id

    def action_view_gate_pass_in(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('affinity_gate_pass.gate_pass_in_action_all')
        if len(self.gate_pass_in_ids) == 1:
            action['views'] = [(self.env.ref('affinity_gate_pass.view_gate_pass_in_form').id, 'form')]
            action['res_id'] = self.gate_pass_in_ids.id
        else:
            action['domain'] = [('id', 'in', self.gate_pass_in_ids.ids)]
        return action

    def action_view_gate_pass_out(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('affinity_gate_pass.gate_pass_out_action_all')
        if len(self.gate_pass_out_ids) == 1:
            action['views'] = [(self.env.ref('affinity_gate_pass.view_gate_pass_out_form').id, 'form')]
            action['res_id'] = self.gate_pass_out_ids.id
        else:
            action['domain'] = [('id', 'in', self.gate_pass_out_ids.ids)]
        return action
