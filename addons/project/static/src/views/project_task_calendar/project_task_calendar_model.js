import { _t } from "@web/core/l10n/translation";
import { CalendarModel } from '@web/views/calendar/calendar_model';
import { ProjectTaskModelMixin } from "../project_task_model_mixin";

export class ProjectTaskCalendarModel extends ProjectTaskModelMixin(CalendarModel) {
    /**
     * @override
     */
    get defaultFilterLabel() {
        this.isCheckProject = 'project_id' in this.meta.filtersInfo;
        if (this.isCheckProject) {
            return _t("Private");
        }
        return super.defaultFilterLabel;
    }

    async load(params = {}) {
        const domain = params.domain || this.meta.domain;
        params.domain = this._processSearchDomain(domain);
        return super.load(params);
    }
}
