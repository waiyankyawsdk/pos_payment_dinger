# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api
from ...dinger_mixin.dataclasses.datamodels import JournalCodeEnum


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('dinger', 'Dinger')]

    is_parent=fields.Boolean(string="Parent")
    parent_method_id=fields.Many2one('pos.payment.method',string="Parent Method")
    parent_payment_method_name=fields.Char(string="Parent Method Name")

    journal_code = fields.Selection(
        selection=JournalCodeEnum.get_selection(),
        string="Bank Journal Code",
    )

    @api.onchange('parent_method_id')
    def _onchange_parent_method(self):
        if self.parent_method_id and self.parent_method_id.use_payment_terminal == "dinger":
            self.parent_payment_method_name = self.parent_method_id.name
            self.is_parent = False
        else:
            self.parent_payment_method_name = False
            self.is_parent = True

    @api.model
    def _load_pos_data_fields(self, config_id):
        params = super()._load_pos_data_fields(config_id)
        params += ['parent_payment_method_name', 'journal_code']
        return params
