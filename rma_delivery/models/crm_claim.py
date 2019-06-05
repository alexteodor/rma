# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    def _get_picking_domain(self):
        domain = super(CrmClaim, self)._get_picking_domain()
        return ['|', ('group_id.claim_id', '=', self.id)] + domain
