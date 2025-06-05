<<<<<<< 1fc971f39cacd78f3fb13407ab039bfe2860d7ef:addons/pos_sale_loyalty/static/src/overrides/models/pos_order_line.js
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
||||||| 0a0dc2f1bd54f44356a5959b8bcd52aaddcf1261:addons/pos_sale_loyalty/static/src/overrides/models/models.js
/** @odoo-module **/


import { Orderline } from "@point_of_sale/app/store/models";
=======
/** @odoo-module **/


import { Orderline, Order } from "@point_of_sale/app/store/models";
>>>>>>> 26ad00e96b064e782d6c08b8efe1e9cde1265e5f:addons/pos_sale_loyalty/static/src/overrides/models/models.js
import { patch } from "@web/core/utils/patch";

patch(PosOrderline.prototype, {
    //@override
    ignoreLoyaltyPoints(args) {
        if (this.sale_order_origin_id) {
            return true;
        }
        return super.ignoreLoyaltyPoints(args);
    },
    //@override
    setQuantityFromSOL(saleOrderLine) {
        // we need to consider reward product such as discount in a quotation
        if (saleOrderLine.reward_id) {
            this.set_quantity(saleOrderLine.product_uom_qty);
        } else {
            super.setQuantityFromSOL(...arguments);
        }
    },
});

patch(Order.prototype, {
    isLineValidForLoyaltyPoints(line) {
        const result = super.isLineValidForLoyaltyPoints(line);
        return !line.sale_order_origin_id && result
    }
})
