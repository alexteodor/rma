# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models

from .invoice_no_date import InvoiceNoDate
from .product_no_supplier import ProductNoSupplier


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    @api.model
    def warranty_values(invoice, product):
        return values

    @api.model
    def _prepare_claim_line(self, invoice_line, warehouse):
        vals = super(CrmClaim, self)._prepare_claim_line(
            invoice_line, warehouse)
        claim_line = self.env['claim.line']
        claim_type = self.claim_type
        claim_date = self.date
        company = self.company_id
        warranty_values = {}
        try:
            warranty = claim_line._warranty_limit_values(
                invoice_line.invoice_id, claim_type, invoice_line.product_id,
                claim_date)
        except (InvoiceNoDate, ProductNoSupplier):
            # we don't mind at this point if the warranty can't be
            # computed and we don't want to block the user
            warranty_values.update({'guarantee_limit': False, 'warning': False})
        else:
            warranty_values.update(warranty)

        warranty_address = claim_line._warranty_return_address_values(
            invoice_line.product_id, company, warehouse)
        warranty_values.update(warranty_address)
        vals.update(warranty_values)
        return vals
