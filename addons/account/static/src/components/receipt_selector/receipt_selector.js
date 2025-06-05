import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { DynamicRadioField, dynamicRadioField } from "@account/components/dynamic_radio_selection/dynamic_radio_selection";


const labels = {
    'in_invoice': _t('Bill'),
    'out_invoice': _t('Invoice'),
    'in_receipt': _t('Receipt'),
    'out_receipt': _t('Receipt'),
};


export class ReceiptSelector extends DynamicRadioField {
    static props = {
        ...DynamicRadioField.props,
    };

    /**
     * Remove the unwanted terms in the English label of the selection values
     * @override
     */
    get items() {
        let items = super.items;
        items.forEach((item) => {
            if (item[0] in labels) {
                item[1] = labels[item[0]];
            }
        });
        return items;
    }
}

export const receiptSelector = {
    ...dynamicRadioField,
    component: ReceiptSelector,
    extractProps() {
        return dynamicRadioField.extractProps(...arguments);
    },
};

registry.category("fields").add("receipt_selector", receiptSelector);
