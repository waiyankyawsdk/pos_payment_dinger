import { Component, useState, useRef, useEffect } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { loadJS } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

export class PrebuiltPopup extends Component {
    static template = "pos_payment_dinger.PrebuiltPopup";
    static components = { Dialog };
    static props = {
        order: Object,
        line: Object,
        uuid: String,
        paymentMethodType: String,
        paymentMethodId: Number,
        getPayload: Function,
        title: String,
        close: Function,
    };

    setup() {
        this.qrCodeRef = useRef("qrCodeRef");
        this._qrResult = null; // Store QR result for step 3
        this.orm = useService('orm');
        this.pos = usePos();
        this.order = this.props.order;
        this.line = this.props.line;
        this.uuid = this.props.uuid;
        this.paymentMethodType = this.props.paymentMethodType;
        this.paymentMethodName=this.props.paymentMethodName;
        this.paymentMethodId = this.props.paymentMethodId;
        this.countryCode = "";
        this._buttonClicked = false;

        const partner = this.props.order.get_partner?.() || {};
        const orderlines = this.order.get_orderlines?.() || [];
        const amount_total = this.order.getTotalDue?.() || 0.00;
        const safeNumber = this.safeNumber.bind(this);

        this.state = useState({
            paymentPaid: false,
            step: 1,
            customerName: partner.name,
            clientId: partner.id,
            email: partner.email,
            phone: partner.phone,
            address: partner.contact_address,
            billCity: partner.city,
            state: partner.state_id?.name || "Yangon",
            country: partner.country_id?.name || "Myanmar",
            postalCode: partner.zip,
            paymentMethod: this.paymentMethodType,
            total: amount_total,
            orderLines: orderlines.map(l => ({
                product: l.product_id.display_name,
                taxes: l.tax_ids,
                discount: safeNumber(l.discount),
                price: safeNumber(l.price_unit),
                quantity: l.qty,
            })),
        });

        // Effect: generate QR code when step changes to 3 and _qrResult is set
        useEffect(
            () => {
                if (this.state.step === 3 && this._qrResult) {
                    this.generateQRCode(this._qrResult);
                }
            },
            () => [this.state.step]
        );
    }

    safeNumber(val) {
        return (val === null || val === false || val === "" || (Array.isArray(val) && val.length === 0)) ? 0.00 : val;
    }

    // Process to convert text to qr code and show in the qrElement
    async generateQRCode(text) {
        await loadJS("/pos_payment_dinger/static/src/lib/qrcode.js");
        const qrElement = this.qrCodeRef.el;
        if (qrElement) {
            const jsonString = JSON.stringify(text);
            qrElement.innerHTML = '';
            new QRCode(qrElement, {
                text: jsonString,
                width: 150,
                height: 150
            });
        } else {
            console.log("QR element is not found!");
        }
    }

    async nextStep() {
        if (this.state.step < 3) {
            if (this.state.step == 2) {
                if (this._buttonClicked) return;
                this._buttonClicked = true;
                // Get country code
//                await this.pos.data.silentCall("pos.payment", "get_country_code", [
//                    [this.paymentMethodId],
//                    this.state.country,
//                ]).then((result) => {
//                    this.countryCode = result;
//                }).catch((error) => {
//                    throw error;
//                });
                this.countryCode="MM";

                // Create Payload
                const payload = {
                    providerName: this.paymentMethodType,
                    methodName: "QR",
                    totalAmount: parseFloat(this.state.total || 0.0),
                    currency: this.pos.currency?.name || "MMK",
                    orderId: this.order?.name || "",
                    email: this.state.email || "",
                    customerPhone: this.state.phone || "",
                    customerName: this.state.customerName || "",
                    state: this.state.state || "Yangon",
                    country: this.countryCode || "MM",
                    postalCode: this.state.postalCode || "15015",
                    billAddress: this.state.address || "No Address",
                    billCity: this.state.billCity || "Yangon",
                    items: JSON.stringify(this.state.orderLines.map(line => ({
                        name: line.product,
                        amount: (line.price).toFixed(2),
                        quantity: line.quantity.toString()
                    }))),
                };


                // Call dinger with payload
                await this.pos.data.silentCall("pos.payment", "make_payment", [
                    payload,
                ]).then(async (result) => {
                    console.log("Start working result :",result);
                    if (result) {
                        console.log("Start working make payment");
                        this._qrResult = result; // Store for useEffect
                        this.state.step += 1;    // Triggers QR code generation in useEffect
                        await this.savePaymentStatus();
                        console.log("Start working make payment");
                        this.pollPaymentStatus(this.order.name);
                    }
                }).catch((error) => {
                    throw error;
                });
            } else {
                this.state.step += 1;
            }
        }
    }

    prevStep() {
        if (this.state.step > 1) {
            this.state.step -= 1;
        }
    }

    onStepClick = (stepNumber) => {
        if (stepNumber < this.state.step) {
            this.state.step = stepNumber;
        }
    }

    //By using rpc call to main method to write the data with draft state
    async savePaymentStatus() {
        const values = {
            'merchantOrderId': this.order.name,
            'transactionId':"",
            'providerName': this.paymentMethodType,
            'methodName': "QR",
            'customerName': this.state.customerName,
            'totalAmount': parseFloat(this.state.total || 0.0),
            'transactionStatus': 'draft',
            'createdAt':'20250618 105033'
        };
        rpc("/pos/payment_status/create_draft", values);
    }

    //Poll status from pos_payment_status.py by searching the line with merchant_order field to get the status value
    async pollPaymentStatus(merchantOrder) {
        let continuePolling = true;
        while (continuePolling) {
            try {
                const results = await this.orm.call(
                    'pos.payment.status',
                    'search_read',
                    [[['merchant_order', '=', merchantOrder]]],
                    { limit: 1, order: 'paid_at desc' }
                );
                if (results.length > 0) {
                    const status = results[0];
                    if (status.state && status.state !== 'draft') {
                        continuePolling = false;
                        this.confirm();
                    } else {
                        await new Promise(resolve => setTimeout(resolve, 3000));
                    }
                } else {
                    await new Promise(resolve => setTimeout(resolve, 3000));
                }
            } catch (_) {
                await new Promise(resolve => setTimeout(resolve, 3000));
            }
        }
    }

    async confirm() {
        this.props.getPayload(this.state);
        this.props.close();
    }
}
