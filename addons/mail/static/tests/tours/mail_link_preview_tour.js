import { contains } from "@web/../tests/utils";
import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("test_mail_link_preview", {
    steps: () => [
        {
            content: "Wait for the chatter to be fully loaded",
            trigger: ".o-mail-Chatter",
            async run() {
                await contains(".o-mail-LinkPreviewVideo", { count: 2 });
            },
        },
        {
            content: "Hover preview and click on the remove button",
            trigger: ".o-mail-LinkPreviewVideo button[aria-label='Remove']",
            run: "click",
        },
        {
            trigger: ".modal-footer button:contains('Delete')",
            run: "click",
        },
    ],
});
