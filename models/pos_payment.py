import requests
import base64
import json
from Crypto.Cipher import PKCS1_v1_5
from odoo import models, api, _
from odoo.exceptions import ValidationError, AccessError
from .encryption import EncryptRSA


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment'

    # Getting the token form the api by using project name,api key and merchant key,
    def _get_dinger_auth_token(self,payment_method_id):
        payment_method = self.env['pos.payment.method'].browse(payment_method_id)
        payment_method.ensure_one()
        if not (payment_method.project_name and payment_method.client_id and payment_method.merchant_name):
            raise ValidationError(_("Dinger credentials are not set on this payment method."))

        print("Dinger Credential of Project Name is :",payment_method.project_name)

        url = "https://staging.dinger.asia/payment-gateway-uat/api/token"
        params = {
            "projectName": payment_method.project_name,  # self.project_name,
            "apiKey": payment_method.client_id,  # self.api_key,
            "merchantName": payment_method.merchant_name,  # self.merchant_key
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        return None

    def get_country_code(self,country):
        url = "https://staging.dinger.asia/payment-gateway-uat/api/countryCodeListEnquiry"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("Dinger Country Code getting success...")
            country_list = data.get("response", [])
            for entry in country_list:
                countries = entry.get("country", "").lower()
                if country.lower() in countries:
                    return entry.get("code")
        return None

    def make_payment(self, token, payload):
        token_value = token.get("response", {}).get("paymentToken")

        # Prepare payload as dict if it's a JSON string
        if isinstance(payload, str):
            try:
                payload_dict = json.loads(payload)
            except json.JSONDecodeError:
                print("Failed to parse decrypted data as JSON:")
                print(payload)
                raise
        else:
            payload_dict = payload

        # Encrypt using your EncryptRSA class
        encryptor = EncryptRSA(**payload_dict)
        encrypted_payload = encryptor.encrypt()

        #Here need to change to production pay url 
        url = "https://staging.dinger.asia/payment-gateway-uat/api/pay"
        headers = {
            "Authorization": f"Bearer {token_value}"
        }
        files = {
            'payload': encrypted_payload
        }
        response = requests.post(url, headers=headers, data=files)
        if response.status_code == 200:
            return response.json()
        return False

    @api.model
    def dinger_connection_token(self,payment_method_id):
        if not self.env.user.has_group('point_of_sale.group_pos_user'):
            raise AccessError(_("Do not have access to fetch token from Diniger"))
        # Implement payment payload send.
        data = self._get_dinger_auth_token(payment_method_id)
        if not data:
            raise ValidationError(_('Complete the Dinger onboarding for company %s.', self.env.company.name))
        return data
