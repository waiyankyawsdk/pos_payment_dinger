# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api
from odoo.exceptions import UserError
from ..dataclasses.datamodels import JournalCodeEnum


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('dinger', 'Dinger')]

    is_parent=fields.Boolean(string="Parent")
    parent_method_id=fields.Many2one('pos.payment.method',string="Parent Method")
    parent_payment_method_name=fields.Char(string="Parent Method Name")

    project_name = fields.Char(
        string="Dinger Project Name",
        help="Name of the project in the Dinger dashboard.",
    )

    public_key = fields.Char(
        string="Public Key",
        help="Wallet public key from the Dinger dashboard.",
    )

    merchant_name = fields.Char(
        string="Merchant Name",
        help="Wallet Merchant key from the Dinger dashboard.",
    )

    merchant_key = fields.Char(
        string="Merchant Key",
        help="Wallet Merchant key from the Dinger dashboard.",
    )

    client_id = fields.Char(
        string="Client Id",
        help="Wallet Client ID from the Dinger dashboard.",
    )

    secret_key = fields.Char(
        string="Secret Key",
        help="Wallet Secret key from the Dinger dashboard.",
    )

    journal_code = fields.Selection(
        selection=JournalCodeEnum.get_selection(),
        string="Bank Journal Code",
    )

    description = fields.Text(
        string="Description",
        default="Payment made by an Odoo Pos.",
    )
    @api.onchange('parent_method_id')
    def _onchange_parent_method(self):
        if self.parent_method_id and self.parent_method_id.use_payment_terminal == "dinger":
            self.payment_method_type = "terminal"
            self.use_payment_terminal = "dinger"
            self.project_name = self.parent_method_id.project_name
            self.public_key = self.parent_method_id.public_key
            self.merchant_name = self.parent_method_id.merchant_name
            self.merchant_key = self.parent_method_id.merchant_key
            self.client_id = self.parent_method_id.client_id
            self.secret_key = self.parent_method_id.secret_key
            self.journal_id = self.parent_method_id.journal_id
            self.outstanding_account_id = self.parent_method_id.outstanding_account_id
            self.parent_payment_method_name = self.parent_method_id.name
            self.is_parent = False
        else:
            # Optionally, clear Dinger fields if parent is not Dinger
            self.use_payment_terminal = False
            self.payment_method_type = False
            self.project_name = False
            self.public_key = False
            self.merchant_name = False
            self.merchant_key = False
            self.client_id = False
            self.secret_key = False
            self.journal_id = False
            self.outstanding_account_id = False
            self.parent_payment_method_name = False
            self.is_parent = True


    @api.model
    def _load_pos_data_fields(self, config_id):
        params = super()._load_pos_data_fields(config_id)
        params += ['parent_payment_method_name','project_name','public_key','merchant_name','merchant_key','client_id','secret_key','journal_code']
        return params
            