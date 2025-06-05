# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_description(self):
        # In a dropshipping context we do not need the description of the purchase order or it will be displayed
        # in Delivery slip report and it may be confusing for the customer to see several times the same text (product name + description_picking).
        return self.product_id._get_description(self.picking_type_id) if self.purchase_line_id and self.purchase_line_id.order_id.dest_address_id else super()._get_description()
