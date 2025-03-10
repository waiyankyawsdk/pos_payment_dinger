
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_pos_dinger = fields.Boolean(string="Dinger Payment Terminal",
                                       help="The transactions are processed by Dinger. Set your Dinger credentials on the related payment method.")
