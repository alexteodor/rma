# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import SavepointCase


class TestRmaGroup(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner1 = cls.env.ref("base.res_partner_3")
        cls.partner2 = cls.env.ref("base.res_partner_2")
        cls.product = cls.env.ref("product.consu_delivery_01")
        cls.location = cls.env.ref("stock.warehouse0").rma_loc_id

    def test_rma_grouping(self):
        rma1 = self.env["rma"].create(
            {
                "partner_id": self.partner1.id,
                "partner_invoice_id": self.partner1.id,
            }
        )
        group = rma1.procurement_group_id
        self.assertTrue(group)
        self.assertEqual(rma1.name, "%s-1" % group.name)
        rma2 = self.env["rma"].create(
            {
                "partner_id": self.partner1.id,
                "partner_invoice_id": self.partner1.id,
            }
        )
        self.assertEqual(rma2.procurement_group_id, group)
        self.assertEqual(rma2.name, "%s-2" % group.name)

        rma3 = self.env["rma"].create(
            {
                "partner_id": self.partner2.id,
                "partner_invoice_id": self.partner2.id,
                "product_id": self.product.id,
                "location_id": self.location.id,
            }
        )

        self.assertNotEqual(rma3.procurement_group_id, group)
        self.assertEqual(rma3.name, "%s-1" % rma3.procurement_group_id.name)

        rma3.action_confirm()
        rma4 = self.env["rma"].create(
            {
                "partner_id": self.partner2.id,
                "partner_invoice_id": self.partner2.id,
                "product_id": self.product.id,
                "location_id": self.location.id,
            }
        )
        # not grouped because rma3 is not at draft state anymore
        self.assertNotEqual(rma3.procurement_group_id, rma4.procurement_group_id)
