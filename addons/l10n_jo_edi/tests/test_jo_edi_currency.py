from odoo import Command
from odoo.tests import tagged
from odoo.addons.l10n_jo_edi.tests.jo_edi_common import JoEdiCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestJoEdiCurrency(JoEdiCommon):
    def _get_xml_currency_code(self, invoice):
        generated_file = self.env['account.edi.xml.ubl_21.jo']._export_invoice(invoice)[0]
        xml_tree = self.get_xml_tree_from_string(generated_file)
        document_currency_code = xml_tree.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode").text
        tax_currency_code = xml_tree.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxCurrencyCode").text
        self.assertEqual(document_currency_code, tax_currency_code)
        return document_currency_code

    def test_jo_xml_currency(self):
        currency_list = [
            'USD',  # United States Dollar
            'EUR',  # Euro
            'SAR',  # Saudi Riyal
            'AED',  # UAE Dirham
            'OMR',  # Rial Omani
            'GBP',  # Pound Sterling
            'QAR',  # Qatari Rial
            'KWD',  # Kuwaiti Dinar
            'BHD',  # Bahraini Dinar
            'AUD',  # Australian Dollar
            'CAD',  # Canadian Dollar (corrected spelling)
            'JPY',  # Japanese Yen
            'CHF',  # Swiss Franc
            'TRY',  # Turkish Lira
            'SYP',  # Syrian Pound
            'EGP',  # Egyptian Pound
        ]
        for currency_code in currency_list:
            with self.subTest(subtest_name=f"XML should have code {currency_code} in DocumentCurrencyCode and TaxCurrencyCode"):
                currency = self.env.ref(f'base.{currency_code}')
                self.setup_currency_rate(currency, 0.5)
                invoice_vals = {
                    'name': f'{currency_code}/998833/0',
                    'invoice_line_ids': [Command.create({})],
                    'currency_id': currency.id,
                }
                invoice = self._l10n_jo_create_invoice(invoice_vals)
                xml_currency_code = self._get_xml_currency_code(invoice)
                self.assertEqual(xml_currency_code, currency.name)
