import { _t } from "@web/core/l10n/translation";
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { ConfirmPopup } from "@web/core/confirmation_dialog/confirmation_dialog";
import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { ConfirmationDialog, AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { sprintf } from "@web/core/utils/strings";
import { loadJS } from "@web/core/assets";
import { markup } from "@odoo/owl";
const { DateTime } = luxon;
export class PaymentDinger extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.paymentLineResolvers = {};
        this.selectedMethod = null;
    }

    //After the payment is selected this method is work
    async send_payment_request(uuid) {
        super.send_payment_request(uuid);
        return this._dinger_pay(uuid)
    }

    _dinger_pay(uuid) {
        var order = this.pos.get_order();

        if (order.get_selected_paymentline().amount < 0) {
            window.alert("Cannot process transactions with negative amount.")
            return Promise.resolve();
        }
        var data = this._dinger_pay_data();
        var line = order.payment_ids.find((paymentLine) => paymentLine.uuid === uuid);
        this._call_dinger(data).then((response) => {
         // This will log the resolved JSON result
            if(response.message == 'Authentication Success'){

                  this.env.services.dialog.add(AlertDialog, {
                    title: _t("Select Payment Methods"),
                    body: markup(`
                            <div class="card shadow-sm">
                                <!-- Payment Method Selection -->
                                <div class="list-group">
                                    <label class="list-group-item list-group-item-action d-flex align-items-center gap-2 py-3">
                                        <input class="form-check-input me-2" type="radio" name="payment_method" value="kpay" id="kpay">
                                        <span class="fw-bold">Kpay</span>
                                    </label>

                                    <label class="list-group-item list-group-item-action d-flex align-items-center gap-2 py-3">
                                        <input class="form-check-input me-2" type="radio" name="payment_method" value="wavepay" id="wavepay">
                                        <span class="fw-bold">Wave Pay</span>
                                    </label>
                                </div>
                        </div>
                    `),
                    confirm: () => {
                        const selectedRadio = document.querySelector('input[name="payment_method"]:checked');
                        if (selectedRadio) {
                            this.selectedMethod = selectedRadio.value;  // Get the selected value
                            // Proceed with next payment logic
                            this.processPayment(this.selectedMethod,response,line,uuid,order);
                        } else {
                            this.env.services.dialog.add(ConfirmationDialog, {
                                    title: _t('Warnning'),
                                    body: _t('No payment method is selected'),
                                    confirmLabel: _t('OK'),
                                    //If selection fail to recall to select box of payment
                                    confirm: () => {},
                                    cancelLabel: _t('Discard'),
                                    cancel: () => { },
                                });
                        }
                    },
                    cancel: () => {}
                  })
            }
            else{
                return false;
            }
        }).catch((error) => {
            console.error("Error fetching token:", error);
        });
    }

    // Handle the payment process based on the selected method
    async processPayment(selectedMethod,respone_token,line,uuid,order) {
        if (selectedMethod === 'kpay') {
            // Process Kpay payment
            // Your Kpay payment logic here
            this._call_dinger_payment(respone_token,"kpay", line,uuid).then((response_pay) => {
                    if(response_pay.message == 'Request Success'){
                        line.set_payment_status("done");
                        // Here i want to add the pop up box to get the payment method
                        return this.waitForPaymentConfirmation(line,order);
                        //Here we need to add the payment of method with pop up box selection
                }
                }).catch((error) => {
                    console.error("Error fetching token:", error);
                });

        } else if (selectedMethod === 'wavepay') {
            // Your Wave Pay payment logic here
            this._call_dinger_payment(respone_token,"wavepay", line,uuid).then((response_pay) => {
                    if(response_pay.message == 'Request Success'){
                        line.set_payment_status("done");
                        // Here i want to add the pop up box to get the payment method
                        return this.waitForPaymentConfirmation(line,order);
                        //Here we need to add the payment of method with pop up box selection
                }
                }).catch((error) => {
                    console.error("Error fetching token:", error);
                });
        } else {
            console.log("Invalid payment method");
        }
    }

    _dinger_get_sale_id() {
        var config = this.pos.config;
        return sprintf("%s (ID: %s)", config.display_name, config.id);
    }

    set_most_recent_service_id(id) {
        this.most_recent_service_id = id;
    }
    pending_dinger_line() {
        return this.pos.getPendingPaymentLine("dinger");
    }

    _dinger_pay_data() {
        var order = this.pos.get_order();
        var config = this.pos.config;
        var line = order.get_selected_paymentline();
        var data = {
            SaleToPOIRequest: {
                MessageHeader: Object.assign(this._dinger_common_message_header(), {
                    MessageCategory: "Payment",
                }),
                PaymentRequest: {
                    SaleData: {
                        SaleTransactionID: {
                            TransactionID: `${order.uuid}--${order.session_id.id}`,
                            TimeStamp: DateTime.now().toFormat("yyyy-MM-dd'T'HH:mm:ssZZ"), // iso format: '2018-01-10T11:30:15+00:00'
                        },
                    },
                    PaymentTransaction: {
                        AmountsReq: {
                            Currency: this.pos.currency.name,
                            RequestedAmount: line.amount,
                        },
                    },
                },
            },
        };
        return data;
    }

    _dinger_common_message_header() {
        var config = this.pos.config;
        this.most_recent_service_id = Math.floor(Math.random() * Math.pow(2, 64)).toString(); // random ID to identify request/response pairs
        this.most_recent_service_id = this.most_recent_service_id.substring(0, 10); // max length is 10

        return {
            ProtocolVersion: "3.0",
            MessageClass: "Service",
            MessageType: "Request",
            SaleID: this._dinger_get_sale_id(config),
            ServiceID: this.most_recent_service_id,
            POIID: this.payment_method_id.dinger_terminal_identifier,
        };
    }

//  This method is get the token of the dinger.
    _call_dinger(data, operation = false) {
        return this.pos.data
            .silentCall("pos.payment", "dinger_connection_token", [])
            .then((result) => {
                return result;  // Ensure the function returns the resolved response
            })
            .catch((error) => {
                console.error("Dinger API Call Failed:", error);
                return Promise.reject(error);
            });
    }

    async _call_dinger_payment(token,payment_method_type, line,uuid){
        line.payment_type=payment_method_type;
        // Load the QRCode library dynamically if not already loaded
        await loadJS("https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js");
        return new Promise((resolve, reject) => {
        // Create a container div for the QR code
        const qrCodeContainerId = "dynamic_qr_code";
        const qrDiv = `<div id="${qrCodeContainerId}" class="d-flex justify-content-center"></div>`

        // Show the dialog with a placeholder div for QR code
        this.env.services.dialog.add(AlertDialog, {
            title: _t("Scan Me"),
            body: markup(qrDiv),
            confirm: () => {
                // Handle confirmation logic if needed
                this.pos.data.silentCall("pos.payment", "make_payment", [
                    [this.payment_method_id.id],  // Pass payment method ID
                    token,
                    payment_method_type,
                    ]).then((result) => {
                        resolve(result);  // Ensure the function returns the resolved response
                    }).catch((error) => {
                        reject(error);
                    });
                },
            cancel: () => {
                reject(new Error("User cancelled payment"));
                // Handle cancellation logic if needed
            }
        });
        // Wait for the DOM to update before generating the QR code
        setTimeout(() => {
            let qrElement = document.getElementById(qrCodeContainerId);
            if (qrElement) {
                new QRCode(qrElement, {
                    text: "hello",  // Use token as QR data
                    width: 150,
                    height: 150
                });
            }
        }, 300); // Delay to allow the modal to render
        });
    }

    waitForPaymentConfirmation(order,line) {
//        order.add_paymentline(line);
        console.log(line)
        console.log("Printing for the order")
        console.log(order)
        return new Promise((resolve) => {});
    }

    //-------------------------------------------------------------------------------------------------------------------------------------
    //Make canceable for for the retry condition by clicking on the red cross button
    async send_payment_cancel(order, uuid) {
        /**
         * Override
         */
        super.send_payment_cancel(...arguments);
        const line = this.pos.get_order().get_selected_paymentline();
        const dingerCancel = await this.dingerCancel();
        if (dingerCancel) {
            line.set_payment_status("retry");
            return true;
        }
    }

    async dingerCancel() {
        if (!this.terminal) {
            return true;
        } else if (this.terminal.getConnectionStatus() != "connected") {
            return true;
        } else {
            const cancelCollectPaymentMethod = await this.terminal.cancelCollectPaymentMethod();
            if (cancelCollectPaymentMethod.error) {
            }
            return true;
        }
    }
    //------------------------------------------------------------------------------------------------------------------

}
