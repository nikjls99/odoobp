# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, models


class ProductCatalogMixin(models.AbstractModel):
    """ This mixin should be inherited when the model should be able to work
    with the product catalog.
    It assumes the model using this mixin has a O2M field where the products are added/removed and
    this field's co-related model should has a method named `_get_product_catalog_lines_data`.
    """
    _name = 'product.catalog.mixin'
    _description = 'Product Catalog Mixin'

    @api.readonly
    def action_add_from_catalog(self):
        kanban_view_id = self.env.ref('product.product_view_kanban_catalog').id
        search_view_id = self.env.ref('product.product_view_search_catalog').id
        additional_context = self._get_action_add_from_catalog_extra_context()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Products'),
            'res_model': 'product.product',
            'views': [(kanban_view_id, 'kanban'), (False, 'form')],
            'search_view_id': [search_view_id, 'search'],
            'domain': self._get_product_catalog_domain(),
            'context': {**self.env.context, **additional_context},
        }

    def _default_order_line_values(self, child_field=False):
        return {
            'quantity': 0,
            'readOnly': self._is_readonly() if self else False,
        }

    def _get_product_catalog_domain(self):
        """Get the domain to search for products in the catalog.

        For a model that uses products that has to be hidden in the catalog, it
        must override this method and extend the appropriate domain.
        :returns: A list of tuples that represents a domain.
        :rtype: list
        """
        return ['|', ('company_id', '=', False), ('company_id', 'parent_of', self.company_id.id), ('type', '!=', 'combo')]

    def _get_product_catalog_record_lines(self, product_ids, **kwargs):
        """ Returns the record's lines grouped by product.
        Must be overrided by each model using this mixin.

        :param list product_ids: The ids of the products currently displayed in the product catalog.
        :rtype: dict
        """
        return {}

    def _get_product_catalog_order_data(self, products, **kwargs):
        """ Returns a dict containing the products' data. Those data are for products who aren't in
        the record yet. For products already in the record, see `_get_product_catalog_lines_data`.

        For each product, its id is the key and the value is another dict with all needed data.
        By default, the price is the only needed data but each model is free to add more data.
        Must be overrided by each model using this mixin.

        :param products: Recordset of `product.product`.
        :param dict kwargs: additional values given for inherited models.
        :rtype: dict
        :return: A dict with the following structure:
            {
                'productId': int
                'quantity': float (optional)
                'productType': string
                'price': float
                'uomDisplayName': string
                'code': string (optional)
                'readOnly': bool (optional)
            }
        """
        return {
            product.id: {
                'productType': product.type,
                'uomDisplayName': product.uom_id.display_name,
                'code': product.code if product.code else '',
            }
            for product in products
        }

    def _get_product_catalog_order_line_info(self, product_ids, child_field=False, **kwargs):
        """ Returns products information to be shown in the catalog.
        :param list product_ids: The products currently displayed in the product catalog, as a list
                                 of `product.product` ids.
        :param dict kwargs: additional values given for inherited models.
        :rtype: dict
        :return: A dict with the following structure:
            {
                'productId': int
                'quantity': float (optional)
                'productType': string
                'price': float
                'uomDisplayName': string
                'code': string (optional)
                'readOnly': bool (optional)
            }
        """
        order_line_info = {}
        default_data = self._default_order_line_values(child_field)

        for product, record_lines in self._get_product_catalog_record_lines(product_ids, child_field=child_field, **kwargs).items():
            order_line_info[product.id] = {
               **record_lines._get_product_catalog_lines_data(parent_record=self, **kwargs),
               'productType': product.type,
               'code': product.code if product.code else '',
            }
            if not order_line_info[product.id]['uomDisplayName']:
                order_line_info[product.id]['uomDisplayName'] = product.uom_id.display_name
            product_ids.remove(product.id)

        products = self.env['product.product'].browse(product_ids)
        product_data = self._get_product_catalog_order_data(products, **kwargs)
        for product_id, data in product_data.items():
            order_line_info[product_id] = {**default_data, **data}
        return order_line_info

    def _get_action_add_from_catalog_extra_context(self):
        return {
            'display_uom': self.env.user.has_group('uom.group_uom'),
            'product_catalog_order_id': self.id,
            'product_catalog_order_model': self._name,
        }

    def _is_readonly(self):
        """ Must be overrided by each model using this mixin.
        :return: Whether the record is read-only or not.
        :rtype: bool
        """
        return False

    def _update_order_line_info(self, product_id, quantity, **kwargs):
        """ Update the line information for a given product or create a new one if none exists yet.
        Must be overrided by each model using this mixin.
        :param int product_id: The product, as a `product.product` id.
        :param int quantity: The product's quantity.
        :param dict kwargs: additional values given for inherited models.
        :return: The unit price of the product, based on the pricelist of the
                 purchase order and the quantity selected.
        :rtype: float
        """
        return 0

    def _create_order_section(self, section_name, **kwargs):
        """ Create a new section.

        :param str section_name: The name of the section to create.
        :param dict kwargs: additional values given for inherited models.
        :return: A dictionary with newly created section information.
        :rtype: dict
        """
        return {}

    def _get_order_sections(self, *, child_field=False, **kwargs):
        """ Returns the sections to be shown in the product catalog.

        :param dict kwargs: additional values given for inherited models.
        :return: A list of dictionaries containing 'id', 'name', 'sequence' and 'line_count' for
                 each section.
        :rtype: list
        """
        if not child_field:
            return []
        sections = [
            {
                'id': sec.id,
                'name': sec.name,
                'sequence': sec.sequence,
                'line_count': len(self[child_field].filtered(
                    lambda line: (
                        line.linked_section_line_id == sec
                        and not line.display_type
                        and line.product_id.product_tmpl_id.type != 'combo'
                    )
                )),
            }
            for sec in self[child_field].filtered(
                lambda line: line.display_type == 'line_section'
            )
        ]

        no_section_lines_count = 0
        for line in self[child_field]:
            if line.display_type == 'line_section':
                break
            if not line.display_type and line.product_id.product_tmpl_id.type != 'combo':
                no_section_lines_count += 1

        sections.append({
            'id': None,
            'name': self.env._('No Section'),
            'sequence': 0,
            'line_count': no_section_lines_count,
        })
        return sorted(sections, key=lambda x: x['sequence'])

    def _resequence_order_sections(self, sections, *, child_field=False, **kwargs):
        """ Resequence the sections of the order based on the provided move and target sections.
        The sections are reordered by updating their sequence numbers.

        :param list sections: A list of dictionaries containing move and target sections.
        :param dict kwargs: additional values given for inherited models.
        :return: A dictonary containing the new sequences of all the sections of order.
        :rtype: dict
        """
        if not child_field:
            return {}
        lines = self[child_field].sorted('sequence')
        move_section, target_section = sections

        move_block = lines.filtered(
            lambda line: line.id == move_section['id']
            or line.linked_section_line_id.id == move_section['id']
        )

        target_block = lines.filtered(
            lambda line: line.id == target_section['id']
            or line.linked_section_line_id.id == target_section['id']
        )

        remaining_lines = lines - move_block
        insert_after = move_section['sequence'] < target_section['sequence']
        insert_index = len(remaining_lines)
        for idx, line in enumerate(remaining_lines):
            if line.id == (target_block[-1].id if insert_after else target_section['id']):
                insert_index = idx + 1 if insert_after else idx
                break

        reordered_lines = (
            remaining_lines[:insert_index] +
            move_block +
            remaining_lines[insert_index:]
        )

        sections = {}
        for sequence, line in enumerate(reordered_lines, start=1):
            line.sequence = sequence
            if line.display_type == 'line_section':
                sections[line.id] = sequence

        return sections
