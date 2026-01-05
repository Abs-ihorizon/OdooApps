# -*- coding: utf-8 -*-

{
    'name': 'PRA Integration with POS',
    'version': '18.0',
    'summary': 'Integrates Odoo POS with Punjab Regulatory Authority (PRA) for automated sales reporting.',
    'description': '''
POS PRA Integration Module
=========================
This module integrates Odoo Point of Sale (POS) with the Punjab Regulatory Authority (PRA) in Pakistan.
It allows real-time submission of sales invoices to PRA and prints the official PRA invoice number on POS receipts.
Key Features:
- Configure PRA API URL and authentication token in POS settings.
- Automatic submission of POS invoices to PRA.
- Display PRA invoice number on POS receipts.
- Logging and error handling for failed submissions.
''',
    'author': 'Affinity Business Suite',
    'website': 'https://affinitysuite.net',
    'support': 'info@affinitysuite.net',
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'affinity_pos_pra_integration/static/src/js/pos_order.js',
            'affinity_pos_pra_integration/static/src/xml/receipt_header.xml',
        ]
    },
    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
        'static/description/cover.png'
    ],
    'license': 'OPL-1',
    'price': 100.00,
    'currency': 'EUR',
    'application': True,
    'installable': True,
    'auto_install': False,
}
