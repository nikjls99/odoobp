# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.fields import Command, Domain


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_frontend_writable_fields(self):
        """Define the fields a portal/public user can change on their contact and address records.

        :rtype: set
        """
        return {
            'name', 'phone', 'email', 'street', 'street2', 'city', 'state_id', 'country_id', 'zip',
            'zipcode', 'vat', 'company_name',
        }

    def _create_company(self, company_name):
        self.ensure_one()
        # Create parent company
        values = dict(name=company_name, is_company=True, vat=self.vat)
        values.update(self._convert_fields_to_values(self._address_fields()))
        new_company = self.create(values)
        # Set new company as my parent
        self.write({
            'parent_id': new_company.id,
            'child_ids': [
                Command.update(partner_id, dict(parent_id=new_company.id))
                for partner_id in self.child_ids.ids
            ],
        })
        return True

    def can_edit_country(self):
        self.ensure_one()
        return True

    def can_edit_vat(self):
        """ `vat` is a commercial field, synced between the parent (commercial
        entity) and the children. Only the commercial entity should be able to
        edit it (as in backend)."""
        self.ensure_one()
        return True

    def _can_be_edited_by_current_customer(self, **kwargs):
        """Return whether partner can be edited by current user."""
        self.ensure_one()
        if self == self._get_current_partner(**kwargs):
            return True
        children_partner_ids = self.env['res.partner']._search([
            ('id', 'child_of', self.commercial_partner_id.id),
            ('type', 'in', ('invoice', 'delivery', 'other')),
        ])
        return self.id in children_partner_ids

    @api.model
    def _get_current_partner(self, **kwargs):
        """ Get main partner of the current user base on logged in user and kwargs. """
        return self.env.user.partner_id

    def _get_delivery_address_domain(self):
        return Domain([
            ('id', 'child_of', self.ids),
            '|', ('type', 'in', ['delivery', 'other']), ('id', '=', self.id),
        ])
