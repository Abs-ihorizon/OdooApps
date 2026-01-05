from odoo import models, fields


class PosConfigInherit(models.Model):
    _inherit = 'pos.config'

    pra_api_url = fields.Char(string='PRA API URL', help='Sandbox/Test URL for PRA')
    pra_api_token = fields.Char(string='PRA API Token', help='Token for PRA integration for this POS')
    pra_registration_number = fields.Char(string='PRA Registration Number', help='Registration number for PRA')
    enable_pra_integration = fields.Boolean(string='Enable PRA Integration',
                                            help='Enable/Disable PRA Integration for this POS')
