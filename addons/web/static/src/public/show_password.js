import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class ShowPassword extends Interaction {
    static selector = ".o_show_password";
    dynamicContent = {
        _root: {
            "t-on-click": () =>
                (this.passwordEl.type = this.passwordEl.type === "password" ? "text" : "password"),
        },
        "i": {
            "t-att-class": () => ({
                "fa-eye": this.passwordEl.type === "password",
                "fa-eye-slash": this.passwordEl.type === "text",
            }),
        },
    };

    setup() {
        this.passwordEl = this.el.closest(".input-group").querySelector("input[type='password']");
    }
}

registry.category("public.interactions").add("web.show_password", ShowPassword);
