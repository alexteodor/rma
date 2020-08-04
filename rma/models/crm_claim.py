# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models


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

    def _get_picking_domain(self):
        self.ensure_one()
        return [('claim_id', '=', self.id)]

    def _get_picking_ids(self):
        """ Search all stock_picking associated with this claim.

        Either directly with claim_id in stock_picking or through a
        procurement_group.
        """
        picking_model = self.env['stock.picking']
        for claim in self:
            domain = claim._get_picking_domain()
            claim.picking_ids = picking_model.search(domain)

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

    picking_ids = fields.One2many('stock.picking',
                                  compute=_get_picking_ids,
                                  string='RMA',
                                  copy=False)
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
    has_product = fields.Boolean(
        related='categ_id.has_product',
        readonly=True)
    origin_type = fields.Selection(
        related='claim_type.origin_type',
        readonly=True)
    rma_number = fields.Char(size=128, help='RMA Number provided by supplier')

    @api.model
    def _get_claim_type_default(self):
        return self.env.ref('crm_claim_type.crm_claim_type_customer')

    claim_type = \
        fields.Many2one(default=_get_claim_type_default,
                        help="Claim classification",
                        required=True)

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
        # Get sequence with sudo because user may not have right on it
        sequence = self.env['ir.sequence'].sudo()
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
