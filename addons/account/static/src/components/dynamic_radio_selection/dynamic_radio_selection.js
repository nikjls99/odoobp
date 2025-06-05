import { registry } from "@web/core/registry";
import { RadioField, radioField } from "@web/views/fields/radio/radio_field";


export class DynamicRadioField extends RadioField {
    static props = {
        ...RadioField.props,
        allowed_values_field: { type: String },
    };

    get allowedValues() {
        return this.props.record.data[this.props.allowed_values_field]?.split(",") || [];
    }

    /**
     * Filter the selection values with the accepted available options.
     * @override
     */
    get items() {
        let items = super.items
        const allowedValues = this.allowedValues;
        if ( this.type === 'selection' && allowedValues.length > 1 ) {
            return items.filter((item) => {
                return (allowedValues.includes(item[0]));
            });
        }
        return [];
    }
}

export const dynamicRadioField = {
    ...radioField,
    component: DynamicRadioField,
    extractProps({ options }) {
        const props = radioField.extractProps(...arguments);
        props.allowed_values_field = options.allowed_values_field;
        return props;
    },
};

registry.category("fields").add("dynamic_radio_selection", dynamicRadioField);
