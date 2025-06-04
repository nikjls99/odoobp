# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.stock_account.tests.test_stockvaluationlayer import TestStockValuationCommon
from odoo.fields import Command


class TestStockAccountProduct(TestStockValuationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fifo_category = cls.env['product.category'].create({
            'name': 'All/Saleable FIFO',
            'parent_id': cls.env.ref('product.product_category_all').id,
            'property_cost_method': 'fifo',
        })
        cls.attribute_legs = cls.env['product.attribute'].create({
            'name': 'Legs',
            'value_ids': [
                Command.create({'name': 'Steel'}),
                Command.create({'name': 'Aluminium'}),
            ]
        })

    def test_update_categ_and_add_attributes(self):
        """
          Check that one can adapt the `property_cost_method` of a product with variants.
        """
        product_tmpl = self.env['product.template'].create({
            'name': 'Test product template with category',
            'is_storable': True,
            'type': 'consu',
            'standard_price': 20.0,
        })

        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        initial_product = product_tmpl.product_variant_ids
        self.env['stock.quant']._update_available_quantity(initial_product, warehouse.lot_stock_id, 10)

        initial_svl_count = len(self.env['stock.valuation.layer'].search([('product_id', '=', initial_product.id)]))

        product_tmpl.write({
            'categ_id': self.fifo_category.id,
            'attribute_line_ids': [Command.create({
                'attribute_id': self.attribute_legs.id,
                'value_ids': [Command.set(self.attribute_legs.value_ids.ids)]
            })]
        })

        self.assertEqual(len(product_tmpl.product_variant_ids), 2, "Expected 2 product variants after attribute update.")

        final_svl_count = len(self.env['stock.valuation.layer'].search([('product_id', 'in', product_tmpl.product_variant_ids.ids)]))
        self.assertEqual(final_svl_count, initial_svl_count, "SVL count should remain unchanged when adding attributes.")
