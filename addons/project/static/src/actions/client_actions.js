import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { markup } from "@odoo/owl";

export function showTemplateUndoNotification(
    env,
    {
        model,
        recordId,
        message,
        undoMethod = "action_undo_convert_to_template",
        actionType = "success",
    }
) {
    const undoNotification = env.services.notification.add(_t(message), {
        type: actionType,
        buttons: [
            {
                name: _t("Undo"),
                icon: "fa-undo",
                onClick: async () => {
                    const res = await env.services.orm.call(model, undoMethod, [recordId]);
                    if (res && undoMethod !== "unlink") {
                        env.services.action.doAction(res);
                    } else if (undoMethod === "unlink") {
                        // Taking out the controller to be restored after unlinking the record
                        const restoreController = env.services.action.currentController.config.breadcrumbs?.at(-2);
                        restoreController?.onSelected();
                    }
                    undoNotification();
                },
            },
        ],
    });
}

export function showTemplateUndoConfirmationDialog(
    env,
    { model, recordId, bodyMessage, confirmLabel, undoMethod = "action_undo_convert_to_template" }
) {
    env.services.dialog.add(ConfirmationDialog, {
        body: bodyMessage,
        confirmLabel: confirmLabel,
        confirm: async () => {
            const action = await env.services.orm.call(model, undoMethod, [recordId]);
            await env.services.action.doAction(action);
        },
        cancelLabel: _t("Discard"),
        cancel: () => {},
    });
}

export function showTemplateConfirmationDialog(env,
    { model, recordId, bodyMessage, confirmLabel, method = "create_template_from_project" }
) {
    env.services.dialog.add(ConfirmationDialog, {
        body: bodyMessage,
        confirmLabel: confirmLabel,
        confirm: async () => {
            const action = await env.services.orm.call(model, method, [recordId]);
            await env.services.action.doAction({
                type: "ir.actions.act_window",
                res_model: model,
                views: [[false, "form"]],
                res_id: action.params.project_id,
            });
            await env.services.action.doAction(action);
        },
        cancelLabel: _t("Discard"),
        cancel: () => {},
    });
}

// Task → Template Notification
registry.category("actions").add("project_show_template_notification", (env, action) => {
    const params = action.params || {};
    showTemplateUndoNotification(env, {
        model: "project.task",
        recordId: params.task_id,
        message: _t("Task converted to template"),
    });
    return params.next;
});

// Task → Undo Confirmation Dialog
registry.category("actions").add("project_show_template_undo_confirmation_dialog", (env, action) => {
    const params = action.params || {};
    showTemplateUndoConfirmationDialog(env, {
        model: "project.task",
        recordId: params.task_id,
        bodyMessage: _t("This task is already a template. Do you want to convert it back to a regular task?"),
        confirmLabel: _t("Convert to Task"),
    });
    return params.next;
});

// Project → Template Create Confirmation
registry.category("actions").add("project_template_create_show_confirmation", (env, action) => {
    const params = action.params || {};
    return showTemplateConfirmationDialog(env, {
        model: "project.project",
        recordId: params.project_id,
        bodyMessage: markup(_t("%s \nDo you want to create a copy of project into template ?", params.message.join("\n"))),
        confirmLabel: _t("Create Template"),
    });
});

// Project → Template Notification
registry.category("actions").add("project_template_show_notification", (env, action) => {
    const params = action.params || {};
    showTemplateUndoNotification(env, {
        model: "project.project",
        recordId: params.project_id,
        message: params.message || _t("Project converted to template."),
        undoMethod: params.undo_method,
    });
    return params.next;
});

// Project → Undo Confirmation Dialog
registry
    .category("actions")
    .add("project_template_show_undo_confirmation_dialog", (env, action) => {
        const params = action.params || {};
        showTemplateUndoConfirmationDialog(env, {
            model: "project.project",
            recordId: params.project_id,
            bodyMessage: markup(_t("%s \nThis project is already a template. Do you want to convert it back to a regular project?", params.message.join("\n"))),
            confirmLabel: _t("Revert to Project"),
        });
        return params.next;
    });
