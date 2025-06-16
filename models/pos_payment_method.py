# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import werkzeug
import pprint
from urllib.parse import parse_qs
from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError, AccessDenied
from ..dataclasses.datamodels import JournalCodeEnum

_logger = logging.getLogger(__name__)
TIMEOUT = 10

UNPREDICTABLE_Dinger_DATA = object()  # sentinel


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
        params += ['parent_payment_method_name']
        params += ['project_name']
        params += ['public_key']
        params += ['merchant_name']
        params += ['merchant_key']
        params += ['client_id']
        params += ['secret_key']
        params +=['journal_code']
        return params

    def _get_dinger_payment_provider(self):
        dinger_payment_provider = self.env['payment.provider'].search([
            ('code', '=', 'dinger'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not dinger_payment_provider:
            raise UserError(_("Dinger payment provider for company %s is missing", self.env.company.name))

        return dinger_payment_provider


    def _dinger_calculate_amount(self, amount):
        currency = self.journal_id.currency_id or self.company_id.currency_id
        return round(amount / currency.rounding)
    
    @api.model
    def dinger_capture_payment(self, paymentIntentId, amount=None):
        """Captures the payment identified by paymentIntentId.

        :param paymentIntentId: the id of the payment to capture
        :param amount: without this parameter the entire authorized
                       amount is captured. Specifying a larger amount allows
                       overcapturing to support tips.
        """
        if not self.env.user.has_group('point_of_sale.group_pos_user'):
            raise AccessError(_("Do not have access to fetch token from Dinger"))

        endpoint = ('payment_intents/%s/capture') % (werkzeug.urls.url_quote(paymentIntentId))

        data = None
        if amount is not None:
            data = {
                "amount_to_capture": self._dinger_calculate_amount(amount),
            }

        return self.sudo()._get_dinger_payment_provider()._dinger_make_request(endpoint, data)

    def action_dinger_key(self):
        res_id = self._get_dinger_payment_provider().id
        # Redirect
        return {
            'name': _('Dinger'),
            'res_model': 'payment.provider',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': res_id,
        }

    def proxy_dinger_request(self, data, operation=False):
        ''' Necessary because Dinger's endpoints don't have CORS enabled '''
        self.ensure_one()
        if not self.env.su and not self.env.user.has_group('point_of_sale.group_pos_user'):
            raise AccessDenied()
        if not data:
            raise UserError(_('Invalid Dinger request'))

        if not operation:
            operation = 'terminal_request'

        return True

    @api.model
    def _is_valid_dinger_request_data(self, provided_data, expected_data):
        if not isinstance(provided_data, dict) or set(provided_data.keys()) != set(expected_data.keys()):
            return False

        for provided_key, provided_value in provided_data.items():
            expected_value = expected_data[provided_key]
            if expected_value == UNPREDICTABLE_Dinger_DATA:
                continue
            if isinstance(expected_value, dict):
                if not self._is_valid_dinger_request_data(provided_value, expected_value):
                    return False
            else:
                if provided_value != expected_value:
                    return False
        return True

    def _get_expected_message_header(self, expected_message_category):
        return {
            'ProtocolVersion': '3.0',
            'MessageClass': 'Service',
            'MessageType': 'Request',
            'MessageCategory': expected_message_category,
            'SaleID': UNPREDICTABLE_Dinger_DATA,
            'ServiceID': UNPREDICTABLE_Dinger_DATA,
            'POIID': self.api_key,
        }

    @api.model
    def _get_valid_acquirer_data(self):
        return {
            'tenderOption': 'AskGratuity',
            'authorisationType': 'PreAuth'
        }

    def _proxy_dinger_request_direct(self, data, operation):
        self.ensure_one()
        TIMEOUT = 10

        _logger.info('Request to Dinger by user #%d:\n%s', self.env.uid, pprint.pformat(data))

        # To call token
        token = self.dinger_connection_token()
        return token
            