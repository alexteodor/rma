# -*- coding: utf-8 -*-
# © 2015 Eezee-It, MONK Software
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from odoo import models, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT


class ClaimMakePicking(models.TransientModel):
    _inherit = 'claim_make_picking.wizard'

    def _get_claim_line_dest_location(self):
        """Return the location_id to use as destination.

        If it's an outoing shipment: take the customer stock property
        lines, or if different, return None.
        """
        picking_type = self.env.context.get('picking_type')
        partner_id = self.env.context.get('partner_id')

        if picking_type == 'out' and partner_id:
            return self.env['res.partner'].browse(
                partner_id).property_stock_customer
        return super(ClaimMakePicking, self)._get_claim_line_dest_location()

    def _create_procurement(self, claim):
        """ Create a procurement order for each line in this claim and put
        all procurements in a procurement group linked to this claim.

        :type claim: crm_claim
        """
        group = self.env['procurement.group'].create({
            'name': claim.code,
            'claim_id': claim.id,
            'move_type': 'direct',
            'partner_id': claim.delivery_address_id.id,
        })

        for line in self.claim_line_ids:
            procurement = self.env['procurement.order'].create({
                'name': line.product_id.name,
                'group_id': group.id,
                'origin': claim.code,
                'warehouse_id': self.delivery_warehouse_id.id,
                'date_planned': time.strftime(DT_FORMAT),
                'product_id': line.product_id.id,
                'product_qty': line.product_returned_quantity,
                'product_uom': line.product_id.product_tmpl_id.uom_id.id,
                'location_id': self.claim_line_dest_location_id.id,
                'company_id': claim.company_id.id,
            })
            procurement.run()
            line.move_out_id = procurement.move_ids[0].id

    @api.multi
    def action_create_picking(self):
        claim = self.env['crm.claim'].browse(self.env.context['active_id'])
        picking_type = self.env.context.get('picking_type')
        if picking_type == 'out':
            return self._create_procurement(claim)
        return super(ClaimMakePicking, self).action_create_picking()
