import { patch } from "@web/core/utils/patch";
import { LivechatButton } from "@im_livechat/embed/common/livechat_button";

patch(LivechatButton.prototype, {
    get isShown() {
        return super.isShown && this.livechatService.options.channel_id;
    },
});
