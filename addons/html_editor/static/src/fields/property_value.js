import { MAIN_PLUGINS } from "@html_editor/plugin_sets";
import { HtmlViewer } from "@html_editor/components/html_viewer/html_viewer";
import { localization } from "@web/core/l10n/localization";
import { patch } from "@web/core/utils/patch";
import { PropertyValue } from "@web/views/fields/properties/property_value";
import { normalizeHTML } from "@html_editor/utils/html";
import { Wysiwyg } from "@html_editor/wysiwyg";

patch(PropertyValue.prototype, {
    setup() {
        this.lastHtmlValue = this.propertyValue;
        return super.setup();
    },

    onEditorLoad(editor) {
        this.editor = editor;
    },

    async onEditorBlur() {
        const value = this.editor.getContent();
        if (normalizeHTML(value) !== normalizeHTML(this.lastHtmlValue)) {
            this.onValueChange(value);
            this.lastHtmlValue = value;
        }
    },

    onWysiwygChange() {
        if (!this.editor.editable.contains(document.activeElement)) {
            // The DOM of the Wysiwyg have been changed, while the user is not editing
            // (eg the chatgpt widget), mark the field as dirty
            this.props.record.model.bus.trigger("FIELD_IS_DIRTY", true);
            this.onEditorBlur();
        }
    },

    /**
     * Wysiwyg key so when the value change, the component is reloaded.
     */
    get wysiwygKey() {
        return `${this.props.id}.${this.propertyValue}`;
    },

    getConfig() {
        return {
            content: this.propertyValue,
            debug: !!this.env.debug,
            direction: localization.direction || "ltr",
            onChange: this.onWysiwygChange.bind(this),
            placeholder: this.props.placeholder,
            Plugins: MAIN_PLUGINS,
            dropImageAsAttachment: true,
            getRecordInfo: () => {
                const { resModel, resId, data, fields, id } = this.props.record;
                return { resModel, resId, data, fields, id };
            },
        };
    },

    getReadonlyConfig() {
        return {
            value: this.propertyValue,
            hasFullHtml: false,
            cssAssetId: "web.assets_frontend",
        };
    },
});

PropertyValue.components = { ...PropertyValue.components, HtmlViewer, Wysiwyg };
