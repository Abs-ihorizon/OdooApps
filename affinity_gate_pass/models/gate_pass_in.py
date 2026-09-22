from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError


class GatePassIn(models.Model):
    _name = 'gate.pass.in'
    _description = 'Gate Pass In'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='Number', required=True, copy=False, readonly=True, default=lambda self: _('New'),
                       tracking=True)
    date = fields.Datetime(string='In Time', required=True, default=fields.Datetime.now, tracking=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('in', 'In'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', required=True, tracking=True)
    location_id = fields.Many2one(comodel_name='stock.location', string='Destination Location',
                                  domain="[('usage', '=', 'internal')]", tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company,
                                 required=True)
    reference = fields.Char(string='Order Reference', readonly=True, help='Doc Ref e.g. PO, Delivery Note, Invoice No.')
    note = fields.Html(string='Terms and conditions')
    remarks = fields.Text(string='Remarks')
    line_ids = fields.One2many(comodel_name='gate.pass.in.line', inverse_name='gate_pass_id', string='Items')
    total_qty = fields.Float(string='Total Qty', compute='_compute_totals', store=True)
    picking_id = fields.Many2one(comodel_name='stock.picking', string='Receipt / GRN', readonly=True)
    purchase_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order', readonly=True)
    sale_id = fields.Many2one(comodel_name='sale.order', string='Sale Order', readonly=True)

    @api.depends('line_ids.received_qty')
    def _compute_totals(self):
        for rec in self:
            rec.total_qty = sum(rec.line_ids.mapped('received_qty'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('gate.pass.in') or _('New')
        return super(GatePassIn, self).create(vals_list)

    def action_in(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('You cannot confirm a gate pass without any items.'))
            if rec.picking_id:
                for line in rec.line_ids:
                    moves = rec.picking_id.move_ids.filtered(
                        lambda m: m.product_id == line.product_id and m.state not in ('done', 'cancel')
                    )
                    if moves:
                        moves[0].quantity = line.received_qty
                    elif line.received_qty > 0:
                        uom = line.uom_id if hasattr(line, 'uom_id') and line.uom_id else line.product_id.uom_id
                        self.env['stock.move'].create({
                            'name': line.product_id.display_name,
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.received_qty,
                            'quantity': line.received_qty,
                            'product_uom': uom.id,
                            'picking_id': rec.picking_id.id,
                            'location_id': rec.picking_id.location_id.id,
                            'location_dest_id': rec.picking_id.location_dest_id.id,
                        })
            rec.state = 'in'

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

    def action_view_purchase(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': self.purchase_id.id,
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

    def should_print_note(self):
        self.ensure_one()
        return bool(self.note and tools.html2plaintext(self.note).strip())
