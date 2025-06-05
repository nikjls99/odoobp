import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

const REQUEST_TIMEOUT = 5000;
const INACTIVITY_TIMEOUT = 90000;

export class PineLabsError extends Error {}

export class PineLabs {
    constructor(...args) {
        this.setup(...args);
    }

    setup(env, pineLabsPaymentMethod, access_token, pos_config, errorCallback) {
        this.env = env;
        this.pineLabsPaymentMethod = pineLabsPaymentMethod;
        this.access_token = access_token;
        this.pos_config = pos_config;
        this.errorCallback = errorCallback;
        this.savedOrder = false;
        this.pollTimeout = null;
        this.inactivityTimeout = null;
        this.paymentStopped = false;
    }

    handleRazorpayResponse(response) {
        if (response?.error) {
            this.paymentStopped
                ? this.errorCallback(new PineLabsError(_t("Transaction failed due to inactivity")))
                : this.errorCallback(new PineLabsError(response.error));
            this.removePaymentHandler(["plutusTransactionReferenceID"]);
            return false;
        }
        localStorage.setItem(
            "plutusTransactionReferenceID",
            response?.plutusTransactionReferenceID
        );
        response?.payment_ref_no && localStorage.setItem("paymentRefNo", response?.payment_ref_no);
        return true;
    }

    async cancelPayment(order) {
        const data = {
            plutusTransactionReferenceID: localStorage.getItem("plutusTransactionReferenceID"),
        };
        try {
            const cancelResponse = await rpc("/pos-self-order/pine-labs-cancel-transaction/", {
                access_token: this.access_token,
                order_id: order.id,
                payment_data: data,
                payment_method_id: this.pineLabsPaymentMethod.id,
            });

            if (cancelResponse) {
                if (cancelResponse.error) {
                    this.errorCallback(new PineLabsError(cancelResponse.error, "warning"));
                    return true;
                }
                this.removePaymentHandler(["plutusTransactionReferenceID", "paymentRefNo"]);
            }
        } catch (error) {
            this.errorCallback(error);
            return false;
        }
    }

    async startPayment(order) {
        const paymentRequestResponse = await this.processPayment(order);
        if (paymentRequestResponse) {
            await this.paymentPolling(this.savedOrder);
        }
    }

    async processPayment(order) {
        try {
            const initialResponse = await rpc(`/kiosk/payment/${this.pos_config.id}/kiosk`, {
                order: order.serializeForORM(),
                access_token: this.access_token,
                payment_method_id: this.pineLabsPaymentMethod.id,
            });
            if (initialResponse) {
                this.savedOrder = initialResponse.order[0];
                return this.handleRazorpayResponse(initialResponse.payment_status);
            }
        } catch (error) {
            this.errorCallback(error);
            return false;
        }
    }

    /**
     * Polling
     * This method calls and handles the Pine Labs payment status.
     * It polls every 5 seconds until payment status is found or timeout occurs.
     */
    async paymentPolling(order) {
        const data = {
            plutusTransactionReferenceID: localStorage.getItem("plutusTransactionReferenceID"),
            payment_ref_no: localStorage.getItem("paymentRefNo"),
        };
        this.stopInactivePayment().then(() => (this.paymentStopped = true));
        const fetchPaymentStatus = async () => {
            try {
                // The transaction will be canceled due to inactivity within 90 seconds.
                if (this.paymentStopped) {
                    await this.cancelPayment(order);
                    return false;
                }

                const statusResponse = await rpc(
                    "/pos-self-order/pine-labs-fetch-payment-status/",
                    {
                        access_token: this.access_token,
                        order_id: order.id,
                        payment_data: data,
                        payment_method_id: this.pineLabsPaymentMethod.id,
                    }
                );
                if (!statusResponse) {
                    this.errorCallback(new PineLabsError(_t("Failed to fetch payment status.")));
                    return false;
                }
                if (statusResponse.error) {
                    this.handleRazorpayResponse(statusResponse);
                    return false;
                }

                const paymentStatus = statusResponse.status;

                if (paymentStatus === "TXN APPROVED") {
                    this.removePaymentHandler(["plutusTransactionReferenceID"]);
                    return true;
                }
                // Clear the previous timeout before setting a new one
                clearTimeout(this.pollTimeout);
                this.pollTimeout = setTimeout(fetchPaymentStatus, REQUEST_TIMEOUT);
            } catch (error) {
                this.errorCallback(error);
            }
        };
        await fetchPaymentStatus();
    }

    stopInactivePayment() {
        return new Promise(
            (resolve) => (this.inactivityTimeout = setTimeout(resolve, INACTIVITY_TIMEOUT))
        );
    }

    removePaymentHandler(payment_data) {
        payment_data.forEach((data) => {
            localStorage.removeItem(data);
        });
        clearTimeout(this.pollTimeout);
        clearTimeout(this.inactivityTimeout);
        this.paymentStopped = false;
    }
}
