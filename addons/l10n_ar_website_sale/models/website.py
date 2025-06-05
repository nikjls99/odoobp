from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'

    l10n_ar_website_sale_show_both_prices = fields.Boolean(
        string="Display Price without National Taxes",
        default=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for website in vals_list:
            if (
                website.get('company_id')
                and self.env['res.company'].browse(website['company_id']).country_code == 'AR'
            ):
                website.setdefault('show_line_subtotals_tax_selection', 'tax_included')
                website.setdefault('l10n_ar_website_sale_show_both_prices', True)
        return super().create(vals_list)
