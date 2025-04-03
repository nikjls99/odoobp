<<<<<<< cc879e5d0e710248679eabb5a5df3dc601523518
import { getKwArgs, models } from "@web/../tests/web_test_helpers";
import { DEFAULT_MAIL_VIEW_ID } from "@mail/../tests/mock_server/mock_models/constants";
||||||| c1d88949a3c305b425ab3a862741ebab7b7cd344
import { models } from "@web/../tests/web_test_helpers";
import { DEFAULT_MAIL_VIEW_ID } from "@mail/../tests/mock_server/mock_models/constants";
=======
import { models } from "@web/../tests/web_test_helpers";
>>>>>>> 984c0bcd2d39a56612112314b319befb282781fe

export class SlideChannel extends models.ServerModel {
    _name = "slide.channel";
    _views = {
        form: /* xml */ `
            <form>
                <chatter/>
            </form>
        `,
    };

    action_grant_access() {
        const kwargs = getKwArgs(arguments, "ids", "partner_id");
        if (kwargs.partner_id) {
            const activities = this.env["mail.activity"].search_read([
                ["request_partner_id", "=", kwargs.partner_id],
            ]);
            this.env["mail.activity"].action_feedback(activities.map(a => a.id));
        }
    }

    action_refuse_access() {
        const kwargs = getKwArgs(arguments, "ids", "partner_id");
        if (kwargs.partner_id) {
            const activities = this.env["mail.activity"].search_read([
                ["request_partner_id", "=", kwargs.partner_id],
            ]);
            this.env["mail.activity"].action_feedback(activities.map(a => a.id));
        }
    }
}
