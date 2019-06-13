# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    sale_id = fields.Many2one('sale.order', string='Sale order',
                              help='Related original Customer sale order')

    @api.onchange('sale_id')
    def _onchange_sale(self):
        claim_with_ctx = self.with_context(
            create_lines=True, claim_from='sale'
        )
        claim_with_ctx.sale_id = self.sale_id
        claim_with_ctx._onchange_warehouse_type_date()
        values = claim_with_ctx._convert_to_write(claim_with_ctx._cache)
        self.update(values)
        if self.sale_id:
            self.delivery_address_id = self.sale_id.partner_shipping_id.id

    @api.model
    def _create_claim_lines_from_sale(self, warehouse):
        lines = self.sale_id.order_line.filtered(
            lambda line: line.product_id.type in ('consu', 'product')
        )
        claim_lines = []
        for line in lines:
            line_vals = self._prepare_claim_line_from_sale(line, warehouse)
            claim_lines.append((0, 0, line_vals))

        return claim_lines

    @api.model
    def _prepare_claim_line_from_sale(self, line, warehouse):
        self.ensure_one()
        claim_line = self.env['claim.line']
        location_dest = claim_line.get_destination_location(
            warehouse, product=line.product_id)
        return {
            'name': line.name,
            'claim_origin': "none",
            'sale_line_id': line.id,
            'product_id': line.product_id.id,
            'product_returned_quantity': line.product_uom_qty,
            'unit_sale_price': line.price_unit,
            'location_dest_id': location_dest.id,
            'state': 'draft',
        }
