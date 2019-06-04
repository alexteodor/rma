# -*- coding: utf-8 -*-
# © 2015 Eezee-It, MONK Software
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, exceptions, api, _


class ClaimMakePicking(models.TransientModel):
    _inherit = 'claim_make_picking.wizard'

    @api.returns('res.partner')
    def _get_common_partner_from_line(self, lines):
        """ If all the lines have the same warranty return partner return that,
        else return an empty recordset
        """
        partners = lines.mapped('warranty_return_partner')
        partners = list(set(partners))
        return partners[0] if len(partners) == 1 else self.env['res.partner']

    @api.returns('res.partner')
    def _get_partner(self, claim):
        partner = super(ClaimMakePicking, self)._get_partner(claim)
        claim_lines = self.claim_line_ids

        # In case of product return, we don't allow one picking for various
        # product if location are different
        # or if partner address is different
        if self.env.context.get('product_return'):
            common_dest_location = self._get_common_dest_location_from_line(
                claim_lines)
            if not common_dest_location:
                raise exceptions.UserError(
                    _('A product return cannot be created for various '
                      'destination locations, please choose line with a '
                      'same destination location.')
                )

            claim_lines.auto_set_warranty()
            common_dest_partner = self._get_common_partner_from_line(
                claim_lines)
            if not common_dest_partner:
                raise exceptions.UserError(
                    _('A product return cannot be created for various '
                      'destination addresses, please choose line with a '
                      'same address.')
                )
            partner = common_dest_partner
        return partner
