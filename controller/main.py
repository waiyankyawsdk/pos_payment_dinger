import json
from odoo import http
from odoo.http import request
from .decryption_aes_ecb_pkcs7padding import decrypt


class PosOrderController(http.Controller):

    # Here dinger make return url and need to modify prebuilt_popup of qr image with check mark
    @http.route('/pos/order/dinger_payment_method', type='json', auth='public', csrf=False)
    def render_order_types(self, **post):
        # payment_result = post.get('paymentResult')
        # check_sum = post.get('checksum')

        # Decrypt the payment result
        # decrypted_str = decrypt(self.secret_key, payment_result)

        # try:
        #     result = json.loads(decrypted_str)
        # except json.JSONDecodeError:
        #     print("Failed to parse decrypted data as JSON:")
        #     print(decrypted_str)
        #     raise

        # ref = result.get('merchantOrderId')  # This is order.name
        # payment_id = result.get('transactionId')
        # status = result.get('transactionStatus')
        # total_amount = result.get('totalAmount')
        # created_at = result.get('createdAt')
        # provider_name = result.get('providerName')
        # method_name = result.get('methodName')
        # customer_name = result.get('customerName')

        # data = request.jsonrequest
        ref = post.get('order_name')
        status = post.get('status')

        print("Status is :", status)

        # Run from controller test endpoint
        request.env['bus.bus'].sendone('payment_status_test123', {'status': 'paid'})

        return {"message": f"Sent status paid on channel 'payment_status_{ref}'"}
