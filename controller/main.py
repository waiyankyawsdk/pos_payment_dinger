import json
from datetime import datetime

from odoo import http
from odoo.http import request, route


@staticmethod
def convert_paid_at(date_str: str) -> str:
    """Convert the date string from Dinger format to Odoo format."""
    return datetime.strptime(date_str, "%Y%m%d %H%M%S").strftime("%Y-%m-%d %H:%M:%S")


@staticmethod
def create_new_pos_payment_status(data):
    """Create or update a pos.payment.status record based on the provided data.

    Args:
        data (dict): Payment data from Dinger webhook or draft creation.
    """
    merchant_order = data.get("merchantOrderId")  # This is order.name
    transaction = data.get("transactionId")
    status = data.get("transactionStatus")
    total_amount = data.get("totalAmount")
    created_at = data.get("createdAt")
    provider_name = data.get("providerName")
    method_name = data.get("methodName")
    customer_name = data.get("customerName")

    # Find the payment status record for this order
    payment_status = (
        request.env["pos.payment.status"]
        .sudo()
        .search([("merchant_order", "=", merchant_order)], limit=1)
    )
    if payment_status:
        # For existing record , update the filed values
        payment_status.reference = transaction
        payment_status.provider_name = provider_name
        payment_status.received_method = method_name
        payment_status.customer_name = customer_name
        payment_status.total = total_amount
        payment_status.state = status
        payment_status.paid_at = convert_paid_at(created_at)
    else:
        # create a new record
        request.env["pos.payment.status"].sudo().create(
            {
                "reference": transaction,
                "merchant_order": merchant_order,
                "provider_name": provider_name,
                "received_method": method_name,
                "customer_name": customer_name,
                "total": total_amount,
                "state": status,
                "paid_at": datetime.now(),
            }
        )


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
        decrypted_str = request.env['pos.payment'].aes_decrypt(payment_result)

        try:
            result = json.loads(decrypted_str)
        except json.JSONDecodeError:
            print("Failed to parse decrypted data as JSON:")
            print(decrypted_str)
            raise
        create_new_pos_payment_status(result)
        return "Data is store successfully"

    # Start write to pos.payment.status for the sale order line with draft state.
    @http.route(
        "/pos/payment_status/create_draft",
        type="json",
        auth="user",
        csrf=False,
        methods=["POST"],
    )
    def create_payment_status_draft(self, **kwargs):
        """Create a new pos.payment.status record from the provided kwargs."""
        create_new_pos_payment_status(kwargs)
        return "Data is store successfully"
