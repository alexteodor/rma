# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class Rma(models.Model):
    _inherit = "rma"

    procurement_group_id = fields.Many2one(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.constrains("procurement_group_id", "partner_shipping_id", "partner_id")
    def check_partner_procurement_group(self):
        for rma in self:
            group = rma.procurement_group_id
            if not group:
                continue
            delivery_address = rma.partner_shipping_id or rma.partner_id
            if group.partner_id != delivery_address:
                raise exceptions.ValidationError(
                    _(
                        "The chosen procurement group is not consistent with the "
                        "partner or shipping address of the rma on %s" % rma.name
                    )
                )

    def _get_available_state_for_rma_grouping(self):
        return [
            "draft",
        ]

    def _get_group_rma_domain(self, vals):
        states = self._get_available_state_for_rma_grouping()
        return [
            ("partner_id", "=", vals.get("partner_id")),
            ("partner_shipping_id", "=", vals.get("partner_shipping_id")),
            ("state", "in", states),
            ("procurement_group_id", "!=", False),
        ]

    def _get_existing_group(self, vals):
        rma = self.search(self._get_group_rma_domain(vals), limit=1)
        return rma.procurement_group_id

    def update_rma_name(self, vals):
        if vals.get("name", _("New")) != _("New"):
            return super().update_rma_name(vals)
        group_id = vals.get("procurement_group_id")
        if group_id:
            group = self.env["procurement.group"].browse(group_id)
            index = group._get_rma_next_index()
            name = group.name
        else:
            index = 1
            vals = super().update_rma_name(vals)
            name = vals.get("name")
        vals["name"] = "{name}-{index}".format(name=name, index=index)
        return vals

    def _get_procurement_group_vals(self):
        vals = super()._get_procurement_group_vals()
        # remove index from group name, since we create it from rma name where we
        # add index during create
        name = vals["name"]
        splitted_name = name.split("-")
        if len(splitted_name) > 1:
            name = "-".join(splitted_name[:-1])
        vals["name"] = name
        return vals

    @api.model
    def create(self, vals):
        # we avoid create_multi because we have to create rma one by one
        # to be able to check if it have to be grouped. Else, in case we create multiple
        # rma at once, it would never be grouped
        if not vals.get("procurement_group_id") and vals.get("partner_id"):
            group = self._get_existing_group(vals)
            vals["procurement_group_id"] = group.id
            vals = self.update_rma_name(vals)
        rma = super().create(vals)
        # create procurement group if not group (so the rma can be grouped)
        if not rma.procurement_group_id:
            group = self.env["procurement.group"].create(
                rma._get_procurement_group_vals()
            )
            rma.write({"procurement_group_id": group.id})
        return rma
