import { POPUP_IMAGE } from "@html_builder/utils/option_sequence";
import { registry } from "@web/core/registry";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";

export class ImagePopUpOptionPlugin extends Plugin {
    static id = "imagePopUpOption";
    static dependencies = [];
    resources = {
        builder_options: [
            withSequence(POPUP_IMAGE, {
                template: "website.ImagePopUpOption",
                selector: "img",
                exclude: "a img, header img, footer img"
            })
        ],
        builder_actions: this.getActions(),
    };
    getActions() {
        return {
            setPopUpOnClick: {
                isApplied: ({ editingElement }) => {
                    const imageEl = editingElement.closest("img");
                    return imageEl && imageEl.classList.contains("o_image_popup");
                },
                apply: ({ editingElement }) => {
                    const imageEl = editingElement.closest("img");
                    const isPopupEnabled = imageEl.classList.contains("o_image_popup");
                    if (imageEl) {
                        if (!isPopupEnabled) {
                            imageEl.classList.add("o_image_popup");
                        } else {
                            imageEl.classList.remove("o_image_popup");
                        }
                    }
                },
            },
        };
    }
}

registry.category("website-plugins").add(ImagePopUpOptionPlugin.id, ImagePopUpOptionPlugin);
