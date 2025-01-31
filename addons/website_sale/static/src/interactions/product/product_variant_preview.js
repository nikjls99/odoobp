import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class ProductVariantPreview extends Interaction {
    static selector = ".o_wsale_attribute_previewer";
    dynamicContent = {
        _window: {
            "t-on-resize": this.debounced(this._updateVariantPreview, 250),
        },
    };

    setup() {
        this.ptavs = [...this.el.children];
        this.indicatorSpan = this.ptavs.splice(this.ptavs.length - 1, 1)[0];
        this.ptavCount = this.ptavs.length + Number(this.el.dataset.hiddenPtavs ?? 0);
        this.displayedPTAVs = 0;
        // Class `gap-1` on parent adds 4px margin for each ptav
        this.margin = 4;
        this._updateVariantPreview();
    }

    /**
     * Hide all attribute values from view to be able to recompute correctly how many elements are
     * to be shown.
     *
     * @private
     *
     * @returns {void}
     */
    _resetDisplay() {
        for (const child of this.el.children) {
            child.classList.add("d-none");
        }
    }

    /**
     * Updates the span to include the correct number of hidden PTAVs and return the
     * new width of the element.
     *
     * @returns {Number}
     */
    _updateAndGetHiddenPTAVsWidth() {
        const hiddenPTAVs = this.ptavCount - this.displayedPTAVs;
        this.indicatorSpan.firstElementChild.textContent = `+${hiddenPTAVs}`;
        this.indicatorSpan.classList.remove("d-none");
        return this.indicatorSpan.offsetWidth + this.margin;
    }

    /**
     * Update the count of hidden PTAVs with the correct number and make it visible.
     *
     * @private
     * @param {Element} currentPTAV
     * @param {Number} availableSpace
     *
     * @returns {void}
     */
    _showHiddenPTAVsElement(currentPTAV, availableSpace) {
        let indicatorSpanWidth = this._updateAndGetHiddenPTAVsWidth();
        while (indicatorSpanWidth >= availableSpace) {
            const currentPTAVWidth = currentPTAV.offsetWidth;
            if (currentPTAV) {
                currentPTAV.classList.add("d-none");
                this.displayedPTAVs--;
                indicatorSpanWidth = this._updateAndGetHiddenPTAVsWidth();
            }
            availableSpace += currentPTAVWidth;
            currentPTAV = currentPTAV.previousElementSibling;
        }
    }

    /**
     * For each ptav check if there is enough space to add on the parent element and update the
     * hidden PTAVs count accordingly, with the truncated elements from the backend.
     *
     * @private
     *
     * @returns {void}
     */
    _updateVariantPreview() {
        this._resetDisplay();
        const availableWidth = this.el.offsetWidth;
        let usedWidth = 0;
        this.displayedPTAVs = 0;
        for (const ptav of this.ptavs) {
            // Remove d-none to be able to get width.
            ptav.classList.remove("d-none");
            usedWidth += ptav.offsetWidth + this.margin;
            this.displayedPTAVs++;
            const availableSpace = availableWidth - usedWidth;
            const isLastPTAV = ptav === this.ptavs[this.ptavs.length - 1];
            // If there is an overflow or if all displayed elements had no overflow, check if there
            // is hidden remaining PTAVs from backend.
            if (
                usedWidth >= availableWidth ||
                (isLastPTAV && this.ptavCount > this.displayedPTAVs)
            ) {
                this._showHiddenPTAVsElement(ptav, availableSpace);
                break;
            }
        }
    }
}

export class ProductVariantPreviewImageHover extends Interaction {
    static selector = ".oe_product_cart";
    dynamicContent = {
        ".o_product_variant_preview": {
            "t-on-mouseenter": this._mouseEnter,
            "t-on-mouseleave": this._mouseLeave,
            "t-on-click": this._onClick,
        },
        ".oe_product_image_link": {
            "t-on-click": this._productRedirectOnClick,
        }
    };

    setup() {
        this.productImg = this.el.querySelector(".oe_product_image_img_wrapper img");
        this.originalImgSrc = this.productImg.getAttribute("src");
        this.variantHref = null;
        this.variantImageSrc = null;
    }

    /**
     * Display the variant image on hover.
     *
     * @private
     * @param {Event} ev
     *
     * @returns {void}
     */
    _mouseEnter(ev) {
        this.variantImageSrc = ev.target.dataset.variantImage;
        if (!this.variantImageSrc) {
            return;
        }
        this._setImgSrc(this.variantImageSrc);
    }

    /**
     * Reset the product image when mouse no longer hovers on the ptav.
     *
     * @private
     *
     * @returns {void}
     */
    _mouseLeave() {
        if (!this.env.isSmall)
            this._setImgSrc(this.originalImgSrc);
    }

    /**
     * Set the image source of the product to the given image source
     *
     * @param {string} imageSrc
     */
    _setImgSrc(imageSrc) {
        this.productImg.src = imageSrc;
    }

    /**
     * On mobile, when ptav is clicked simulate on hover behavior and change product image
     * to variant image.
     * If not on mobile, redirect to product page with variant selected.
     *
     * @param {Event} ev
     * @returns
     */
    _onClick(ev) {
        const targetDataset = ev.target.closest('.o_product_variant_preview').dataset;
        this.variantHref = targetDataset.variantHref;
        if (this.env.isSmall) {
            this.variantImageSrc = targetDataset.variantImage;
            if (!this.variantImageSrc) {
                return;
            }
            this._setImgSrc(this.variantImageSrc);
        }
        else {
            window.location.href = encodeURI(this.variantHref);
        }
    }

    /**
     * Override default behavior when ptav is selected on mobile, to select variant on product page
     * when product card is clicked.
     *
     * @param {Event} ev
     * @returns
     */
    _productRedirectOnClick(ev) {
        if (this.env.isSmall && this.variantHref) {
            ev.preventDefault();
            window.location.href = encodeURI(this.variantHref);
        }
    }
}

registry
    .category("public.interactions")
    .add("website_sale.product_variant_preview", ProductVariantPreview);
registry
    .category("public.interactions")
    .add("website_sale.product_variant_preview_image_hover", ProductVariantPreviewImageHover);
