import { FeedbackPanel } from "@im_livechat/embed/common/feedback_panel/feedback_panel";
import { patch } from "@web/core/utils/patch";

patch(FeedbackPanel.prototype, {
    get allowNewSession() {
        return super.allowNewSession && this.livechatService.options.channel_id;
    },
});
