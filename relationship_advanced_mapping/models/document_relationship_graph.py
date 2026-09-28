# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import AccessError, UserError


class DocumentRelationshipGraph(models.AbstractModel):
    _inherit = "document.relationship.graph"

    _native_models = {
        "sale.order", "purchase.order", "stock.picking", "account.move",
        "account.payment", "quality.check", "quality.alert",
        "stock.landed.cost", "mrp.production",
    }

    @api.model
    def _get_custom_config(self, model_name):
        return self.env["document.relationship.model"].search([
            ("model_name", "=", model_name),
            ("active", "=", True),
            ("enable_relationship_map", "=", True),
        ], limit=1)

    @api.model
    def get_graph_data(self, res_model, res_id):
        if not isinstance(res_model, str) or res_model not in self.env:
            raise UserError(_("Unsupported document model."))
        if res_model not in self._native_models and not self._get_custom_config(res_model):
            raise UserError(_("Relationship Map is not configured for this model."))
        return super().get_graph_data(res_model, res_id)

    @api.model
    def _field_value(self, record, field):
        return record[field.name] if field and field.name in record._fields else False

    @api.model
    def _display_value(self, value):
        if not value:
            return ""
        if hasattr(value, "display_name"):
            return value.display_name
        return str(value)

    @api.model
    def _add_node(self, record, graph):
        config = self._get_custom_config(record._name)
        if not config:
            return super()._add_node(record, graph)

        node_id = "%s_%s" % (record._name, record.id)
        if node_id in graph["nodes"]:
            return

        name_value = self._field_value(record, config.name_field_id)
        date_value = self._field_value(record, config.date_field_id)
        partner = self._field_value(record, config.partner_field_id)
        amount = self._field_value(record, config.amount_field_id) or 0.0
        currency = self._field_value(record, config.currency_field_id)
        status_value = self._field_value(record, config.status_field_id)
        technical_status = status_value.id if hasattr(status_value, "id") else status_value
        state_label = self._display_value(status_value)
        status_category = "in_progress"
        status_color = False

        if technical_status not in (False, None, ""):
            mapping = self.env["document.relationship.status.mapping"].search([
                ("model_config_id", "=", config.id),
                ("technical_value", "=", str(technical_status)),
            ], limit=1)
            if mapping:
                state_label = mapping.display_label
                status_category = mapping.status_category
                status_color = mapping.color

        graph["nodes"][node_id] = {
            "id": node_id,
            "model": record._name,
            "res_id": record.id,
            "document_type": config.document_type_label,
            "name": self._display_value(name_value),
            "date": str(date_value) if date_value else "",
            "partner_name": partner.display_name if partner else "",
            "partner_id": partner.id if partner else False,
            "state": str(technical_status or ""),
            "state_label": state_label,
            "status_category": status_category,
            "status_color": status_color or "",
            "amount": amount,
            "currency": currency.name if currency else "",
            "node_color": config.default_color or "",
            "icon": config.icon or "fa-file-o",
        }

    @api.model
    def _records_user_can_read(self, records):
        readable = self.env[records._name].browse()
        for record in records.exists():
            try:
                record.check_access_rights("read")
                record.check_access_rule("read")
                readable |= record
            except AccessError:
                continue
        return readable

    @api.model
    def _related_pairs(self, rule, current_record):
        source_model = rule.source_model_config_id.model_name
        target_model = rule.target_model_config_id.model_name
        field = rule.relationship_field_id
        pairs = []

        if rule.field_owner == "source":
            if current_record._name == source_model:
                targets = self._records_user_can_read(current_record[field.name])
                pairs.extend((current_record, target) for target in targets)
            elif current_record._name == target_model:
                sources = self.env[source_model].search([(field.name, "in", [current_record.id])])
                sources = self._records_user_can_read(sources)
                pairs.extend((source, current_record) for source in sources)
        else:
            if current_record._name == target_model:
                sources = self._records_user_can_read(current_record[field.name])
                pairs.extend((source, current_record) for source in sources)
            elif current_record._name == source_model:
                targets = self.env[target_model].search([(field.name, "in", [current_record.id])])
                targets = self._records_user_can_read(targets)
                pairs.extend((current_record, target) for target in targets)
        return pairs

    @api.model
    def _explore_relations(self, record, graph):
        super()._explore_relations(record, graph)
        config = self._get_custom_config(record._name)
        if not config:
            return

        rules = self.env["document.relationship.rule"].search([
            ("active", "=", True),
            "|",
            ("source_model_config_id", "=", config.id),
            ("target_model_config_id", "=", config.id),
        ])
        for rule in rules:
            for source, target in self._related_pairs(rule, record):
                if rule.direction == "target_to_source":
                    edge_source, edge_target = target, source
                else:
                    edge_source, edge_target = source, target
                self._add_edge(
                    edge_source._name, edge_source.id,
                    edge_target._name, edge_target.id,
                    rule.edge_label or rule.relationship_code,
                    graph,
                )
                opposite = target if record._name == source._name and record.id == source.id else source
                opposite_key = "%s_%s" % (opposite._name, opposite.id)
                if opposite_key not in graph["processed"]:
                    graph["queue"].append((opposite._name, opposite.id))
