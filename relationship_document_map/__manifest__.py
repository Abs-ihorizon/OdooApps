{
    "name": "Relationship Document Map",
    "version": "19.0.1.0.0",
    "category": "Productivity",
    "summary": "Visualize sales, purchase, inventory, invoice, payment, return, quality and manufacturing document relationships",
    "description": """
Affinity Business Suite delivers Odoo implementation, customization, training
and support services for organizations across multiple industries and regions.

Relationship Document Map provides an interactive upstream and downstream
document flow for Odoo 19. Users can trace quotations, sales orders, purchase
orders, deliveries, receipts, invoices, vendor bills, payments, returns,
quality checks and manufacturing documents from one connected visual map.
    """,
    "author": "Affinity Business Suite",
    "website": "https://affinitysuite.net",
    "support": "info@affinitysuite.net",
    "price": 65.0,
    "currency": "EUR",
    "depends": [
        "base", "web", "sale_management", "purchase", "stock", "account"
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
        "views/other_document_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "relationship_document_map/static/lib/vis-network.min.js",
            "relationship_document_map/static/src/scss/relationship_map.scss",
            "relationship_document_map/static/src/js/relationship_map.js",
            "relationship_document_map/static/src/xml/relationship_map.xml",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
