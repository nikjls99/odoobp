# Part of Odoo. See LICENSE file for full copyright and licensing details.

import werkzeug


from odoo import _, http
from odoo.addons.l10n_tw_edi_ecpay.utils import EcPayAPI
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, route


class WebsiteSaleL10nTW(WebsiteSale):
    def _is_valid_mobile_barcode(self, carrier_number):
        json_data = {
            "MerchantID": request.env.company.sudo().l10n_tw_edi_ecpay_merchant_id,
            "BarCode": carrier_number,
        }

        response_data = EcPayAPI(request.env.company).call_ecpay_api("/CheckBarcode", json_data)
        return int(response_data.get("RtnCode")) == 1 and response_data.get("IsExist") == "Y"

    def _is_valid_tax_id(self, tax_id):
        json_data = {
            "MerchantID": request.env.company.sudo().l10n_tw_edi_ecpay_merchant_id,
            "UnifiedBusinessNo": tax_id,
        }

        response_data = EcPayAPI(request.env.company).call_ecpay_api("/GetCompanyNameByTaxID", json_data)
        return int(response_data.get("RtnCode")) == 1 and response_data.get("CompanyName")

    def _is_valid_love_code(self, love_code):
        json_data = {
            "MerchantID": request.env.company.sudo().l10n_tw_edi_ecpay_merchant_id,
            "LoveCode": love_code,
        }

        response_data = EcPayAPI(request.env.company).call_ecpay_api("/CheckLoveCode", json_data)
        return int(response_data.get("RtnCode")) == 1 and response_data.get("IsExist") == "Y"

    @route('/shop/l10n_tw_invoicing_info', type='http', auth='public', methods=['GET', 'POST'], website=True, sitemap=False)
    def l10n_tw_invoicing_info(self, **kw):
        order = request.website.sale_get_order()
        l10n_tw_edi_is_b2b = bool(order.partner_id.parent_id or order.partner_id.company_type == "company")
        # === GET ===
        default_vals = {}
        if request.httprequest.method == 'GET':
            if order.l10n_tw_edi_is_print or l10n_tw_edi_is_b2b:
                default_vals['print_group'] = "1"
            elif order.l10n_tw_edi_love_code:
                default_vals['print_group'] = "2"
            else:
                default_vals['print_group'] = "0"
            default_vals['identifier'] = order.partner_id.vat
            default_vals["is_b2b"] = l10n_tw_edi_is_b2b
            default_vals['love_code'] = order.l10n_tw_edi_love_code
            default_vals['carrier_type'] = order.l10n_tw_edi_carrier_type if order.l10n_tw_edi_carrier_type else "0"
            default_vals['carrier_number'] = order.l10n_tw_edi_carrier_number

        # === POST & possibly redirect ===
        errors = {}
        if request.httprequest.method == 'POST':
            default_vals = {
                'print_group': kw.get('print_group'),
                'love_code': kw.get('l10n_tw_edi_love_code'),
                'identifier': kw.get('identifier'),
                'carrier_type': kw.get('l10n_tw_edi_carrier_type'),
                'carrier_number': kw.get('l10n_tw_edi_carrier_number'),
                'is_b2b': l10n_tw_edi_is_b2b,
            }
            if kw.get('print_group') == '0':
                if kw.get('l10n_tw_edi_carrier_type') == '2' and not kw.get('l10n_tw_edi_carrier_number'):
                    errors['carrier_number'] = _('Carrier number is invalid')
                if kw.get('l10n_tw_edi_carrier_type') == '3' \
                        and not self._is_valid_mobile_barcode(kw.get('l10n_tw_edi_carrier_number')):
                    errors['carrier_number'] = _('Mobile Barcode is invalid')
            elif kw.get('print_group') == '1' and l10n_tw_edi_is_b2b and not self._is_valid_tax_id(kw.get('identifier')):
                errors['identifier'] = _('Tax ID is invalid')
            elif kw.get('print_group') == '2' and not self._is_valid_love_code(kw.get('l10n_tw_edi_love_code')):
                errors['love_code'] = _('Love Code is invalid')

            order.write({
                'l10n_tw_edi_is_print': default_vals['print_group'] == '1',
                'l10n_tw_edi_love_code': default_vals['love_code'] if default_vals['print_group'] == '2' and 'love_code' not in errors else False,
                'l10n_tw_edi_carrier_type': default_vals['carrier_type'] if default_vals['print_group'] == '0' and default_vals['carrier_type'] != "0" and "carrier_number" not in errors else False,
                'l10n_tw_edi_carrier_number': default_vals['carrier_number'] if default_vals['print_group'] == '0' and default_vals['carrier_type'] in ['2', '3'] and "carrier_number" not in errors else False,
            })

            if default_vals['print_group'] == '1' and l10n_tw_edi_is_b2b and 'identifier' not in errors:
                if order.partner_id.parent_id:
                    order.partner_id.parent_id.vat = kw.get("identifier")
                else:
                    order.partner_id.vat = kw.get("identifier")

            if not errors:
                return request.redirect("/shop/confirm_order")

        values = {
            'request': request,
            'website_sale_order': order,
            'l10n_tw_show_extra_info': True,
            'default_vals': default_vals,
            'errors': errors,
        }

        return request.render('l10n_tw_edi_ecpay_website_sale.l10n_tw_edi_invoicing_info', values)

    @http.route("/payment/ecpay/check_mobile_barcode/<int:sale_order_id>", type="json", auth="public")
    def check_mobile_barcode(self, sale_order_id, **kwargs):
        try:
            _ = CustomerPortal._document_check_access(self, 'sale.order', sale_order_id, kwargs.get("access_token", False))
        except (AccessError, MissingError):
            raise werkzeug.exceptions.NotFound

        return self._is_valid_mobile_barcode(kwargs.get("carrier_number", False))

    @http.route("/payment/ecpay/check_love_code/<int:sale_order_id>", type="json", auth="public")
    def check_love_code(self, sale_order_id, **kwargs):
        try:
            _ = CustomerPortal._document_check_access(self, 'sale.order', sale_order_id, kwargs.get("access_token", False))
        except (AccessError, MissingError):
            raise werkzeug.exceptions.NotFound
        return self._is_valid_love_code(kwargs.get("love_code", False))

    @http.route("/payment/ecpay/check_tax_id/<int:sale_order_id>", type="json", auth="public")
    def check_tax_id(self, sale_order_id, **kwargs):
        try:
            _ = CustomerPortal._document_check_access(self, 'sale.order', sale_order_id, kwargs.get("access_token", False))
        except (AccessError, MissingError):
            raise werkzeug.exceptions.NotFound

        return self._is_valid_tax_id(kwargs.get("identifier", False))

    def _prepare_address_form_values(self, order_sudo, partner_sudo, address_type, **kwargs):
        rendering_values = super()._prepare_address_form_values(
            order_sudo, partner_sudo, address_type=address_type, **kwargs
        )
        rendering_values["invoice_edi_formats"] = dict(partner_sudo._fields['invoice_edi_format'].selection)
        return rendering_values

    def _handle_extra_form_data(self, extra_form_data, address_values):
        super()._handle_extra_form_data(extra_form_data, address_values)
        if extra_form_data.get('invoice_edi_format'):
            partner_id = request.website.sale_get_order().partner_id
            if partner_id.parent_id:
                request.website.sale_get_order().partner_id.parent_id.invoice_edi_format = extra_form_data.get('invoice_edi_format')
            else:
                request.website.sale_get_order().partner_id.invoice_edi_format = extra_form_data.get('invoice_edi_format')
