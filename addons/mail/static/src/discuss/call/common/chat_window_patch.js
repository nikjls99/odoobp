import { ChatWindow } from "@mail/core/common/chat_window";
import { Call } from "@mail/discuss/call/common/call";
import { useService } from "@web/core/utils/hooks";

import { patch } from "@web/core/utils/patch";

Object.assign(ChatWindow.components, { Call });

patch(ChatWindow.prototype, {
    setup() {
        super.setup(...arguments);
        this.nativePip = useService("discuss.native_pip");
    },
});
