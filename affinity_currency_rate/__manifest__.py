# -*- coding: utf-8 -*-

{
    'name': 'Affinity Currency Rate',
    'author': 'Affinity Business Suite',
    'website': 'https://affinitysuite.net',
    'support': 'info@affinitysuite.net',
    'category': 'Accounting',
    'summary': 'Transaction-specific currency rates for Affinity Withholding Tax',
    'description': '''
Technical dependency providing transaction-specific currency rates for the
Affinity Withholding Tax and Currency Rate Management application.
''',
    'version': '19.0.1.0.2',
    'depends': ['account'],
    'data': [
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'wizard/account_payment_register_views.xml',
    ],
    'assets': {},
    'images': [],
    'license': 'OPL-1',
    'application': False,
    'auto_install': False,
    'installable': True,
}
