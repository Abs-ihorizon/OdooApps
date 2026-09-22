from odoo import api, models, fields, _


class GatePassGuest(models.Model):
    _name = 'gate.pass.guest'
    _description = 'Gate Pass Guest'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='Pass Number', required=True, copy=False, readonly=True, default=lambda self: _('New'),
                       tracking=True)
    guest_name = fields.Char(string='Guest Name', required=True, tracking=True)
    contact_number = fields.Char(string='Contact Number', required=True, tracking=True)
    cnic_or_id = fields.Char(string='CNIC / ID Number', tracking=True)
    visitor_type = fields.Selection(selection=[
        ('visitor', 'Visitor'),
        ('vendor', 'Vendor / Supplier'),
        ('interview', 'Interviewee'),
        ('official', 'Official Work'),
        ('other', 'Other')
    ], string='Visitor Type', default='visitor', required=True, tracking=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Company / Organization')
    check_in = fields.Datetime(string='Check In Time', default=fields.Datetime.now, required=True, tracking=True)
    check_out = fields.Datetime(string='Check Out Time', tracking=True)
    host_id = fields.Many2one(comodel_name='res.users', string='Host / Whom to Meet', required=True,
                              default=lambda self: self.env.user, tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company,
                                 required=True)
    vehicle_number = fields.Char(string='Vehicle Number')
    belongings = fields.Text(string='Belongings / Items Brought')
    purpose = fields.Text(string='Purpose of Visit', required=True)
    remarks = fields.Text(string='Remarks')
    badge_number = fields.Char(string='Badge / Card No.')
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('in', 'Checked In'),
        ('out', 'Checked Out'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('gate.pass.guest') or _('New')
        return super(GatePassGuest, self).create(vals_list)

    def action_check_in(self):
        for rec in self:
            rec.write({
                'state': 'in',
                'check_in': fields.Datetime.now()
            })

    def action_check_out(self):
        for rec in self:
            rec.write({
                'state': 'out',
                'check_out': fields.Datetime.now()
            })

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
