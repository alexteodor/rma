# -*- coding: utf-8 -*-
# Copyright 2019 Benoît GUILLOT <benoit.guillot@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class CrmClaimCategory(models.Model):
    _inherit = "crm.claim.category"

    has_product = fields.Boolean(
        string="Has product",
        help="The claims linked to this category manage products")
