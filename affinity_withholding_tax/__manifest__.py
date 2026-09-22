# -*- coding: utf-8 -*-

{
    'name': 'Affinity Withholding Tax and Currency Rate Management',
    'author': 'Affinity Business Suite',
    'website': 'https://affinitysuite.net',
    'support': 'info@affinitysuite.net',
    'category': 'Accounting/Accounting',
    'summary': 'Automate WHT, bulk payments, partial payments and currency rate management in Odoo Accounting',
    'description': '''
Affinity Withholding Tax and Currency Rate Management

Process individual, bulk and partial payments with automatic withholding tax
calculation while managing transaction-specific currency rates in Odoo
Accounting.
''',
    'version': '19.0.1.0.2',
    'depends': ['account', 'sale', 'affinity_currency_rate'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_payment_register_views.xml',
        'views/account_payment_views.xml',
    ],
    'assets': {},
    'images': ['static/description/app_dp.png'],
    'price': 122.58,
    'currency': 'EUR',
    'license': 'OPL-1',
    'application': True,
    'auto_install': False,
    'installable': True,
}
