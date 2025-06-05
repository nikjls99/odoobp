import { Component, useState } from "@odoo/owl";
import { useTransformOperations } from "@html_editor/main/media/image_transform_button";
import { useDomState } from "@html_builder/core/utils";

export class ImageTransformButton extends Component {
    static template = "website.ImageTransformButton";
    static props = { id: String };

    setup() {
        this.state = useState({ active: false });
        this.domState = useDomState(
            (editingElement) => ({
                applied: editingElement.matches(`[style*="transform"]`)
            })
        );
        this.document = this.env.editor.document;
        this.editable = this.env.editor.editable;
        this.addStep = this.env.editor.shared.history.addStep.bind(this);
        Object.assign(this.props, useTransformOperations(
            this.state,
            this.document,
            this.editable,
            this.addStep,
        ));
    }

    getTargetedImage() {
        const targetedNodes = this.env.editor.shared.selection.getTargetedNodes();
        return targetedNodes.find((node) => node.tagName === "IMG");
    }

    onResetButtonClick() {
        this.resetImageTransformation(this.getTargetedImage());
        if (this.props.isImageTransformationOpen()) {
            this.props.closeImageTransformation();
        }
    }

    resetImageTransformation(image) {
        image.setAttribute(
            "style",
            (image.getAttribute("style") || "").replace(/[^;]*transform[\w:]*;?/g, "")
        );
        this.addStep();
    }

    onTransformButtonClick() {
        let image = this.getTargetedImage();
        if (!this.props.isImageTransformationOpen()) {
            this.props.openImageTransformation(image);
        }
    }
}
