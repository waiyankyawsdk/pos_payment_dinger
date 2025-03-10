import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PaymentDinger } from "@pos_test/app/payment_dinger";

register_payment_method("dinger", PaymentDinger);