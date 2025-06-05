import { registry } from "@web/core/registry";
import { Call } from "@mail/discuss/call/common/call";
import { reactive } from "@odoo/owl";

const CALL_PIP_ID = Symbol("discuss.native.pip");

export const callPipService = {
    dependencies: ["mail.popout"],
    /**
     * @param {import("@web/env").OdooEnv} env
     * @param {import("services").ServiceFactories} services
     */
    start(env, services) {
        const popoutService = services["mail.popout"];
        let pipWindow = null;
        const state = reactive({
            isPipMode: false,
        });
        popoutService.addHooks(
            {
                afterPopoutClosed: () => {
                    console.log("popoutclosed");
                    state.isPipMode = false;
                    env.services["discuss.rtc"]?.channel?.openChatWindow();
                },
            },
            { id: CALL_PIP_ID }
        );
        function closePip() {
            state.isPipMode = false;
            pipWindow?.close(CALL_PIP_ID);
        }
        async function openPip() {
            const channel = env.services["discuss.rtc"]?.channel;
            if (!channel) {
                return;
            }
            state.isPipMode = true;
            if (!window.documentPictureInPicture) {
                return;
            }
            console.log(state.isPipMode);
            pipWindow = await popoutService.pip(
                Call,
                { isPip: true, thread: channel },
                { id: CALL_PIP_ID }
            );
            if (pipWindow) {
                pipWindow.document.body.style.backgroundColor = "black";
                pipWindow.document.body.style.overflow = "hidden";
            } else {
                state.isPipMode = false;
            }
        }
        return reactive({
            get isNativePipAvailable() {
                return Boolean(window.documentPictureInPicture);
            },
            state,
            closePip,
            openPip,
        });
    },
};

registry.category("services").add("discuss.native_pip", callPipService);
