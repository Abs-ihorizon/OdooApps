from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError


class GatePassOut(models.Model):
    _name = 'gate.pass.out'
    _description = 'Gate Pass Out'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='Number', required=True, copy=False, readonly=True, default=lambda self: _('New'),
                       tracking=True)
    date = fields.Datetime(string='Out Time', required=True, default=fields.Datetime.now, tracking=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('out', 'Out'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', required=True, tracking=True)
    location_id = fields.Many2one(comodel_name='stock.location', string='Source Location',
                                  domain="[('usage', '=', 'internal')]", tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company,
                                 required=True)
    reference = fields.Char(string='Order Reference', readonly=True, help='Doc Ref e.g. SO, Dispatch Note, Invoice No.')
    note = fields.Html(string='Terms and conditions')
    remarks = fields.Text(string='Remarks')
    line_ids = fields.One2many(comodel_name='gate.pass.out.line', inverse_name='gate_pass_id', string='Items')
    total_qty = fields.Float(string='Total Qty', compute='_compute_totals', store=True)
    picking_id = fields.Many2one(comodel_name='stock.picking', string='Delivery Order', readonly=True)
    sale_id = fields.Many2one(comodel_name='sale.order', string='Sale Order', readonly=True)
    purchase_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order', readonly=True)

    @api.depends('line_ids.dispatched_qty')
    def _compute_totals(self):
        for rec in self:
            rec.total_qty = sum(rec.line_ids.mapped('dispatched_qty'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('gate.pass.out') or _('New')
        return super(GatePassOut, self).create(vals_list)

    def action_out(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('You cannot confirm a gate pass without any items.'))
            if rec.picking_id and rec.picking_id.state != 'done':
                raise UserError(
                    _('You cannot mark Gate Pass Out as Out until the related Delivery Order (%s) is validated.') % rec.picking_id.name)
            rec.state = 'out'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_view_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': self.picking_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_sale(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_purchase(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': self.purchase_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def should_print_note(self):
        self.ensure_one()
        return bool(self.note and tools.html2plaintext(self.note).strip())
