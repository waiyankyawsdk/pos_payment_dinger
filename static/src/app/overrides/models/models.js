import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PaymentDinger } from "@pos_payment_dinger/app/payment_dinger";

register_payment_method("dinger", PaymentDinger);