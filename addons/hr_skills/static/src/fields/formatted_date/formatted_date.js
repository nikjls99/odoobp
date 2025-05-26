import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class FormattedDate extends Component {
    static template = "hr_skills.FormattedDate";
    static props = {
        ...standardFieldProps,
        dayFormat: String,
        monthFormat: String,
        yearFormat: String,
    };

    get value() {
        return this.props.record.data[this.props.name];
    }
}

export const formattedDate = {
    component: FormattedDate,
    supportedOptions: [
        {
            label: _t("Day Format"),
            name: "day_format",
            type: "string",
            default: "numeric",

        },
        {
            label: _t("Month Format"),
            name: "month_format",
            type: "string",
            default: "numeric",
        },
        {
            label: _t("Year Format"),
            name: "year_format",
            type: "string",
            default: "numeric",
        },
    ],
    supportedTypes: ["date"],
    extractProps({ options }) {
        return {
            dayFormat: options.day_format || "numeric",
            monthFormat: options.month_format || "numeric",
            yearFormat: options.year_format || "numeric",
        };
    },
};

registry.category("fields").add("formatted_date", formattedDate);
