/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onMounted, useRef } from "@odoo/owl";

export class RelationshipMap extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.mapContainer = useRef("mapContainer");
        
        this.state = useState({
            loading: true,
            error: null,
            empty: false,
            fullscreen: false,
            nodes: [],
            edges: [],
        });

        this.network = null;
        this.graphData = null;

        onWillStart(async () => {
            await this.fetchGraphData();
        });
        
        onMounted(() => {
            if (!this.state.loading && !this.state.error && !this.state.empty && this.graphData) {
                this.renderGraph(this.graphData);
            }
        });
    }

    async fetchGraphData() {
        const { active_model, active_id } = this.props.action.context;
        if (!active_model || !active_id) {
            this.state.error = "Missing root document context.";
            this.state.loading = false;
            return;
        }

        try {
            const data = await this.orm.call(
                "document.relationship.graph",
                "get_graph_data",
                [active_model, active_id]
            );
            if (data.nodes.length === 0) {
                this.state.empty = true;
            } else {
                this.graphData = data;
                this.state.nodes = data.nodes;
                this.state.edges = data.edges;
            }
        } catch (error) {
            this.state.error = "Error fetching graph data. " + error.message;
            console.error(error);
        } finally {
            this.state.loading = false;
        }
    }
    
    getNodeTheme(node) {
        // Status colors
        const cat = node.status_category;
        let statusColor = '#6c757d'; // default grey
        if (cat === 'completed') statusColor = '#198754'; // green
        else if (cat === 'in_progress') statusColor = '#0dcaf0'; // info/blue
        else if (cat === 'cancel') statusColor = '#dc3545'; // red
        else if (cat === 'partial') statusColor = '#ffc107'; // yellow

        // Document specific colors & icons
        let docColor = '#607d8b'; // default grey-blue
        let icon = 'fa-file-o';

        if (node.model === 'sale.order') {
            docColor = '#1976d2'; // Blue
            icon = 'fa-shopping-bag';
        } else if (node.model === 'purchase.order') {
            docColor = '#ff5722'; // Deep Orange
            icon = 'fa-shopping-cart';
        } else if (node.model === 'crm.lead') {
            docColor = '#fbc02d';
            icon = 'fa-star';
        } else if (node.model === 'stock.picking' && node.document_type === 'Delivery Order') {
            docColor = '#009688'; // Teal
            icon = 'fa-truck';
        } else if (node.model === 'stock.picking' && node.document_type === 'Receipt') {
            docColor = '#795548'; // Brown
            icon = 'fa-download';
        } else if (node.model === 'stock.picking' && (node.document_type === 'Sales Return' || node.document_type === 'Purchase Return')) {
            docColor = '#e91e63'; // Pink
            icon = 'fa-undo';
        } else if (node.model === 'account.move' && node.document_type === 'Customer Invoice') {
            docColor = '#9c27b0'; // Purple
            icon = 'fa-file-text-o';
        } else if (node.model === 'account.move' && node.document_type === 'Vendor Bill') {
            docColor = '#673ab7'; // Deep Purple
            icon = 'fa-file-text-o';
        } else if (node.model === 'account.move' && (node.document_type === 'Credit Note' || node.document_type === 'Refund')) {
            docColor = '#ff9800'; // Orange
            icon = 'fa-file-text';
        } else if (node.model === 'account.payment') {
            docColor = '#4caf50'; // Green
            icon = 'fa-money';
        } else if (node.model === 'quality.check') {
            docColor = '#8bc34a'; // Light Green
            icon = 'fa-check-square-o';
        } else if (node.model === 'quality.alert') {
            docColor = '#f44336'; // Red
            icon = 'fa-exclamation-triangle';
        } else if (node.model === 'stock.landed.cost') {
            docColor = '#795548'; // Brown
            icon = 'fa-ship';
        } else if (node.model === 'mrp.production') {
            docColor = '#607d8b'; // Blue Grey
            icon = 'fa-wrench';
        }
        
        return { docColor: docColor, statusColor: statusColor, icon: icon };
    }

    renderGraph(data) {
        if (!window.vis) {
            this.state.error = "Vis.js library failed to load.";
            return;
        }
        
        const nodes = data.nodes.map(node => {
            return {
                id: node.id,
                shape: 'box',
                label: ' ', 
                color: 'transparent',
                font: { color: 'transparent', size: 1 },
                widthConstraint: { minimum: 210, maximum: 210 },
                heightConstraint: { minimum: 95 },
                borderWidth: 0,
                shadow: false,
                odooModel: node.model,
                odooId: node.res_id
            };
        });

        const edges = data.edges.map(edge => {
            return {
                id: edge.id,
                from: edge.source,
                to: edge.target,
                label: edge.relation_type,
                arrows: 'to',
                font: { align: 'middle', size: 10, color: '#9ba4a8', background: '#f0f4f8' },
                color: { color: '#cfd8dc', highlight: '#9ba4a8' },
                smooth: { type: 'cubicBezier' }
            };
        });

        const container = this.mapContainer.el;
        const visData = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };
        const options = {
            layout: {
                hierarchical: {
                    direction: 'LR',
                    sortMethod: 'directed',
                    levelSeparation: 300,
                    nodeSpacing: 120
                }
            },
            physics: false,
            interaction: { dragNodes: true, dragView: true, zoomView: true, hover: true }
        };
        
        this.network = new vis.Network(container, visData, options);
        
        this.network.on("afterDrawing", (ctx) => {
            const positions = this.network.getPositions();
            const scale = this.network.getScale();
            for (const nodeId in positions) {
                const domPos = this.network.canvasToDOM(positions[nodeId]);
                const el = document.getElementById('node_' + nodeId);
                if (el) {
                    el.style.left = domPos.x + 'px';
                    el.style.top = domPos.y + 'px';
                    el.style.display = 'flex';
                    el.style.transform = `translate(-50%, -50%) scale(${scale})`;
                }
            }
        });
        
        this.network.on("doubleClick", (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const nodeData = nodes.find(n => n.id === nodeId);
                if (nodeData) {
                    this.openDocument({model: nodeData.odooModel, res_id: nodeData.odooId});
                }
            }
        });
        
        // Ensure cursor styling respects interactive nodes through the invisible HTML overlay
        this.network.on("hoverNode", function () {
            container.style.cursor = 'pointer';
        });
        this.network.on("blurNode", function () {
            container.style.cursor = 'default';
        });
        this.network.on("dragStart", function () {
            container.style.cursor = 'grabbing';
        });
        this.network.on("dragEnd", function () {
            container.style.cursor = 'default';
        });
    }

    openDocument(node) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: node.model,
            res_id: node.res_id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    resetView() { if (this.network) this.network.fit(); }
    toggleFullscreen() {
        this.state.fullscreen = !this.state.fullscreen;
        setTimeout(() => { if (this.network) this.network.fit(); }, 100);
    }
}

RelationshipMap.template = "abs_document_relationship_map.RelationshipMap";
registry.category("actions").add("document_relationship_map_action", RelationshipMap);
