import { Component, useRef, useState } from "@odoo/owl";
import { Deferred } from "@web/core/utils/concurrency";
import { memoize } from "@web/core/utils/functions";

const generateGifSnapshot = memoize(async (src) => {
    const deferred = new Deferred();
    const gif = document.createElement("img");
    gif.crossOrigin = "anonymous";
    gif.src = src;
    gif.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = gif.width;
        canvas.height = gif.height;
        canvas.getContext("2d").drawImage(gif, 0, 0, gif.width, gif.height);
        deferred.resolve(canvas.toDataURL("image/gif"));
    };
    return deferred;
});

/**
 * @typedef {Object} Props
 * @property {string} src
 * @property {string} [alt]
 * @property {string} [class]
 * @property {((event: Event) => void)} [onLoad]
 * @property {boolean} [paused]
 * @extends {Component<Props, Env>}
 */
export class Gif extends Component {
    static template = "mail.Gif";
    static props = {
        src: { type: String, required: true },
        alt: { type: String, optional: true },
        class: { type: String, optional: true },
        onLoad: { type: Function, optional: true },
        paused: { type: Boolean, optional: true },
    };
    static components = {};

    setup() {
        this.gif = useRef("gif");
        this.state = useState({ snapshot: null });
    }

    onLoad() {
        this.props.onLoad?.(...arguments);
        generateGifSnapshot(this.props.src).then((snapshot) => (this.state.snapshot = snapshot));
    }
}
