/** @odoo-module */

import { kanbanView } from "@web/views/kanban/kanban_view";
import { RelationalModel } from "@web/model/relational_model/relational_model";

export class ProjectSharingTaskKanbanModel extends RelationalModel {
    async _webReadGroupUnity(config) {
        config.context = {
            ...config.context,
            project_kanban: true,
        };
        return super._webReadGroupUnity(...arguments);
    }
}

kanbanView.Model = ProjectSharingTaskKanbanModel;
