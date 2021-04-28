# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    rma_ids = fields.One2many("rma", "procurement_group_id")

    def _get_rma_next_index(self):
        self.ensure_one()
        rma_names = sorted(self.rma_ids.mapped("name"))
        index = 1
        if rma_names:
            split_name = rma_names[-1].split("-")
            if len(split_name) > 1:
                index = int(rma_names[-1].split("-")[-1])
                index += 1
        return index
