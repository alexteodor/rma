# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Vauxoo
# © 2015 Eezee-It
# © 2009-2013 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'RMA Delivery',
    'version': '10.0.1.0.0',
    'category': 'Generic Modules/CRM & SRM',
    'author': "Akretion, Camptocamp, Eezee-it, MONK Software, Vauxoo, "
              "Techspawn Solutions, "
              "Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com, http://www.camptocamp.com, '
               'http://www.eezee-it.com, http://www.wearemonk.com, '
               'http://www.vauxoo.com',
    'license': 'AGPL-3',
    'depends': [
        'rma',
    ],
    'data': [
        "wizards/claim_make_picking.xml",
        'views/crm_claim.xml',
        "views/claim_line.xml",
    ],
    'installable': True,
    'auto_install': False,
}
