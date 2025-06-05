# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.addons.mail.tools.discuss import Store


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _to_store(self, store: Store, fields, *, main_user_by_partner=None, **kwargs):
        super()._to_store(store, fields, **kwargs)
        if "im_status" in fields:
            for partner in self:
                main_user = (main_user_by_partner and main_user_by_partner.get(partner)) or partner.main_user_id
                store.add(partner, {"remote_work_location_type": main_user.remote_work_location_type})
