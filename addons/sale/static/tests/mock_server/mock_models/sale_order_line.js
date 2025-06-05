import { fields, models } from "@web/../tests/web_test_helpers";


export class SaleOrderLine extends models.ServerModel {
    _name = "sale.order.line";

    translated_product_name = fields.Char({store: true});
}
