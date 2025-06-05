import { patch } from "@web/core/utils/patch";
import { SelfOrder } from "@pos_self_order/app/services/self_order_service";
import { PineLabs, PineLabsError } from "@pos_self_order_pine_labs/app/pine_labs";

patch(SelfOrder.prototype, {
    async setup() {
        await super.setup(...arguments);

        const pineLabsPaymentMethod = this.models["pos.payment.method"].find(
            (p) => p.use_payment_terminal === "pine_labs"
        );

        if (pineLabsPaymentMethod) {
            this.pineLabs = new PineLabs(
                this.env,
                pineLabsPaymentMethod,
                this.access_token,
                this.config,
                this.handlePineLabsError.bind(this)
            );
        }
    },

    filterPaymentMethods(pms) {
        const pm = super.filterPaymentMethods(...arguments);
        const razorpay_pm = pms.filter((rec) => rec.use_payment_terminal === "pine_labs");
        return [...new Set([...pm, ...razorpay_pm])];
    },

    handlePineLabsError(error, type) {
        this.paymentError = true;
        this.handleErrorNotification(error, type);
    },

    handleErrorNotification(error, type = "danger") {
        let errorMessage = "";
        if (error instanceof PineLabsError) {
            errorMessage = `Pine Labs Error: ${error.message}`;
            this.notification.add(errorMessage, {
                type: type,
            });
        } else {
            super.handleErrorNotification(...arguments);
        }
    },
});
