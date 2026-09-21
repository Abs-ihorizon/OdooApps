# -*- coding: utf-8 -*-

{
    'name': 'Affinity Withholding Tax',
    'author': 'Affinity Business Suite',
    'website': 'https://affinitysuite.net',
    'support': 'info@affinitysuite.net',
    'category': 'Taxation',
    'summary': 'Affinity Withholding Tax Module',
    'description': '''Affinity Withholding Tax Module''',
    'version': '19.0.1.0.2',
    'depends': ['account', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_payment_register_views.xml',
        'views/account_payment_views.xml',
    ],
    'assets': {},
    'price': 4000000,
    'currency': 'EUR',
    'license': 'OPL-1',
    'application': False,
    'auto_install': False,
    'installable': True,
}
