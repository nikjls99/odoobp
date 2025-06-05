import { EcpayConfirmPopup } from "@l10n_tw_edi_ecpay_pos/js/ecpay_confirm_popup";
import { EcpayInfoPopup } from "@l10n_tw_edi_ecpay_pos/js/ecpay_info_popup";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        if (
            this.currentOrder.get_partner() &&
            this.currentOrder.get_partner().id === this.pos.session._default_tw_customer_id
        ) {
            this.currentOrder.set_to_invoice(true);
            this.currentOrder.set_invoice_info(false, false, false, false);
        }
    },

    // @override
    async toggleIsToInvoice() {
        if (
            this.pos.company.country_id?.code === "TW" &&
            this.pos.config.is_ecpay_enabled &&
            !this.currentOrder.is_to_invoice() &&
            !this.currentOrder.get_orderlines().some((line) => line.refunded_orderline_id) &&
            this.currentOrder.get_partner() &&
            this.currentOrder.get_partner().id !== this.pos.session._default_tw_customer_id
        ) {
            const l10n_tw_edi_is_b2b = Boolean(
                this.currentOrder.get_partner().parent_id ||
                    this.currentOrder.get_partner().company_type === "company"
            );
            let confirm = false;
            if (l10n_tw_edi_is_b2b) {
                confirm = { confirm: 1 }; // B2B orders do not require confirmation
            } else {
                confirm = await makeAwaitable(this.dialog, EcpayConfirmPopup, {
                    order: this.currentOrder,
                });
            }

            if (!confirm) {
                this.currentOrder.set_to_invoice(!this.currentOrder.is_to_invoice());
                return;
            }

            if (confirm.confirm === 1) {
                const payload = await makeAwaitable(this.dialog, EcpayInfoPopup, {
                    order: this.currentOrder,
                });

                if (!payload) {
                    this.currentOrder.set_to_invoice(!this.currentOrder.is_to_invoice());
                    return;
                }

                this.currentOrder.set_invoice_info(
                    "printFlag" in payload.data ? payload.data.printFlag : false,
                    "loveCode" in payload.data ? payload.data.loveCode : false,
                    "carrierType" in payload.data && payload.data.carrierType !== "0"
                        ? payload.data.carrierType
                        : false,
                    "carrierNumber" in payload.data ? payload.data.carrierNumber : false
                );
                if ("identifier" in payload.data) {
                    let partner_id = this.currentOrder.get_partner().id;
                    if (this.currentOrder.get_partner().parent_name) {
                        partner_id = this.currentOrder.get_partner().parent_id.id;
                    }
                    await this.pos.data.ormWrite("res.partner", [partner_id], {
                        vat: payload.data.identifier,
                    });
                }
            } else {
                this.currentOrder.set_invoice_info(false, false, false, false);
            }
        }
        super.toggleIsToInvoice(...arguments);
    },
});
