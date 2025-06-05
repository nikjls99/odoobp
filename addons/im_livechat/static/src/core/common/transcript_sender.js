import { isValidEmail } from "@im_livechat/core/common/misc";
import { rpc } from "@web/core/network/rpc";

import { Component, useState } from "@odoo/owl";
import { useAutofocus } from "@web/core/utils/hooks";

/**
 * @typedef {Object} Props
 * @property {import("models").Thread}
 * @extends {Component<Props, Env>}
 */
export class TranscriptSender extends Component {
    static template = "im_livechat.TranscriptSender";
    static props = ["thread"];

    STATUS = Object.freeze({
        IDLE: "idle",
        SENDING: "sending",
        SENT: "sent",
        FAILED: "failed",
    });

    setup() {
        this.isValidEmail = isValidEmail;
        this.state = useState({
            email: "",
            status: this.STATUS.IDLE,
        });
        useAutofocus({ refName: "inputRef", mobile: false });
    }

    get isButtonDisabled() {
        return (
            !this.state.email ||
            !this.isValidEmail(this.state.email) ||
            [this.STATUS.SENDING, this.STATUS.SENT].includes(this.state.status)
        );
    }

    /**
     * @param {KeyboardEvent} ev
     */
    onKeydown(ev) {
        if (ev.key == "Enter" && !this.isButtonDisabled) {
            this.onClickSend();
        }
    }

    async onClickSend() {
        this.state.status = this.STATUS.SENDING;
        try {
            await this.sendTranscript();
            this.state.status = this.STATUS.SENT;
        } catch {
            this.state.status = this.STATUS.FAILED;
        }
    }

    async sendTranscript() {
        await rpc("/im_livechat/email_livechat_transcript", this.sendTranscriptOptions);
    }

    get sendTranscriptOptions() {
        return {
            channel_id: this.props.thread.id,
            email: this.state.email,
        };
    }
}
