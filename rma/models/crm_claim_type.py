# -*- coding: utf-8 -*-
# Copyright 2019 Benoît GUILLOT <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CrmClaimType(models.Model):
    _inherit = 'crm.claim.type'

    origin_type = fields.Selection(
        selection=[('customer', 'Customer'), ('supplier', 'Supplier')],
        string="Type")
