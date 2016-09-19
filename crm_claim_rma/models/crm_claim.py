# -*- coding: utf-8 -*-
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, exceptions, fields, models

from .invoice_no_date import InvoiceNoDate
from .product_no_supplier import ProductNoSupplier
from collections import defaultdict


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    def _get_default_warehouse(self):
        company_id = self.env.user.company_id.id
        wh_obj = self.env['stock.warehouse']
        wh = wh_obj.search([('company_id', '=', company_id)], limit=1)
        if not wh:
            raise exceptions.UserError(
                _('There is no warehouse for the current user\'s company.')
            )
        return wh

    def _get_picking_ids(self):
        """ Search all stock_picking associated with this claim.

        Either directly with claim_id in stock_picking or through a
        procurement_group.
        """
        picking_model = self.env['stock.picking']
        for claim in self:
            claim.picking_ids = picking_model.search([
                '|',
                ('claim_id', '=', claim.id),
                ('group_id.claim_id', '=', claim.id)
            ])

    @api.multi
    def name_get(self):
        res = []
        for claim in self:
            code = claim.code and str(claim.code) or ''
            res.append((claim.id, '[' + code + '] ' + claim.name))
        return res

    company_id = fields.Many2one(change_default=True,
                                 default=lambda self:
                                 self.env['res.company']._company_default_get(
                                     'crm.claim'))

    claim_line_ids = fields.One2many('claim.line', 'claim_id',
                                     string='Return lines')
    planned_revenue = fields.Float('Expected revenue')
    planned_cost = fields.Float('Expected cost')
    real_revenue = fields.Float()
    real_cost = fields.Float()
    invoice_ids = fields.One2many('account.invoice', 'claim_id', 'Refunds',
                                  copy=False)
    picking_ids = fields.One2many('stock.picking',
                                  compute=_get_picking_ids,
                                  string='RMA',
                                  copy=False)
    invoice_id = fields.Many2one('account.invoice', string='Invoice',
                                 help='Related original Cusotmer invoice')
    pick = fields.Boolean('Pick the product in the store')
    delivery_address_id = fields.Many2one('res.partner',
                                          string='Partner delivery address',
                                          help="This address will be used to "
                                          "deliver repaired or replacement "
                                          "products.")
    sequence = fields.Integer(default=lambda *args: 1)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   required=True,
                                   default=_get_default_warehouse)
    rma_number = fields.Char(size=128, help='RMA Number provided by supplier')
    order_id = fields.Many2one(
        'sale.order',
        string='Sale order',
        help="Related original customer sale order")

    @api.model
    def _get_claim_type_default(self):
        return self.env.ref('crm_claim_type.crm_claim_type_customer')

    claim_type = \
        fields.Many2one(default=_get_claim_type_default,
                        help="Claim classification",
                        required=True)

    @api.model
    def _get_claim_line_vals(self, line, location_dest):
        return {
            'name': line.name,
            'claim_origin': 'none',
            'product_id': line.product_id.id,
            'unit_sale_price': line.price_unit,
            'location_dest_id': location_dest.id,
            'state': 'draft',
            'order_line_id': line.id,
            'product_returned_quantity': line.product_uom_qty,
        }

    @api.onchange('order_id')
    def _onchange_sale_order_id(self):
        claim_lines = []
        if not self.warehouse_id:
            self.warehouse_id = self._get_default_warehouse()
        warehouse = self.warehouse_id
        company = self.company_id
        claim_line_obj = self.env['claim.line']
        for line in self.order_id.order_line:
            location_dest = claim_line_obj.get_destination_location(
                line.product_id, warehouse)
            claim_line = self._get_claim_line_vals(line, location_dest)
            claim_lines.append((0, 0, claim_line))
        value = self._convert_to_cache(
            {'claim_line_ids': claim_lines}, validate=False)
        self.update(value)
        
        if self.order_id:
            self.delivery_address_id = self.order_id.partner_shipping_id
        if not self.partner_id:
            self.partner_id = self.order_id.partner_id.id

    def onchange_partner_id(self, cr, uid, ids, partner_id,
                                   email=False, context=None):
        res = super(CrmClaim, self).onchange_partner_id(cr, uid, ids,
                                                         partner_id,
                                                         email=email,
                                                         context=context)
        res['domain'] = {}
        if not partner_id:
            res['domain']['order_id'] = []
            return res
        res['domain']['order_id'] = [('partner_id', '=', partner_id)]
        return res


    @api.model
    def message_get_reply_to(self, res_ids, default=None):
        """ Override to get the reply_to of the parent project.
        """
        results = dict.fromkeys(res_ids, default or False)
        if res_ids:
            claims = self.browse(res_ids)
            results.update({
                claim.id: self.env['crm.team'].message_get_reply_to(
                    [claim.team_id], default
                )[claim.team_id] for claim in claims if claim.team_id
            })

        return results

    @api.multi
    def message_get_suggested_recipients(self):
        recipients = super(CrmClaim, self).message_get_suggested_recipients()
        try:
            for claim in self:
                if claim.partner_id:
                    claim._message_add_suggested_recipient(
                        recipients,
                        partner=claim.partner_id,
                        reason=_('Customer')
                    )
                elif claim.email_from:
                    claim._message_add_suggested_recipient(
                        recipients,
                        email=claim.email_from,
                        reason=_('Customer Email')
                    )
        except exceptions.AccessError:
            # no read access rights -> just ignore suggested recipients
            # because this imply modifying followers
            pass
        return recipients

    def _get_sequence_number(self, code_id):
        claim_type_code = self.env['crm.claim.type'].\
            browse(code_id).ir_sequence_id.code
        sequence = self.env['ir.sequence']

        return claim_type_code and sequence.next_by_code(
            claim_type_code
        ) or '/'

    @api.model
    def create(self, values):
        values = values or {}
        if 'code' not in values or not values.get('code') \
                or values.get('code') == '/':

            claim_type = values.get('claim_type')
            if not claim_type:
                claim_type = self._get_claim_type_default().id

            values['code'] = self._get_sequence_number(claim_type)

        return super(CrmClaim, self).create(values)

    @api.multi
    def copy(self, default=None):
        self.ensure_one()

        default = default or {}
        std_default = {
            'code': '/'
        }

        std_default.update(default)
        return super(CrmClaim, self).copy(default=std_default)
