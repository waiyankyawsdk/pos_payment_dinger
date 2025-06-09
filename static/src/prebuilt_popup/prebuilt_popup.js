/** @odoo-module */
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { loadJS } from "@web/core/assets";
import { Component, useState} from "@odoo/owl";

export class PrebuiltPopup extends Component {
    static template = "pos_payment_dinger.PrebuiltPopup";
    static components = { Dialog };
    setup() {
        this.pos = usePos();
        this.order = this.props.order;
        this.line = this.props.line;
        this.uuid = this.props.uuid;
        this.paymentMethodType = this.props.paymentMethodType;
        this.paymentMethodId = this.props.paymentMethodId;
        this.token = this.props.token;
        const partner = this.props.order.get_partner?.() || {};
        const payment_lines = this.order.paymentlines;
        const orderlines = this.order.get_orderlines?.() || [];
        const amount_total = this.order.getTotalDue?.() || 0.00;
        const safeNumber = this.safeNumber.bind(this);
        const getTaxPercentage = this.getTaxPercentage.bind(this);

        this.state = useState({
            step: 1,
            customerName: partner.name,
            email: partner.email,
            phone: partner.phone,
            address: partner.address,
            paymentMethod: this.paymentMethodType,
            total:amount_total,
            orderLines: orderlines.map(l => ({
                product: l.product_id.display_name,
                tax:getTaxPercentage(l.tax_ids_after_fiscal_position),
                discount:safeNumber(l.discount),
                price: safeNumber(l.price_unit),
                quantity: l.qty,
            })),
        });
    }

    safeNumber(val) {
        return (val === null || val === false || val === "" || (Array.isArray(val) && val.length === 0)) ? 0.00 : val;
    }

    getTaxPercentage(taxIds) {
        if (!Array.isArray(taxIds) || taxIds.length === 0) return 0.00;

        let total = 0;
        for (let id of taxIds) {
            const tax = this.pos.taxes.find(t => t.id === id);
            if (tax) {
                total += tax.amount || 0;
            }
        }
        return total;
    }

    async generateQRCode(text) {
        await loadJS("https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js");
        // Create a container div for the QR code
        const qrCodeContainerId = "dynamic_qr_code";
        const qrDiv = `o<div id="${qrCodeContainerId}" class="d-flex justify-content-center"></div>`
            let qrElement = document.getElementById(qrCodeContainerId);
            if (qrElement) {
                 const jsonString = JSON.stringify(text);
                 console.log(jsonString);
                new QRCode(qrElement, {
                    text: jsonString,  // Use token as QR data
                    width: 150,
                    height: 150
                });
            }
    }

    //Here need to create payload and silent call to diner pay method
     async nextStep() {
        if (this.state.step < 3) {
            if(this.state.step==2){
            //Here initiate call to dinger with payload
                this.pos.data.silentCall("pos.payment", "make_payment", [
                                            [this.paymentMethodId],  // Pass payment method ID
                                            this.token,
                                            this.paymentMethodType,
                                            ]).then(async (result) => {
                                                await this.generateQRCode(result);
                                                this.state.step += 1;
                                            }).catch((error) => {
                                                throw error;
                                            });
            }
            else{
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
            console.log(stepNumber);
        }
    }

    //Compose payload and call dinger pay method from python
    async confirm() {
        this.props.getPayload(this.state);
        this.props.close();
    }
}
