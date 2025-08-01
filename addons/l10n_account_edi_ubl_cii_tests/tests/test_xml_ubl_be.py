import base64
from lxml import etree

from odoo import Command
from odoo.addons.l10n_account_edi_ubl_cii_tests.tests.common import TestUBLCommon
from odoo.addons.account.tests.test_account_move_send import TestAccountMoveSendCommon
from odoo.tests import tagged


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestUBLBE(TestUBLCommon, TestAccountMoveSendCommon):

    @classmethod
    @TestUBLCommon.setup_country("be")
    def setUpClass(cls):
        super().setUpClass()

        cls.company.vat = "BE0246697724"

        # seller
        cls.partner_1 = cls.env['res.partner'].create({
            'name': "partner_1",
            'street': "Chaussée de Namur 40",
            'zip': "1367",
            'city': "Ramillies",
            'vat': 'BE0202239951',
            'country_id': cls.env.ref('base.be').id,
            'bank_ids': [(0, 0, {'acc_number': 'BE15001559627230'})],
            'ref': 'ref_partner_1',
            'invoice_edi_format': 'ubl_bis3',
        })

        # buyer
        cls.partner_2 = cls.env['res.partner'].create({
            'name': "partner_2",
            'street': "Rue des Bourlottes 9",
            'zip': "1367",
            'city': "Ramillies",
            'vat': 'BE0477472701',
            'country_id': cls.env.ref('base.be').id,
            'bank_ids': [(0, 0, {'acc_number': 'BE90735788866632'})],
            'ref': 'ref_partner_2',
            'invoice_edi_format': 'ubl_bis3',
        })

        cls.tax_25 = cls.env['account.tax'].create({
            'name': 'tax_25',
            'amount_type': 'percent',
            'amount': 25,
            'type_tax_use': 'purchase',
            'country_id': cls.env.ref('base.be').id,
        })

        cls.tax_21 = cls.env['account.tax'].create({
            'name': 'tax_21',
            'amount_type': 'percent',
            'amount': 21,
            'type_tax_use': 'sale',
            'country_id': cls.env.ref('base.be').id,
            'sequence': 10,
        })

        cls.tax_15 = cls.env['account.tax'].create({
            'name': 'tax_15',
            'amount_type': 'percent',
            'amount': 15,
            'type_tax_use': 'sale',
            'country_id': cls.env.ref('base.be').id,
        })

        cls.tax_12 = cls.env['account.tax'].create({
            'name': 'tax_12',
            'amount_type': 'percent',
            'amount': 12,
            'type_tax_use': 'sale',
            'country_id': cls.env.ref('base.be').id,
        })

        cls.tax_6 = cls.env['account.tax'].create({
            'name': 'tax_6',
            'amount_type': 'percent',
            'amount': 6,
            'type_tax_use': 'sale',
            'country_id': cls.env.ref('base.be').id,
        })

        cls.tax_0 = cls.env['account.tax'].create({
            'name': 'tax_0',
            'amount_type': 'percent',
            'amount': 0,
            'type_tax_use': 'sale',
            'country_id': cls.env.ref('base.be').id,
        })

        cls.pay_term = cls.env['account.payment.term'].create({
            'name': "2/7 Net 30",
            'note': "Payment terms: 30 Days, 2% Early Payment Discount under 7 days",
            'early_discount': True,
            'discount_percentage': 2,
            'discount_days': 7,
            'line_ids': [
                Command.create({'value': 'percent', 'value_amount': 100.0, 'nb_days': 30})],
        })

    ####################################################
    # Test export - import
    ####################################################

    def test_export_import_invoice(self):
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            delivery_date='2017-01-15',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 2.0,
                    'product_uom_id': self.env.ref('uom.product_uom_dozen').id,
                    'price_unit': 990.0,
                    'discount': 10.0,
                    'tax_ids': [(6, 0, self.tax_21.ids)],
                },
                {
                    'product_id': self.product_b.id,
                    'quantity': 10.0,
                    'product_uom_id': self.env.ref('uom.product_uom_unit').id,
                    'price_unit': 100.0,
                    'tax_ids': [(6, 0, self.tax_12.ids)],
                },
                {
                    'product_id': self.product_b.id,
                    'quantity': -1.0,
                    'product_uom_id': self.env.ref('uom.product_uom_unit').id,
                    'price_unit': 100.0,
                    'tax_ids': [(6, 0, self.tax_12.ids)],
                },
            ],
        )
        attachment = self._assert_invoice_attachment(
            invoice.ubl_cii_xml_id,
            xpaths=f'''
                <xpath expr="./*[local-name()='ID']" position="replace">
                    <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:ID>
                </xpath>
                <xpath expr=".//*[local-name()='InvoiceLine'][1]/*[local-name()='ID']" position="replace">
                    <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:ID>
                </xpath>
                <xpath expr=".//*[local-name()='InvoiceLine'][2]/*[local-name()='ID']" position="replace">
                    <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:ID>
                </xpath>
                <xpath expr=".//*[local-name()='InvoiceLine'][3]/*[local-name()='ID']" position="replace">
                    <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:ID>
                </xpath>
                <xpath expr=".//*[local-name()='PaymentMeans']/*[local-name()='PaymentID']" position="replace">
                    <cbc:PaymentID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:PaymentID>
                </xpath>
                <xpath expr=".//*[local-name()='AdditionalDocumentReference']/*[local-name()='Attachment']/*[local-name()='EmbeddedDocumentBinaryObject']" position="attributes">
                    <attribute name="mimeCode">application/pdf</attribute>
                    <attribute name="filename">{invoice.invoice_pdf_report_id.name}</attribute>
                </xpath>
            ''',
            expected_file_path='from_odoo/bis3_out_invoice.xml',
        )
        self.assertEqual(attachment.name[-12:], "ubl_bis3.xml")
        self._assert_imported_invoice_from_etree(invoice, attachment)

    def test_export_import_invoice_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_export_import_invoice()

    def test_export_import_refund(self):
        refund = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_refund',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 2.0,
                    'product_uom_id': self.env.ref('uom.product_uom_dozen').id,
                    'price_unit': 990.0,
                    'discount': 10.0,
                    'tax_ids': [(6, 0, self.tax_21.ids)],
                },
                {
                    'product_id': self.product_b.id,
                    'quantity': 10.0,
                    'product_uom_id': self.env.ref('uom.product_uom_unit').id,
                    'price_unit': 100.0,
                    'tax_ids': [(6, 0, self.tax_12.ids)],
                },
                {
                    'product_id': self.product_b.id,
                    'quantity': -1.0,
                    'product_uom_id': self.env.ref('uom.product_uom_unit').id,
                    'price_unit': 100.0,
                    'tax_ids': [(6, 0, self.tax_12.ids)],
                },
            ],
        )
        attachment = self._assert_invoice_attachment(
            refund.ubl_cii_xml_id,
            xpaths=f'''
                <xpath expr="./*[local-name()='ID']" position="replace">
                    <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:ID>
                </xpath>
                <xpath expr="./*[local-name()='PaymentMeans']/*[local-name()='PaymentID']" position="replace">
                    <cbc:PaymentID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:PaymentID>
                </xpath>
                <xpath expr=".//*[local-name()='CreditNoteLine'][1]/*[local-name()='ID']" position="replace">
                    <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:ID>
                </xpath>
                <xpath expr=".//*[local-name()='CreditNoteLine'][2]/*[local-name()='ID']" position="replace">
                    <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:ID>
                </xpath>
                <xpath expr=".//*[local-name()='CreditNoteLine'][3]/*[local-name()='ID']" position="replace">
                    <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:ID>
                </xpath>
                <xpath expr=".//*[local-name()='AdditionalDocumentReference']/*[local-name()='Attachment']/*[local-name()='EmbeddedDocumentBinaryObject']" position="attributes">
                    <attribute name="mimeCode">application/pdf</attribute>
                    <attribute name="filename">{refund.invoice_pdf_report_id.name}</attribute>
                </xpath>
            ''',
            expected_file_path='from_odoo/bis3_out_refund.xml',
        )
        self.assertEqual(attachment.name[-12:], "ubl_bis3.xml")
        self._assert_imported_invoice_from_etree(refund, attachment)

    def test_export_import_refund_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_export_import_refund()

    def test_export_import_cash_rounding(self):
        cash_rounding_line = self.env['account.cash.rounding'].create({
            'name': '1.0 Line',
            'rounding': 1.00,
            'strategy': 'add_invoice_line',
            'profit_account_id': self.company_data['default_account_revenue'].copy().id,
            'loss_account_id': self.company_data['default_account_expense'].copy().id,
            'rounding_method': 'HALF-UP',
        })

        cash_rounding_tax = self.env['account.cash.rounding'].create({
            'name': '1.0 Tax',
            'rounding': 1.00,
            'strategy': 'biggest_tax',
            'rounding_method': 'HALF-UP',
        })

        test_data = [
            {
                'invoice_cash_rounding_id': False,
                'expected': {
                    'xml_file': 'from_odoo/bis3_out_invoice_cash_rounding_line.xml',
                    # There is no rounding amount
                    'xpaths': '''
                        <xpath expr="./*[local-name()='LegalMonetaryTotal']/*[local-name()='PayableRoundingAmount']" position="replace"/>
                        <xpath expr="./*[local-name()='LegalMonetaryTotal']/*[local-name()='PayableAmount']" position="replace">
                            <cbc:PayableAmount currencyID="USD" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">84.70</cbc:PayableAmount>
                        </xpath>
                    ''',
                },
                'expected_rounding_invoice_line_values': None,
            },
            {
                'invoice_cash_rounding_id': cash_rounding_tax,
                'expected': {
                    'xml_file': 'from_odoo/bis3_out_invoice_cash_rounding_tax.xml',
                    'xpaths': None,
                },
                'expected_rounding_invoice_line_values': None,
            },
            {
                'invoice_cash_rounding_id': cash_rounding_line,
                'expected': {
                    'xml_file': 'from_odoo/bis3_out_invoice_cash_rounding_line.xml',
                    'xpaths': None,
                },
                # We create an invoice line for the rounding amount.
                # (This adjusts the base amount of the invoice.)
                'expected_rounding_invoice_line_values': {
                    'display_type': 'product',
                    'name': 'Rounding',
                    'quantity': 1,
                    'product_id': False,
                    'price_unit': 0.30,
                    'amount_currency': -0.30,
                    'balance': -0.15,
                    'currency_id': self.other_currency.id,
                }
            },
        ]
        for test in test_data:
            cash_rounding_method = test['invoice_cash_rounding_id']
            with self.subTest(sub_test_name=f"cash rounding method: {cash_rounding_method.name if cash_rounding_method else 'None'}"):
                invoice = self._generate_move(
                    seller=self.partner_1,
                    buyer=self.partner_2,
                    move_type='out_invoice',
                    currency_id=self.other_currency.id,
                    invoice_cash_rounding_id=cash_rounding_method.id if cash_rounding_method else False,
                    invoice_line_ids=[
                        {
                            'product_id': self.product_a.id,
                            'quantity': 1,
                            'price_unit': 70.00,
                            'tax_ids': [Command.set([self.tax_21.id])],
                        },
                    ],
                )

                attachment = invoice.ubl_cii_xml_id
                self.assertTrue(attachment)
                self._assert_invoice_attachment(invoice.ubl_cii_xml_id, test['expected']['xpaths'], test['expected']['xml_file'])

                # Check that importing yields the expected results.

                # For the 'add_invoice_line' strategy we create a dedicated invoice line for the cash rounding.
                rounding_invoice_line_values = test['expected_rounding_invoice_line_values']
                if rounding_invoice_line_values:
                    invoice.button_draft()
                    invoice.invoice_cash_rounding_id = False  # Do not round twice
                    invoice.invoice_line_ids.create([{
                        'company_id': invoice.company_id.id,
                        'move_id': invoice.id,
                        'partner_id': invoice.partner_id.id,
                        **rounding_invoice_line_values,
                    }])
                    invoice.action_post()

                self._assert_imported_invoice_from_etree(invoice, attachment)

                # Check that importing a bill yields the expected results.

                bill = self.company_data['default_journal_purchase']._create_document_from_attachment(attachment.ids)
                self.assertTrue(bill)
                self.assert_same_invoice(invoice, bill, partner_id=self.partner_1.id)

    def test_export_import_cash_rounding_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_export_import_cash_rounding()

    def test_encoding_in_attachment_ubl(self):
        invoice = self._generate_move(
            seller=self.partner_1,
            buyer=self.partner_2,
            move_type='out_invoice',
            invoice_line_ids=[{'product_id': self.product_a.id}],
        )
        self._test_encoding_in_attachment(invoice.ubl_cii_xml_id, 'ubl_bis3.xml')

    def test_sending_to_public_admin(self):
        """ A public administration has no VAT, but has an arbitrary number (see:
        https://pch.gouvernement.lu/fr/peppol.html). Then, the `EndpointID` node should be filled with this arbitrary
        number (use the field `peppol_endpoint`).
        In addition, when the Seller has no VAT, the node PartyTaxScheme and PartyLegalEntity may contain the Seller
        identifier or the Seller legal registration identifier.
        """
        def check_attachment(invoice, expected_file):
            self._assert_invoice_attachment(
                invoice.ubl_cii_xml_id,
                xpaths=f'''
                    <xpath expr="./*[local-name()='PaymentMeans']/*[local-name()='PaymentID']" position="replace">
                        <cbc:PaymentID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:PaymentID>
                    </xpath>
                    <xpath expr=".//*[local-name()='InvoiceLine'][1]/*[local-name()='ID']" position="replace">
                        <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">___ignore___</cbc:ID>
                    </xpath>
                    <xpath expr=".//*[local-name()='AdditionalDocumentReference']/*[local-name()='Attachment']/*[local-name()='EmbeddedDocumentBinaryObject']" position="attributes">
                        <attribute name="mimeCode">application/pdf</attribute>
                        <attribute name="filename">{invoice.invoice_pdf_report_id.name}</attribute>
                    </xpath>
                ''',
                expected_file_path=expected_file,
            )
        # Setup a public admin in Luxembourg without VAT
        self.partner_2.write({
            'vat': None,
            'peppol_eas': '9938',
            'peppol_endpoint': '00005000041',
            'country_id': self.env.ref('base.lu').id,
        })
        invoice_vals = {
            'move_type': 'out_invoice',
            'invoice_line_ids': [{
                'product_id': self.product_a.id,
                'quantity': 2,
                'price_unit': 100,
                'tax_ids': [(6, 0, self.tax_21.ids)],
            }],
        }
        invoice1 = self._generate_move(self.partner_1, self.partner_2, **invoice_vals)
        check_attachment(invoice1, "from_odoo/bis3_out_invoice_public_admin_1.xml")
        # Switch the partner's roles
        invoice2 = self._generate_move(self.partner_2, self.partner_1, **invoice_vals)
        check_attachment(invoice2, "from_odoo/bis3_out_invoice_public_admin_2.xml")

    def test_sending_to_public_admin_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_sending_to_public_admin()

    def test_rounding_price_unit(self):
        """ OpenPeppol states that:
        * All document level amounts shall be rounded to two decimals for accounting
        * Invoice line net amount shall be rounded to two decimals
        See: https://docs.peppol.eu/poacc/billing/3.0/bis/#_rounding
        Do not round the unit prices. It allows to obtain the correct line amounts when prices have more than 2
        digits.
        """
        # Set the allowed number of digits for the price_unit
        decimal_precision = self.env['decimal.precision'].search([('name', '=', 'Product Price')], limit=1)
        self.assertTrue(bool(decimal_precision), "The decimal precision for Product Price is required for this test")
        decimal_precision.digits = 4

        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 10000,
                    'price_unit': 0.4567,
                    'tax_ids': [(6, 0, self.tax_21.ids)],
                }
            ],
        )
        self._assert_invoice_attachment(invoice.ubl_cii_xml_id, None, 'from_odoo/bis3_out_invoice_rounding.xml')

    def test_rounding_price_unit_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_rounding_price_unit()

    def test_inverting_negative_price_unit(self):
        """ We can not have negative unit prices, so we try to invert the unit price and quantity.
        """
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 1,
                    'price_unit': 100.0,
                    'tax_ids': [(6, 0, self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 1,
                    'price_unit': -25.0,
                    'tax_ids': [(6, 0, self.tax_21.ids)],
                }
            ],
        )
        self._assert_invoice_attachment(invoice.ubl_cii_xml_id, None, 'from_odoo/bis3_out_invoice_negative_unit_price.xml')

    def test_inverting_negative_price_unit_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_inverting_negative_price_unit()

    def test_export_with_fixed_taxes_case1(self):
        # CASE 1: simple invoice with a recupel tax
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 1,
                    'price_unit': 99,
                    'tax_ids': [(6, 0, [self.recupel.id, self.tax_21.id])],
                }
            ],
        )
        self.assertEqual(invoice.amount_total, 121)
        self._assert_invoice_attachment(invoice.ubl_cii_xml_id, None, 'from_odoo/bis3_ecotaxes_case1.xml')

    def test_export_with_fixed_taxes_case1_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_export_with_fixed_taxes_case1()

    def test_export_with_fixed_taxes_case2(self):
        # CASE 2: Same but with several ecotaxes
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 1,
                    'price_unit': 98,
                    'tax_ids': [(6, 0, [self.recupel.id, self.auvibel.id, self.tax_21.id])],
                }
            ],
        )
        self.assertEqual(invoice.amount_total, 121)
        self._assert_invoice_attachment(invoice.ubl_cii_xml_id, None, 'from_odoo/bis3_ecotaxes_case2.xml')

    def test_export_with_fixed_taxes_case2_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_export_with_fixed_taxes_case2()

    def test_export_with_fixed_taxes_case3(self):
        # CASE 3: same as Case 1 but taxes are Price Included
        self.recupel.price_include_override = 'tax_included'
        self.tax_21.price_include_override = 'tax_included'

        # Price TTC = 121 = (99 + 1 ) * 1.21
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 1,
                    'price_unit': 121,
                    'tax_ids': [(6, 0, [self.recupel.id, self.tax_21.id])],
                }
            ],
        )
        self.assertEqual(invoice.amount_total, 121)
        self._assert_invoice_attachment(invoice.ubl_cii_xml_id, None, 'from_odoo/bis3_ecotaxes_case3.xml')

    def test_export_with_fixed_taxes_case3_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_export_with_fixed_taxes_case3()

    def test_export_with_fixed_taxes_case4(self):
        """ CASE 4: simple invoice with a recupel tax + discount
        1) Subtotal (price after discount, without taxes): 99 * 2 * (1-0.9) = 178.2
        2) Taxes:
            - recupel = 2
            - VAT = (178.2 + 2) * 0.21 = 37.842
        3) Total = 178.2 + 2 + 37.842 = 218.042
        """
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 2,
                    'discount': 10,
                    'price_unit': 99,
                    'tax_ids': [(6, 0, [self.recupel.id, self.tax_21.id])],
                }
            ],
        )
        self.assertEqual(invoice.amount_total, 218.042)
        self._assert_invoice_attachment(invoice.ubl_cii_xml_id, None, 'from_odoo/bis3_ecotaxes_case4.xml')

    def test_export_with_fixed_taxes_case4_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_export_with_fixed_taxes_case4()

    def test_export_payment_terms(self):
        """
        Tests the early payment discount using the example case from the VBO/FEB.

        ------------- + Price + Tax + Cash Discount (2%) + Taxable Amount + VAT --
        Product A     |   200 |  6% |                 -4 |            196 |  11.76
        Product B     |  2400 | 21% |                -48 |           2352 | 493.92
        --------------+-------+-----+--------------------+----------------+-------

        Subtotal (Taxable amount incl. payment discount): 2548
        VAT: 505.68
        Payable amount (excl. payment discount): 3105.68
        Payable amount (incl. payment discount): 3053.68
        """
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            invoice_payment_term_id=self.pay_term.id,
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 1,
                    'price_unit': 200,
                    'tax_ids': [(6, 0, [self.tax_6.id])],
                },
                {
                    'product_id': self.product_b.id,
                    'quantity': 1,
                    'price_unit': 2400,
                    'tax_ids': [(6, 0, [self.tax_21.id])],
                }
            ],
        )
        self._assert_invoice_attachment(invoice.ubl_cii_xml_id, None, 'from_odoo/bis3_pay_term.xml')

    def test_export_payment_terms_fixed_tax(self):
        """
        Tests the early payment discount combined with a fixed tax.

        ------------- + Price + Tax + Cash Discount (2%) + ------- Taxable Amount + VAT ----
        Product A     |    99 | 21% |              -1.98 |  97.02 + 1 (fixed tax) |  20.5842
        --------------+-------+-----+--------------------+------------------------+---------
        NB: The fixed taxes (recupel, auvibel, etc) are excluded from the early payment discount !

        Subtotal (Taxable amount incl. payment discount): 97.02 + 1
        VAT: (97.02 + 1) * 0.21 = 20.58
        Payable amount (excl. payment discount): 99 + 1 + 20.58 = 120.58
        Payable amount (incl. payment discount): 97.02 + 1 + 20.58 = 118.60
        """
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            invoice_payment_term_id=self.pay_term.id,
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 1,
                    'price_unit': 99,
                    'tax_ids': [(6, 0, [self.tax_21.id, self.recupel.id])],
                },
            ],
        )
        self._assert_invoice_attachment(invoice.ubl_cii_xml_id, None, 'from_odoo/bis3_pay_term_ecotax.xml')

    def test_export_payment_terms_with_discount(self):
        self.maxDiff = None
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            currency_id=self.env.company.currency_id.id,
            move_type='out_invoice',
            invoice_payment_term_id=self.pay_term.id,
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 20,
                    'discount': 41,
                    'price_unit': 180.75,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 480,
                    'discount': 41,
                    'price_unit': 25.80,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 3,
                    'discount': 39,
                    'price_unit': 532.5,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 3,
                    'discount': 39,
                    'price_unit': 74.25,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 3,
                    'discount': 39,
                    'price_unit': 369.0,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 5,
                    'discount': 39,
                    'price_unit': 79.5,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 5,
                    'discount': 39,
                    'price_unit': 107.5,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 5,
                    'discount': 39,
                    'price_unit': 160.0,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 5,
                    'discount': 39,
                    'price_unit': 276.75,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 60,
                    'discount': 39,
                    'price_unit': 8.32,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 60,
                    'discount': 39,
                    'price_unit': 8.32,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 12,
                    'discount': 39,
                    'price_unit': 37.65,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 12,
                    'discount': 39,
                    'price_unit': 89.4,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 12,
                    'discount': 39,
                    'price_unit': 149.4,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 6,
                    'discount': 39,
                    'price_unit': 124.8,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 1,
                    'discount': 39,
                    'price_unit': 253.2,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 12,
                    'discount': 39,
                    'price_unit': 48.3,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 20,
                    'discount': 39,
                    'price_unit': 34.8,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 10,
                    'discount': 39,
                    'price_unit': 48.3,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 10,
                    'discount': 39,
                    'price_unit': 72.0,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 5,
                    'discount': 39,
                    'price_unit': 96.0,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 3,
                    'discount': 39,
                    'price_unit': 115.5,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 4,
                    'discount': 39,
                    'price_unit': 50.75,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 30,
                    'discount': 39,
                    'price_unit': 21.37,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 3,
                    'discount': 39,
                    'price_unit': 40.8,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 3,
                    'discount': 39,
                    'price_unit': 40.8,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 3,
                    'discount': 39,
                    'price_unit': 32.9,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': -1,
                    'price_unit': 1337.83,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
            ],
        )
        self._assert_invoice_attachment(invoice.ubl_cii_xml_id, None, 'from_odoo/bis3_pay_term_discount.xml')

    def test_export_with_changed_taxes(self):
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            send=False,
            move_type='out_invoice',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 1,
                    'price_unit': 200,
                    'tax_ids': [Command.set([self.tax_21.id])],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 1,
                    'price_unit': 200,
                    'tax_ids': [Command.set([self.tax_21.id])],
                },
                {
                    'product_id': self.product_b.id,
                    'quantity': 1,
                    'price_unit': 100,
                    'tax_ids': [Command.set([self.tax_12.id])],
                },
                {
                    'product_id': self.product_b.id,
                    'quantity': 1,
                    'price_unit': 100,
                    'tax_ids': [Command.set([self.tax_12.id])],
                },
            ],
        )
        self.assertRecordValues(invoice, [{
            'amount_untaxed': 600.00,
            'amount_tax': 108.00,  # tax_12: 24.00 ; tax_21: 84.00
            'amount_total': 708.00
        }])

        invoice.button_draft()
        tax_lines = invoice.line_ids.filtered(lambda line: line.display_type == 'tax')
        tax_line_21 = next((line for line in tax_lines if line.name == 'tax_21'))
        tax_line_12 = next((line for line in tax_lines if line.name == 'tax_12'))
        invoice.line_ids = [
            Command.update(tax_line_21.id, {'amount_currency': -84.03}), # distribute  3 cents over 2 lines
            Command.update(tax_line_12.id, {'amount_currency': -23.99}), # distribute -1 cent  over 2 lines
        ]

        invoice.action_post()
        invoice._generate_and_send(mail_template_id=self.move_template.id, sending_methods=['manual'])

        self.assertRecordValues(invoice, [{
            'amount_untaxed': 600.00,
            'amount_tax': 108.02,  # tax_12: 23.99 ; tax_21: 84.03
            'amount_total': 708.02
        }])

        self._assert_invoice_attachment(invoice.ubl_cii_xml_id, None, 'from_odoo/bis3_export_with_changed_taxes.xml')

    def test_export_with_changed_taxes_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_export_with_changed_taxes()

    def test_export_rounding_price_amount(self):
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'quantity': 3,
                    'price_unit': 102.15,
                    'tax_ids': [Command.set([self.tax_12.id])],
                },
                {
                    'product_id': self.product_a.id,
                    'quantity': 3,
                    'price_unit': 83.60,
                    'tax_ids': [Command.set([self.tax_21.id])],
                },
            ],
        )
        price_amounts = etree.fromstring(invoice.ubl_cii_xml_id.raw).findall('.//{*}InvoiceLine/{*}Price/{*}PriceAmount')
        self.assertEqual(price_amounts[0].text, '102.15')
        self.assertEqual(price_amounts[1].text, '83.6')

    def test_export_rounding_price_amount_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_export_rounding_price_amount()

    def test_export_tax_exempt(self):
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'price_unit': 990.0,
                    'tax_ids': [(6, 0, self.tax_0.ids)],
                },
            ],
        )
        self._assert_invoice_attachment(invoice.ubl_cii_xml_id, None, 'from_odoo/bis3_out_invoice_tax_exempt.xml')

    def test_export_tax_exempt_new(self):
        self.env['ir.config_parameter'].sudo().set_param('account_edi_ubl_cii.use_new_dict_to_xml_helpers', True)
        self.test_export_tax_exempt()

    ####################################################
    # Test import
    ####################################################

    def test_import_partner_ubl(self):
        invoice = self._generate_move(
            seller=self.partner_1,
            buyer=self.partner_2,
            move_type='out_invoice',
            invoice_line_ids=[{'product_id': self.product_a.id}],
        )
        self._test_import_partner(invoice.ubl_cii_xml_id, self.partner_1, self.partner_2)

    def test_import_in_journal_ubl(self):
        invoice = self._generate_move(
            seller=self.partner_1,
            buyer=self.partner_2,
            move_type='out_invoice',
            invoice_line_ids=[{'product_id': self.product_a.id}],
        )
        self._test_import_in_journal(invoice.ubl_cii_xml_id)

    def test_import_and_create_partner_ubl(self):
        """ Tests whether the partner is created at import if no match is found when decoding the EDI attachment
        """
        partner_vals = {
            'name': "Buyer",
            'email': "buyer@yahoo.com",
            'phone': "1111",
            'vat': "BE980737405",
        }
        # assert there is no matching partner
        partner_match = self.env['res.partner']._retrieve_partner(**partner_vals)
        self.assertFalse(partner_match)

        # Import attachment as an invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.company_data['default_journal_sale'].id,
        })
        self._update_invoice_from_file(
            module_name='l10n_account_edi_ubl_cii_tests',
            subfolder='tests/test_files/from_odoo',
            filename='ubl_test_import_partner.xml',
            invoice=invoice)

        # assert a new partner has been created
        self.assertRecordValues(invoice.partner_id, [partner_vals])

    def test_import_export_invoice_xml(self):
        """
        Test whether the elements only specific to ubl_be are correctly exported
        and imported in the xml file
        """
        acc_bank = self.env['res.partner.bank'].create({
            'acc_number': 'BE15001559627231',
            'partner_id': self.company_data['company'].partner_id.id,
        })

        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            move_type='out_invoice',
            partner_id=self.partner_1.id,
            partner_bank_id=acc_bank.id,
            invoice_date='2017-01-01',
            date='2017-01-01',
            invoice_line_ids=[{
                'product_id': self.product_a.id,
                'product_uom_id': self.env.ref('uom.product_uom_dozen').id,
                'price_unit': 275.0,
                'quantity': 5,
                'discount': 20.0,
                'tax_ids': [(6, 0, self.tax_21.ids)],
            }],
        )

        attachment = invoice.ubl_cii_xml_id
        self.assertTrue(attachment)

        xml_content = base64.b64decode(attachment.with_context(bin_size=False).datas)
        xml_etree = self.get_xml_tree_from_string(xml_content)

        self.assertEqual(
            xml_etree.find('{*}ProfileID').text,
            'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0'
        )
        self.assertEqual(
            xml_etree.find('{*}CustomizationID').text,
            'urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0'
        )
        # Export: in bis3, under Country, the Name element should not appear, but IdentificationCode still should
        self.assertIsNotNone(xml_etree.find('.//{*}Country/{*}IdentificationCode'))
        self.assertIsNone(xml_etree.find('.//{*}Country/{*}Name'))

        # Import:
        created_bill = self.env['account.move'].create({'move_type': 'in_invoice'})
        created_bill.message_post(attachment_ids=[attachment.id])
        self.assertTrue(created_bill)

    def test_import_invoice_xml(self):
        kwargs = {
            'subfolder': 'tests/test_files/from_odoo',
            'invoice_vals': {
                'currency_id': self.other_currency.id,
                'amount_total': 3164.22,
                'amount_tax': 482.22,
                'invoice_lines': [{
                    'price_subtotal': subtotal,
                    'price_unit': price_unit,
                    'discount': discount,
                } for (subtotal, price_unit, discount) in [(1782, 990, 10), (1000, 100, 0), (-100, 100, 0)]]
            },
        }
        self._assert_imported_invoice_from_file(filename='bis3_out_invoice.xml', **kwargs)
        # same as the file above, but the <cac:Price> are missing in the invoice lines
        self._assert_imported_invoice_from_file(filename='bis3_out_invoice_no_prices.xml', **kwargs)

    def test_import_invoice_xml_open_peppol_examples(self):
        # Source: https://github.com/OpenPEPPOL/peppol-bis-invoice-3/tree/master/rules/examples
        subfolder = 'tests/test_files/from_peppol-bis-invoice-3_doc'
        # source: Allowance-example.xml
        self._assert_imported_invoice_from_file(
            subfolder=subfolder,
            filename='bis3_allowance.xml',
            invoice_vals={
                'amount_total': 7125,
                'amount_tax': 1225,
                'invoice_lines': [{'price_subtotal': x} for x in (200, -200, 3999, 1, 1000, 899, 1)],
            },
        )
        # source: base-creditnote-correction.xml
        self._assert_imported_invoice_from_file(
            subfolder=subfolder,
            filename='bis3_credit_note.xml',
            move_type='in_refund',
            invoice_vals={
                'amount_total': 1656.25,
                'amount_tax': 331.25,
                'invoice_lines': [{'price_subtotal': x} for x in (25, 2800, -1500)],
            },
        )
        # source: base-negative-inv-correction.xml
        self._assert_imported_invoice_from_file(
            subfolder=subfolder,
            filename='bis3_invoice_negative_amounts.xml',
            move_type='in_refund',
            invoice_vals={
                'amount_total': 1656.25,
                'amount_tax': 331.25,
                'invoice_lines': [{'price_subtotal': x} for x in (25, 2800, -1500)],
            },
        )
        # source: vat-category-E.xml
        self._assert_imported_invoice_from_file(
            subfolder=subfolder,
            filename='bis3_tax_exempt_gbp.xml',
            invoice_vals={
                'currency_id': self.env.ref('base.GBP').id,
                'amount_total': 1200,
                'amount_tax': 0,
                'invoice_lines': [{'price_subtotal': 1200}],
            },
        )

    def test_import_existing_invoice_flip_move_type(self):
        """ Tests whether the move_type of an existing invoice can be flipped when importing an attachment
        For instance: with an email alias to create account_move, first the move is created (using alias_defaults,
        which contains move_type = 'out_invoice') then the attachment is decoded, if it represents a credit note,
        the move type needs to be changed to 'out_refund'
        """
        invoice = self.env['account.move'].create({'move_type': 'out_invoice'})
        self._update_invoice_from_file(
            'l10n_account_edi_ubl_cii_tests',
            'tests/test_files/from_odoo',
            'bis3_out_refund.xml',
            invoice,
        )
        self.assertRecordValues(invoice, [{'move_type': 'out_refund', 'amount_total': 3164.22}])

    def test_import_fixed_taxes(self):
        """ Tests whether we correctly decode the xml attachments created using fixed taxes.
        See the tests above to create these xml attachments ('test_export_with_fixed_taxes_case_[X]').
        NB: use move_type = 'out_invoice' s.t. we can retrieve the taxes used to create the invoices.
        """
        subfolder = "tests/test_files/from_odoo"
        # The tax 21% from l10n_be is retrieved since it's a duplicate of self.tax_21
        tax_21 = self.env.ref(f'account.{self.env.company.id}_attn_VAT-OUT-21-L')
        self._assert_imported_invoice_from_file(
            subfolder=subfolder,
            filename='bis3_ecotaxes_case1.xml',
            move_type='out_invoice',
            invoice_vals={
                'currency_id': self.other_currency.id,
                'amount_total': 121,
                'amount_tax': 22,
                'invoice_lines': [{
                    'price_unit': 99,
                    'discount': 0,
                    'price_subtotal': 99,
                    'tax_ids': (tax_21 + self.recupel).ids,
                }]
            }
        )
        self._assert_imported_invoice_from_file(
            subfolder=subfolder,
            filename='bis3_ecotaxes_case2.xml',
            move_type='out_invoice',
            invoice_vals={
                'currency_id': self.other_currency.id,
                'amount_total': 121,
                'amount_tax': 23,
                'invoice_lines': [{
                    'price_unit': 98,
                    'discount': 0,
                    'price_subtotal': 98,
                    'tax_ids': (tax_21 + self.recupel + self.auvibel).ids,
                }]
            },
        )
        self._assert_imported_invoice_from_file(
            subfolder=subfolder,
            filename='bis3_ecotaxes_case3.xml',
            move_type='out_invoice',
            invoice_vals={
                'currency_id': self.other_currency.id,
                'amount_total': 121,
                'amount_tax': 22,
                'invoice_lines': [{
                    'price_unit': 99,
                    'discount': 0,
                    'price_subtotal': 99,
                    'tax_ids': (tax_21 + self.recupel).ids,
                }]
            },
        )
        self._assert_imported_invoice_from_file(
            subfolder=subfolder,
            filename='bis3_ecotaxes_case4.xml',
            move_type='out_invoice',
            invoice_vals={
                'currency_id': self.other_currency.id,
                'amount_total': 218.04,
                'amount_tax': 39.84,
                'invoice_lines': [{
                    'price_unit': 99,
                    'quantity': 2,
                    'discount': 10,
                    'price_subtotal': 178.2,
                    'tax_ids': (tax_21 + self.recupel).ids,
                }]
            },
        )

    def test_import_payment_terms(self):
        # The tax 21% from l10n_be is retrieved since it's a duplicate of self.tax_21
        tax_21 = self.env.ref(f'account.{self.env.company.id}_attn_VAT-OUT-21-L')
        self._assert_imported_invoice_from_file(
            subfolder='tests/test_files/from_odoo',
            filename='bis3_pay_term.xml',
            move_type='out_invoice',
            invoice_vals={
                'currency_id': self.other_currency.id,
                'amount_total': 3105.68,
                'amount_tax': 505.68,
                'invoice_lines': [
                    {
                        'price_unit': price_unit,
                        'price_subtotal': price_unit,
                        'discount': 0,
                        'tax_ids': tax.ids,
                    } for (price_unit, tax) in [
                        (-4, self.tax_6),
                        (-48, tax_21),
                        (52, self.tax_0),
                        (200, self.tax_6),
                        (2400, tax_21),
                    ]
                ]
            },
        )

    ####################################################
    # Test Send & print
    ####################################################

    def test_send_and_print(self):
        invoice = self._generate_move(
            self.partner_1,
            self.partner_2,
            send=False,
            move_type='out_invoice',
            invoice_line_ids=[
                {
                    'product_id': self.product_a.id,
                    'tax_ids': [Command.set(self.tax_21.ids)],
                },
            ],
        )
        self.assertEqual(self.partner_2.invoice_edi_format, 'ubl_bis3')
        wizard = self.create_send_and_print(invoice, sending_methods=['manual'])
        self.assertRecordValues(wizard, [{
            'sending_methods': ['manual'],
            'invoice_edi_format': 'ubl_bis3',
            'extra_edi_checkboxes': False,
        }])
        self._assert_mail_attachments_widget(wizard, [
            {
                'mimetype': 'application/pdf',
                'name': 'INV_2017_00001.pdf',
                'placeholder': True,
            },
            {
                'mimetype': 'application/xml',
                'name': 'INV_2017_00001_ubl_bis3.xml',
                'placeholder': True,
            },
        ])
        self.assertFalse(invoice.invoice_pdf_report_id)
        self.assertFalse(invoice.ubl_cii_xml_id)

        # Send.
        wizard.action_send_and_print()
        self.assertTrue(invoice.invoice_pdf_report_id)
        self.assertTrue(invoice.ubl_cii_xml_id)
        invoice_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', invoice._name),
            ('res_id', '=', invoice.id),
            ('res_field', 'in', ('invoice_pdf_report_file', 'ubl_cii_xml_file')),
        ])
        self.assertEqual(len(invoice_attachments), 2)

        # Send again.
        wizard = self.create_send_and_print(invoice, sending_methods=['manual'])
        self.assertRecordValues(wizard, [{
            'sending_methods': ['manual'],
            'invoice_edi_format': 'ubl_bis3',
        }])
        self._assert_mail_attachments_widget(wizard, [
            {
                'id': invoice.invoice_pdf_report_id.id,
                'mimetype': 'application/pdf',
                'name': 'INV_2019_00001.pdf',
            },
            {
                'id': invoice.ubl_cii_xml_id.id,
                'mimetype': 'application/xml',
                'name': 'INV_2019_00001_ubl_bis3.xml',
            },
        ])
        wizard.action_send_and_print()
        self.assertTrue(invoice.invoice_pdf_report_id)
        self.assertTrue(invoice.ubl_cii_xml_id)
        invoice_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', invoice._name),
            ('res_id', '=', invoice.id),
            ('res_field', 'in', ('invoice_pdf_report_file', 'ubl_cii_xml_file')),
        ])
        self.assertEqual(len(invoice_attachments), 2)

    def test_import_quantity_and_or_unit_price_zero(self):
        """ Tests some special handling cases in which the quantity or unit_price are missing.
        """
        subfolder = "tests/test_files/from_odoo"
        # The tax 21% from l10n_be is retrieved since it's a duplicate of self.tax_21
        tax_21 = self.env.ref(f'account.{self.env.company.id}_attn_VAT-OUT-21-L')
        self._assert_imported_invoice_from_file(
            subfolder=subfolder,
            filename='bis3_out_invoice_quantity_and_or_unit_price_zero.xml',
            move_type='out_invoice',
            invoice_vals={
                'amount_total': 3630,
                'amount_tax': 630,
                'currency_id': self.other_currency.id,
                'invoice_lines': [
                    {
                        'price_unit': price_unit,
                        'quantity': quantity,
                        'discount': 0,
                        'tax_ids': tax_21.ids,
                        'price_subtotal': 1000,
                    } for price_unit, quantity in [(1000, 1), (100, 10), (10, 100)]
                ]
            }
        )
