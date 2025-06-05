import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";
import { ControlPanel } from "@web/search/control_panel/control_panel";

export class ProjectTaskControlPanel extends ControlPanel {
    static template = "project.ProjectTaskControlPanel";

    setup() {
        super.setup();
        this.showSubtasksKey = "showSubtasks";
        this.state.showSubtasks = JSON.parse(browser.localStorage.getItem(this.showSubtasksKey) || "false");
    }

    get showSubtasksTitle() {
        if (this.state.showSubtasks) {
            return _t("Hide sub-tasks");
        }
        return _t("Show sub-tasks");
    }

    onClickShowSubtasks(ev) {
        this.state.showSubtasks = !this.state.showSubtasks;
        browser.localStorage.setItem(this.showSubtasksKey, this.state.showSubtasks);
        this.env.searchModel.search();
    }
}
