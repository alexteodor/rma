# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2016 Cyril Gaudin (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    rma_out_route_id = fields.Many2one(
        comodel_name="stock.location.route", string="RMA delivery route")
