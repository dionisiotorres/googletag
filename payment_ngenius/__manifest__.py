# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Ngenius Payment Acquirer',
    'category': 'Accounting/Payment',
    'summary': 'Payment Acquirer: Ngenius Implementation',
    'description': """
    Ngenius Payment Acquirer for UEA.

    Ngenius payment gateway supports multiple currency.
    """,
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_ngenius_templates.xml',
        'views/templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook',
}
