# -*- coding: utf-8 -*-

{
    'name': 'Gate Pass Management',
    'author': 'Affinity Business Suite',
    'website': 'https://affinitysuite.net',
    'support': 'info@affinitysuite.net',
    'category': 'Inventory',
    'summary': 'Manage Gate Pass In, Gate Pass Out, warehouse movements and visitor entry in Odoo',
    'description': '''
Affinity Warehouse Gate Pass Management connects gate operations with Odoo Sales,
Purchase and Inventory. Manage incoming and outgoing goods, guest and vehicle
entries, controlled warehouse workflows, searchable history and printable reports.
''',
    'version': '19.0.1.0.2',
    'depends': ['sale_stock', 'purchase'],
    'data': [
        'data/ir_sequence.xml',
        'data/report_paperformat.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'report/report_gate_in_template.xml',
        'report/report_gate_out_template.xml',
        'report/report_gate_pass_guest.xml',
        'report/ir_actions_report.xml',
        'views/gate_pass_guest_views.xml',
        'views/gate_pass_in_views.xml',
        'views/gate_pass_out_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'affinity_gate_pass/static/src/components/product_line_description/product_line_description.js',
            'affinity_gate_pass/static/src/components/product_line_description/product_line_description.xml',
        ],
    },
    'price': 15,
    'currency': 'EUR',
    'images': ['static/description/delivery_gate_pass_out.png'],
    'license': 'OPL-1',
    'application': True,
    'auto_install': False,
    'installable': True,
}
