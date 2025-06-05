from odoo import Command
from odoo.addons.l10n_in.tests.common import L10nInTestInvoicingCommon
from odoo.tests import tagged
from datetime import date

TEST_DATE = date(2023, 5, 20)


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestGstrSection(L10nInTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.init_invoice(
            move_type='out_invoice',
            products=cls.product_a,
            post=True,
        )

        cls.partner_b.l10n_in_gst_treatment = "regular"

        cls.consumer_partner = cls.partner_a.copy({
            'vat': None,
            'l10n_in_gst_treatment': "consumer",
        })

        cls.deemed_export_partner = cls.partner_a.copy({"l10n_in_gst_treatment": "deemed_export"})
        cls.composition_partner = cls.partner_a.copy({"l10n_in_gst_treatment": "composition"})
        cls.uin_holders_partner = cls.partner_a.copy({"l10n_in_gst_treatment": "uin_holders"})
        cls.large_unregistered_partner = cls.consumer_partner.copy({"state_id": cls.state_in_mh.id, "l10n_in_gst_treatment": "unregistered"})
        cls.partner_foreign.l10n_in_gst_treatment = "overseas"

        cls.igst_base_tag = cls.env.ref('l10n_in.tax_tag_base_igst')
        cls.igst_tag = cls.env.ref('l10n_in.tax_tag_igst')

        cls.nil_rated_tag = cls.env.ref('l10n_in.tax_tag_nil_rated')

    @classmethod
    def setup_armageddon_tax(cls, tax_name, company_data):
        # TODO: default_account_tax_sale is not set when default_tax is group of tax
        # so when this method is called it's raise error so by overwrite this and stop call super.
        return cls.env["account.tax"]

    def _setup_moves(self, reverse_inv_func, invoice_date=TEST_DATE):
        b2b_invoice = self._init_inv(partner=self.partner_b, taxes=self.igst_sale_18, line_vals={'price_unit': 500, 'quantity': 2}, invoice_date=invoice_date)
        b2b_invoice_reverse = reverse_inv_func(inv=b2b_invoice, line_vals={'quantity': 1})

        b2b_intrastate_invoice = self._init_inv(partner=self.partner_a, taxes=self.sgst_sale_18, line_vals={'price_unit': 500, 'quantity': 2}, invoice_date=invoice_date)
        b2b_intrastate_invoice_reverse = reverse_inv_func(inv=b2b_intrastate_invoice, line_vals={'quantity': 1})

        b2c_intrastate_invoice = self._init_inv(partner=self.consumer_partner, taxes=self.sgst_sale_18, line_vals={'price_unit': 500, 'quantity': 2}, invoice_date=invoice_date)
        b2c_intrastate_invoice_reverse = reverse_inv_func(inv=b2c_intrastate_invoice, line_vals={'quantity': 1})

        b2cl_invoice = self._init_inv(partner=self.large_unregistered_partner, taxes=self.igst_sale_18, line_vals={'price_unit': 250000, 'quantity': 1}, invoice_date=invoice_date)
        b2cl_invoice_reverse = reverse_inv_func(inv=b2cl_invoice, line_vals={'quantity': 0.5})

        export_invoice = self._init_inv(partner=self.partner_foreign, taxes=self.igst_sale_18, line_vals={'price_unit': 500, 'quantity': 2}, invoice_date=invoice_date)
        export_invoice_reverse = reverse_inv_func(inv=export_invoice, line_vals={'quantity': 1})

        b2b_invoice_nilratedtax = self._init_inv(partner=self.partner_b, taxes=self.nil_rated_tax, line_vals={'price_unit': 500, 'quantity': 2}, invoice_date=invoice_date)
        b2b_invoice_nilratedtax_reverse = reverse_inv_func(inv=b2b_invoice_nilratedtax, line_vals={'quantity': 1})

        b2b_invoice_exemptedtax = self._init_inv(partner=self.partner_b, taxes=self.exempt_tax, line_vals={'price_unit': 500, 'quantity': 2}, invoice_date=invoice_date)
        b2b_invoice_exemptedtax_reverse = reverse_inv_func(inv=b2b_invoice_exemptedtax, line_vals={'quantity': 1})

        b2b_invoice_nongsttax = self._init_inv(partner=self.partner_b, taxes=self.non_gst_supplies, line_vals={'price_unit': 500, 'quantity': 2}, invoice_date=invoice_date)
        b2b_invoice_nongsttax_reverse = reverse_inv_func(inv=b2b_invoice_nongsttax, line_vals={'quantity': 1})

        b2b_invoice_deemed_export = self._init_inv(partner=self.deemed_export_partner, taxes=self.igst_sale_18, line_vals={'price_unit': 500, 'quantity': 2}, invoice_date=invoice_date)
        b2b_invoice_deemed_export_reverse = reverse_inv_func(inv=b2b_invoice_deemed_export, line_vals={'quantity': 1})  # Creates and posts credit note for the above invoice

        b2b_invoice_composition = self._init_inv(partner=self.composition_partner, taxes=self.igst_sale_18, line_vals={'price_unit': 500, 'quantity': 2}, invoice_date=invoice_date)
        b2b_invoice_composition_reverse = reverse_inv_func(inv=b2b_invoice_composition, line_vals={'quantity': 1})

        b2b_invoice_uin_holders = self._init_inv(partner=self.uin_holders_partner, taxes=self.igst_sale_18, line_vals={'price_unit': 500, 'quantity': 2}, invoice_date=invoice_date)
        b2b_invoice_uin_holders_reverse = reverse_inv_func(inv=b2b_invoice_uin_holders, line_vals={'quantity': 1})

        # if no tax is applied then it will be out of scope and not considered in GSTR1
        out_of_scope_invoice = self._init_inv(partner=self.partner_b, taxes=[], line_vals={'price_unit': 500, 'quantity': 2}, invoice_date=invoice_date)

        # for b2b invoice with 2 invoice_line_ids having different taxes
        b2b_invoice_gst_and_nil_rated_tax = self._init_inv(partner=self.partner_b, taxes=self.nil_rated_tax, line_vals={'price_unit': 700, 'quantity': 2}, post=False, invoice_date=invoice_date)
        existing_line_vals = b2b_invoice.invoice_line_ids[0].read(['product_id', 'account_id', 'price_unit', 'quantity', 'tax_ids'])[0]
        b2b_invoice_gst_and_nil_rated_tax.write({
            'invoice_line_ids': [
                Command.create({
                    'product_id': existing_line_vals['product_id'][0],
                    'account_id': existing_line_vals['account_id'][0],
                    'price_unit': existing_line_vals['price_unit'],
                    'quantity': existing_line_vals['quantity'],
                    'tax_ids': [(6, 0, existing_line_vals['tax_ids'])],
                })
            ]
        })
        b2b_invoice_gst_and_nil_rated_tax.action_post()

        # b2b invoice with special economic zone
        b2b_sez_invoice_gst_and_nil_rated_tax = b2b_invoice_gst_and_nil_rated_tax.copy(default={'l10n_in_gst_treatment': 'special_economic_zone', 'invoice_date': invoice_date})
        b2b_sez_invoice_gst_and_nil_rated_tax.action_post()

        moves = {
            'b2b_invoice': b2b_invoice,
            'b2b_invoice_reverse': b2b_invoice_reverse,
            'b2b_intrastate_invoice': b2b_intrastate_invoice,
            'b2b_intrastate_invoice_reverse': b2b_intrastate_invoice_reverse,
            'b2c_intrastate_invoice': b2c_intrastate_invoice,
            'b2c_intrastate_invoice_reverse': b2c_intrastate_invoice_reverse,
            'b2cl_invoice': b2cl_invoice,
            'b2cl_invoice_reverse': b2cl_invoice_reverse,
            'export_invoice': export_invoice,
            'export_invoice_reverse': export_invoice_reverse,
            'b2b_invoice_nilratedtax': b2b_invoice_nilratedtax,
            'b2b_invoice_nilratedtax_reverse': b2b_invoice_nilratedtax_reverse,
            'b2b_invoice_exemptedtax': b2b_invoice_exemptedtax,
            'b2b_invoice_exemptedtax_reverse': b2b_invoice_exemptedtax_reverse,
            'b2b_invoice_nongsttax': b2b_invoice_nongsttax,
            'b2b_invoice_nongsttax_reverse': b2b_invoice_nongsttax_reverse,
            'b2b_invoice_deemed_export': b2b_invoice_deemed_export,
            'b2b_invoice_deemed_export_reverse': b2b_invoice_deemed_export_reverse,
            'b2b_invoice_composition': b2b_invoice_composition,
            'b2b_invoice_composition_reverse': b2b_invoice_composition_reverse,
            'b2b_invoice_uin_holders': b2b_invoice_uin_holders,
            'b2b_invoice_uin_holders_reverse': b2b_invoice_uin_holders_reverse,
            'out_of_scope_invoice': out_of_scope_invoice,
            'b2b_invoice_gst_and_nil_rated_tax': b2b_invoice_gst_and_nil_rated_tax,
            'b2b_sez_invoice_gst_and_nil_rated_tax': b2b_sez_invoice_gst_and_nil_rated_tax,
        }

        return moves

    def _assert_gstr_section(self, move, expected_section):
        lines = move.line_ids.filtered(lambda l: bool(l.tax_tag_ids.ids))
        for line in lines:
            self.assertEqual(line.l10n_in_gstr_section, expected_section)

    def test_gstr1_sections(self):
        moves = self._setup_moves(self._create_credit_note)

        self._assert_gstr_section(moves['b2b_invoice'], 'sale_b2b_regular')
        self._assert_gstr_section(moves['b2b_invoice_reverse'], 'sale_cdnr_regular')
        self._assert_gstr_section(moves['b2b_intrastate_invoice'], 'sale_b2b_regular')
        self._assert_gstr_section(moves['b2b_intrastate_invoice_reverse'], 'sale_cdnr_regular')
        self._assert_gstr_section(moves['b2c_intrastate_invoice'], 'sale_b2cs')
        self._assert_gstr_section(moves['b2c_intrastate_invoice_reverse'], 'sale_b2cs')
        self._assert_gstr_section(moves['b2cl_invoice'], 'sale_b2cl')
        self._assert_gstr_section(moves['b2cl_invoice_reverse'], 'sale_cdnur_b2cl')
        self._assert_gstr_section(moves['export_invoice'], 'sale_exp_wp')
        self._assert_gstr_section(moves['export_invoice_reverse'], 'sale_cdnur_exp_wp')
        self._assert_gstr_section(moves['b2b_invoice_nilratedtax'], 'sale_nil_rated')
        self._assert_gstr_section(moves['b2b_invoice_nilratedtax_reverse'], 'sale_nil_rated')
        self._assert_gstr_section(moves['b2b_invoice_exemptedtax'], 'sale_nil_rated')
        self._assert_gstr_section(moves['b2b_invoice_exemptedtax_reverse'], 'sale_nil_rated')
        self._assert_gstr_section(moves['b2b_invoice_nongsttax'], 'sale_nil_rated')
        self._assert_gstr_section(moves['b2b_invoice_nongsttax_reverse'], 'sale_nil_rated')
        self._assert_gstr_section(moves['b2b_invoice_deemed_export'], 'sale_deemed_export')
        self._assert_gstr_section(moves['b2b_invoice_deemed_export_reverse'], 'sale_cdnr_deemed_export')
        self._assert_gstr_section(moves['b2b_invoice_composition'], 'sale_b2b_regular')
        self._assert_gstr_section(moves['b2b_invoice_composition_reverse'], 'sale_cdnr_regular')
        self._assert_gstr_section(moves['b2b_invoice_uin_holders'], 'sale_b2b_regular')
        self._assert_gstr_section(moves['b2b_invoice_uin_holders_reverse'], 'sale_cdnr_regular')

        # Invoice without Tax
        for line in moves['out_of_scope_invoice'].line_ids:
            self.assertEqual(line.l10n_in_gstr_section, 'sale_out_of_scope')

        # Invoices with multiple Taxes
        lines = moves['b2b_invoice_gst_and_nil_rated_tax'].line_ids.filtered(lambda l: bool(l.tax_tag_ids.ids))
        for line in lines:
            if line.tax_tag_ids.id in (self.igst_base_tag.id, self.igst_tag.id):
                self.assertEqual(line.l10n_in_gstr_section, 'sale_b2b_regular')
            elif line.tax_tag_ids.id == self.nil_rated_tag.id:
                self.assertEqual(line.l10n_in_gstr_section, 'sale_nil_rated')

        lines = moves['b2b_sez_invoice_gst_and_nil_rated_tax'].line_ids.filtered(lambda l: bool(l.tax_tag_ids.ids))
        for line in lines:
            if line.tax_tag_ids.id in (self.igst_base_tag.id, self.igst_tag.id):
                self.assertEqual(line.l10n_in_gstr_section, 'sale_sez_wp')
            elif line.tax_tag_ids.id == self.nil_rated_tag.id:
                self.assertEqual(line.l10n_in_gstr_section, 'sale_nil_rated')
