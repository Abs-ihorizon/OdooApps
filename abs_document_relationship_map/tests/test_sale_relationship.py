# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestSaleRelationshipGraph(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleRelationshipGraph, cls).setUpClass()
        
        # Setup basic records
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
        })
        
        # Create Sales Order
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                })
            ]
        })
        cls.sale_order.action_confirm()
        
        # Get Picking (created on confirm for consu/storable if stock is installed)
        cls.picking = cls.sale_order.picking_ids[:1] if 'picking_ids' in cls.sale_order._fields else False
        
        # Create Invoice
        cls.invoice = cls.sale_order._create_invoices()
        cls.invoice.action_post()
        
        cls.graph_service = cls.env['document.relationship.graph']

    def test_01_graph_from_sale_order(self):
        """Test building graph starting from a Sales Order"""
        graph = self.graph_service.get_graph_data('sale.order', self.sale_order.id)
        
        nodes = {node['id']: node for node in graph['nodes']}
        edges = graph['edges']
        
        so_node_id = f"sale.order_{self.sale_order.id}"
        inv_node_id = f"account.move_{self.invoice.id}"
        
        self.assertIn(so_node_id, nodes)
        self.assertIn(inv_node_id, nodes)
        
        if self.picking:
            pick_node_id = f"stock.picking_{self.picking.id}"
            self.assertIn(pick_node_id, nodes)
            
            # Check edge SO -> Picking
            self.assertTrue(any(e['source'] == so_node_id and e['target'] == pick_node_id for e in edges))
            
        # Check edge SO -> Invoice
        self.assertTrue(any(e['source'] == so_node_id and e['target'] == inv_node_id for e in edges))

    def test_02_graph_from_invoice(self):
        """Test building graph starting from an Invoice (should traverse upstream to SO)"""
        graph = self.graph_service.get_graph_data('account.move', self.invoice.id)
        
        nodes = {node['id']: node for node in graph['nodes']}
        
        so_node_id = f"sale.order_{self.sale_order.id}"
        inv_node_id = f"account.move_{self.invoice.id}"
        
        # Graph should traverse upstream to find the Sale Order
        self.assertIn(so_node_id, nodes)
        self.assertIn(inv_node_id, nodes)
