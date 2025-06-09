from odoo import models


# Inherit pos.order model
class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _prepare_tax_base_line_values(self):
        res = super()._prepare_tax_base_line_values()
        for line in res:
            # Reduce tax amount by $20
            line['price_unit'] = line['price_unit'] - 20.0

        return res
