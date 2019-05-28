# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import calendar
import math
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, exceptions, fields, models


class ClaimLine(models.Model):

    _name = "claim.line"

    _inherit = 'mail.thread'
    _description = "List of product to return"

    SUBJECT_LIST = [('none', 'Not specified'),
                    ('legal', 'Legal retractation'),
                    ('cancellation', 'Order cancellation'),
                    ('damaged', 'Damaged delivered product'),
                    ('error', 'Shipping error'),
                    ('exchange', 'Exchange request'),
                    ('lost', 'Lost during transport'),
                    ('perfect_conditions',
                     'Perfect Conditions'),
                    ('imperfection', 'Imperfection'),
                    ('physical_damage_client',
                     'Physical Damage by Client'),
                    ('physical_damage_company',
                     'Physical Damage by Company'),
                    ('other', 'Other')]

    def _default_location_dest_id(self):
        company_id = self.env.user.company_id.id
        wh_obj = self.env['stock.warehouse']
        wh = wh_obj.search([('company_id', '=', company_id)], limit=1)
        if not wh:
            raise exceptions.UserError(
                _('There is no warehouse for the current user\'s company.')
            )
        return wh.lot_stock_id

    number = fields.Char(
        readonly=True,
        default='/',
        help='Claim Line Identification Number')
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=False,
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'claim.line'))
    date = fields.Date('Claim Line Date',
                       index=True,
                       default=fields.date.today())
    name = fields.Char('Description', default='none', required=False,
                       help="More precise description of the problem")
    priority = fields.Selection([('0_not_define', 'Not Define'),
                                 ('1_normal', 'Normal'),
                                 ('2_high', 'High'),
                                 ('3_very_high', 'Very High')],
                                'Priority', default='0_not_define',
                                help="Priority attention of claim line")
    claim_diagnosis = fields.\
        Selection([('damaged', 'Product Damaged'),
                   ('repaired', 'Product Repaired'),
                   ('good', 'Product in good condition'),
                   ('hidden', 'Product with hidden physical damage'),
                   ],
                  help="To describe the line product diagnosis")
    claim_origin = fields.Selection(SUBJECT_LIST, 'Claim Subject',
                                    required=False, help="To describe the "
                                    "line product problem")
    product_id = fields.Many2one('product.product', string='Product',
                                 help="Returned product")
    product_returned_quantity = \
        fields.Float('Quantity', digits=(12, 2),
                     help="Quantity of product returned")
    unit_sale_price = fields.Float(digits=(12, 2),
                                   help="Unit sale price of the product. "
                                   "Auto filled if retrun done "
                                   "by invoice selection. Be careful "
                                   "and check the automatic "
                                   "value as don't take into account "
                                   "previous refunds, invoice "
                                   "discount, can be for 0 if product "
                                   "for free,...")
    return_value = fields.Float(compute='_compute_line_total_amount',
                                string='Total return',
                                help="Quantity returned * Unit sold price",)
    prodlot_id = fields.Many2one('stock.production.lot',
                                 string='Serial/Lot number',
                                 help="The serial/lot of "
                                      "the returned product")
    display_name = fields.Char('Name', compute='_compute_display_name')
    claim_id = fields.Many2one('crm.claim', string='Related claim',
                               ondelete='cascade',
                               help="To link to the case.claim object")
    state = fields.Selection([('draft', 'Draft'),
                              ('refused', 'Refused'),
                              ('confirmed', 'Confirmed, waiting for product'),
                              ('in_to_control', 'Received, to control'),
                              ('in_to_treate', 'Controlled, to treate'),
                              ('treated', 'Treated')],
                             string='State', default='draft')
    substate_id = fields.Many2one('substate.substate', string='Sub state',
                                  help="Select a sub state to precise the "
                                       "standard state. Example 1: "
                                       "state = refused; substate could "
                                       "be warranty over, not in "
                                       "warranty, no problem,... . "
                                       "Example 2: state = to treate; "
                                       "substate could be to refund, to "
                                       "exchange, to repair,...")
    last_state_change = fields.Date(string='Last change', help="To set the"
                                    "last state / substate change")
    move_in_id = fields.Many2one('stock.move',
                                 string='Move Line from picking in',
                                 copy=False,
                                 help='The move line related'
                                 ' to the returned product')
    location_dest_id = fields.Many2one('stock.location',
                                       string='Return Stock Location',
                                       default=_default_location_dest_id,
                                       help='The return stock location'
                                       ' of the returned product')
    claim_type = fields.Many2one(related='claim_id.claim_type',
                                 string="Claim Line Type",
                                 store=True,
                                 readonly=True,
                                 help="Claim classification")

    # Method to calculate total amount of the line : qty*UP
    @api.multi
    def _compute_line_total_amount(self):
        for line in self:
            line.return_value = (line.unit_sale_price *
                                 line.product_returned_quantity)

    def _get_subject(self, num):
        if num > 0 and num <= len(self.SUBJECT_LIST):
            return self.SUBJECT_LIST[num - 1][0]
        else:
            return self.SUBJECT_LIST[0][0]

    @api.model
    def _get_sequence_number(self):
        """ Return the value of the sequence for the number field in the
        claim.line model.
        """
        return self.env['ir.sequence'].next_by_code('claim.line')

    @api.model
    def create(self, vals):
        """Return write the identify number once the claim line is create.
        """
        vals = vals or {}

        if ('number' not in vals) or (vals.get('number', False) == '/'):
            vals['number'] = self._get_sequence_number()

        res = super(ClaimLine, self).create(vals)
        return res

    @api.multi
    @api.depends('claim_id.code', 'name')
    def _compute_display_name(self):
        for line_id in self:
            line_id.display_name = "%s - %s" % (
                line_id.claim_id.code, line_id.name)
