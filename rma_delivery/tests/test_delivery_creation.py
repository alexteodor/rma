# -*- coding: utf-8 -*-
# © 2015 Vauxoo
# © 2014 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestPickingCreation(common.TransactionCase):

    """ Test the correct pickings are created by the wizard. """

    def setUp(self):
        super(TestPickingCreation, self).setUp()

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

    def test_01_new_delivery(self):
        """Test wizard creates and runs a procurement for a new delivery
        """

        group_model = self.env['procurement.group']

        wizardchangeproductqty = self.env['stock.change.product.qty']
        wizard_chg_qty = wizardchangeproductqty.with_context({
            'active_id': self.product_id.id,
        }).create({
            'product_id': self.product_id.id,
            'new_quantity': 12,
        })

        wizard_chg_qty.change_product_qty()

        self.assertEqual(0, group_model.search_count([
            ('claim_id', '=', self.claim_id.id)
        ]))
        wizard = self.wizard_make_picking.with_context({
            'active_id': self.claim_id.id,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': 'out',
        }).create({})
        wizard.action_create_picking()

        procurement_group = group_model.search([
            ('claim_id', '=', self.claim_id.id)
        ])
        self.assertEqual(1, len(procurement_group))

        self.assertEquals(len(self.claim_id.picking_ids), 1,
                          "Incorrect number of pickings created")

        # Should have 1 procurement by product:
        # One on Customer location and one on output
        self.assertEqual(3, len(procurement_group.procurement_ids))

        # And 2 pickings
        self.assertEqual(1, len(self.claim_id.picking_ids))

        self.assertEquals(self.warehouse_id.lot_stock_id,
                          self.claim_id.picking_ids.location_id,
                          "Incorrect source location")
        self.assertEquals(self.customer_location_id,
                          self.claim_id.picking_ids.location_dest_id,
                          "Incorrect destination location")
