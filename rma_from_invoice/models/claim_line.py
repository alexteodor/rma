# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models


class ClaimLine(models.Model):
    _inherit = "claim.line"

    invoice_line_id = fields.Many2one('account.invoice.line',
                                      string='Invoice Line',
                                      copy=False,
                                      help='The invoice line related'
                                      ' to the returned product')
    refund_line_id = fields.Many2one('account.invoice.line',
                                     string='Refund Line',
                                     copy=False,
                                     help='The refund line related'
                                     ' to the returned product')
    invoice_date = fields.Datetime(related='invoice_line_id.invoice_id.'
                                   'create_date',
                                   help="Date of Claim Invoice")
    invoice_id = fields.Many2one(related='invoice_line_id.invoice_id',
                                 store=True,
                                 readonly=True)
