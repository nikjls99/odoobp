import { TranscriptSender } from "@im_livechat/core/common/transcript_sender";
import { threadActionsRegistry } from "@mail/core/common/thread_actions";
import { useComponent } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { usePopover } from "@web/core/popover/popover_hook";

threadActionsRegistry.add("send-conversation", {
    close(component, action) {
        action.popover?.close();
    },
    component: TranscriptSender,
    componentProps(action) {
        return { close: () => action.close() };
    },
    condition(component) {
        return component.thread?.channel_type === "livechat" && !component.thread.livechat_active;
    },
    icon: "fa fa-fw fa-paper-plane",
    iconLarge: "fa fa-fw fa-lg fa-paper-plane",
    name(component) {
        return component.props.chatWindow?.isOpen
            ? _t("Send conversation")
            : _t("Send a copy of the conversation");
    },
    open(component, action) {
        action.popover?.open(component.root.el.querySelector(`[name="${action.id}"]`), {
            thread: component.thread,
        });
    },
    setup(action) {
        const component = useComponent();
        if (!component.props.chatWindow) {
            action.popover = usePopover(TranscriptSender, {
                onClose: () => action.close(),
            });
        }
    },
    toggle: true,
    sequenceGroup(component) {
        return component.props.chatWindow?.isOpen ? 20 : 5;
    },
});
