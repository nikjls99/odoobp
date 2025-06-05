import { Component, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ProjectTemplateDropdown extends Component {
    static template = "project.ProjectTemplateDropdown";

    static props = {
        hotkey: {
            type: String,
            optional: true,
        },
        newButtonClasses: String,
        onCreate: Function,
        context: Object,
        getAdditionalContext: {
            type: Function,
            optional: true,
        },
        isDisabled: {
            type: Boolean,
            optional: true,
        },
    };
    static defaultProps = {
        hotkey: "r",
        isDisabled: false,
    };

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        onWillStart(this.onWillStart);
        this.projectTemplates = [];
    }

    get readFields() {
        return ["id", "name"];
    }

    async onWillStart() {
        this.projectTemplates = await this.orm.searchRead(
            "project.project",
            [["is_template", "=", true]],
            this.readFields
        );
    }

    contextPreprocess(templateId) {
        const context = { ...this.props.context };
        if (this.props.getAdditionalContext) {
            Object.assign(context, this.props.getAdditionalContext());
        }
        return context;
    }

    async createProjectFromTemplate(templateId) {
        if (this.env.config.viewType === "kanban") {
            const action = await this.orm.call(
                "project.template.create.wizard",
                "action_open_template_view",
                [],
                {
                    context: {
                        ...this.contextPreprocess(templateId),
                        template_id: templateId,
                    },
                }
            );
            this.action.doAction(action);
        } else {
            this.action.switchView("form", {
                resId: (await this.orm.call(
                    "project.project",
                    "action_create_from_template",
                    [templateId],
                    {
                        context: this.contextPreprocess(templateId),
                    }
                ))[0],
                focusTitle: true,
            });
        }
    }
}
