import { waitFor, waitForNone } from "@odoo/hoot-dom";
import { expect } from "@odoo/hoot";

export async function expectToolbarOpened() {
    await waitFor(".o-we-toolbar");
    expect(".o-we-toolbar").toHaveCount(1);
}

export async function expectToolbarClosed() {
    await waitForNone(".o-we-toolbar");
    expect(".o-we-toolbar").toHaveCount(0);
}
