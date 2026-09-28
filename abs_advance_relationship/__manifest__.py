{
    "name": "Relationship Advanced Mapping",
    "version": "19.0.1.2.0",
    "category": "Productivity",
    "summary": "Connect custom Odoo models with configurable relationships, smart buttons, status colors and document maps",
    "description": """
Affinity Business Suite delivers Odoo implementation, customization, training
and support services for organizations across multiple industries and regions.

Relationship Advanced Mapping extends Relationship Document Map with secure,
configuration-driven custom model mapping. Administrators can register custom
documents, connect them through real Many2one, One2many or Many2many fields,
configure status labels and generate Actions menu entries or form smart buttons.
    """,
    "author": "Affinity Business Suite",
    "website": "https://affinitysuite.net",
    "support": "info@affinitysuite.net",
    "price": 65.0,
    "currency": "EUR",
    "depends": ["abs_document_relationship_map"],
    "data": [
        "security/ir.model.access.csv",
        "views/document_relationship_model_views.xml",
        "views/document_relationship_rule_views.xml",
        "views/document_relationship_status_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "abs_advance_relationship/static/src/js/relationship_map_patch.js",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
