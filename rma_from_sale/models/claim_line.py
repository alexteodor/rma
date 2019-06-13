# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models


class ClaimLine(models.Model):
    _inherit = "claim.line"

    sale_line_id = fields.Many2one('sale.order.line',
                                   string='Sale Order Line',
                                   copy=False,
                                   help='The sale order line related'
                                        ' to the returned product')
