# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import werkzeug
import pprint
import base64
from urllib.parse import parse_qs
from Crypto.Cipher import AES, PKCS1_v1_5
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError, AccessError, AccessDenied

_logger = logging.getLogger(__name__)
TIMEOUT = 10

UNPREDICTABLE_Dinger_DATA = object()  # sentinel


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('dinger', 'Dinger')]

    # payment_t=fields.Char(string="Payment Type")

    project_name = fields.Char(
        string="Dinger Project Name",
        help="Name of the project in the Dinger dashboard.",
    )

    api_key = fields.Char(
        string="Dinger Wallet Api Key",
        help="Wallet API key from the Dinger dashboard.",
    )

    public_key = fields.Char(
        string="Dinger Wallet Public Key",
        help="Wallet public key from the Dinger dashboard.",
    )

    merchant_key = fields.Char(
        string="Dinger Wallet Merchant Key",
        help="Wallet Merchant key from the Dinger dashboard.",
    )

    description = fields.Text(
        string="Description",
        default="Payment made by an Odoo Pos.",
    )

    #
    @api.model
    def _load_pos_data_fields(self, config_id):
        params = super()._load_pos_data_fields(config_id)
        params += ['project_name']
        params += ['api_key']
        params += ['public_key']
        params += ['merchant_key']
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

    #
    # def stripe_payment_intent(self, amount):
    #     if not self.env.user.has_group('point_of_sale.group_pos_user'):
    #         raise AccessError(_("Do not have access to fetch token from Dinger"))
    #
    #     # For Terminal payments, the 'payment_method_types' parameter must include
    #     # at least 'card_present' and the 'capture_method' must be set to 'manual'.
    #     endpoint = 'https://api.dinger.asia/'
    #     currency = self.journal_id.currency_id or self.company_id.currency_id
    #
    #     params = [
    #         ("currency", currency.name),
    #         ("amount", self._dinger_calculate_amount(amount)),
    #         ("payment_method_types[]", "card_present"),
    #         ("capture_method", "manual"),
    #     ]
    #
    #     if currency.name == 'AUD' and self.company_id.country_code == 'AU':
    #         # See https://stripe.com/docs/terminal/payments/regional?integration-country=AU
    #         # This parameter overrides "capture_method": "manual" above.
    #         params.append(("payment_method_options[card_present][capture_method]", "manual_preferred"))
    #     elif currency.name == 'CAD' and self.company_id.country_code == 'CA':
    #         params.append(("payment_method_types[]", "interac_present"))
    #
    #     try:
    #         data = werkzeug.urls.url_encode(params)
    #         resp = requests.post(endpoint, data=data, auth=(self.sudo()._get_stripe_secret_key(), ''), timeout=TIMEOUT)
    #     except requests.exceptions.RequestException:
    #         _logger.exception("Failed to call stripe_payment_intent endpoint")
    #         raise UserError(_("There are some issues between us and Dinger, try again later."))
    #
    #     return resp.json()
    #
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

    #
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

        # if 'SaleToPOIRequest' in data and data['SaleToPOIRequest']['MessageHeader']['MessageCategory'] == 'Payment' and 'PaymentRequest' in data['SaleToPOIRequest']:  # Clear only if it is a payment request
        # self.sudo().dinger_latest_response = ''  # avoid handling old responses multiple times

        if not operation:
            operation = 'terminal_request'

        return True

        # return self._proxy_dinger_request_direct(data, operation)

        # # These checks are not optimal. This RPC method should be changed.
        #
        # is_capture_data = operation == 'capture' and hasattr(self, 'dinger_merchant_account') and self._is_valid_dinger_request_data(data, {
        #     'originalReference': UNPREDICTABLE_Dinger_DATA,
        #     'modificationAmount': {
        #         'value': UNPREDICTABLE_Dinger_DATA,
        #         'currency': UNPREDICTABLE_Dinger_DATA,
        #     },
        #     'merchantAccount': self.dinger_merchant_account,
        # })
        #
        # is_adjust_data = operation == 'adjust' and hasattr(self, 'dinger_merchant_account') and self._is_valid_dinger_request_data(data, {
        #     'originalReference': UNPREDICTABLE_Dinger_DATA,
        #     'modificationAmount': {
        #         'value': UNPREDICTABLE_Dinger_DATA,
        #         'currency': UNPREDICTABLE_Dinger_DATA,
        #     },
        #     'merchantAccount': self.dinger_merchant_account,
        #     'additionalData': {
        #         'industryUsage': 'DelayedCharge',
        #     },
        # })
        #
        # is_cancel_data = operation == 'terminal_request' and self._is_valid_dinger_request_data(data, {
        #     'SaleToPOIRequest': {
        #         'MessageHeader': self._get_expected_message_header('Abort'),
        #         'AbortRequest': {
        #             'AbortReason': 'MerchantAbort',
        #             'MessageReference': {
        #                 'MessageCategory': 'Payment',
        #                 'SaleID': UNPREDICTABLE_Dinger_DATA,
        #                 'ServiceID': UNPREDICTABLE_Dinger_DATA,
        #             },
        #         },
        #     },
        # })
        #
        # is_payment_request_with_acquirer_data = operation == 'terminal_request' and self._is_valid_adyen_request_data(data, self._get_expected_payment_request(True))
        #
        # if is_payment_request_with_acquirer_data:
        #     parsed_sale_to_acquirer_data = parse_qs(data['SaleToPOIRequest']['PaymentRequest']['SaleData']['SaleToAcquirerData'])
        #     valid_acquirer_data = self._get_valid_acquirer_data()
        #     is_payment_request_with_acquirer_data = len(parsed_sale_to_acquirer_data.keys()) <= len(valid_acquirer_data.keys())
        #     if is_payment_request_with_acquirer_data:
        #         for key, values in parsed_sale_to_acquirer_data.items():
        #             if len(values) != 1:
        #                 is_payment_request_with_acquirer_data = False
        #                 break
        #             value = values[0]
        #             valid_value = valid_acquirer_data.get(key)
        #             if valid_value == UNPREDICTABLE_Dinger_DATA:
        #                 continue
        #             if value != valid_value:
        #                 is_payment_request_with_acquirer_data = False
        #                 break
        #
        # is_payment_request_without_acquirer_data = operation == 'terminal_request' and self._is_valid_dinger_request_data(data, self._get_expected_payment_request(False))
        #
        # if not is_payment_request_without_acquirer_data and not is_payment_request_with_acquirer_data and not is_adjust_data and not is_cancel_data and not is_capture_data:
        #     raise UserError(_('Invalid Adyen request'))
        #
        # if is_payment_request_with_acquirer_data or is_payment_request_without_acquirer_data:
        #     acquirer_data = data['SaleToPOIRequest']['PaymentRequest']['SaleData'].get('SaleToAcquirerData')
        #     msg_header = data['SaleToPOIRequest']['MessageHeader']
        #     metadata = 'metadata.pos_hmac=' + self._get_hmac(msg_header['SaleID'], msg_header['ServiceID'], msg_header['POIID'], data['SaleToPOIRequest']['PaymentRequest']['SaleData']['SaleTransactionID']['TransactionID'])
        #
        #     data['SaleToPOIRequest']['PaymentRequest']['SaleData']['SaleToAcquirerData'] = acquirer_data + '&' + metadata if acquirer_data else metadata
        #
        # return self._proxy_dinger_request_direct(data, operation)

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

        # headers = {
        #     'x-api-key': self.sudo().api_key,
        # }
        # req = requests.post(endpoint, json=data, headers=headers, timeout=TIMEOUT)
        #
        # # Authentication error doesn't return JSON
        # if req.status_code == 401:
        #     return {
        #         'error': {
        #             'status_code': req.status_code,
        #             'message': req.text
        #         }
        #     }
        #
        # if req.text == 'ok':
        return token

        # return req.json()

    def _get_adyen_endpoints(self):
        return {
            'terminal_request': 'https://terminal-api-%s.adyen.com/async',
        }
