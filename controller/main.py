import json

from odoo import http
from odoo.http import request, route

class PosOrderController(http.Controller):
    _webhook_url = "/pos/order/dinger_webhook"

    # Here dinger make return url and need to modify prebuilt_popup of qr image with check mark
    @route(_webhook_url, type="http", auth="none", csrf=False, methods=["POST"])
    def render_order_types(self):
        """Receive payment result from Dinger and store it in pos.payment.status.

        Returns:
            _type_: _description_
        """
        post = request.httprequest.get_json(force=True)
        payment_result = post.get("paymentResult")
        # check_sum = post.get("checksum")

        # Decrypt the payment result
        decrypted_str = request.env["pos.payment"].aes_decrypt(payment_result,"api")

        try:
            result = json.loads(decrypted_str)
        except json.JSONDecodeError:
            print("Failed to parse decrypted data as JSON:")
            print(decrypted_str)
            raise

        status_id=request.env["pos.payment.status"].sudo().create_payment_status(result)
        return status_id

    # Start write to pos.payment.status for the sale order line with draft state
    @http.route(
        "/pos/payment_status/create_draft",
        type="json",
        auth="user",
        csrf=False,
        methods=["POST"],
    )
    def create_payment_status_draft(self, **kwargs):
        """Create a new pos.payment.status record from the provided kwargs."""
        status_id=request.env["pos.payment.status"].sudo().create_payment_status(kwargs)
        return status_id
