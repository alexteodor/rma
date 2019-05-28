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

        # Create the claim with a claim line
        self.claim_id = claim.create(
            {
                'name': 'TEST CLAIM',
                'code': '/',
                'claim_type': self.env.ref('crm_claim_type.'
                                           'crm_claim_type_customer').id,
                'delivery_address_id': self.partner_id.id,
                'partner_id': self.env.ref('base.res_partner_2').id,
                'claim_line_ids': [(0, 0, {
                    'product_id': self.product_id.id,
                    'product_returned_quantity': 1})]
            })
        self.warehouse_id = self.claim_id.warehouse_id

    def test_00_new_product_return(self):
        """Test wizard creates a correct picking for product return

        """
        wizard = self.wizard_make_picking.with_context({
            'active_id': self.claim_id.id,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': 'in',
            'product_return': True,
        }).create({})
        wizard.action_create_picking()

        self.assertEquals(len(self.claim_id.picking_ids), 1,
                          "Incorrect number of pickings created")
        picking = self.claim_id.picking_ids[0]
        self.assertEquals(picking.location_id, self.customer_location_id,
                          "Incorrect source location")
        self.assertEquals(picking.location_dest_id,
                          self.warehouse_id.lot_stock_id,
                          "Incorrect destination location")

    def test_02_new_product_return(self):
        """Test wizard creates a correct picking for product return
        """
        wizard = self.wizard_make_picking.with_context({
            'active_id': self.claim_id.id,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': 'in',
        }).create({})
        wizard.action_create_picking()

        self.assertEquals(len(self.claim_id.picking_ids), 1,
                          "Incorrect number of pickings created")
        picking = self.claim_id.picking_ids[0]

        self.assertEquals(picking.location_id, self.customer_location_id,
                          "Incorrect source location")
        self.assertEquals(picking.location_dest_id,
                          self.warehouse_id.lot_stock_id,
                          "Incorrect destination location")

    def test_04_display_name(self):
        """
        It tests that display_name for each line has a message for it
        """
        claim_line_ids = self.env['crm.claim'].browse(
            self.ref('crm_claim.crm_claim_6')
        )[0].claim_line_ids

        all_values = sum([bool(line_id.display_name)
                          for line_id in claim_line_ids])
        self.assertEquals(len(claim_line_ids), all_values)
