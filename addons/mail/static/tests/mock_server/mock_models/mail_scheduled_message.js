import { mailDataHelpers } from "@mail/../tests/mock_server/mail_mock_server";
import { fields, models, serverState } from "@web/../tests/web_test_helpers";

export class MailScheduledMessage extends models.ServerModel {
<<<<<<< cc879e5d0e710248679eabb5a5df3dc601523518
    _inherit = ["mail.scheduled.message"];
    _views = {
        [`form,${DEFAULT_MAIL_VIEW_ID}`]: `<form/>`,
    };
||||||| c1d88949a3c305b425ab3a862741ebab7b7cd344
    _inherit = "mail.scheduled.message";
    _views = {
        [`form,${DEFAULT_MAIL_VIEW_ID}`]: `<form/>`,
    };
=======
    _inherit = "mail.scheduled.message";
>>>>>>> 984c0bcd2d39a56612112314b319befb282781fe

    author_id = fields.Generic({ default: () => serverState.partnerId });

    _to_store(ids, store) {
        /** @type {import("mock_models").IrAttachment} */
        const IrAttachment = this.env["ir.attachment"];
        /** @type {import("mock_models").ResPartner} */
        const ResPartner = this.env["res.partner"];

        const messages = this.browse(ids);
        for (const message of messages) {
            store.add("mail.scheduled.message", {
                attachment_ids: mailDataHelpers.Store.many(
                    IrAttachment.browse(message.attachment_ids)
                ),
                author: mailDataHelpers.Store.one(ResPartner.browse(message.author_id)),
                body: message.body,
                id: message.id,
                scheduled_date: message.scheduled_date,
                subject: message.subject,
                is_note: message.is_note,
            });
        }
    }
}
