# -*- coding: utf-8 -*-
# © 2015 Vauxoo
# © 2014 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class TestRefundCreation(TransactionCase):


    def setUp(self):
        super(TestRefundCreation, self).setUp()

        self.wizard_make_picking = self.env['claim_make_picking.wizard']
        self.stockpicking = self.env['stock.picking']
        claim = self.env['crm.claim']

        self.product_id = self.env.ref('product.product_product_4')
        self.partner_id = self.env.ref('base.res_partner_12')

        self.customer_location_id = self.env.ref(
            'stock.stock_location_customers'
        )

        uom_unit = self.env.ref('product.product_uom_unit')
        self.sale_order = self.env['sale.order'].create({
            'state': 'done',
            'partner_id':  self.env.ref('base.res_partner_2').id,
            'partner_invoice_id':  self.env.ref('base.res_partner_2').id,
            'partner_shipping_id':  self.env.ref('base.res_partner_2').id,
            'pricelist_id':  self.env.ref('product.list0').id,
            'order_line': [
                (0, False, {
                    'name': product.name,
                    'product_id': product.id,
                    'product_uom_qty': qty,
                    'qty_delivered': qty,
                    'product_uom': uom_unit.id,
                    'price_unit': product.list_price

                }) for product, qty in [
                    (self.env.ref('product.product_product_24'), 5),
                    (self.env.ref('product.product_product_25'), 3),
                    (self.env.ref('product.product_product_27'), 2),
                ]
            ]
        })
        invoice_id = self.sale_order.action_invoice_create()[0]
        self.invoice = self.env['account.invoice'].browse(invoice_id)

        # Create the claim with a claim line
        self.claim_id = claim.create(
            {
                'name': 'TEST CLAIM',
                'code': '/',
                'claim_type': self.env.ref('crm_claim_type.'
                                           'crm_claim_type_customer').id,
                'delivery_address_id': self.partner_id.id,
                'partner_id': self.env.ref('base.res_partner_2').id,
                'invoice_id': invoice_id,
            })
        self.claim_id.with_context({'create_lines': True}).\
            _onchange_invoice_warehouse_type_date()
        self.warehouse_id = self.claim_id.warehouse_id


    def test_01_invoice_refund(self):
        claim_id = self.env['crm.claim'].browse(
            self.ref('crm_claim.crm_claim_6')
        )
        self.invoice.action_invoice_open()
        # self.invoice.action_invoice_paid()
        claim_id.write({
            'invoice_id': self.invoice.id
        })
        claim_id.with_context({'create_lines': True}).\
            _onchange_invoice_warehouse_type_date()

        invoice_refund_wizard_id = self.env['account.invoice.refund'].\
            with_context({
                # Test that invoice_ids is correctly passed as active_ids
                'invoice_ids': [claim_id.invoice_id.id],
                'claim_line_ids':
                [[4, cl.id, False] for cl in claim_id.claim_line_ids],
                'description': "Testing Invoice Refund for Claim",
            }).create({})

        self.assertEqual(
            "Testing Invoice Refund for Claim",
            invoice_refund_wizard_id.description
        )

        res = invoice_refund_wizard_id.invoice_refund()

        self.assertTrue(res)
        self.assertEquals(res['res_model'], 'account.invoice')
        self.assertEqual(2, len(res['domain']))

        # Second leaf is ('id', 'in', [created_invoice_id])
        self.assertEqual(('id', 'in'), res['domain'][1][:2])
        self.assertEqual(1, len(res['domain'][1][2]))

        refund_invoice = self.env['account.invoice'].browse(
            res['domain'][1][2]
        )
        self.assertEqual('out_refund', refund_invoice.type)
