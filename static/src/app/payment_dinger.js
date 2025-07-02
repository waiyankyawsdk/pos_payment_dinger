import {_t} from '@web/core/l10n/translation';
import {PaymentInterface} from '@point_of_sale/app/payment/payment_interface';
import {PrebuiltPopup} from '@pos_payment_dinger/prebuilt_popup/prebuilt_popup';
import {makeAwaitable} from '@point_of_sale/app/store/make_awaitable_dialog';
export class PaymentDinger extends PaymentInterface {
	setup() {
		super.setup(...arguments);
		this.paymentLineResolvers = {};
		this.selectedMethod = null;
		this.dialog = this.env.services.dialog;
	}

	// After the payment is selected this method is work
	async send_payment_request(uuid) {
		super.send_payment_request(uuid);
		return this._dinger_pay(uuid);
	}

	_dinger_pay(uuid) {
		const order = this.pos.get_order();

		if (order.get_selected_paymentline().amount < 0) {
			return Promise.resolve();
		}

		const line = order.payment_ids.find(paymentLine => paymentLine.uuid === uuid);

		// Process to show popup for the prebuilt checkout form
		this.processPayment(this.selectedMethod, line, uuid);
	}

	// This method is parse value to show checkout form
	async processPayment(selectedMethod, line, uuid) {
		if (selectedMethod !== '') {
			this._call_dinger_payment(selectedMethod, line, uuid).then(response_pay => {
				if (typeof response_pay !== 'undefined' && response_pay) {
					// If payment of response pay have data, it make the payment is done and set the current order line to done
					line.set_payment_status('done');
				}
			}).catch(error => {
				console.error('Error fetching token:', error);
			});
		}
	}

	// Start show the prebuilt dialog box
	async _call_dinger_payment(payment_method_type, line, uuid) {
		line.payment_type = payment_method_type;
		const order = this.pos.get_order();

		const payload_result = await makeAwaitable(this.dialog, PrebuiltPopup, {
			title: _t('Custom Popup!'),
			order,
			line,
			uuid,
			paymentMethodType: this.payment_method_id.journal_code,
			paymentMethodId: this.payment_method_id.id,
		});
		return payload_result;
	}

	// Make canceable for for the retry condition by clicking on the red cross button
	async send_payment_cancel(args) {
		/**
         * Override
         */
		super.send_payment_cancel(...args);
		const line = this.pos.get_order().get_selected_paymentline();
		const dingerCancel = await this.dingerCancel();
		if (dingerCancel) {
			line.set_payment_status('retry');
			return true;
		}
	}

	async dingerCancel() {
		if (!this.terminal) {
			return true;
		}

		if (this.terminal.getConnectionStatus() !== 'connected') {
			return true;
		}

		return true;
	}
}
