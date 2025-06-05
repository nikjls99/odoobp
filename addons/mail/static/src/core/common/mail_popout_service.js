import { App } from "@odoo/owl";

import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { getTemplate } from "@web/core/templates";

const DEFAULT_ID = Symbol("default");

export const mailPopoutService = {
    start(env) {
        const externalWindows = new Map();
        const hooksMap = new Map();
        let app;

        /**
         * Reset the external window to its initial state:
         * - Reset the external window header from main window (for appropriate title and other meta data)
         * - clear the external window's document body
         * - destroy the current app mounted on the window
         */
        function reset(id = DEFAULT_ID) {
            const externalWindow = externalWindows.get(id);
            if (externalWindow?.document) {
                externalWindow.document.head.textContent = "";
                externalWindow.document.write(window.document.head.outerHTML);
                externalWindow.document.body = externalWindow.document.createElement("body");
            }
            if (app) {
                app.destroy();
                app = null;
            }
        }

        /**
         * Poll the external window to detect when it is closed.
         * the afterPopoutClosed hook (afterFn) is then called after the window is closed
         */
        async function pollClosedWindow(id = DEFAULT_ID) {
            const externalWindow = externalWindows.get(id);
            while (externalWindows.get(id)) {
                await new Promise((r) => setTimeout(r, 1000));
                if (externalWindow.closed) {
                    externalWindows.delete(id);
                    const hooks = hooksMap.get(id);
                    hooks?.afterPopoutClosed?.();
                }
            }
        }

        /**
         * This function registers hooks (before/after the window popout)
         * @param {Object} hooks : An object containing the hooks to be registered.
         * @param {Function} hooks.beforePopout : this function is called before the external window is created.
         * @param {Function} hooks.afterPopoutClosed : this function is called after the external window is closed.
         * @param {Object} options : An object containing options for the hooks.
         * @param {any} options.id : An identifier for the hooks. If not provided, the default ID is used.
         */
        function addHooks(hooks, { id = DEFAULT_ID } = {}) {
            hooksMap.set(id, hooks);
        }

        function _addStyle(window) {
            // Copy all style sheets.
            [...document.styleSheets].forEach((styleSheet) => {
                try {
                    const cssRules = [...styleSheet.cssRules].map((rule) => rule.cssText).join("");
                    const style = document.createElement("style");

                    style.textContent = cssRules;
                    window.document.head.appendChild(style);
                } catch {
                    const link = document.createElement("link");
                    link.rel = "stylesheet";
                    link.type = styleSheet.type;
                    link.media = styleSheet.media;
                    link.href = styleSheet.href;
                    window.document.head.appendChild(link);
                }
            });
        }

        async function pip(component, props, { id = DEFAULT_ID } = {}) {
            if (!window.documentPictureInPicture) {
                return;
            }
            let externalWindow = externalWindows.get(id);
            if (!externalWindow || externalWindow.closed) {
                const hooks = hooksMap.get(id);
                hooks?.beforePopout?.();
                externalWindow = await window.documentPictureInPicture.requestWindow();
                externalWindow.addEventListener("unload", () => {
                    const hooks = hooksMap.get(id);
                    hooks?.afterPopoutClosed?.();
                });
                _addStyle(externalWindow);
                window.addEventListener("beforeunload", () => {
                    if (externalWindow && !externalWindow.closed) {
                        externalWindow.close();
                    }
                });
                externalWindows.set(id, externalWindow);
                pollClosedWindow(id);
            }
            env.isPipWindow = true;
            reset();
            app = new App(component, {
                name: "Popout",
                env,
                props,
                getTemplate,
            });
            app.mount(externalWindow.document.body);
            return externalWindow;
        }

        /**
         * Mounts the passed component (with its props) on an external window.
         * If the external window does not exist, it is created.
         * @param {class} component: The component to be mounted.
         * @param {Props} props: The props of the component.
         * @returns {Window} The external window
         */
        function popout(component, props, { id = DEFAULT_ID } = {}) {
            let externalWindow = externalWindows.get(id);
            if (!externalWindow || externalWindow.closed) {
                const hooks = hooksMap.get(id);
                hooks?.beforePopout?.();
                externalWindow = browser.open("about:blank", "_blank", "popup=yes");
                window.addEventListener("beforeunload", () => {
                    if (externalWindow && !externalWindow.closed) {
                        externalWindow.close();
                    }
                });
                externalWindows.set(id, externalWindow);
                pollClosedWindow(id);
            }

            reset(id);
            app = new App(component, {
                name: "Popout",
                env,
                props,
                getTemplate,
            });
            app.mount(externalWindow.document.body);
            return externalWindow;
        }

        function getExternalWindow(id = DEFAULT_ID) {
            const externalWindow = externalWindows.get(id);
            return externalWindow && !externalWindow.closed ? externalWindow : null;
        }

        return {
            get externalWindow() {
                // for backwards compatibility as a getter retuning the default external window
                return getExternalWindow();
            },
            popout,
            pip,
            reset,
            addHooks,
        };
    },
};

registry.category("services").add("mail.popout", mailPopoutService);
