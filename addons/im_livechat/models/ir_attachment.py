# Part of Odoo. See LICENSE file for full copyright and licensing details.

from werkzeug.urls import url_encode

from odoo import api, fields, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    download_url = fields.Char(compute="_compute_download_url", string="Download URL")

    @api.depends("type", "url", "public", "access_token")
    def _compute_download_url(self):
        """Compute the download URL for the attachment."""
        self.generate_access_token()
        for attachment in self:
            if attachment.type == "url":
                attachment.download_url = attachment.url
            else:
                params = {"download": "true"}
                if not attachment.public:
                    params["access_token"] = attachment.access_token
                attachment.download_url = "/web/content/%s?%s" % (attachment.id, url_encode(params))
