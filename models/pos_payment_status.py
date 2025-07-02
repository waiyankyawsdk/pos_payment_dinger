"""
This module defines the PaymentStatus model, which is used to
store the status information from the Dinger payment callback.
"""

from datetime import datetime

from odoo import fields, models

from ...dinger_mixin.dataclasses.datamodels import (JournalCodeEnum,
                                                    TransactionStatusEnum)

@staticmethod
def convert_paid_at(date_str: str) -> str:
    """Convert the date string from Dinger format to Odoo format."""
    return datetime.strptime(date_str, "%Y%m%d %H%M%S").strftime("%Y-%m-%d %H:%M:%S")


class PaymentStatus(models.Model):
    """To store the status information from the dinger payment call back.
    This model is used to keep track of the status of payment transactions
    received from the Dinger payment gateway. It captures details such as
    the transaction ID, reference number, merchant order ID, provider name,
    customer name, total amount, status, and the date and time when the payment
    was made. This information is essential for reconciling payments and
    providing accurate transaction records within the Odoo system.

    Args:
        models (_type_): _description_
    """

    _name = "pos.payment.status"
    _description = "To store the status information from the dinger payment call back"
    _rec_name = "merchant_order"

    # That is transaction id from dinger
    reference = fields.Char(string="Reference")
    merchant_order = fields.Char(
        string="Merchant Order",
        help="Reference to the POS order associated with this payment status.",
    )
    provider_name = fields.Selection(
        selection=JournalCodeEnum.get_selection(), string="Provider Name"
    )
    received_method = fields.Char(string="Received By")
    customer_name = fields.Char(string="Customer")
    # Here need to change float to monetary : fact- return value are float amount
    total = fields.Float(string="Total")
    state = fields.Selection(
        selection=TransactionStatusEnum.get_selection(),
        string="Status",
        default="draft",
    )
    paid_at = fields.Datetime(string="Paid At")

    def create_payment_status(self, data:dict):
        """Create or update a pos.payment.status record based on the provided data.

        Args:
        data (dict): Payment data from Dinger webhook or draft creation.
        """
        merchant_order = data.get("merchantOrderId")  # This is order.name

        vals = {
            "reference": data.get("transactionId"),
            "provider_name": data.get("providerName"),
            "received_method": data.get("methodName"),
            "customer_name": data.get("customerName"),
            "total": data.get("totalAmount"),
            "state": data.get("transactionStatus"),
            "paid_at": convert_paid_at(data.get("createdAt")),
        }

        record = self.env["pos.payment.status"].sudo().search(
            [("merchant_order", "=", merchant_order)], limit=1
        )
        if record:
            record.write(vals)
        else:
            vals["merchant_order"] = merchant_order
            record=self.env["pos.payment.status"].sudo().create(vals)
        return record.id
