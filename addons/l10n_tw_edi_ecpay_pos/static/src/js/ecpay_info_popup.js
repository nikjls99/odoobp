import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState } from "@odoo/owl";

export class EcpayInfoPopup extends Component {
    static template = "l10n_tw_edi_ecpay_pos.EcpayInfoPopup";
    static components = { Dialog };
    static props = {
        order: Object,
        getPayload: Function,
        close: Function,
        newPartner: { optional: true },
    };

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
        const order = this.props.order;
        const partner = order.get_partner() || this.props.newPartner;
        this.l10n_tw_edi_is_b2b = Boolean(
            partner && (partner.parent_id || partner.company_type === "company")
        );
        this.validTaxID = false;
        this.validCarrierNumber = false;
        this.validLoveCode = false;
        let printGroup = "0";
        if (order.l10n_tw_edi_is_print || this.l10n_tw_edi_is_b2b) {
            printGroup = "1";
        } else if (order.l10n_tw_edi_love_code) {
            printGroup = "2";
        }
        const identifierGroup = order.l10n_tw_edi_is_print && partner?.vat ? "1" : "0";
        this.state = useState({
            printGroup: printGroup,
            identifierGroup: identifierGroup,
            carrierType: order.l10n_tw_edi_carrier_type || "0",
            showLoveCode: Boolean(order?.l10n_tw_edi_love_code),
            showCarrierType: printGroup === "0",
            showCarrierNumber:
                order.l10n_tw_edi_carrier_type === "2" || order.l10n_tw_edi_carrier_type === "3",
            showValidateTaxID: Boolean(partner?.vat),
            showValidateCarrierNumber: Boolean(order?.l10n_tw_edi_carrier_number),
            showValidateLoveCode: Boolean(order?.l10n_tw_edi_love_code),
            showReEnterCarrierNumber: false,
            showReEnterLoveCode: false,
            showReEnterTaxID: false,
            carrierNumberPlaceholder: false,
            data: {},
        });

        onMounted(() => {
            if (partner) {
                document.querySelector("#identifier").value = partner.vat || "";
                document.querySelector("#l10n_tw_edi_love_code").value =
                    order.l10n_tw_edi_love_code || "";
                document.querySelector("#l10n_tw_edi_carrier_number").value =
                    order.l10n_tw_edi_carrier_number || "";
            }
        });
    }

    _onChangePrintGroup(ev) {
        const printGroup = ev.target.value;
        if (printGroup === "0") {
            this.state.showLoveCode = false;
            this.state.showCarrierType = true;
            this.state.printGroup = "0";
        } else if (printGroup === "1") {
            this.state.showLoveCode = false;
            this.state.showCarrierType = false;
            this.state.printGroup = "1";
        } else {
            this.state.showLoveCode = true;
            this.state.showCarrierType = false;
            this.state.printGroup = "2";
        }
    }

    _onChangeCarrierType(ev) {
        const carrierType = ev.target.value;
        if (carrierType === "2") {
            this.state.carrierNumberPlaceholder = _t("2 capital letters following 14 digits");
            this.state.showCarrierNumber = true;
        } else if (carrierType === "3") {
            this.state.carrierNumberPlaceholder = _t("/ following 7 alphanumeric or +-. string");
            this.state.showCarrierNumber = true;
        } else {
            this.state.showCarrierNumber = false;
        }
        this.validCarrierNumber = false;
        this.state.carrierType = carrierType;
    }

    _onInputCarrierNumber(ev) {
        const carrierType = document.querySelector("#l10n_tw_edi_carrier_type").value;
        if (carrierType === "2") {
            const re = /^[A-Z]{2}[0-9]{14}$/;
            this.validCarrierNumber = Boolean(re.test(ev.target.value));
        } else if (carrierType === "3") {
            const re = /^\/[0-9a-zA-Z+-.]{7}$/;
            this.state.showValidateCarrierNumber = Boolean(re.test(ev.target.value));
        } else {
            this.state.showValidateCarrierNumber = false;
        }
    }

    _onInputLoveCode(ev) {
        const re = /^([xX]{1}[0-9]{2,6}|[0-9]{3,7})$/;
        this.state.showValidateLoveCode = Boolean(re.test(ev.target.value));
    }

    _onInputTaxID(ev) {
        const re = /^[0-9]{8}$/;
        this.state.showValidateTaxID = Boolean(re.test(ev.target.value));
    }

    async _onClickValidateCarrierNumber() {
        try {
            const result = await this.pos.data.call(
                "pos.order",
                "l10n_tw_edi_check_mobile_barcode",
                [document.querySelector("#l10n_tw_edi_carrier_number").value]
            );
            if (result) {
                this.validCarrierNumber = true;
                this.state.showValidateCarrierNumber = false;
                this.state.showReEnterCarrierNumber = true;
                this.dialog.add(AlertDialog, {
                    title: _t("Success"),
                    body: _t("Carrier Number is valid"),
                });
            }
        } catch (error) {
            this.dialog.add(AlertDialog, {
                title: _t("ECpay Error"),
                body: error.data.message,
            });
        }
    }

    async _onClickValidateLoveCode() {
        try {
            const result = await this.pos.data.call("pos.order", "l10n_tw_edi_check_love_code", [
                document.querySelector("#l10n_tw_edi_love_code").value,
            ]);
            if (result) {
                this.validLoveCode = true;
                this.state.showValidateLoveCode = false;
                this.state.showReEnterLoveCode = true;
                this.dialog.add(AlertDialog, {
                    title: _t("Success"),
                    body: _t("Love Code is valid"),
                });
            }
        } catch (error) {
            this.dialog.add(AlertDialog, {
                title: _t("ECpay Error"),
                body: error.data.message,
            });
        }
    }

    async _onClickValidateTaxID() {
        try {
            const result = await this.pos.data.call("pos.order", "l10n_tw_edi_check_tax_id", [
                document.querySelector("#identifier").value,
            ]);
            if (result) {
                this.validTaxID = true;
                this.state.showValidateTaxID = false;
                this.state.showReEnterTaxID = true;
                this.dialog.add(AlertDialog, {
                    title: _t("Success"),
                    body: _t("Tax ID is valid"),
                });
            }
        } catch (error) {
            this.dialog.add(AlertDialog, {
                title: _t("ECpay Error"),
                body: error.data.message,
            });
        }
    }

    _onClickReenterCarrierNumber() {
        this.validCarrierNumber = false;
        this.state.showValidateCarrierNumber = true;
        this.state.showReEnterCarrierNumber = false;
    }

    _onClickReenterLoveCode() {
        this.validLoveCode = false;
        this.state.showValidateLoveCode = true;
        this.state.showReEnterLoveCode = false;
    }

    _onClickReenterTaxID() {
        this.validTaxID = false;
        this.state.showValidateTaxID = true;
        this.state.showReEnterTaxID = false;
    }

    validateData() {
        const partner = this.props.order.get_partner() || this.props.newPartner;
        const customerEmail = partner.email || "";
        const customerPhone = partner.phone || "";
        const identifier = document.querySelector("#identifier").value;
        if (this.l10n_tw_edi_is_b2b) {
            if (!this.validTaxID) {
                return [false, "Please enter correct tax id"];
            }
            if (!customerEmail && !customerPhone) {
                return [false, "Please enter correct email or phone number"];
            }
        }
        if (this.state.showLoveCode && !this.validLoveCode) {
            return [false, "Please enter correct love code"];
        }
        if (
            this.state.showCarrierType &&
            this.state.showCarrierNumber &&
            !this.validCarrierNumber
        ) {
            return [false, "Please enter correct carrier number"];
        }

        if (this.state.printGroup === "1") {
            this.state.data.printFlag = true;
            if (this.l10n_tw_edi_is_b2b) {
                partner.vat = identifier;
                this.state.data.identifier = identifier;
            }
        }
        if (this.state.showLoveCode) {
            this.state.data.loveCode = document.querySelector("#l10n_tw_edi_love_code").value;
        }
        if (this.state.showCarrierType) {
            this.state.data.carrierType = document.querySelector("#l10n_tw_edi_carrier_type").value;
            if (this.state.showCarrierNumber) {
                this.state.data.carrierNumber = document.querySelector(
                    "#l10n_tw_edi_carrier_number"
                ).value;
            }
        }
        return [true, "Data is valid"];
    }

    confirm() {
        const [is_valid, valid_message] = this.validateData();
        if (is_valid) {
            this.props.getPayload(this.state);
            this.props.close();
        } else {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t(valid_message),
            });
            return;
        }
    }
}
