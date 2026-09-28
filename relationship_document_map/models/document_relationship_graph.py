# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessError

class DocumentRelationshipGraph(models.AbstractModel):
    _name = 'document.relationship.graph'
    _description = 'Document Relationship Graph Service'

    @api.model
    def get_graph_data(self, res_model, res_id):
        graph = {
            'nodes': {},
            'edges': set(),
            'processed': set(),
            'queue': [(res_model, res_id)]
        }
        
        while graph['queue']:
            curr_model, curr_id = graph['queue'].pop(0)
            node_key = f"{curr_model}_{curr_id}"
            
            if node_key in graph['processed']:
                continue
            graph['processed'].add(node_key)
            
            record = self.env[curr_model].browse(curr_id)
            if not record.exists():
                continue
                
            try:
                record.check_access_rights('read')
                record.check_access_rule('read')
            except AccessError:
                continue
                
            self._add_node(record, graph)
            self._explore_relations(record, graph)
            
        formatted_edges = []
        node_ids = set(graph['nodes'].keys())
        for src, tgt, rel in graph['edges']:
            if src != tgt and src in node_ids and tgt in node_ids:
                formatted_edges.append({
                    "id": f"{src}_to_{tgt}_{rel}",
                    "source": src,
                    "target": tgt,
                    "relation_type": rel
                })
                
        return {
            "root_id": f"{res_model}_{res_id}",
            "nodes": list(graph['nodes'].values()),
            "edges": formatted_edges,
        }

    @api.model
    def _add_node(self, record, graph):
        node_id = f"{record._name}_{record.id}"
        if node_id in graph['nodes']:
            return
            
        doc_type, name_field, date_field, amount_field = self._get_node_metadata(record)
        
        state = record.state if 'state' in record._fields else ''
        status_cat = self._get_status_category(record)
        
        state_label = state
        if state and 'state' in record._fields and hasattr(record._fields['state'], '_description_selection'):
            selection = dict(record._fields['state']._description_selection(record.env))
            state_label = selection.get(state, state)

        partner = getattr(record, 'partner_id', False) if 'partner_id' in record._fields else False
        currency = getattr(record, 'currency_id', False) if 'currency_id' in record._fields else False
        
        graph['nodes'][node_id] = {
            "id": node_id,
            "model": record._name,
            "res_id": record.id,
            "document_type": doc_type,
            "name": getattr(record, name_field, '') if name_field and name_field in record._fields else '',
            "date": str(getattr(record, date_field, '')) if date_field and date_field in record._fields and getattr(record, date_field, False) else '',
            "partner_name": partner.name if partner else '',
            "partner_id": partner.id if partner else False,
            "state": state,
            "state_label": state_label,
            "status_category": status_cat,
            "amount": getattr(record, amount_field, 0.0) if amount_field and amount_field in record._fields else 0.0,
            "currency": currency.name if currency else ''
        }

    @api.model
    def _get_node_metadata(self, record):
        if record._name == 'sale.order':
            return 'Sales Order', 'name', 'date_order', 'amount_total'
        elif record._name == 'purchase.order':
            return 'Purchase Order', 'name', 'date_approve', 'amount_total'
        elif record._name == 'stock.picking':
            is_return = False
            if 'move_ids' in record._fields:
                is_return = any(m.origin_returned_move_id for m in record.move_ids if 'origin_returned_move_id' in m._fields)
            doc_type = 'Transfer'
            if 'picking_type_id' in record._fields and record.picking_type_id:
                code = record.picking_type_id.code
                if code == 'outgoing':
                    doc_type = 'Sales Return' if is_return else 'Delivery Order'
                elif code == 'incoming':
                    doc_type = 'Purchase Return' if is_return else 'Receipt'
            return doc_type, 'name', 'scheduled_date', None
        elif record._name == 'account.move':
            doc_type = 'Customer Invoice'
            if 'move_type' in record._fields:
                if record.move_type == 'out_refund':
                    doc_type = 'Credit Note'
                elif record.move_type == 'in_invoice':
                    doc_type = 'Vendor Bill'
                elif record.move_type == 'in_refund':
                    doc_type = 'Refund'
            return doc_type, 'name', 'invoice_date', 'amount_total'
        elif record._name == 'account.payment':
            doc_type = 'Customer Payment'
            if 'payment_type' in record._fields and record.payment_type == 'outbound':
                doc_type = 'Vendor Payment'
            return doc_type, 'name', 'date', 'amount'
        elif record._name == 'quality.check':
            return 'Quality Check', 'name', 'control_date', None
        elif record._name == 'quality.alert':
            return 'Quality Alert', 'name', 'date_assign', None
        elif record._name == 'stock.landed.cost':
            return 'Landed Cost', 'name', 'date', 'amount_total'
        elif record._name == 'mrp.production':
            return 'Manufacturing Order', 'name', 'date_planned_start', None
        return 'Document', 'name', 'create_date', None

    @api.model
    def _add_edge(self, src_model, src_id, tgt_model, tgt_id, relation_type, graph):
        src_key = f"{src_model}_{src_id}"
        tgt_key = f"{tgt_model}_{tgt_id}"
        graph['edges'].add((src_key, tgt_key, relation_type))

    @api.model
    def _get_status_category(self, record):
        if 'state' not in record._fields:
            return 'in_progress'
        state = record.state
        if state in ('draft', 'cancel'):
            return state
        if state == 'done':
            return 'completed'
        if record._name == 'account.move' and 'payment_state' in record._fields:
            if record.payment_state in ('paid', 'in_payment', 'reversed'):
                return 'completed'
            if record.payment_state == 'partial':
                return 'partial'
        if record._name == 'purchase.order' and state == 'purchase':
            return 'completed'
        if record._name == 'quality.check':
            if getattr(record, 'quality_state', '') == 'pass':
                return 'completed'
            elif getattr(record, 'quality_state', '') == 'fail':
                return 'cancel'
        if record._name == 'mrp.production':
            if state == 'done':
                return 'completed'
            if state == 'cancel':
                return 'cancel'
        return 'in_progress'

    @api.model
    def _explore_relations(self, record, graph):
        if record._name == 'sale.order':
            if 'picking_ids' in record._fields:
                for picking in record.picking_ids:
                    self._add_edge('sale.order', record.id, 'stock.picking', picking.id, 'delivery', graph)
                    graph['queue'].append(('stock.picking', picking.id))
            if 'invoice_ids' in record._fields:
                for invoice in record.invoice_ids:
                    self._add_edge('sale.order', record.id, 'account.move', invoice.id, 'invoice', graph)
                    graph['queue'].append(('account.move', invoice.id))
                    
            # Link Purchase Orders (MTO / Dropship)
            pos = self.env['purchase.order'].browse()
            if 'purchase.order' in self.env and record.name:
                po_fields = self.env['purchase.order']._fields
                if 'origin' in po_fields:
                    pos = self.env['purchase.order'].search([('origin', 'ilike', record.name)])
            
            for po in pos:
                self._add_edge('sale.order', record.id, 'purchase.order', po.id, 'purchase', graph)
                graph['queue'].append(('purchase.order', po.id))

            # Link Manufacturing Orders (MTO)
            mrps = self.env['mrp.production'].browse()
            if 'mrp.production' in self.env and record.name:
                mrp_fields = self.env['mrp.production']._fields
                domain = []
                if 'origin' in mrp_fields:
                    domain.append(('origin', 'ilike', record.name))
                if 'procurement_group_id' in record._fields and record.procurement_group_id and 'procurement_group_id' in mrp_fields:
                    if domain:
                        domain = ['|'] + domain + [('procurement_group_id', '=', record.procurement_group_id.id)]
                    else:
                        domain = [('procurement_group_id', '=', record.procurement_group_id.id)]
                if domain:
                    mrps = self.env['mrp.production'].search(domain)
                
            for mrp in mrps:
                self._add_edge('sale.order', record.id, 'mrp.production', mrp.id, 'manufacturing', graph)
                graph['queue'].append(('mrp.production', mrp.id))

        elif record._name == 'purchase.order':
            if 'picking_ids' in record._fields:
                for picking in record.picking_ids:
                    self._add_edge('purchase.order', record.id, 'stock.picking', picking.id, 'receipt', graph)
                    graph['queue'].append(('stock.picking', picking.id))
            if 'invoice_ids' in record._fields:
                for invoice in record.invoice_ids:
                    self._add_edge('purchase.order', record.id, 'account.move', invoice.id, 'bill', graph)
                    graph['queue'].append(('account.move', invoice.id))
                    
            # Reverse link to Sale Order
            if 'origin' in record._fields and record.origin:
                sos = self.env['sale.order'].search([('name', '=', record.origin)])
                for so in sos:
                    self._add_edge('sale.order', so.id, 'purchase.order', record.id, 'purchase', graph)
                    graph['queue'].append(('sale.order', so.id))

        elif record._name == 'stock.picking':
            if 'sale_id' in record._fields and record.sale_id:
                self._add_edge('sale.order', record.sale_id.id, 'stock.picking', record.id, 'delivery', graph)
                graph['queue'].append(('sale.order', record.sale_id.id))
                
            if 'purchase_id' in record._fields and record.purchase_id:
                self._add_edge('purchase.order', record.purchase_id.id, 'stock.picking', record.id, 'receipt', graph)
                graph['queue'].append(('purchase.order', record.purchase_id.id))
                
            if 'backorder_id' in record._fields and record.backorder_id:
                self._add_edge('stock.picking', record.backorder_id.id, 'stock.picking', record.id, 'backorder', graph)
                graph['queue'].append(('stock.picking', record.backorder_id.id))
                
            backorders = self.env['stock.picking'].search([('backorder_id', '=', record.id)])
            for backorder in backorders:
                self._add_edge('stock.picking', record.id, 'stock.picking', backorder.id, 'backorder', graph)
                graph['queue'].append(('stock.picking', backorder.id))
                
            if 'move_ids' in record._fields:
                for move in record.move_ids:
                    if 'origin_returned_move_id' in move._fields and move.origin_returned_move_id.picking_id:
                        orig_picking = move.origin_returned_move_id.picking_id
                        self._add_edge('stock.picking', orig_picking.id, 'stock.picking', record.id, 'return', graph)
                        graph['queue'].append(('stock.picking', orig_picking.id))
                    if 'returned_move_ids' in move._fields:
                        for ret_move in move.returned_move_ids:
                            if ret_move.picking_id:
                                self._add_edge('stock.picking', record.id, 'stock.picking', ret_move.picking_id.id, 'return', graph)
                                graph['queue'].append(('stock.picking', ret_move.picking_id.id))

            if 'quality.check' in self.env:
                qc_fields = self.env['quality.check']._fields
                if 'picking_id' in qc_fields:
                    checks = self.env['quality.check'].search([('picking_id', '=', record.id)])
                    for check in checks:
                        self._add_edge('stock.picking', record.id, 'quality.check', check.id, 'quality check', graph)
                        graph['queue'].append(('quality.check', check.id))
                    
            if 'quality.alert' in self.env:
                qa_fields = self.env['quality.alert']._fields
                if 'picking_id' in qa_fields:
                    alerts = self.env['quality.alert'].search([('picking_id', '=', record.id)])
                    for alert in alerts:
                        self._add_edge('stock.picking', record.id, 'quality.alert', alert.id, 'quality alert', graph)
                        graph['queue'].append(('quality.alert', alert.id))
                    
            if 'stock.landed.cost' in self.env:
                lc_fields = self.env['stock.landed.cost']._fields
                if 'picking_ids' in lc_fields:
                    landed_costs = self.env['stock.landed.cost'].search([('picking_ids', 'in', record.id)])
                    for lc in landed_costs:
                        self._add_edge('stock.picking', record.id, 'stock.landed.cost', lc.id, 'landed cost', graph)
                        graph['queue'].append(('stock.landed.cost', lc.id))
                    
        elif record._name == 'mrp.production':
            if 'sale_order_id' in record._fields and record.sale_order_id:
                self._add_edge('sale.order', record.sale_order_id.id, 'mrp.production', record.id, 'manufacturing', graph)
                graph['queue'].append(('sale.order', record.sale_order_id.id))
            elif 'origin' in record._fields and record.origin:
                sos = self.env['sale.order'].search([('name', '=', record.origin)])
                for so in sos:
                    self._add_edge('sale.order', so.id, 'mrp.production', record.id, 'manufacturing', graph)
                    graph['queue'].append(('sale.order', so.id))
                    
            if 'picking_ids' in record._fields:
                for picking in record.picking_ids:
                    self._add_edge('mrp.production', record.id, 'stock.picking', picking.id, 'transfer', graph)
                    graph['queue'].append(('stock.picking', picking.id))

        elif record._name == 'quality.check':
            if 'picking_id' in record._fields and record.picking_id:
                self._add_edge('stock.picking', record.picking_id.id, 'quality.check', record.id, 'quality check', graph)
                graph['queue'].append(('stock.picking', record.picking_id.id))

        elif record._name == 'quality.alert':
            if 'picking_id' in record._fields and record.picking_id:
                self._add_edge('stock.picking', record.picking_id.id, 'quality.alert', record.id, 'quality alert', graph)
                graph['queue'].append(('stock.picking', record.picking_id.id))
                
        elif record._name == 'stock.landed.cost':
            if 'picking_ids' in record._fields:
                for picking in record.picking_ids:
                    self._add_edge('stock.picking', picking.id, 'stock.landed.cost', record.id, 'landed cost', graph)
                    graph['queue'].append(('stock.picking', picking.id))
            if 'vendor_bill_id' in record._fields and record.vendor_bill_id:
                self._add_edge('account.move', record.vendor_bill_id.id, 'stock.landed.cost', record.id, 'vendor bill', graph)
                graph['queue'].append(('account.move', record.vendor_bill_id.id))
            if 'account_move_id' in record._fields and record.account_move_id:
                self._add_edge('stock.landed.cost', record.id, 'account.move', record.account_move_id.id, 'valuation entry', graph)
                graph['queue'].append(('account.move', record.account_move_id.id))

        elif record._name == 'account.move':
            if 'line_ids' in record._fields:
                for line in record.line_ids:
                    if 'sale_line_ids' in line._fields:
                        for sale_line in line.sale_line_ids:
                            if sale_line.order_id:
                                self._add_edge('sale.order', sale_line.order_id.id, 'account.move', record.id, 'invoice', graph)
                                graph['queue'].append(('sale.order', sale_line.order_id.id))
                    if 'purchase_line_id' in line._fields and line.purchase_line_id and line.purchase_line_id.order_id:
                        self._add_edge('purchase.order', line.purchase_line_id.order_id.id, 'account.move', record.id, 'bill', graph)
                        graph['queue'].append(('purchase.order', line.purchase_line_id.order_id.id))
                                
            if 'reversed_entry_id' in record._fields and record.reversed_entry_id:
                self._add_edge('account.move', record.reversed_entry_id.id, 'account.move', record.id, 'credit_note', graph)
                graph['queue'].append(('account.move', record.reversed_entry_id.id))
                
            reversals = self.env['account.move'].search([('reversed_entry_id', '=', record.id)])
            for rev in reversals:
                self._add_edge('account.move', record.id, 'account.move', rev.id, 'credit_note', graph)
                graph['queue'].append(('account.move', rev.id))
            
            if hasattr(record, '_get_reconciled_payments'):
                payments = record._get_reconciled_payments()
                for payment in payments:
                    self._add_edge('account.move', record.id, 'account.payment', payment.id, 'payment', graph)
                    graph['queue'].append(('account.payment', payment.id))
                    
            if 'stock.landed.cost' in self.env:
                lc_fields = self.env['stock.landed.cost']._fields
                if 'vendor_bill_id' in lc_fields:
                    lc_bills = self.env['stock.landed.cost'].search([('vendor_bill_id', '=', record.id)])
                    for lc in lc_bills:
                        self._add_edge('account.move', record.id, 'stock.landed.cost', lc.id, 'landed cost', graph)
                        graph['queue'].append(('stock.landed.cost', lc.id))
                if 'account_move_id' in lc_fields:
                    lc_entries = self.env['stock.landed.cost'].search([('account_move_id', '=', record.id)])
                    for lc in lc_entries:
                        self._add_edge('stock.landed.cost', lc.id, 'account.move', record.id, 'valuation entry', graph)
                        graph['queue'].append(('stock.landed.cost', lc.id))

        elif record._name == 'account.payment':
            if 'reconciled_invoice_ids' in record._fields:
                for inv in record.reconciled_invoice_ids:
                    self._add_edge('account.move', inv.id, 'account.payment', record.id, 'payment', graph)
                    graph['queue'].append(('account.move', inv.id))
