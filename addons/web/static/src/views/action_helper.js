import { Component } from "@odoo/owl";
import { Widget } from "@web/views/widgets/widget";

export class ActionHelper extends Component {
    static template = "web.ActionHelper";
    static components = { Widget };
    static props = ["noContentHelp?", "useSampleModel?"];

    get hasFacets() {
        return this.env.searchModel.facets.length > 0;
    }

    get showWidgetSampleData() {
        return !this.props.useSampleModel ? false : this.props.useSampleModel;
    }

    get showDefaultHelper() {
        return !this.props.noContentHelp;
    }

    removeFacets() {
        this.env.searchModel.clearQuery();
    }
}
