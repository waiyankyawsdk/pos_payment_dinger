import { _t } from "@web/core/l10n/translation";
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { ConfirmPopup } from "@web/core/confirmation_dialog/confirmation_dialog";
import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { ConfirmationDialog, AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PrebuiltPopup } from "@pos_payment_dinger/prebuilt_popup/prebuilt_popup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { sprintf } from "@web/core/utils/strings";
import { loadJS } from "@web/core/assets";
const { DateTime } = luxon;
export class PaymentDinger extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.paymentLineResolvers = {};
        this.selectedMethod = null;
        this.dialog = this.env.services.dialog;
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
//        var data = this._dinger_pay_data();
        var line = order.payment_ids.find((paymentLine) => paymentLine.uuid === uuid);


        this.processPayment(this.selectedMethod,"test",line,uuid,order);

        /* For testing
        //Start call token
        this._call_dinger(data).then((response) => {
         // This will log the resolved JSON result
            if(response.message == 'Authentication Success'){

               // Process to show popup for the prebuilt checkout form
               this.processPayment(this.selectedMethod,response,line,uuid,order);
            }
            else{
                return false;
            }
         }).catch((error) => {
            console.error("Error fetching token:", error);
         });
         */
    }

    // This method is parse value to show checkout form
    async processPayment(selectedMethod,respone_token,line,uuid,order) {
        if (selectedMethod != '') {
            this._call_dinger_payment(respone_token,selectedMethod, line,uuid).then((response_pay) => {
//                if(response_pay.message == 'Request Success'){
//                    line.set_payment_status("done");
//                    return this.waitForPaymentConfirmation(line,order);
//                }
                    if (typeof response_pay !== 'undefined' && response_pay) {
                        line.set_payment_status("done");
                        return this.waitForPaymentConfirmation(line, order);
                    } else {
                        console.warn("No payload returned from Dinger popup.");
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
        const order = this.pos.get_order();

        const payload_result = await makeAwaitable(this.dialog, PrebuiltPopup, {
            title: _t("Custom Popup!"),
            order: order,
            line: line,
            uuid: uuid,
            paymentMethodType: this.payment_method_id.name,
            paymentMethodId:this.payment_method_id.id,
            token:token,
        },);
        //        this.validateOrder(true);
        return payload_result;
    }

    waitForPaymentConfirmation(order,line) {
        return new Promise((resolve) => {
            this.paymentLineResolvers[this.pending_dinger_line().uuid] = resolve;
        });
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
