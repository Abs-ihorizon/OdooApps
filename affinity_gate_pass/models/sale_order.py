from odoo import fields, models


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    gate_pass_in_ids = fields.One2many(comodel_name='gate.pass.in', inverse_name='sale_id', string='Gate Pass In')
    gate_pass_in_count = fields.Integer(string='Gate Pass In Count', compute='_compute_gate_pass_counts')
    gate_pass_out_ids = fields.One2many(comodel_name='gate.pass.out', inverse_name='sale_id', string='Gate Pass Out')
    gate_pass_out_count = fields.Integer(string='Gate Pass Out Count', compute='_compute_gate_pass_counts')

    def _compute_gate_pass_counts(self):
        for order in self:
            order.gate_pass_in_count = len(order.gate_pass_in_ids)
            order.gate_pass_out_count = len(order.gate_pass_out_ids)

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
