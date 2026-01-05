# -- coding: utf-8 --

{
    'name': 'Bank Reconciliation',
    'author': 'Affinity Business Suite',
    'website': 'https://affinitysuite.net',
    'support': 'info@affinitysuite.net',
    'category': 'Accounting',
    'summary': 'Replace default bank statement reconciliation with a manual traditional method',
    'description': '''This module replaces the default Odoo bank statement reconciliation with a manual approach. Users can reconcile statements line by line by entering dates and verifying balances as per company books and bank.''',
    'version': '18.0',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'report/brs_report_template.xml',
        'report/ir_actions_report.xml',
        'wizard/bank_statement_views.xml',
        'wizard/brs_report_wizard_views.xml',
        'views/account_journal_views.xml',
        'views/account_move_line_views.xml',
        'views/account_move_views.xml',
    ],
    'assets': {},
    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
        'static/description/cover.png'
    ],
    'price': 65,
    'currency': 'EUR',
    'license': 'OPL-1',
    'application': True,
    'auto_install': False,
    'installable': True,
}
