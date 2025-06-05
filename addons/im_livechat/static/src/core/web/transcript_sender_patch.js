import { TranscriptSender } from "@im_livechat/core/common/transcript_sender";
import { ActionPanel } from "@mail/discuss/core/common/action_panel";
import { onWillStart } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

patch(TranscriptSender.prototype, {
    setup() {
        super.setup();
        this.notificationService = useService("notification");
        this.orm = useService("orm");
        onWillStart(async () => {
            if (this.props.thread.correspondent.persona.type == "guest") return;
            const [result] = await this.orm.read(
                "res.partner",
                [this.props.thread.correspondent.persona.id],
                ["email"]
            );
            this.state.email = result?.email;
        });
    },
    get sendTranscriptOptions() {
        return { ...super.sendTranscriptOptions, log_notification: true };
    },
    async sendTranscript() {
        await super.sendTranscript();
        this.notificationService.add(
            _t("Conversation sent to %(email)s", { email: this.state.email }),
            { type: "success" }
        );
        this.props.close();
    },
});

TranscriptSender.components = { ...TranscriptSender.components, ActionPanel };
TranscriptSender.props = [...TranscriptSender.props, "close"];
