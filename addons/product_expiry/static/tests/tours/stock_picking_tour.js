import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add('test_generate_serial_with_expiration', {
    steps: () => [
        {
            trigger: "button:contains('Details')",
            run: "click",
        },
        // Check if the expiration date is already present before generating/importing lots.
        {
            trigger: "td.o_field_cell[name=expiration_date]",
            run: () => {
                const exp_date = document.querySelectorAll("td.o_field_cell[name=expiration_date]")[0];
                if (!exp_date.innerText) {
                    throw new Error("Missing expiration date.");
                }
            }
        },
        {
            trigger: '.o_widget_generate_serials > button',
            run: "click",
        },
        {
            trigger: ".modal .btn-primary:contains('New')",
            run: "click",
        },
        {
            trigger: ".modal .btn-primary:contains('Generate')",
            run: "click",
        },
        // Check that the expiration date is now set after generating Serials/Lots.
        {
            trigger: "td.o_field_cell[name=expiration_date]",
            run: () => {
                const exp_date = document.querySelectorAll("td.o_field_cell[name=expiration_date]")[0];
                if (!exp_date.innerText) {
                    throw new Error("Missing expiration date.");
                }
            }
        },
        {
            trigger: ".modal button:contains(save)",
            run: "click",
        },
        {
            trigger: "button.o_form_button_save",
            run: "click",
        },
        {
            trigger: ".o_form_saved",
        },
    ],
});
