import { Plugin } from "@html_editor/plugin";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";
import { ProductsListPageOption } from "@website_sale/website_builder/products_list_page_option";

class ProductsListPageOptionPlugin extends Plugin {
    static id = "productsListPageOptionPlugin";
    static dependencies = ["history"];

    resources = {
        builder_options: [
            {
                OptionComponent: ProductsListPageOption,
                selector: "main:has(.o_wsale_products_page)",
                applyTo: "#o_wsale_container",
                editableOnly: false,
                title: _t("Products Page"),
                groups: ["website.group_website_designer"],
            },
        ],
        builder_actions: this.getActions(),
        save_handlers: this.onSave.bind(this),
    };

    getActions() {
        return {
            setPpg: {
                reload: {},
                getValue: ({ editingElement }) => parseInt(editingElement.dataset.ppg),
                apply: ({ value }) => {
                    const PPG_LIMIT = 10000;
                    let ppg = parseInt(value);
                    if (!ppg || ppg < 1) {
                        return false;
                    }
                    ppg = Math.min(ppg, PPG_LIMIT);
                    return rpc("/shop/config/website", { shop_ppg: ppg });
                },
            },
            setPpr: {
                reload: {},
                isApplied: ({ editingElement, value }) =>
                    parseInt(editingElement.dataset.ppr) === value,
                apply: ({ value }) => {
                    const ppr = parseInt(value);
                    return rpc("/shop/config/website", { shop_ppr: ppr });
                },
            },
            setGap: {
                isApplied: () => true,
                getValue: ({ editingElement }) =>
                    editingElement.style.getPropertyValue("--o-wsale-products-grid-gap"),
                apply: ({ editingElement, value }) => {
                    editingElement.style.setProperty("--o-wsale-products-grid-gap", value);
                    editingElement.dataset.gapToSave = value;
                },
            },
            setDefaultSort: {
                reload: {},
                isApplied: ({ editingElement, value }) =>
                    editingElement.dataset.defaultSort === value,
                apply: ({ value }) => rpc("/shop/config/website", { shop_default_sort: value }),
            },
            previewTemplate: {
                isApplied: ({ editingElement, params: { appliedSelector, previewClass } }) => {
                    console.log("CCCCisApplied", !!editingElement.querySelector(appliedSelector), editingElement, appliedSelector)
                    return !!editingElement.querySelector(appliedSelector) || !!editingElement.classList.contains(`${previewClass}_on`);
                },
                apply: ({ editingElement, params: { templateId, previewClass, placeBefore, placeAfter } }) => {
                    console.log("previewTemplate", editingElement, templateId, placeBefore, placeAfter)
                    editingElement.classList.toggle(...previewClass.split(" "), this.dependencies.history.getIsPreviewing());
                    editingElement.classList.add(...previewClass.split(" ").map((cls) => `${cls}_on`));
                    editingElement.classList.remove(...previewClass.split(" ").map((cls) => `${cls}_off`));
                    // if (!value) throw new Error("no value is not implemented");
                    const renderedEl = renderToElement(templateId);
                    if (placeBefore) {
                        for (const el of editingElement.querySelectorAll(placeBefore)) {
                            el.insertAdjacentElement('beforebegin', renderedEl.cloneNode(true))
                        }
                    }
                    if (placeAfter) {
                        for (const el of editingElement.querySelectorAll(placeAfter)) {
                            el.insertAdjacentElement('afterend', renderedEl.cloneNode(true))
                        }
                    }
                },
                clean: ({ editingElement, params: { templateId, previewClass } }) => {
                    console.log("clean")
                    editingElement.classList.toggle(...previewClass.split(" "), this.dependencies.history.getIsPreviewing());
                    editingElement.classList.remove(...previewClass.split(" ").map((cls) => `${cls}_on`));
                    editingElement.classList.add(...previewClass.split(" ").map((cls) => `${cls}_off`));
                    for (const el of editingElement.querySelectorAll(`[data-wsale-injected-preview='${templateId}']`)) {
                        el.remove();
                    }
                },
            },
        };
    }

    async onSave() {
        const pageEl = this.editable.querySelector("#o_wsale_container");
        if (pageEl) {
            const gapToSave = pageEl.dataset.gapToSave;
            if (typeof gapToSave !== "undefined") {
                return rpc("/shop/config/website", { shop_gap: gapToSave });
            }
        }
    }
}

registry
    .category("website-plugins")
    .add(ProductsListPageOptionPlugin.id, ProductsListPageOptionPlugin);
