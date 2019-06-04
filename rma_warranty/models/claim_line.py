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
from odoo.tools import (DEFAULT_SERVER_DATE_FORMAT,
                        DEFAULT_SERVER_DATETIME_FORMAT)

from .invoice_no_date import InvoiceNoDate
from .product_no_supplier import ProductNoSupplier


class ClaimLine(models.Model):
    _inherit = "claim.line"

    WARRANT_COMMENT = [
        ('valid', _("Valid")),
        ('expired', _("Expired")),
        ('not_define', _("Not Defined"))]

    @api.model
    def get_warranty_return_partner(self):
        return self.env['product.supplierinfo'].fields_get(
            'warranty_return_partner')['warranty_return_partner']['selection']


    applicable_guarantee = fields.Selection([('us', 'Company'),
                                             ('supplier', 'Supplier'),
                                             ('brand', 'Brand manufacturer')],
                                            'Warranty type')
    guarantee_limit = fields.Date('Warranty limit', readonly=True,
                                  help="The warranty limit is "
                                       "computed as: invoice date + warranty "
                                       "defined on selected product.")
    warning = fields.Selection(WARRANT_COMMENT,
                               'Warranty', readonly=True,
                               help="If warranty has expired")
    warranty_type = fields.Selection(
        get_warranty_return_partner,
        help="Who is in charge of the warranty return treatment towards "
        "the end customer. Company will use the current company "
        "delivery or default address and so on for supplier and brand "
        "manufacturer. Does not necessarily mean that the warranty "
        "to be applied is the one of the return partner (ie: can be "
        "returned to the company and be under the brand warranty")
    warranty_return_partner = fields.Many2one('res.partner',
                                              string='Warranty Address',
                                              help="Where the customer has to "
                                                   "send back the product(s)")

    @staticmethod
    def warranty_limit(start, warranty_duration):
        """ Take a duration in float, return the duration in relativedelta

        ``relative_delta(months=...)`` only accepts integers.
        We have to extract the decimal part, and then, extend the delta with
        days.

        """
        decimal_part, months = math.modf(warranty_duration)
        months = int(months)
        # If we have a decimal part, we add the number them as days to
        # the limit.  We need to get the month to know the number of
        # days.
        delta = relativedelta(months=months)
        monthday = start + delta
        __, days_month = calendar.monthrange(monthday.year, monthday.month)
        # ignore the rest of the days (hours) since we expect a date
        days = int(days_month * decimal_part)
        return start + relativedelta(months=months, days=days)

    def _warranty_limit_values(self, invoice, claim_type, product, claim_date):
        if not (invoice and claim_type and product and claim_date):
            return {'guarantee_limit': False, 'warning': False}

        invoice_date = invoice.create_date
        if not invoice_date:
            raise InvoiceNoDate

        warning = 'not_define'
        invoice_date = datetime.strptime(invoice_date,
                                         DEFAULT_SERVER_DATETIME_FORMAT)

        if isinstance(claim_type, self.env['crm.claim.type'].__class__):
            claim_type = claim_type.id

        if claim_type == self.env.ref('crm_claim_type.'
                                      'crm_claim_type_supplier').id:
            try:
                warranty_duration = product.seller_ids[0].warranty_duration
            except IndexError:
                raise ProductNoSupplier
        else:
            warranty_duration = product.warranty

        limit = self.warranty_limit(invoice_date, warranty_duration)
        if warranty_duration > 0:
            claim_date = datetime.strptime(claim_date,
                                           DEFAULT_SERVER_DATETIME_FORMAT)
            if limit < claim_date:
                warning = 'expired'
            else:
                warning = 'valid'

        return {'guarantee_limit': limit.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'warning': warning}

    def set_warranty_limit(self):

        self.ensure_one()

        claim = self.claim_id
        invoice_id = self.invoice_line_id and self.invoice_line_id.invoice_id \
            or claim.invoice_id
        try:
            values = self._warranty_limit_values(
                invoice_id, claim.claim_type,
                self.product_id, claim.date)
        except InvoiceNoDate:
            raise exceptions.UserError(
                _('Cannot find any date for invoice. '
                  'Must be a validated invoice.')
            )
        except ProductNoSupplier:
            raise exceptions.UserError(
                _('The product has no supplier configured.')
            )

        self.write(values)
        return True

    @api.model
    def auto_set_warranty(self):
        """ Set warranty automatically
        if the user has not himself pressed on 'Calculate warranty state'
        button, it sets warranty for him"""
        for line in self:
            if not line.warning:
                line.set_warranty()
        return True

    def _warranty_return_address_values(self, product, company, warehouse):
        """ Return the partner to be used as return destination and
        the destination stock location of the line in case of return.

        We can have various cases here:
            - company or other: return to company partner or
              crm_return_address_id if specified
            - supplier: return to the supplier address
        """
        if not (product and company and warehouse):
            return {
                'warranty_return_partner': False,
                'warranty_type': False,
                'location_dest_id': False
            }
        sellers = product.seller_ids
        if sellers:
            seller = sellers[0]
            return_address_id = seller.warranty_return_address.id
            return_type = seller.warranty_return_partner
        else:
            # when no supplier is configured, returns to the company
            return_address = (company.crm_return_address_id or
                              company.partner_id)
            return_address_id = return_address.id
            return_type = 'company'
        location_dest = self.get_destination_location(warehouse, product=product)
        return {
            'warranty_return_partner': return_address_id,
            'warranty_type': return_type,
            'location_dest_id': location_dest.id
        }

    def set_warranty_return_address(self):
        self.ensure_one()
        claim = self.claim_id
        values = self._warranty_return_address_values(
            self.product_id, claim.company_id, claim.warehouse_id)
        self.write(values)
        return True

    @api.multi
    def set_warranty(self):
        """ Calculate warranty limit and address
        """
        for line_id in self:
            if not line_id.product_id:
                raise exceptions.UserError(_('Please set product first'))

            if not line_id.invoice_line_id:
                raise exceptions.UserError(_('Please set invoice first'))

            line_id.set_warranty_limit()
            line_id.set_warranty_return_address()

    @api.returns('stock.location')
    def get_destination_location(self, warehouse, product=None):
        """ Compute and return the destination location to take
        for a return. Always take 'Supplier' one when return type different
        from company.
        """
        location_dest = super(ClaimLine, self).get_destination_location(
            warehouse, product=product)

        if product and product.seller_ids:
            seller = product.seller_ids[0]
            if seller.warranty_return_partner != 'company' \
                    and seller.name and \
                    seller.name.property_stock_supplier:
                location_dest = seller.name.property_stock_supplier

        return location_dest
