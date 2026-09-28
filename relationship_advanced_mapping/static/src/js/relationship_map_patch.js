/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { RelationshipMap } from "@relationship_document_map/js/relationship_map";

patch(RelationshipMap.prototype, {
    getNodeTheme(node) {
        const theme = super.getNodeTheme(node);
        return {
            docColor: node.node_color || theme.docColor,
            statusColor: node.status_color || theme.statusColor,
            icon: node.icon || theme.icon,
        };
    },
});
