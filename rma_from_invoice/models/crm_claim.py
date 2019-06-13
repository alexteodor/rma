# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    invoice_ids = fields.One2many('account.invoice', 'claim_id', 'Refunds',
                                  copy=False)
    invoice_id = fields.Many2one('account.invoice', string='Invoice',
                                 help='Related original Customer invoice')

    @api.onchange('invoice_id')
    def _onchange_invoice(self):
        # Since no parameters or context can be passed from the view,
        # this method exists only to call the onchange below with
        # a specific context (to recreate claim lines).
        # This does require to re-assign self.invoice_id in the new object
        claim_with_ctx = self.with_context(
            create_lines=True, claim_from='invoice'
        )
        claim_with_ctx.invoice_id = self.invoice_id
        claim_with_ctx._onchange_warehouse_type_date()
        values = claim_with_ctx._convert_to_write(claim_with_ctx._cache)
        self.update(values)
        if self.invoice_id:
            self.delivery_address_id = self.invoice_id.partner_id.id

    @api.onchange('warehouse_id', 'claim_type', 'date')
    def _onchange_warehouse_type_date(self):
        context = self.env.context
        if not self.warehouse_id:
            self.warehouse_id = self._get_default_warehouse()

        warehouse = self.warehouse_id
        create_lines = context.get('create_lines')

        if create_lines:
            claim_lines = getattr(self, '_create_claim_lines_from_%s' % context.get('claim_from'))(warehouse)
            value = self._convert_to_cache(
                {'claim_line_ids': claim_lines}, validate=False)
            self.update(value)

    @api.model
    def _create_claim_lines_from_invoice(self, warehouse):
        lines = self.invoice_id.invoice_line_ids.filtered(
            lambda line: line.product_id.type in ('consu', 'product')
        )
        claim_lines = []
        for invoice_line in lines:
            line_vals = self._prepare_claim_line_from_invoice(invoice_line, warehouse)
            claim_lines.append((0, 0, line_vals))
        return claim_lines

    @api.model
    def _prepare_claim_line_from_invoice(self, invoice_line, warehouse):
        self.ensure_one()
        claim_line = self.env['claim.line']
        location_dest = claim_line.get_destination_location(
            warehouse, product=invoice_line.product_id)
        return {
            'name': invoice_line.name,
            'claim_origin': "none",
            'invoice_line_id': invoice_line.id,
            'product_id': invoice_line.product_id.id,
            'product_returned_quantity': invoice_line.quantity,
            'unit_sale_price': invoice_line.price_unit,
            'location_dest_id': location_dest.id,
            'state': 'draft',
        }
