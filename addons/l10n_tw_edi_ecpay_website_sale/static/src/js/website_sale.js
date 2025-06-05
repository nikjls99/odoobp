/** @odoo-module **/
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { WebsiteSale } from "@website_sale/js/website_sale";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

WebsiteSale.include({
    events: Object.assign({}, WebsiteSale.prototype.events || {}, {
        "change #print_group": "_onChangePrintGroup",
        "change #l10n_tw_edi_carrier_type": "_onChangeCarrierType",
        "input #identifier": "_onInputIdentifier",
        "input #l10n_tw_edi_carrier_number": "_onInputCarrierNumber",
        "input #l10n_tw_edi_love_code": "_onInputLoveCode",
        "click #validate_carrier_number": "_onClickValidateCarrierNumber",
        "click #validate_love_code": "_onClickValidateLoveCode",
        "click #validate_tax_id": "_onClickValidateTaxID",
        "click #reenter_carrier_number": "_onClickReenterCarrierNumber",
        "click #reenter_love_code": "_onClickReenterLoveCode",
        "click #reenter_tax_id": "_onClickReenterTaxID",
    }),

    init() {
        this._super(...arguments);
        if (document.querySelector("#ecpay_invoice_method")) {
            this.showLoveCode = !document
                .querySelector("#ecpay_invoice_love_code")
                .classList.contains("d-none");
            this.showCarrierType = !document
                .querySelector("#ecpay_carrier_type_group")
                .classList.contains("d-none");
            this.showCarrier = !document
                .querySelector("#ecpay_invoice_carrier_number")
                .classList.contains("d-none");
            this.validIdentifier = false;
            this.validCarrierNumber = false;
            this.validLoveCode = false;
            this.showValidateCarrierNumber = false;
            if (
                document.querySelector("#l10n_tw_edi_carrier_type").value === "3" &&
                document.querySelector("#l10n_tw_edi_carrier_number").value !== ""
            ) {
                this.showValidateCarrierNumber = true;
                document.querySelector("#validate_carrier_number").classList.remove("d-none");
            }
            this.showValidateLoveCode = false;
            if (document.querySelector("#l10n_tw_edi_love_code").value !== "") {
                this.showValidateLoveCode = true;
                document.querySelector("#validate_love_code").classList.remove("d-none");
            }
            this.showValidateTaxID = false;
            if (document.querySelector("#identifier").value !== "") {
                this.showValidateTaxID = true;
                document.querySelector("#validate_tax_id").classList.remove("d-none");
            }
        }
    },

    _get_token_info() {
        const form = document.getElementById("ecpay_invoice_form");
        const saleOrderId = form.getAttribute("date-order-id");
        const accessToken = form.getAttribute("data-access-token");
        return [saleOrderId, accessToken];
    },

    showInvoiceItems() {
        const elementsToShow = new Map([
            ["#ecpay_invoice_love_code", this.showLoveCode],
            ["#ecpay_carrier_type_group", this.showCarrierType],
            ["#ecpay_invoice_carrier_number", this.showCarrier],
            ["#validate_carrier_number", this.showValidateCarrierNumber],
            ["#validate_love_code", this.showValidateLoveCode],
            ["#validate_tax_id", this.showValidateTaxID],
        ]);

        elementsToShow.forEach((isShown, selector) => {
            this.el.querySelector(selector).classList.toggle("d-none", !isShown);
        });
    },

    _onChangePrintGroup(ev) {
        const printGroup = ev.target.value;
        if (printGroup === "0") {
            this.showLoveCode = false;
            this.showCarrierType = true;
        } else if (printGroup === "1") {
            this.showLoveCode = false;
            this.showCarrierType = false;
        } else {
            this.showLoveCode = true;
            this.showCarrierType = false;
        }
        this.showInvoiceItems();
    },

    _onChangeCarrierType(ev) {
        const carrierType = ev.target.value;
        if (carrierType === "2") {
            document.querySelector("#l10n_tw_edi_carrier_number").placeholder = _t(
                "2 capital letters following 14 digits"
            );
            this.showCarrier = true;
            this.showValidateCarrierNumber = false;
        } else if (carrierType === "3") {
            document.querySelector("#l10n_tw_edi_carrier_number").placeholder = _t(
                "/ following 7 alphanumeric or +-. string"
            );
            this.showCarrier = true;
            this.showValidateCarrierNumber =
                document.querySelector("#l10n_tw_edi_carrier_number").value !== "";
        } else {
            this.showCarrier = false;
        }
        this.validCarrierNumber = false;
        this.showInvoiceItems();
    },

    _onInputIdentifier: function (ev) {
        this.validIdentifier = false;
        const re = /^[0-9]{8}$/;
        if (re.test(ev.target.value)) {
            this.showValidateTaxID = true;
        } else {
            this.showValidateTaxID = false;
        }
        this.showInvoiceItems();
    },

    _onInputCarrierNumber(ev) {
        const carrierType = this.el.querySelector("#l10n_tw_edi_carrier_type").value;
        if (carrierType === "2") {
            const re = /^[A-Z]{2}[0-9]{14}$/;
            this.validCarrierNumber = Boolean(re.test(ev.target.value));
        } else if (carrierType === "3") {
            const re = /^\/[0-9a-zA-Z+-.]{7}$/;
            if (re.test(ev.target.value)) {
                this.showValidateCarrierNumber = true;
            } else {
                this.showValidateCarrierNumber = false;
            }
        } else {
            this.showValidateCarrierNumber = false;
        }
        this.showInvoiceItems();
    },

    _onInputLoveCode(ev) {
        this.validLoveCode = false;
        const re = /^([xX]{1}[0-9]{2,6}|[0-9]{3,7})$/;
        if (re.test(ev.target.value)) {
            this.showValidateLoveCode = true;
        } else {
            this.showValidateLoveCode = false;
        }
        this.showInvoiceItems();
    },

    async _onClickValidateCarrierNumber() {
        try {
            const [saleOrderId, accessToken] = this._get_token_info();
            const result = await rpc("/payment/ecpay/check_mobile_barcode/" + saleOrderId, {
                access_token: accessToken,
                carrier_number: this.el.querySelector("#l10n_tw_edi_carrier_number").value,
            });
            if (result) {
                this.validCarrierNumber = true;
                this.showValidateCarrierNumber = false;
                this.el.querySelector("#reenter_carrier_number").classList.remove("d-none");
                this.el.querySelector("#l10n_tw_edi_carrier_number").readonly = true;
            } else {
                this.call("dialog", "add", WarningDialog, {
                    title: _t("Error"),
                    message: _t("Carrier number is invalid"),
                });
            }
        } catch (error) {
            this.call("dialog", "add", WarningDialog, {
                title: _t("ECpay Error"),
                message: _t(error.data.message),
            });
        }
        this.showInvoiceItems();
    },

    async _onClickValidateLoveCode() {
        try {
            const [saleOrderId, accessToken] = this._get_token_info();
            const result = await rpc("/payment/ecpay/check_love_code/" + saleOrderId, {
                access_token: accessToken,
                love_code: this.el.querySelector("#l10n_tw_edi_love_code").value,
            });

            if (result) {
                this.validLoveCode = true;
                this.showValidateLoveCode = false;
                this.el.querySelector("#reenter_love_code").classList.remove("d-none");
                this.el.querySelector("#l10n_tw_edi_love_code").readOnly = true;
            } else {
                this.call("dialog", "add", WarningDialog, {
                    title: _t("Error"),
                    message: _t("Love code is invalid"),
                });
            }
        } catch (error) {
            this.call("dialog", "add", WarningDialog, {
                title: _t("ECpay Error"),
                message: _t(error.data.message),
            });
        }
        this.showInvoiceItems();
    },

    async _onClickValidateTaxID() {
        try {
            const [saleOrderId, accessToken] = this._get_token_info();
            const result = await rpc("/payment/ecpay/check_tax_id/" + saleOrderId, {
                access_token: accessToken,
                identifier: this.el.querySelector("#identifier").value,
            });
            if (result) {
                this.validIdentifier = true;
                this.showValidateTaxID = false;
                this.el.querySelector("#reenter_tax_id").classList.remove("d-none");
                this.el.querySelector("#identifier").readOnly = true;
            } else {
                this.call("dialog", "add", WarningDialog, {
                    title: _t("Error"),
                    message: _t("Tax ID is invalid"),
                });
            }
        } catch (error) {
            this.call("dialog", "add", WarningDialog, {
                title: _t("ECpay Error"),
                message: _t(error.data.message),
            });
        }
        this.showInvoiceItems();
    },

    _onClickReenterCarrierNumber() {
        this.validCarrierNumber = false;
        this.showValidateCarrierNumber = true;
        this.el.querySelector("#reenter_carrier_number").classList.add("d-none");
        this.el.querySelector("#l10n_tw_edi_carrier_number").removeAttribute("readonly");
        this.showInvoiceItems();
    },

    _onClickReenterLoveCode() {
        this.validLoveCode = false;
        this.showValidateLoveCode = true;
        this.el.querySelector("#reenter_love_code").classList.add("d-none");
        this.el.querySelector("#l10n_tw_edi_love_code").removeAttribute("readonly");
        this.showInvoiceItems();
    },

    _onClickReenterTaxID() {
        this.validIdentifier = false;
        this.showValidateTaxID = true;
        this.el.querySelector("#reenter_tax_id").classList.add("d-none");
        this.el.querySelector("#identifier").removeAttribute("readonly");
        this.showInvoiceItems();
    },
});
